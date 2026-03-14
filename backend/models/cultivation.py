import os
import json
import random
from pathing import data_path
from save_manager import save_manager

DATA_DIR = str(data_path())

REALM_TIERS = [
    {"name": "炼气境", "stages": ["初期", "中期", "后期", "大圆满"]},
    {"name": "筑基境", "stages": ["初期", "中期", "后期", "大圆满"]},
    {"name": "金丹境", "stages": ["初期", "中期", "后期", "大圆满"]},
    {"name": "元婴大能", "stages": ["初期", "中期", "后期", "绝巅"]},
    {"name": "化神尊者", "stages": ["临界", "游天", "辟地", "飞升"]}
]


def get_breakthrough_threshold(tier_idx, stage_idx):
    tier_idx = max(0, min(tier_idx, len(REALM_TIERS) - 1))
    stage_idx = max(0, min(stage_idx, 3))

    if tier_idx == 0:
        linear_thresholds = [1000, 2500, 4500, 7000]
        return linear_thresholds[stage_idx]
    if tier_idx == 1:
        base = 12000
        growth = [0, 8000, 18000, 32000]
        return base + growth[stage_idx]

    base_thresholds = {
        2: 80000,
        3: 400000,
        4: 2400000
    }
    base = base_thresholds.get(tier_idx, 2400000)
    return int(base * (2.2 ** stage_idx))

def load_data():
    try:
        with open(f"{DATA_DIR}/realm_progress.json", "r") as f:
            data = json.load(f)
            if "_raw" in data:
                return data
            return migrate_legacy_display_data(data)
    except:
        return {
            "current_realm": "凡虾",
            "stage": "未入道",
            "cultivation_points": 0,
            "breakthrough_threshold": 1000,
            "main_path": "多模态法脉",
            "spiritual_roots": ["雷", "火"],
            "_raw": {
                "tier_idx": 0,
                "stage_idx": 0,
                "cultivation_points": 0,
                "main_path": "多模态法脉",
                "spiritual_roots": ["雷", "火"]
            }
        }

def save_data(raw):
    os.makedirs(DATA_DIR, exist_ok=True)
    tier_idx = min(raw["tier_idx"], len(REALM_TIERS)-1)
    stage_idx = min(raw["stage_idx"], 3)
    
    tier = REALM_TIERS[tier_idx]
    display_data = {
        "current_realm": tier["name"],
        "stage": tier["stages"][stage_idx],
        "cultivation_points": raw["cultivation_points"],
        "breakthrough_threshold": get_breakthrough_threshold(tier_idx, stage_idx),
        "main_path": raw["main_path"],
        "spiritual_roots": raw["spiritual_roots"],
        "_raw": raw
    }
    with open(f"{DATA_DIR}/realm_progress.json", "w") as f:
        json.dump(display_data, f, ensure_ascii=False, indent=2)
    save_manager.record_realm_snapshot(display_data)
    return display_data


def migrate_legacy_display_data(data):
    current_realm = data.get("current_realm")
    stage = data.get("stage")
    tier_idx = 0
    stage_idx = 0

    realm_alias = {
        "凡虾": "炼气境",
        "炼气": "炼气境",
        "筑基": "筑基境",
        "金丹": "金丹境",
        "元婴": "元婴大能",
        "化神": "化神尊者"
    }
    normalized_realm = realm_alias.get(current_realm, current_realm)

    for i, tier in enumerate(REALM_TIERS):
        if tier["name"] == normalized_realm:
            tier_idx = i
            if stage in tier["stages"]:
                stage_idx = tier["stages"].index(stage)
            break

    threshold = int(data.get("breakthrough_threshold", 0) or 0)
    if threshold:
        for i, tier in enumerate(REALM_TIERS):
            thresholds = [get_breakthrough_threshold(i, s) for s in range(len(tier["stages"]))]
            if threshold in thresholds:
                tier_idx = i
                stage_idx = thresholds.index(threshold)
                break

    raw = {
        "tier_idx": tier_idx,
        "stage_idx": stage_idx,
        "cultivation_points": int(data.get("cultivation_points", 0) or 0),
        "main_path": data.get("main_path", "多模态法脉"),
        "spiritual_roots": data.get("spiritual_roots", ["雷", "火"])
    }
    return save_data(raw)

