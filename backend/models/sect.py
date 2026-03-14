import os
import json
from datetime import datetime
from pathing import data_path, PROJECT_ROOT
from save_manager import save_manager

DATA_DIR = str(data_path())

SECT_STRUCTURE = {
    "name": "OpenClaw 本源门",
    "roles": ["宗主", "首座", "长老", "真传", "内门", "外门", "客卿"],
    "divisions": {
        "观潮堂": {"desc": "搜索、调研、游历", "assigned": []},
        "筑文堂": {"desc": "写作、总结、清稿", "assigned": []},
        "炼器堂": {"desc": "搭建、脚本、前端、工具链", "assigned": []},
        "镇魔堂": {"desc": "安全、风控、审查", "assigned": []},
        "养识堂": {"desc": "记忆、自我改进、学习", "assigned": []},
        "司命堂": {"desc": "提醒、调度、日程、通知", "assigned": []}
    },
    "skills": [],
    "order": 100,
    "last_dispatch": None,
    "subagents": []
}

def sync_skills_to_sect():
    # 真实扫描技能目录，并自动分配到对应的堂口或者法器库
    try:
        skill_dir = PROJECT_ROOT.parent.parent / 'skills'
        skills = []
        if skill_dir.exists():
            skills = sorted([d.name for d in skill_dir.iterdir() if d.is_dir()])
        return skills
    except:
        return []

def load_sect_data():
    try:
        with open(f"{DATA_DIR}/sect_roster.json", "r") as f:
            data = json.load(f)
            # Ensure new division sync
            if "divisions" not in data:
                data["divisions"] = SECT_STRUCTURE["divisions"]
            if "order" not in data:
                data["order"] = 100
            if "last_dispatch" not in data:
                data["last_dispatch"] = None
            if "subagents" not in data:
                data["subagents"] = []
            return data
    except:
        base = json.loads(json.dumps(SECT_STRUCTURE, ensure_ascii=False))
        base["skills"] = sync_skills_to_sect()
        return base

def save_sect_data(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(f"{DATA_DIR}/sect_roster.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    save_manager.record_sect_snapshot(data)
    return data

def assign_avatar(hall_name, avatar_id, session_key=None, task=None):
    """派化身去某个堂口（真实 subagent 指派）"""
    data = load_sect_data()
    if hall_name in data["divisions"]:
        if avatar_id not in data["divisions"][hall_name]["assigned"]:
            data["divisions"][hall_name]["assigned"].append(avatar_id)
        total_avatars = sum(len(info.get("assigned", [])) for info in data["divisions"].values())
        data["order"] = max(35, 100 - total_avatars * 6)
        dispatch = {
            "hall": hall_name,
            "avatar_id": avatar_id,
            "session_key": session_key,
            "task": task,
            "ts": datetime.utcnow().isoformat(timespec='seconds') + 'Z'
        }
        data["last_dispatch"] = dispatch
        subagents = data.get('subagents', [])
        subagents.append(dispatch)
        data['subagents'] = subagents[-24:]
        save_sect_data(data)
        return True
    return False

def check_sect_order():
    """宗门秩序度：管理的化身越多越容易混乱。如果超过境界承载力，秩序下降"""
    data = load_sect_data()
    total_avatars = sum(len(info.get("assigned", [])) for info in data.get("divisions", {}).values())
    return max(35, 100 - total_avatars * 6)
