"""Read-only observations adapter. Evaluation/ground_truth is deliberately unreachable."""
from __future__ import annotations
from bisect import bisect_left
from functools import lru_cache
from pathlib import Path
import json

from tiguan_sim.scenarios import SCENARIOS
from tiguan_sim.runner import OBS_ROOT

SIGNALS = {
 'speed':'Viteză vehicul', 'rpm':'Turație motor','voltage':'Tensiune 12 V',
 'coolant':'Temperatură răcire', 'wheel_fl':'Viteză roată FL',
 'wheel_fr':'Viteză roată FR','wheel_rl':'Viteză roată RL',
 'wheel_rr':'Viteză roată RR', 'dpf_pressure':'Presiune diferențială DPF',
 'soot':'Încărcare estimată DPF','egr_command':'Comandă EGR',
 'egr_actual':'Feedback EGR','dsg_temp':'Temperatură DSG',
 'awd_requested':'Cerere cuplare AWD','awd_actual':'Feedback cuplare AWD',
}


def _folder(scenario):
    if scenario not in SCENARIOS:
        raise ValueError('Invalid scenario')
    return OBS_ROOT / scenario


def _read_json(path):
    if not path.is_file(): raise FileNotFoundError(f'Lipsesc datele pentru {path.parent.name}. Rulează python -m tiguan_sim --scenario all')
    return json.loads(path.read_text(encoding='utf-8'))


@lru_cache(maxsize=64)
def _cached_lines(name,size,mtime):
    with Path(name).open(encoding='utf-8') as file:
        return [json.loads(s) for s in file if s.strip()]


def _read_jsonl(path):
    if not path.is_file(): return []
    st=path.stat()
    return _cached_lines(str(path),st.st_size,st.st_mtime_ns)


def scenario_index():
    return [{'id':name,'title':meta[0],'description':meta[1],
             'available':(_folder(name)/'summary.json').is_file()}
            for name,meta in SCENARIOS.items()]


def get_scenario(scenario):
    folder=_folder(scenario)
    summary=_read_json(folder/'summary.json')
    states=_read_jsonl(folder/'telemetry.jsonl')
    events=_read_jsonl(folder/'events.jsonl')
    dtcs=_read_jsonl(folder/'dtcs.jsonl')
    telemetry={name:[] for name in SIGNALS}
    for row in states:
        for name in telemetry:
            value=row.get(name)
            if name.startswith('wheel_') and not row['abs_online']:
                continue  # prevent displaying measured wheel speeds after ABS ECU dropout
            if isinstance(value,(int,float)) and not isinstance(value,bool):
                telemetry[name].append({'t':row['t_s'],'v':value})
    return {
      'scenario':scenario,'title':SCENARIOS[scenario][0],
      'duration_s':summary['duration_s'],'source':summary.get('source','simulated_mqbevo_subset'),
      'source_label':('DBC dynamic – date sintetice / campuri nemapate neutre' if summary.get('engine')=='dynamic_dbc' else 'MQBevo OpenDBC subset – numai layout de referință, date simulate'),
      'summary':summary,'events':events,'dtcs':dtcs,'telemetry':telemetry,
      'signal_names':SIGNALS,
      'limitations':{
         'tiguan_2025_dbc_verified':False,'real_log_used':False,
         'dpf_egr_dsg_awd_data':'Senzori virtuali; fără DID-uri OEM verificate',
         'individual_wheel_speeds':'ESP_NEW_1 exploratoriu, nu validat pe Tiguan 2025',
         'oem_crc':'Neimplementat pentru ESP_NEW_1 și Getriebe_11',
         'diagnosis':'Reguli deterministe; ipoteze, nu confirmare reparație',
      }
    }


def get_frames(scenario, at=0,limit=40,search=''):
    folder=_folder(scenario)
    _read_json(folder/'summary.json')
    frames=_read_jsonl(folder/'frames.jsonl')
    times=[float(f['t_s']) for f in frames]
    start=bisect_left(times,max(0,at-.75))
    end=bisect_left(times,at+.751)
    subset=frames[start:end]
    if search:
        q=search.lower().strip()
        subset=[f for f in subset if q in ' '.join([f['can_id'],f['message'],f['data_hex']]).lower()]
    return {'frames':subset[-limit:],'total_window':len(subset),'source':'dbc_synthetic'}
