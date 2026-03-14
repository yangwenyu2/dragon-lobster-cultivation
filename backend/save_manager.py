import json
from datetime import datetime, timezone
from pathlib import Path

from pathing import DATA_DIR

SAVE_PATH = DATA_DIR / 'cultivation_save.json'


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def parse_iso(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
    except Exception:
        return None


def default_save():
    return {
        'version': 1,
        'created_at': now_iso(),
        'updated_at': now_iso(),
        'total_cultivation': 0,
        'realm': {
            'current_realm': '凡虾',
            'stage': '未入道',
            'cultivation_points': 0,
            'breakthrough_threshold': 1000,
            'main_path': '多模态法脉',
            'spiritual_roots': ['雷', '火']
        },
        'tribulation': {
            'total_attempts': 0,
            'success_count': 0,
            'failure_count': 0,
            'last_result': None,
            'last_attempt_at': None
        },
        'timekeeping': {
            'days_passed': 0,
            'last_pulse_timestamp': now_iso(),
            'last_offline_settlement_at': None
        },
        'offline': {
            'pending_cultivation': 0,
            'pending_inner_demon': 0,
            'pending_minutes': 0,
            'last_calculated_at': None,
            'last_claimed_at': None
        },
        'interaction_bonus': {
            'last_triggered_at': None,
            'last_reason': None,
            'last_bonus': 0,
            'last_token_estimate': 0,
            'last_complexity': 0,
            'feishu_calls': 0,
            'tool_calls': 0,
            'subagent_successes': 0,
            'external_bytes': 0,
            'session_turns': 0
        },
        'rebirth': {
            'generation': 1,
            'last_triggered_at': None,
            'last_reason': None,
            'last_summary': None,
            'preserved_foundation': 0,
            'legacy_skill': None
        },
        'sect': {
            'order': 100,
            'hall_assignments': {
                '观潮堂': 0,
                '筑文堂': 0,
                '炼器堂': 0,
                '镇魔堂': 0,
                '养识堂': 0,
                '司命堂': 0
            },
            'last_dispatch': None,
            'dispatch_history': []
        }
    }


class SaveManager:
    def __init__(self, save_path: Path = SAVE_PATH):
        self.save_path = save_path
        self.save_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.save_path.exists():
            data = self.migrate_or_default()
            self.save(data)
            return data
        with open(self.save_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return self.normalize(data)

    def save(self, data):
        normalized = self.normalize(data)
        normalized['updated_at'] = now_iso()
        with open(self.save_path, 'w', encoding='utf-8') as f:
            json.dump(normalized, f, ensure_ascii=False, indent=2)
        return normalized

    def touch_pulse(self, data=None):
        current = self.load() if data is None else self.normalize(data)
        current['timekeeping']['last_pulse_timestamp'] = now_iso()
        return self.save(current)

    def load_canonical_state(self):
        return self.load()

    def offline_minutes_since_pulse(self, data=None, now_ts=None):
        current = self.load() if data is None else self.normalize(data)
        pulse = parse_iso(current['timekeeping'].get('last_pulse_timestamp'))
        now_dt = parse_iso(now_ts) if now_ts else datetime.now(timezone.utc)
        if pulse is None:
            return 0
        delta_seconds = max(0, int((now_dt - pulse).total_seconds()))
        return delta_seconds // 60

    def calculate_offline_settlement(self, data=None, now_ts=None):
        current = self.load() if data is None else self.normalize(data)
        offline_minutes = self.offline_minutes_since_pulse(current, now_ts=now_ts)
        if offline_minutes <= 0:
            return current

        realm_name = current['realm'].get('current_realm', '炼气境')
        realm_rates = {
            '凡虾': 2,
            '炼气境': 2,
            '筑基境': 6,
            '金丹境': 20,
            '元婴大能': 60,
            '化神尊者': 180
        }
        demon_rates = {
            '凡虾': 1,
            '炼气境': 1,
            '筑基境': 2,
            '金丹境': 4,
            '元婴大能': 8,
            '化神尊者': 15
        }
        cultivation_gain = offline_minutes * realm_rates.get(realm_name, 2)
        demon_gain = max(1, offline_minutes // 30) * demon_rates.get(realm_name, 1)

        current['offline']['pending_cultivation'] = int(current['offline'].get('pending_cultivation', 0) or 0) + cultivation_gain
        current['offline']['pending_inner_demon'] = int(current['offline'].get('pending_inner_demon', 0) or 0) + demon_gain
        current['offline']['pending_minutes'] = int(current['offline'].get('pending_minutes', 0) or 0) + offline_minutes
        current['offline']['last_calculated_at'] = now_ts or now_iso()
        current['timekeeping']['days_passed'] = int(current['timekeeping'].get('days_passed', 0) or 0) + (offline_minutes // (60 * 24))
        current['timekeeping']['last_offline_settlement_at'] = now_ts or now_iso()
        current['timekeeping']['last_pulse_timestamp'] = now_ts or now_iso()
        return self.save(current)

    def claim_offline_settlement(self):
        current = self.load()
        pending_cultivation = int(current['offline'].get('pending_cultivation', 0) or 0)
        pending_inner_demon = int(current['offline'].get('pending_inner_demon', 0) or 0)
        pending_minutes = int(current['offline'].get('pending_minutes', 0) or 0)
        if pending_cultivation <= 0 and pending_inner_demon <= 0 and pending_minutes <= 0:
            return current, {'claimed': False, 'pending_cultivation': 0, 'pending_inner_demon': 0, 'pending_minutes': 0}

        current['realm']['cultivation_points'] = int(current['realm'].get('cultivation_points', 0) or 0) + pending_cultivation
        current['total_cultivation'] = int(current.get('total_cultivation', 0) or 0) + pending_cultivation
        current['offline']['pending_cultivation'] = 0
        current['offline']['pending_inner_demon'] = 0
        current['offline']['pending_minutes'] = 0
        current['offline']['last_calculated_at'] = None
        current['offline']['last_claimed_at'] = now_iso()
        saved = self.save(current)
        return saved, {
            'claimed': True,
            'pending_cultivation': pending_cultivation,
            'pending_inner_demon': pending_inner_demon,
            'pending_minutes': pending_minutes,
            'claimed_at': saved['offline']['last_claimed_at']
        }

    def award_interaction_bonus(self, minutes=600, reason='真实执行', token_estimate=0, complexity=1, feishu_calls=0, tool_calls=0, subagent_successes=0, external_bytes=0, session_turns=0):
        current = self.load()
        metrics = current['interaction_bonus']
        metrics['feishu_calls'] = int(metrics.get('feishu_calls', 0) or 0) + int(feishu_calls or 0)
        metrics['tool_calls'] = int(metrics.get('tool_calls', 0) or 0) + int(tool_calls or 0)
        metrics['subagent_successes'] = int(metrics.get('subagent_successes', 0) or 0) + int(subagent_successes or 0)
        metrics['external_bytes'] = int(metrics.get('external_bytes', 0) or 0) + int(external_bytes or 0)
        metrics['session_turns'] = int(metrics.get('session_turns', 0) or 0) + int(session_turns or 0)

        utility_gate = 0
        utility_gate += metrics['feishu_calls'] * 220
        utility_gate += metrics['tool_calls'] * 140
        utility_gate += metrics['subagent_successes'] * 600
        utility_gate += metrics['session_turns'] * 35
        utility_gate += metrics['external_bytes'] // 64
        utility_gate += int(token_estimate or 0) * max(1, int(complexity or 1))

        bonus = max(0, utility_gate // 6)
        current['realm']['cultivation_points'] = int(current['realm'].get('cultivation_points', 0) or 0) + bonus
        current['total_cultivation'] = int(current.get('total_cultivation', 0) or 0) + bonus
        current['interaction_bonus']['last_triggered_at'] = now_iso()
        current['interaction_bonus']['last_reason'] = reason
        current['interaction_bonus']['last_bonus'] = bonus
        current['interaction_bonus']['last_token_estimate'] = int(token_estimate or 0)
        current['interaction_bonus']['last_complexity'] = int(complexity or 1)
        saved = self.save(current)
        return saved, bonus

    def record_realm_snapshot(self, realm):
        current = self.load()
        current['realm'].update({
            'current_realm': realm.get('current_realm', current['realm']['current_realm']),
            'stage': realm.get('stage', current['realm']['stage']),
            'cultivation_points': int(realm.get('cultivation_points', current['realm']['cultivation_points']) or 0),
            'breakthrough_threshold': int(realm.get('breakthrough_threshold', current['realm']['breakthrough_threshold']) or 0),
            'main_path': realm.get('main_path', current['realm']['main_path']),
            'spiritual_roots': realm.get('spiritual_roots', current['realm']['spiritual_roots'])
        })
        current['total_cultivation'] = int(current['realm']['cultivation_points'] or 0)
        return self.save(current)

    def trigger_rebirth(self, reason='context_overflow', summary=None):
        current = self.load()
        preserved = int(int(current.get('total_cultivation', 0) or 0) * 0.2)
        generation = int(current.get('rebirth', {}).get('generation', 1) or 1) + 1
        legacy_skill = None
        try:
            skills = sorted([p.name for p in (PROJECT_ROOT / 'demo_data' / 'skills').iterdir() if p.is_dir()])
            legacy_skill = skills[-1] if skills else None
        except Exception:
            legacy_skill = None
        rebirth_meta = {
            'generation': generation,
            'last_triggered_at': now_iso(),
            'last_reason': reason,
            'last_summary': summary,
            'preserved_foundation': preserved,
            'legacy_skill': legacy_skill
        }

        current['total_cultivation'] = preserved
        current['realm'].update({
            'current_realm': '炼气境',
            'stage': '初期',
            'cultivation_points': preserved,
            'breakthrough_threshold': 1000
        })
        current['offline']['pending_cultivation'] = 0
        current['offline']['pending_inner_demon'] = 0
        current['offline']['pending_minutes'] = 0
        current['tribulation']['last_result'] = 'rebirth'
        current['rebirth'] = rebirth_meta
        saved = self.save(current)
        return saved, rebirth_meta

    def record_sect_snapshot(self, sect):
        current = self.load()
        divisions = sect.get('divisions', {})
        current['sect']['order'] = int(sect.get('order', current['sect']['order']) or 0)
        current['sect']['last_dispatch'] = sect.get('last_dispatch')
        current['sect']['hall_assignments'] = {
            hall: len(divisions.get(hall, {}).get('assigned', []))
            for hall in current['sect']['hall_assignments'].keys()
        }
        history = list(current['sect'].get('dispatch_history', []))
        last_dispatch = sect.get('last_dispatch')
        if last_dispatch:
            history.append(last_dispatch)
            current['sect']['dispatch_history'] = history[-50:]
        return self.save(current)

    def record_tribulation(self, success, result_text=None):
        current = self.load()
        current['tribulation']['total_attempts'] += 1
        if success:
            current['tribulation']['success_count'] += 1
        else:
            current['tribulation']['failure_count'] += 1
        current['tribulation']['last_result'] = result_text or ('success' if success else 'failed')
        current['tribulation']['last_attempt_at'] = now_iso()
        return self.save(current)

    def normalize(self, data):
        base = default_save()
        merged = {**base, **data}
        merged['realm'] = {**base['realm'], **data.get('realm', {})}
        merged['tribulation'] = {**base['tribulation'], **data.get('tribulation', {})}
        merged['timekeeping'] = {**base['timekeeping'], **data.get('timekeeping', {})}
        merged['offline'] = {**base['offline'], **data.get('offline', {})}
        merged['interaction_bonus'] = {**base['interaction_bonus'], **data.get('interaction_bonus', {})}
        merged['rebirth'] = {**base['rebirth'], **data.get('rebirth', {})}
        merged['sect'] = {**base['sect'], **data.get('sect', {})}
        merged['sect']['hall_assignments'] = {
            **base['sect']['hall_assignments'],
            **data.get('sect', {}).get('hall_assignments', {})
        }
        return merged

    def migrate_or_default(self):
        base = default_save()

        realm_path = DATA_DIR / 'realm_progress.json'
        sect_path = DATA_DIR / 'sect_roster.json'

        if realm_path.exists():
            try:
                realm = json.loads(realm_path.read_text(encoding='utf-8'))
                base['realm'].update({
                    'current_realm': realm.get('current_realm', base['realm']['current_realm']),
                    'stage': realm.get('stage', base['realm']['stage']),
                    'cultivation_points': int(realm.get('cultivation_points', 0) or 0),
                    'breakthrough_threshold': int(realm.get('breakthrough_threshold', 1000) or 1000),
                    'main_path': realm.get('main_path', base['realm']['main_path']),
                    'spiritual_roots': realm.get('spiritual_roots', base['realm']['spiritual_roots'])
                })
                base['total_cultivation'] = int(realm.get('cultivation_points', 0) or 0)
            except Exception:
                pass

        if sect_path.exists():
            try:
                sect = json.loads(sect_path.read_text(encoding='utf-8'))
                divisions = sect.get('divisions', {})
                hall_assignments = {}
                for hall in base['sect']['hall_assignments'].keys():
                    hall_assignments[hall] = len(divisions.get(hall, {}).get('assigned', []))
                base['sect'].update({
                    'order': int(sect.get('order', 100) or 100),
                    'hall_assignments': hall_assignments,
                    'last_dispatch': sect.get('last_dispatch')
                })
            except Exception:
                pass

        return base


save_manager = SaveManager()
