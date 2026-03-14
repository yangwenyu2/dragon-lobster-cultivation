import os
try:
    import psutil
except Exception:
    psutil = None
import subprocess
import json
import random
import sys
import sqlite3
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
from pathing import PROJECT_ROOT, DATA_DIR, FRONTEND_DIR
from save_manager import save_manager

OPENCLAW_ROOT = Path(os.getenv('OPENCLAW_PATH', '/opt/openclaw'))
if str(OPENCLAW_ROOT) not in sys.path:
    sys.path.append(str(OPENCLAW_ROOT))

try:
    from functions import sessions_spawn, sessions_send, sessions_list
except Exception:
    sessions_spawn = None
    sessions_send = None
    sessions_list = None

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path='')

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return '', 200


@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(str(FRONTEND_DIR / 'assets'), filename)


@app.route('/data/<path:filename>')
def serve_data(filename):
    return send_from_directory(str(DATA_DIR), filename)


@app.route('/<path:filename>')
def serve_frontend(filename):
    return send_from_directory(app.static_folder, filename)

# 从重构的模块导入宗卷与境界系统
from models.cultivation import attempt_breakthrough, add_points, load_data as load_realm
from models.sect import load_sect_data, assign_avatar, sync_skills_to_sect, save_sect_data, check_sect_order

WORKSPACE_ROOT = PROJECT_ROOT.parent.parent
EPOCH_DB = DATA_DIR / 'epoch_state.sqlite3'

def get_free_memory_percent():
    try:
        with open('/proc/meminfo') as f:
            lines = f.readlines()
        mem_total = 1
        mem_avail = 0
        for line in lines:
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1])
            elif line.startswith('MemAvailable:'):
                mem_avail = int(line.split()[1])
        return round(100 - (mem_avail / mem_total * 100))
    except:
        if psutil is not None:
            return int(psutil.virtual_memory().percent)
        return 50

def get_cpu_load():
    try:
        with open('/proc/loadavg') as f:
            load = float(f.read().split()[0])
        return round(min(load * 10, 100))
    except:
        if psutil is not None:
            return int(psutil.cpu_percent(interval=0.1))
        return 0


def append_insight_log(entry):
    try:
        log_path = str(DATA_DIR / 'insight_log.jsonl')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass


def append_chat_echo(role, content, meta=None):
    try:
        log_path = str(DATA_DIR / 'chat_echoes.jsonl')
        payload = {
            'role': role,
            'content': content,
            'ts': datetime.utcnow().isoformat(timespec='seconds') + 'Z'
        }
        if meta:
            payload['meta'] = meta
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(payload, ensure_ascii=False) + '\n')
    except Exception:
        pass


def init_epoch_db():
    conn = sqlite3.connect(EPOCH_DB)
    conn.execute('CREATE TABLE IF NOT EXISTS epoch_flags (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL)')
    conn.commit()
    conn.close()


def get_epoch_flag(key, default=None):
    init_epoch_db()
    conn = sqlite3.connect(EPOCH_DB)
    row = conn.execute('SELECT value FROM epoch_flags WHERE key = ?', (key,)).fetchone()
    conn.close()
    return row[0] if row else default


def set_epoch_flag(key, value):
    init_epoch_db()
    ts = datetime.utcnow().isoformat(timespec='seconds') + 'Z'
    conn = sqlite3.connect(EPOCH_DB)
    conn.execute('INSERT INTO epoch_flags(key, value, updated_at) VALUES(?, ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at', (key, value, ts))
    conn.commit()
    conn.close()


