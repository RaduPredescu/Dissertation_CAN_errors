"""DBC-driven synthetic CAN generator. No hardware interface is provided.

Uses cantools when installed (supports Intel/Motorola, signed, multiplexed).
An intentionally restricted built-in fallback supports the bundled Intel-only
reference subset when cantools cannot be installed in an offline environment.
A DBC is a wire-layout catalogue, not a real vehicle dynamics model.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import math
import re

from .dbc_codec import load_dbc as load_subset, encode as encode_subset, decode as decode_subset
from .scenarios import DURATION, DT, SCENARIOS, GROUND_TRUTH, vehicle_state
from .detector import infer_events, derive_dtcs

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DBC = ROOT / 'dbc' / 'vw_mqbevo_reference_subset.dbc'
DEFAULT_MAP = ROOT / 'config' / 'signal_sources.json'
OBS_ROOT = ROOT / 'output' / 'observations'
EVAL_ROOT = ROOT / 'output' / 'evaluation'

CRC_FIELDS = re.compile(r'(CHECKSUM|\bCRC\b|CRC_|_CRC|XCHECK)', re.I)
COUNTER_FIELDS = re.compile(r'(COUNTER|ALIVE|ROLLING_COUNT)', re.I)
SPECIAL = re.compile(r'(CHECKSUM|\bCRC\b|CRC_|_CRC|COUNTER|ALIVE|ROLLING_COUNT|XCHECK)', re.I)


def _number(value):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and math.isfinite(value):
        return float(value)
    return None


def _serialize(value):
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        return round(value, 6)
    return str(value)


@dataclass
class Catalog:
    path: Path
    backend: str
    messages: list

    @classmethod
    def open(cls, path: Path):
        path = Path(path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f'DBC file missing: {path}')
        try:
            import cantools
        except ImportError:
            if path.name != 'vw_mqbevo_reference_subset.dbc':
                raise RuntimeError('Full / advanced DBC parsing requires cantools: python -m pip install cantools')
            return cls(path, 'limited-subset-fallback', list(load_subset(path).values()))
        try:
            db = cantools.database.load_file(str(path), strict=False, prune_choices=True)
        except Exception as exc:
            raise ValueError(f'Cannot parse DBC using cantools: {exc}') from exc
        return cls(path, f'cantools-{cantools.__version__}', list(db.messages))

    def signal_info(self, s):
        if self.backend == 'limited-subset-fallback':
            return dict(name=s.name, start=s.start, length=s.length,
                        byte_order=s.byte_order, signed=False, scale=s.factor,
                        offset=s.offset, minimum=None, maximum=None, unit=None,
                        choices={}, multiplexer_ids=None, multiplexer_signal=None,
                        is_multiplexer=False)
        conv = s.conversion
        return dict(name=s.name, start=s.start, length=s.length,
                    byte_order=s.byte_order, signed=s.is_signed,
                    scale=_serialize(conv.scale), offset=_serialize(conv.offset),
                    minimum=s.minimum, maximum=s.maximum, unit=s.unit,
                    choices={str(k): str(v) for k, v in (s.choices or {}).items()},
                    multiplexer_ids=s.multiplexer_ids,
                    multiplexer_signal=s.multiplexer_signal,
                    is_multiplexer=s.is_multiplexer)

    @staticmethod
    def signals(msg):
        return list(msg.signals.values()) if isinstance(msg.signals, dict) else list(msg.signals)

    @staticmethod
    def can_id(msg):
        return msg.can_id if hasattr(msg, 'can_id') else msg.frame_id

    @staticmethod
    def length(msg):
        return msg.size if hasattr(msg, 'size') else msg.length

    @staticmethod
    def ecu(msg):
        return msg.ecu if hasattr(msg, 'ecu') else (msg.senders[0] if msg.senders else 'Unknown')

    @staticmethod
    def cycle(msg):
        return getattr(msg, 'cycle_time', None)

    def is_fd(self, msg):
        return self.length(msg) > 8 or bool(getattr(msg, 'is_fd', False))

    def encode(self, msg, values):
        if self.backend == 'limited-subset-fallback':
            return encode_subset(msg, values)
        return msg.encode(values, strict=False)

    def decode(self, msg, raw):
        if self.backend == 'limited-subset-fallback':
            return decode_subset(msg, raw)
        return msg.decode(raw, decode_choices=False)

    def meta(self):
        return {'dbc_file': self.path.name,
                'dbc_sha256': hashlib.sha256(self.path.read_bytes()).hexdigest(),
                'parser': self.backend, 'messages': len(self.messages),
                'signals': sum(len(self.signals(m)) for m in self.messages),
                'vehicle_verified': False, 'actual_vehicle_capture': False}

    def describe(self, msg, signal_sources):
        signal_list = [self.signal_info(s) for s in self.signals(msg)]
        mapped = set(signal_sources.get(msg.name, {}))
        for s in signal_list:
            if s['name'] in mapped:
                s['generation'] = 'behavior_model'
                s['state_source'] = signal_sources[msg.name][s['name']]
            elif SPECIAL.search(s['name']):
                s['generation'] = 'placeholder_counter_or_checksum'
            else:
                s['generation'] = 'neutral_synthetic'
        return {'name': msg.name, 'can_id': f'0x{self.can_id(msg):X}',
                'length': self.length(msg), 'is_fd': self.is_fd(msg),
                'sender': self.ecu(msg), 'cycle_time_ms': self.cycle(msg),
                'signal_count': len(signal_list), 'mapped_signals': sum(s['generation']=='behavior_model' for s in signal_list),
                'signals': signal_list}



@lru_cache(maxsize=8)
def _cached_catalog(path_text, size, mtime_ns):
    return Catalog.open(Path(path_text))


def get_catalog(path):
    p=Path(path).resolve()
    st=p.stat()
    return _cached_catalog(str(p),st.st_size,st.st_mtime_ns)

def load_mapping(path=DEFAULT_MAP):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data.get('messages'), dict):
        raise ValueError('Config must contain a messages object')
    return data


def safe_default(info, tick):
    name = info['name']
    lo, hi = _number(info['minimum']), _number(info['maximum'])
    if SPECIAL.search(name):
        # Placeholder only: OEM checksum/counter is NOT calculated or validated.
        val = tick % 16 if re.search('COUNTER|ALIVE|ROLLING_COUNT', name, re.I) else 0
    else:
        val = 0
        if lo is not None and lo > 0:
            val = lo
        if hi is not None and hi < 0:
            val = hi
    if lo is not None: val = max(lo, val)
    if hi is not None: val = min(hi, val)
    return val


def _mux_values(signals):
    """Choose a valid first multiplexer branch; nested muxes are best-effort."""
    selected = {}
    for s in signals:
        if s['is_multiplexer']:
            values = set()
            for branch in signals:
                if branch['multiplexer_signal'] == s['name'] and branch['multiplexer_ids']:
                    values.update(branch['multiplexer_ids'])
            selected[s['name']] = min(values) if values else 0
    return selected


def fields_for(msg, catalog: Catalog, state, tick, mapping):
    """Supply all active fields; unrelated signals get neutral synthetic values."""
    infos = [catalog.signal_info(s) for s in catalog.signals(msg)]
    spec = mapping.get('messages', {}).get(msg.name, {})
    choices = _mux_values(infos)
    values, origin = {}, {}
    for info in infos:
        key = info['name']
        branch = info['multiplexer_signal']
        if branch is not None and info['multiplexer_ids'] is not None:
            if choices.get(branch, 0) not in info['multiplexer_ids']:
                continue
        if key in choices:
            val = choices[key]
            why = 'mux_selector'
        elif key in spec:
            state_key = spec[key]
            if state_key not in state:
                raise ValueError(f'Missing modeled state {state_key} for {msg.name}.{key}')
            val = state[state_key]
            why = 'behavior_model'
        else:
            val = safe_default(info, tick)
            why = 'placeholder' if SPECIAL.search(key) else 'neutral_synthetic'
        lo, hi = _number(info['minimum']), _number(info['maximum'])
        if isinstance(val,(int,float)):
            if lo is not None: val = max(lo,val)
            if hi is not None: val = min(hi,val)
        values[key] = val
        origin[key] = why
    return values, origin


def _jsonl(path, entries):
    with path.open('w', encoding='utf-8') as fp:
        for entry in entries:
            fp.write(json.dumps(entry, ensure_ascii=False, separators=(',', ':')) + '\n')


def run_dynamic_scenario(scenario, dbc_path=DEFAULT_DBC, mapping_path=DEFAULT_MAP,
                         output_root=OBS_ROOT, evaluation_root=EVAL_ROOT,
                         max_messages=0, min_cycle_ms=500):
    if scenario not in SCENARIOS:
        raise ValueError('Unknown scenario')
    if max_messages < 0 or min_cycle_ms < 1:
        raise ValueError('Invalid runtime options')
    catalog = get_catalog(dbc_path)
    mapping = load_mapping(mapping_path)
    messages = sorted(catalog.messages, key=lambda x: catalog.can_id(x))
    if max_messages:
        messages = messages[:max_messages]
    states = [vehicle_state(round(i * DT, 5), scenario) for i in range(round(DURATION/DT)+1)]
    frames, failed = [], {}
    for msg in messages:
        # DBC cycle-time is a hint, not a measured transmit rate. Never
        # accelerate beyond the requested simulation sampling cap.
        declared_ms = catalog.cycle(msg)
        interval_ms = max(min_cycle_ms, declared_ms or min_cycle_ms)
        interval_steps = max(1, math.ceil(interval_ms / (DT * 1000)))
        online_key = mapping.get('message_online_state', {}).get(msg.name)
        for tick in range(0, len(states), interval_steps):
            state = states[tick]
            if online_key and not state.get(online_key, False):
                continue
            try:
                values, origins = fields_for(msg, catalog, state, tick, mapping)
                raw = catalog.encode(msg, values)
                decoded = catalog.decode(msg, raw)
                # If using choices, only provide JSON-safe values.
                decoded = {k:_serialize(v) for k,v in decoded.items()}
            except (ValueError, KeyError, TypeError, OverflowError, IndexError, AssertionError) as exc:
                failed.setdefault(msg.name, str(exc)[:150])
                break
            frames.append({
                't_s': state['t_s'], 'can_id': f'0x{catalog.can_id(msg):X}',
                'data_hex': raw.hex().upper(), 'message': msg.name, 'ecu': catalog.ecu(msg),
                'is_fd': catalog.is_fd(msg), 'length':len(raw), 'signals': decoded,
                'signal_origin': origins, 'generation_mode': 'dbc_structural_synthetic',
                'format_provenance': 'DBC reference; Tiguan 2025 not verified',
                'crc_validated':False if any(CRC_FIELDS.search(n) for n in values) else None,
                'counter_validated':False if any(COUNTER_FIELDS.search(n) for n in values) else None,
                'bus_injectable':False,
            })
    frames.sort(key=lambda f: (f['t_s'], int(f['can_id'], 16)))
    events = infer_events(states)
    dtcs = derive_dtcs(events)
    folder = Path(output_root) / scenario
    folder.mkdir(parents=True,exist_ok=True)
    _jsonl(folder / 'frames.jsonl', frames)
    _jsonl(folder / 'telemetry.jsonl', [{k:v for k,v in row.items() if k not in ('scenario','fault_type')} for row in states])
    _jsonl(folder / 'events.jsonl', events)
    _jsonl(folder / 'dtcs.jsonl', dtcs)
    with (folder/'candump.log').open('w',encoding='utf-8') as fp:
        for f in frames:
            fp.write(f'({1700000000+f["t_s"]:.6f}) vcan0 {f["can_id"][2:]}{"##0" if f["is_fd"] else "#"}{f["data_hex"]}\n')
    meta = catalog.meta()
    summary = {
        'scenario': scenario, 'engine': 'dynamic_dbc', 'duration_s':DURATION,
        'frames_sent':len(frames), 'fd_frames':sum(1 for f in frames if f['is_fd']),
        'messages_in_dbc':meta['messages'], 'messages_requested':len(messages),
        'messages_emitted':len({f['message'] for f in frames}),
        'messages_skipped':failed, 'events_detected':[e['type'] for e in events],
        'confirmed_dtcs':[d['code'] for d in dtcs],
        'source':'synthetic_dbc_structural', 'dbc_name':meta['dbc_file'],
        'dbc_sha256':meta['dbc_sha256'], 'parser':meta['parser'],
        'real_vehicle_capture':False, 'vehicle_compatibility_verified':False,
        'oem_checksum_implemented':False, 'sampling_floor_ms':min_cycle_ms,
        'note':'Unmapped signals use neutral synthetic placeholders; DBC timing is not a validated bus schedule.',
    }
    (folder / 'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    private = Path(evaluation_root) / scenario
    private.mkdir(parents=True,exist_ok=True)
    (private/'ground_truth.json').write_text(json.dumps({
        'scenario':scenario, 'injected_faults':GROUND_TRUTH[scenario],
        'injection_starts_s':22, 'internal_only':True,
    },ensure_ascii=False,indent=2),encoding='utf-8')
    return summary


def catalog_index(dbc_path=DEFAULT_DBC, mapping_path=DEFAULT_MAP, search='', offset=0, limit=60):
    catalog = get_catalog(dbc_path)
    mapping = load_mapping(mapping_path)
    matches = [catalog.describe(m, mapping['messages']) for m in catalog.messages]
    if search:
        q = search.strip().lower()
        matches = [m for m in matches if q in m['name'].lower() or q in m['can_id'].lower() or
                   any(q in s['name'].lower() for s in m['signals'])]
    total = len(matches)
    small = [{k:v for k,v in m.items() if k!='signals'} for m in matches[offset:offset+limit]]
    return {'dbc':catalog.meta(), 'total':total, 'offset':offset, 'limit':limit,
            'messages':small, 'data_note':'Catalog is sourced from the chosen DBC; vehicle matching is unverified.'}


def catalog_detail(name, dbc_path=DEFAULT_DBC, mapping_path=DEFAULT_MAP):
    catalog = get_catalog(dbc_path)
    mapping = load_mapping(mapping_path)
    for msg in catalog.messages:
        if msg.name == name:
            return catalog.describe(msg,mapping['messages'])
    raise KeyError(name)