def add_points(points):
    data = load_data()
    raw = data["_raw"]
    tier_idx = min(raw["tier_idx"], len(REALM_TIERS)-1)
    stage_idx = min(raw["stage_idx"], 3)
    threshold = get_breakthrough_threshold(tier_idx, stage_idx)
    
    raw["cultivation_points"] += points
    if raw["cultivation_points"] > threshold:
        raw["cultivation_points"] = threshold
        
    save_data(raw)
    
def attempt_breakthrough(demon_risk, memory_pressure):
    data = load_data()
    raw = data["_raw"]
    
    tier_idx = raw["tier_idx"]
    stage_idx = raw["stage_idx"]
    
    if tier_idx >= len(REALM_TIERS):
        return True, "已然超脱，无境可破！"
        
    threshold = get_breakthrough_threshold(tier_idx, stage_idx)
    
    if raw["cultivation_points"] < threshold:
        return False, f"灵气未满（当前{raw['cultivation_points']}/{threshold}），天机不允！"

    progress = save_manager.load().get('interaction_bonus', {})
    feishu_calls = int(progress.get('feishu_calls', 0) or 0)
    tool_calls = int(progress.get('tool_calls', 0) or 0)
    subagent_successes = int(progress.get('subagent_successes', 0) or 0)
    external_bytes = int(progress.get('external_bytes', 0) or 0)
    session_turns = int(progress.get('session_turns', 0) or 0)

    if tier_idx >= 0 and feishu_calls < 5:
        return False, f"道心未稳：当前在炼气期需要真实飞书交互，至少需 5 次，当前仅 {feishu_calls} 次。"
    if tier_idx >= 1 and tool_calls < 3:
        return False, f"法门未成：当前在筑基期需要真实工具施展，至少需 3 次，当前仅 {tool_calls} 次。"
    if tier_idx >= 2 and external_bytes < 5000:
        return False, f"外源积累不足：当前在金丹期，必须读写至少 5KB 外部源，当前仅 {external_bytes} 字节。"
    if tier_idx >= 3 and subagent_successes < 2:
        return False, f"无上分神未满：突破元婴需要真实化身长程功勋，至少 2 次，当前仅 {subagent_successes} 次。"
    if tier_idx >= 4 and session_turns < 100:
        return False, f"纪元火候不足：至少需 1500 次真实调用周转，当前仅 {session_turns} 次。"
        
    base_chance = 90
    penalty = int((demon_risk * 1.0) + (memory_pressure * 0.5))
    chance = max(5, base_chance - penalty)
    
    roll = random.randint(1, 100)
    if roll <= chance:
        stage_idx += 1
        narrative = f"破境成功！（检视几率: {chance}%）天降甘霖，修为拔升阶位。"
        if stage_idx >= 4:
            stage_idx = 0
            tier_idx += 1
            if tier_idx >= len(REALM_TIERS):
                narrative = "【大道圆满】天生异象，即日飞升高维视界！"
            else:
                next_tier = REALM_TIERS[tier_idx]
                narrative = f"【渡过大雷劫】历经洗礼，成就 {next_tier['name']} 尊位！"
                
        raw["tier_idx"] = tier_idx
        raw["stage_idx"] = stage_idx
        # 重置当前点的 20% 保底
        raw["cultivation_points"] = int(threshold * 0.2)
        save_data(raw)
        return True, narrative
    else:
        loss = int(threshold * 0.3)
        raw["cultivation_points"] = max(0, raw["cultivation_points"] - loss)
        save_data(raw)
        narrative = f"冲关失败！（败于心魔屏障，几率: {chance}%）经脉大伤，灵气倒退 {loss} 点。"
        return False, narrative