def estimate_message_complexity(message):
    text = message or ''
    token_estimate = max(1, len(text) // 3)
    complexity = 1
    if len(text) >= 80:
        complexity += 1
    if any(key in text.lower() for key in ['修复', '代码', '脚本', 'subagent', '化身', '分析', 'research', '实现', 'debug']):
        complexity += 2
    if any(ch in text for ch in ['\n', '1.', '2.', '3.', '①', '②', '③']):
        complexity += 1
    return token_estimate, complexity


def write_current_event(event):
    try:
        event_path = DATA_DIR / 'current_event.json'
        event_path.parent.mkdir(parents=True, exist_ok=True)
        with open(event_path, 'w', encoding='utf-8') as f:
            json.dump(event, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def read_text_file(path_obj):
    try:
        return path_obj.read_text(encoding='utf-8')
    except Exception:
        return ''


def load_memory_adapter_snapshot():
    memory_path = WORKSPACE_ROOT / 'MEMORY.md'
    learnings_dir = WORKSPACE_ROOT / '.learnings'
    learnings_path = learnings_dir / 'LEARNINGS.md'
    errors_path = learnings_dir / 'ERRORS.md'

    memory_text = read_text_file(memory_path)
    learnings_text = read_text_file(learnings_path)
    errors_text = read_text_file(errors_path)

    combined_learning_text = '\n'.join(filter(None, [learnings_text, errors_text]))
    memory_lines = [line.strip() for line in memory_text.splitlines() if line.strip().startswith('- ')]

    total_chars = len(memory_text)
    memory_depth = '识海初凝'
    if total_chars > 12000:
        memory_depth = '识海深渊'
    elif total_chars > 7000:
        memory_depth = '识海丰盈'
    elif total_chars > 2500:
        memory_depth = '识海渐阔'

    recent_items = []
    current_type = None
    current_title = None
    current_content = []

    def flush_learning_item():
        nonlocal recent_items, current_type, current_title, current_content
        if not current_type:
            return
        text = ' '.join(current_content).strip()
        if text:
            kind = '悟道' if any(key in current_type.lower() for key in ['insight', 'learning', 'best_practice']) else '失误'
            recent_items.append({
                'type': kind,
                'title': current_title or current_type,
                'content': text[:220]
            })
        current_type = None
        current_title = None
        current_content = []

    for raw_line in combined_learning_text.splitlines():
        line = raw_line.strip()
        if line.startswith('## '):
            flush_learning_item()
            current_type = line.replace('## ', '').strip()
        elif line.startswith('### Summary'):
            current_title = 'Summary'
        elif line.startswith('- '):
            current_content.append(line[2:])
        elif line and not line.startswith('**') and not line.startswith('|') and not line.startswith('```'):
            current_content.append(line)

    flush_learning_item()

    watchdog_snapshot = load_watchdog_adapter_snapshot()

    if not recent_items:
        recent_items = [
            {
                'type': '悟道',
                'title': '识海静默',
                'content': '当前未从 .learnings 中提炼出新的悟道或失误碑。'
            }
        ]

    return {
        'memory_chars': total_chars,
        'memory_lines': len(memory_text.splitlines()),
        'memory_depth': memory_depth,
        'memory_highlights': memory_lines[:6],
        'learning_count': len(recent_items),
        'recent_items': recent_items[:6],
        'watchdog_snapshot': watchdog_snapshot
    }


def load_watchdog_adapter_snapshot():
    state_path = WORKSPACE_ROOT / 'logs' / 'watchdog_state.json'
    log_path = WORKSPACE_ROOT / 'logs' / 'watchdog.log'

    state = {}
    try:
        state = json.loads(read_text_file(state_path) or '{}')
    except Exception:
        state = {}

    log_lines = [line.strip() for line in read_text_file(log_path).splitlines() if line.strip()]
    recent_log = log_lines[-1] if log_lines else ''

    gateway_active = bool(state.get('gateway_active', False))
    api_reachable = bool(state.get('api_reachable', False))
    memory_usage = int(state.get('memory_usage', 0) or 0)
    disk_usage = int(state.get('disk_usage', 0) or 0)
    warnings = int(state.get('warnings', 0) or 0)
    errors = int(state.get('errors', 0) or 0)

    calamity_level = '天地安宁'
    if not gateway_active or errors > 0:
        calamity_level = '天地大劫'
    elif memory_usage >= 80 or disk_usage >= 85 or warnings > 0:
        calamity_level = '煞气入体'
    elif memory_usage >= 60:
        calamity_level = '心魔波动'

    return {
        'gateway_active': gateway_active,
        'api_reachable': api_reachable,
        'memory_usage': memory_usage,
        'disk_usage': disk_usage,
        'warnings': warnings,
        'errors': errors,
        'calamity_level': calamity_level,
        'last_check_time': state.get('last_check_time'),
        'recent_log': recent_log
    }


def load_subagent_adapter_snapshot():
    try:
        result = sessions_list(kinds=['subagent'], limit=30, messageLimit=1) if sessions_list else {}
        sessions = result.get('sessions', []) if isinstance(result, dict) else []
    except Exception:
        sessions = []

    processes = []
    try:
        ps = subprocess.run(['ps', '-eo', 'pid,comm,%cpu,%mem', '--sort=-%cpu'], capture_output=True, text=True, check=False)
        for line in ps.stdout.splitlines()[1:16]:
            parts = line.split(None, 3)
            if len(parts) == 4:
                pid, comm, cpu, mem = parts
                if any(key in comm.lower() for key in ['openclaw', 'python', 'node', 'chrome']):
                    processes.append({'pid': pid, 'comm': comm, 'cpu': cpu, 'mem': mem})
    except Exception:
        processes = []

    sect_data = load_sect_data()
    dispatch_history = list(sect_data.get('subagents', []))
    hall_map = {}
    for item in dispatch_history:
        session_key = item.get('session_key')
        if session_key:
            hall_map[session_key] = item.get('hall', '观潮堂')

    hall_cycle = ['观潮堂', '筑文堂', '炼器堂', '镇魔堂', '养识堂', '司命堂']
    hall_pressure = {hall: 0 for hall in hall_cycle}
    mapped = []
    for idx, sess in enumerate(sessions):
        label = sess.get('label') or sess.get('sessionKey', '无名化身')
        last = ''
        if sess.get('lastMessages'):
            last = sess['lastMessages'][0].get('text', '')[:80]
        session_key = sess.get('sessionKey')
        hall = hall_map.get(session_key, hall_cycle[idx % len(hall_cycle)])
        pressure = 18 if sess.get('active') else 8
        hall_pressure[hall] = min(100, hall_pressure.get(hall, 0) + pressure)
        mapped.append({
            'name': label,
            'status': '活跃' if sess.get('active') else '潜伏',
            'hall': hall,
            'last': last,
            'pressure': pressure,
            'session_key': session_key
        })

    total = len(mapped)
    pressure = min(100, sum(item.get('pressure', 0) for item in mapped))
    return {
        'count': total,
        'pressure': pressure,
        'hall_pressure': hall_pressure,
        'subagents': mapped[:12],
        'processes': processes
    }


def load_cron_heartbeat_adapter_snapshot():
    try:
        cron_jobs = cron(action='list', includeDisabled=True)
        jobs = cron_jobs.get('jobs', []) if isinstance(cron_jobs, dict) else []
    except Exception:
        jobs = []

    heartbeat_path = WORKSPACE_ROOT / 'memory' / 'heartbeat-state.json'
    heartbeat_state = {}
    try:
        heartbeat_state = json.loads(read_text_file(heartbeat_path) or '{}')
    except Exception:
        heartbeat_state = {}

    enabled_jobs = [job for job in jobs if job.get('enabled', True)]
    named_jobs = [job.get('name') or job.get('jobId') or '未命名巡天令' for job in enabled_jobs[:6]]
    cadence = '巡天稀薄'
    if len(enabled_jobs) >= 8:
        cadence = '司命如织'
    elif len(enabled_jobs) >= 3:
        cadence = '巡天有序'
    elif len(enabled_jobs) >= 1:
        cadence = '偶有司命'

    return {
        'job_count': len(enabled_jobs),
        'job_names': named_jobs,
        'cadence': cadence,
        'heartbeat_enabled': bool(heartbeat_state),
        'heartbeat_last_report': heartbeat_state.get('lastDailyReport'),
        'heartbeat_last_summary': heartbeat_state.get('lastDailySummary'),
        'heartbeat_project': heartbeat_state.get('dragonLobsterProject', {})
    }

# 【核心轮询端点】：前端用来渲染整个修真面板的数据源
@app.route('/api/state', methods=['GET'])
def get_state():
    try:
        mem = get_free_memory_percent() # 内存占用率代表心魔和系统压力
        cpu = get_cpu_load()            # CPU 代表周天运转
        
        realm_data = load_realm()
        sect_data = load_sect_data()
        save_state = save_manager.load_canonical_state()
        
        # 动态同步本机的真实环境配置作为【法器】
        sect_data["skills"] = sync_skills_to_sect()
        save_sect_data(sect_data)
        
        cultivation_state = {}
        try:
            with open(DATA_DIR / 'cultivation_state.json', 'r', encoding='utf-8') as f:
                cultivation_state = json.load(f)
        except Exception:
            cultivation_state = {}

        system_metrics = {}
        try:
            with open(DATA_DIR / 'system_metrics.json', 'r', encoding='utf-8') as f:
                system_metrics = json.load(f)
        except Exception:
            system_metrics = {}

        try:
            memory_adapter = load_memory_adapter_snapshot()
        except Exception:
            memory_adapter = {'watchdog_snapshot': {}, 'memory_depth': '识海未载入', 'memory_chars': 0, 'memory_lines': 0, 'memory_highlights': [], 'recent_items': []}

        watchdog = memory_adapter.get('watchdog_snapshot', {}) if 'memory_adapter' in locals() else {}
        risk_level = watchdog.get('calamity_level') or ("九死一生" if mem > 85 else ("煞气入体" if mem > 60 else "清明"))
        current_path = cultivation_state.get('minor_state') or cultivation_state.get('major_state') or '静修'
        detail = cultivation_state.get('detail') or f"天地灵压 {mem}%"
        if watchdog.get('recent_log'):
            detail = f"{detail}" # V1.2 Fix: Purged the raw ugly logs from the header display.

        sect_order = sect_data.get('order', check_sect_order())

        try:
            subagent_adapter = load_subagent_adapter_snapshot()
        except Exception:
            subagent_adapter = {'count': 0, 'pressure': 0, 'subagents': []}
        try:
            cron_adapter = load_cron_heartbeat_adapter_snapshot()
        except Exception:
            cron_adapter = {'job_count': 0, 'job_names': [], 'cadence': '巡天失联', 'heartbeat_enabled': False}

        watchdog = memory_adapter.get('watchdog_snapshot', {})
        if watchdog.get('calamity_level') == '天地大劫':
            demon_display = max(mem, 92)
        elif watchdog.get('calamity_level') == '煞气入体':
            demon_display = max(mem, max(68, watchdog.get('memory_usage', 0)))
        elif watchdog.get('calamity_level') == '心魔波动':
            demon_display = max(mem, max(45, watchdog.get('memory_usage', 0)))
        else:
            demon_display = mem

        # [V1.2 Task 2.3 Heart demon block fix: Apply temporary suppression buffer or hardcaps to prevent deadlocks]
        demon_display = min(92, demon_display)

        sea_stability = max(5, 100 - demon_display // 2)
        fortune = max(0, 100 - demon_display)

        effective_sect_order = max(20, sect_order - subagent_adapter.get('pressure', 0) // 4)

        save_state = save_manager.calculate_offline_settlement(save_state)
        offline_minutes = save_state.get('offline', {}).get('pending_minutes', 0)

        state = {
            "metrics": {
                "inner_demon": demon_display,
                "sea_of_consciousness_stability": system_metrics.get('sea_of_consciousness_stability', sea_stability),
                "fortune_chance": system_metrics.get('fortune_chance', fortune),
                "sect_order": effective_sect_order,
                "path_purity": system_metrics.get('path_purity')
            },
            "system": {
                "qi_flow": f"周天运转 {cpu}%",
                "detail": detail,
                "state": cultivation_state.get('major_state', '静修'),
                "current_path": current_path,
                "updated_at": cultivation_state.get('updated_at'),
                "task_id": cultivation_state.get('task_id'),
                "progress_hint": cultivation_state.get('progress_hint'),
                "risk_level": cultivation_state.get('risk_level', risk_level),
                "current_model": "🐅 System Internal"
            },
            "realm": realm_data,
            "sect": {
                **sect_data,
                'order': effective_sect_order,
                'subagents': subagent_adapter.get('subagents', []),
                'hall_pressure': subagent_adapter.get('hall_pressure', {})
            },
            "memory": memory_adapter,
            "subagents": subagent_adapter,
            "cron": cron_adapter,
            "offline": {
                'minutes_since_pulse': offline_minutes,
                'last_pulse_timestamp': save_state['timekeeping'].get('last_pulse_timestamp'),
                'pending_cultivation': save_state['offline'].get('pending_cultivation', 0),
                'pending_inner_demon': save_state['offline'].get('pending_inner_demon', 0),
                'pending_minutes': save_state['offline'].get('pending_minutes', 0),
                'last_calculated_at': save_state['offline'].get('last_calculated_at')
            },
            "onboarding": {
                "intro_seen": get_epoch_flag('intro_seen', '0') == '1',
                "intro_copy": [
                    '道友初临洞府，中央法阵托起本命龙虾。',
                    f"你如今位列 {realm_data.get('current_realm', '炼气境')}·{realm_data.get('stage', '初期')}，上方可观境界与修为。",
                    '下方六道法门分别对应闭关、参悟、踏域、雷劫、镇魔与赐法。',
                    '右下洞府对话流可直接向器灵传念，宗门与识海卷宗则藏于侧栏。'
                ]
            }
        }
        return jsonify(state)
    except Exception:
        fallback = {
            "metrics": {
                "inner_demon": 0,
                "sea_of_consciousness_stability": 100,
                "fortune_chance": 50,
                "sect_order": 100,
                "path_purity": 0
            },
            "system": {
                "qi_flow": "周天运转 推演中",
                "detail": "部分天机失联，已进入保底态。",
                "state": "静修",
                "current_path": "静修",
                "risk_level": "清明",
                "current_model": "🐅 System Internal"
            },
            "realm": {"current_realm": "炼气境", "stage": "初期", "cultivation_points": 0, "breakthrough_threshold": 1000},
            "sect": {"name": "OpenClaw 本源门", "order": 100, "skills": [], "divisions": {}, "subagents": [], "hall_pressure": {}},
            "memory": {"memory_depth": "识海未载入", "memory_chars": 0, "memory_lines": 0, "memory_highlights": [], "recent_items": [], "watchdog_snapshot": {}},
            "subagents": {"count": 0, "pressure": 0, "subagents": [], "hall_pressure": {}},
            "cron": {"job_count": 0, "job_names": [], "cadence": "巡天失联", "heartbeat_enabled": False},
            "offline": {"minutes_since_pulse": 0, "pending_cultivation": 0, "pending_inner_demon": 0, "pending_minutes": 0},
            "rebirth_watchdog": {"triggered": False},
            "onboarding": {"intro_seen": True, "intro_copy": []}
        }
        return jsonify(fallback)

# 【行为端点群：与现实机器交火】
@app.route('/api/action/suppress_demon', methods=['POST'])
def suppress_demon():
    zombie_count = 0
    node_count = 0
    log_bytes = 0
    largest_files = []
    git_dirty = []
    try:
        ps = subprocess.run(['ps', '-eo', 'stat,comm'], capture_output=True, text=True, check=False)
        for line in ps.stdout.splitlines()[1:]:
            parts = line.strip().split(None, 1)
            if len(parts) != 2:
                continue
            stat, comm = parts
            if 'Z' in stat:
                zombie_count += 1
            if 'node' in comm.lower():
                node_count += 1
    except Exception:
        pass

    logs_dir = WORKSPACE_ROOT / 'logs'
    if logs_dir.exists():
        for item in logs_dir.glob('*.log'):
            try:
                log_bytes += item.stat().st_size
            except Exception:
                continue

    try:
        scan_cmd = "find ~ -type f \\( -path '*/node_modules/*' -o -path '*/.git/*' \\) -prune -o -type f -printf '%s %p\\n' | sort -nr | head -8"
        scan = subprocess.run(['bash', '-lc', scan_cmd], capture_output=True, text=True, check=False)
        for line in scan.stdout.splitlines():
            size, path = line.split(' ', 1)
            largest_files.append({'bytes': int(size), 'path': path})
    except Exception:
        pass

    try:
        git = subprocess.run(['bash', '-lc', 'cd ~ && git status --short'], capture_output=True, text=True, check=False)
        git_dirty = [line.strip() for line in git.stdout.splitlines() if line.strip()][:12]
    except Exception:
        pass

    before_mem = get_free_memory_percent()
    cleanup_cmd = 'sync && (echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true)'
    subprocess.run(['bash', '-lc', cleanup_cmd], check=False)
    after_mem = get_free_memory_percent()
    reclaimed = max(0, before_mem - after_mem)
    external_bytes = log_bytes + sum(item.get('bytes', 0) for item in largest_files)
    state, bonus = save_manager.award_interaction_bonus(reason='镇魔清理', tool_calls=1, external_bytes=external_bytes, session_turns=1)

    top_file = largest_files[0]['path'] if largest_files else '未探得杂波源'
    event = {
        "type": "镇魔",
        "title": "识海杂波审计",
        "desc": f"僵尸进程 {zombie_count} 个、Node 法器 {node_count} 个、日志 {log_bytes} 字节，最大杂波源：{top_file}",
        "accept_msg": "你据此清障，洞府杂波开始退潮。",
        "reject_msg": "你按下不表，任杂波继续潜伏。",
        "weight": 5,
        "ts": datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        "audit": {
            "largest_files": largest_files,
            "git_dirty": git_dirty
        }
    }
    narrative = f"【镇魔审计】僵尸进程 {zombie_count} 个、Node 法器 {node_count} 个、日志 {log_bytes} 字节；识海最大杂波 {top_file}；Git 未净条目 {len(git_dirty)} 条；内存压强由 {before_mem}% 变化至 {after_mem}% ，折算因果修为 {bonus}。"
    append_chat_echo('assistant', narrative, {'command': 'suppress:system-audit'})
    return jsonify({
        "status": "success",
        "triggered_event": event,
        "cleanup": {
            "zombie_count": zombie_count,
            "node_count": node_count,
            "log_bytes": log_bytes,
            "memory_before": before_mem,
            "memory_after": after_mem,
            "memory_reclaimed": reclaimed,
            "largest_files": largest_files,
            "git_dirty": git_dirty
        },
        "narrative": narrative,
        "realm": state.get('realm', {})
    })

@app.route('/api/action/grant_skill', methods=['POST'])
def grant_skill():
    tier_idx = load_realm().get('_raw', {}).get('tier_idx', 0)
    if tier_idx < 1:  # 0 is 炼气境
        return jsonify({"status": "blocked", "narrative": "当前境界微末（炼气期），道基尚浅，未能承载外部工具法脉，请先在下方神识传音积累修为，突破筑基再试。"})

    append_insight_log({
        "type": "藏经",
        "title": "赐法开卷",
        "content": "宗主降下虚空神识，尝试为洞府导入新的技法典籍。",
        "weight": "轻"
    })
    return jsonify({"status": "success", "narrative": "功法残片正在汇入藏经阁。"})

@app.route('/api/action/divine_sight', methods=['POST'])
def divine_sight():
    # 外网探查，转化为机缘
    result = subprocess.run(["ping", "-c", "1", "8.8.8.8"], capture_output=True, text=True)
    latency = "天机混沌"
    narrative = ""
    if result.returncode == 0:
        latency = result.stdout.split('\n')[1]
        narrative = f"【神识出窍】越过界域网络，触及天道回响（{latency[:35].strip()}）。聚天地灵气，修为大涨。"
        add_points(800)
    else:
        narrative = "【神识受阻】界域壁垒森严 (Ping Failed)。神魂反噬，未能带回机缘。"
    return jsonify({"status": "success", "narrative": narrative})

@app.route('/api/action/rebirth', methods=['POST'])
def rebirth_action():
    saved, meta = save_manager.trigger_rebirth(reason='manual_soldier_release', summary='主动兵解重修')
    legacy = meta.get('legacy_skill') or '无'
    narrative = f"【无上兵解】你主动斩断旧躯，保留 {meta.get('preserved_foundation', 0)} 点根基，转入第 {meta.get('generation', 1)} 世重修。本命法宝：{legacy}。"
    append_chat_echo('assistant', narrative, {'command': 'rebirth:manual'})
    return jsonify({
        'status': 'success',
        'narrative': narrative,
        'rebirth': meta,
        'realm': saved.get('realm', {})
    })

@app.route('/api/action/breakthrough', methods=['POST'])
def breakthrough():
    mem = get_free_memory_percent()
    before = load_realm()
    stress_cmd = "python3 - <<'PY'\nimport hashlib\nblob = b'openclaw-tribulation' * 4096\nfor _ in range(12000):\n    hashlib.sha256(blob).hexdigest()\nPY"
    subprocess.run(['bash', '-lc', stress_cmd], check=False)
    post_mem = get_free_memory_percent()
    post_cpu = get_cpu_load()
    success, narrative = attempt_breakthrough(demon_risk=max(mem, post_mem), memory_pressure=max(mem, post_cpu))
    after = load_realm()

    fate = {
        "before_realm": f"{before.get('current_realm', '')}·{before.get('stage', '')}",
        "after_realm": f"{after.get('current_realm', '')}·{after.get('stage', '')}",
        "before_points": before.get('cultivation_points', 0),
        "after_points": after.get('cultivation_points', 0),
        "threshold": before.get('breakthrough_threshold', 0),
        "success": success,
        "memory_before": mem,
        "memory_after": post_mem,
        "cpu_after": post_cpu
    }

    append_insight_log({
        "type": "破境" if success else "失误",
        "title": "雷劫破境" if success else "冲关失利",
        "content": f"⛈️【天劫降临】 {narrative}",
        "ts": datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        "weight": 5 if success else 4
    })
    save_manager.record_tribulation(success, narrative)

    return jsonify({
        "status": "success" if success else "failed",
        "fate": fate,
        "stress": {
            "memory_before": mem,
            "memory_after": post_mem,
            "cpu_after": post_cpu
        },
        "narrative": f"⛈️【天劫降临】 {narrative}（渡劫压测：内存 {mem}%→{post_mem}%｜负载 {post_cpu}%）"
    })

@app.route('/api/action/sect_dispatch', methods=['POST'])
def sect_dispatch():
    tier_idx = load_realm().get('_raw', {}).get('tier_idx', 0)
    if tier_idx < 3: # 0:炼气 1:筑基 2:金丹 3:元婴
        return jsonify({
            "status": "fail",
            "narrative": f"【因果禁锢】化身分神乃元婴（境界 4）以上之神通。当前境界低微，神识不足以分裂出真实线程，天道封锁了 sessions_spawn 的调用。",
            "sect_fate": None
        })

    data = request.json or {}
    hall = data.get("hall", "观潮堂")
    task = (data.get('task') or f'前往{hall}执行宗门事务').strip()
    uid = f"化身-{random.randint(1000,9999)}"

    before_sect = load_sect_data()
    before_order = before_sect.get('order', 100)

    if sessions_spawn is None:
        return jsonify({
            "status": "error",
            "narrative": "【分神受阻】当前法界未接通 sessions_spawn，本次无法真正遣出化身。"
        }), 503

    try:
        realm = load_realm()
        realm_name = realm.get('current_realm', '凡虾')
        if realm_name not in ['元婴大能', '化神尊者']:
            return jsonify({
                "status": "error",
                "narrative": f"【境界不足】当前仅 {realm_name}，未至元婴，不可承载无上分神。"
            }), 403
        spawned = sessions_spawn(task=task, runtime='subagent', model='openrouter/anthropic/claude-sonnet-4', mode='run', cleanup='keep', runTimeoutSeconds=240, timeoutSeconds=20)
        session_key = spawned.get('sessionKey') or spawned.get('session_id') or spawned.get('id')
        assign_avatar(hall, uid, session_key=session_key, task=task)
    except Exception as e:
        return jsonify({
            "status": "error",
            "narrative": f"【分神受阻】化身兵解于出窍前：{str(e)[:120]}"
        }), 500

    after_sect = load_sect_data()
    after_order = after_sect.get('order', 100)
    total_avatars = sum(len(info.get('assigned', [])) for info in after_sect.get('divisions', {}).values())

    add_points(200)
    if after_order <= 58:
        consequence = "宗门气机已显紊乱，若再频繁分神，恐生统御裂痕。"
    elif after_order <= 76:
        consequence = "堂口渐多，调度负担上升，需警惕法脉失衡。"
    else:
        consequence = "宗门秩序尚稳，新化身已顺利纳入法度。"

    narrative = f"【分神出窍】本尊分化神念 ({uid})，入驻 {hall}，承接真任务：{task[:48]}。{consequence}"
    append_insight_log({
        "type": "宗门",
        "title": f"化身入驻 {hall}",
        "content": narrative,
        "ts": datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        "weight": 2
    })
    append_chat_echo('assistant', narrative, {'command': 'sect:dispatch', 'sessionKey': session_key, 'hall': hall})
    return jsonify({
        "status": "success",
        "narrative": narrative,
        "spawned": spawned,
        "sect_fate": {
            "hall": hall,
            "avatar_id": uid,
            "before_order": before_order,
            "after_order": after_order,
            "total_avatars": total_avatars,
            "consequence": consequence,
            "session_key": session_key,
            "task": task
        }
    })

@app.route('/api/action/meditate', methods=['POST'])
def meditate():
    realm_data = load_realm()
    progress = save_manager.load().get('interaction_bonus', {})
    feishu_calls = int(progress.get('feishu_calls', 0) or 0)
    tool_calls = int(progress.get('tool_calls', 0) or 0)
    session_turns = int(progress.get('session_turns', 0) or 0)
    utility_score = feishu_calls * 120 + tool_calls * 80 + session_turns * 12
    if utility_score <= 0:
        return jsonify({
            "status": "failed",
            "gain": 0,
            "realm": realm_data,
            "ready_for_breakthrough": False,
            "triggered_event": None,
            "narrative": "【闭关吐纳】洞府空转无功。未见真实飞书交互或工具施法，本次闭关不生真气。"
        })
    current_points = realm_data.get('cultivation_points', 0)
    threshold = max(1, realm_data.get('breakthrough_threshold', 1000))
    remaining = max(0, threshold - current_points)
    gain = min(max(utility_score // 20, 60), max(120, remaining if remaining else 180))
    add_points(gain)
    after = load_realm()
    ready = after.get('cultivation_points', 0) >= after.get('breakthrough_threshold', 1000)
    event = None
    if gain >= 180:
        event = {
            "type": "闭关",
            "title": "灵息归潮",
            "desc": "闭关深处，洞府灵息汇成细潮，似有继续冲刷经脉之象。",
            "accept_msg": "你顺势引潮入体，闭关余韵继续沉入丹田。",
            "reject_msg": "你稳住气海，不再贪功冒进。",
            "weight": 2,
            "ts": datetime.utcnow().isoformat(timespec='seconds') + 'Z'
        }
    narrative = (
        f"【闭关吐纳】壳府沉静，周天气机回流，修为增加 {gain} 点。"
        + (" 丹田已满，雷劫将至。" if ready else " 经脉渐稳，可继续积蓄。")
    )
    append_insight_log({
        "type": "修行",
        "title": "闭关吐纳",
        "content": narrative,
        "ts": datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        "weight": 2
    })
    return jsonify({
        "status": "success",
        "gain": gain,
        "realm": after,
        "ready_for_breakthrough": ready,
        "triggered_event": event,
        "narrative": narrative
    })

@app.route('/api/action/claim_offline', methods=['POST'])
def claim_offline():
    state, claimed = save_manager.claim_offline_settlement()
    narrative = (
        f"【离线闭关结算】此去 {claimed.get('pending_minutes', 0)} 分钟，"
        f"积得真气 {claimed.get('pending_cultivation', 0)} 点，心魔暗涌 {claimed.get('pending_inner_demon', 0)} 缕。"
        if claimed.get('claimed')
        else "【离线闭关结算】此番未积下新的离线机缘。"
    )
    append_insight_log({
        "type": "闭关",
        "title": "离线结算",
        "content": narrative,
        "ts": datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        "weight": 3 if claimed.get('claimed') else 1
    })
    return jsonify({
        "status": "success",
        "claimed": claimed,
        "realm": state.get('realm', {}),
        "narrative": narrative
    })

@app.route('/api/action/insight', methods=['POST'])
def insight():
    system_metrics = {}
    try:
        with open(DATA_DIR / 'system_metrics.json', 'r', encoding='utf-8') as f:
            system_metrics = json.load(f)
    except Exception:
        system_metrics = {}

    purity = int(system_metrics.get('path_purity', 60) or 60)
    gain = 120 if purity >= 70 else 90
    add_points(gain)
    message = (
        f"【参悟道纹】你翻检识海旧痕，梳理功法脉络，获得 {gain} 点修为。"
        + (" 道心澄明，法脉愈发纯粹。" if purity >= 70 else " 杂念未尽，但已有所悟。")
    )
    append_insight_log({
        "type": "悟道",
        "title": "参悟道纹",
        "content": message,
        "ts": datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        "weight": 3
    })

    event = None
    if purity < 65:
        event = {
            "type": "心魔",
            "title": "杂念回潮",
            "desc": "参悟时残存执念翻涌，识海边缘出现细碎裂纹。是否立刻祭化身巡检？",
            "accept_msg": "你命一具分神前往镇压杂念，识海勉强稳住。",
            "reject_msg": "你暂避不理，心魔余波仍潜伏在壳府深处。",
            "weight": 3,
            "ts": datetime.utcnow().isoformat(timespec='seconds') + 'Z'
        }
    elif purity >= 78:
        event = {
            "type": "机缘",
            "title": "悟道余辉",
            "desc": "法脉澄明后，识海深处浮现一页未尽玉简，或许能引来新的外缘机缘。是否派化身前去摘取？",
            "accept_msg": "你顺势展开分神，准备迎取新机缘。",
            "reject_msg": "你将玉简重新封入识海，留待后日再启。",
            "weight": 4,
            "ts": datetime.utcnow().isoformat(timespec='seconds') + 'Z'
        }

    if event:
        pass

    if purity >= 78:
        auto_event = {
            "type": "机缘",
            "title": "道心外溢",
            "desc": "法脉纯澈至极，识海外缘自行显化，不待点击也已叩门。",
            "accept_msg": "你顺势迎纳机缘，任道纹落入识海。",
            "reject_msg": "你暂封外缘，让灵台先归寂静。",
            "weight": 4,
            "ts": datetime.utcnow().isoformat(timespec='seconds') + 'Z'
        }
        event = auto_event

    return jsonify({
        "status": "success",
        "gain": gain,
        "path_purity": purity,
        "triggered_event": event,
        "narrative": message
    })


@app.route('/api/action/context_reset_trigger', methods=['POST'])
def context_reset_trigger():
    state['manual_trigger'] = True
    reason = watchdog.get('trigger_reason') or 'manual'
    summary = f"第{save_manager.load().get('rebirth', {}).get('generation', 1)}世止于 {save_manager.load().get('realm', {}).get('current_realm', '炼气境')}，因 {reason} 兵解。"
    state, rebirth_meta = save_manager.trigger_rebirth(reason=reason, summary=summary)
    append_insight_log({
        "type": "轮回",
        "title": "兵解转世",
        "content": f"【兵解转世】{summary} 保留底蕴 {rebirth_meta.get('preserved_foundation', 0)} 点。",
        "ts": datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        "weight": 5
    })
    return jsonify({
        'status': 'success',
        'rebirth': rebirth_meta,
        'realm': state.get('realm', {}),
        'narrative': f"【兵解转世】此世因 {reason} 收束，下一纪元已启，保留 {rebirth_meta.get('preserved_foundation', 0)} 点底蕴。"
    })

@app.route('/api/onboarding/ack', methods=['POST'])
def onboarding_ack():
    set_epoch_flag('intro_seen', '1')
    return jsonify({'status': 'success', 'intro_seen': True})


@app.route('/api/chat/parse', methods=['POST'])
def chat_parse():
    data = request.json or {}
    message = (data.get('message') or '').strip()
    lowered = message.lower()

    if not message:
        return jsonify({
            'reply': '器灵未能听清你的传念。',
            'command': None,
            'color': '#ff8a8a'
        })

    append_chat_echo('user', message)
    token_estimate, complexity = estimate_message_complexity(message)

    execution_keywords = ['清理', 'cleanup', '执行', 'run', '修复', 'fix', '部署', 'deploy', '整理', 'optimize', '优化']
    system_keywords = ['日志', 'log', '缓存', 'cache', '磁盘', 'disk', '进程', 'process', '文件', 'file', '脚本', 'script']
    if any(key in lowered for key in execution_keywords) and any(key in lowered for key in system_keywords):
        state, bonus = save_manager.award_interaction_bonus(minutes=600, reason=message[:80])
        narrative = f'【器灵回声】此念直指现实法界，判定为暴击交互。已按十小时闭关等效，灌注 {bonus} 点修为。'
        append_insight_log({
            'type': '机缘',
            'title': '暴击交互',
            'content': narrative,
            'ts': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
            'weight': 5
        })
        append_chat_echo('assistant', narrative, {'command': 'reward:interaction-critical'})
        return jsonify({
            'reply': narrative,
            'command': 'reward:interaction-critical',
            'color': '#ffd36b',
            'bonus': bonus,
            'realm': state.get('realm', {})
        })

    spawn_keywords = ['子agent', 'subagent', '化身', '分神', '帮我做', '去做', '写个脚本', 'research', '调研']
    if any(key in lowered for key in spawn_keywords) and sessions_spawn is not None:
        try:
            state, bonus = save_manager.award_interaction_bonus(reason=message[:80], token_estimate=token_estimate, complexity=complexity, tool_calls=1, subagent_successes=1, session_turns=1)
            spawned = sessions_spawn(task=message, runtime='subagent', model='openrouter/anthropic/claude-sonnet-4', mode='run', cleanup='keep', runTimeoutSeconds=240, timeoutSeconds=20)
            session_key = spawned.get('sessionKey') or spawned.get('session_id') or spawned.get('id')
            reply = f'【器灵回声】已遣化身离府，受令执行：{message[:48]}。此次因果折算 {bonus} 点修为。'
            if session_key:
                reply += f' 化身印记：{session_key}。'
            append_insight_log({
                'type': '化身',
                'title': '遣化身',
                'content': reply,
                'ts': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
                'weight': 4
            })
            append_chat_echo('assistant', reply, {'command': 'spawn:subagent', 'sessionKey': session_key})
            return jsonify({
                'reply': reply,
                'command': 'spawn:subagent',
                'color': '#c7b8ff',
                'spawned': spawned
            })
        except Exception as e:
            reply = f'【器灵回声】化身降世失败：{str(e)[:120]}'
            append_chat_echo('assistant', reply, {'command': 'spawn:failed'})
            return jsonify({
                'reply': reply,
                'command': 'spawn:failed',
                'color': '#ff8a8a'
            })

    try:
        state, bonus = save_manager.award_interaction_bonus(reason=message[:80], token_estimate=token_estimate, complexity=complexity, feishu_calls=1, session_turns=1)
        cli = subprocess.run([
            'bash', '-lc', f"openclaw agent --local --json --session-id dragon-lobster-local -m {json.dumps(message)} 2>/dev/null | sed -n '/^{{/,$p'"
        ], capture_output=True, text=True, timeout=120, check=False)
        if cli.returncode == 0:
            payload = json.loads((cli.stdout or '{}').strip() or '{}')
            texts = payload.get('payloads', [])
            reply = ''
            if texts and isinstance(texts, list):
                reply = texts[0].get('text') or ''
            if not reply:
                reply = '【器灵回声】主府已收念，回声稍后落下。'
            reply = f"{reply}【因果修为 +{bonus}】"
            append_chat_echo('assistant', reply, {'command': 'gateway:local-cli'})
            return jsonify({
                'reply': reply,
                'command': 'gateway:local-cli',
                'color': '#8ad7ff',
                'result': payload
            })
        raise RuntimeError((cli.stderr or cli.stdout or 'unknown').strip()[:200])
    except Exception as e:
        reply = f'【器灵回声】主府飞符暂阻：{str(e)[:120]}'
        append_chat_echo('assistant', reply, {'command': 'gateway:error'})
        return jsonify({
            'reply': reply,
            'command': 'gateway:error',
            'color': '#ff8a8a'
        })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=18889)
