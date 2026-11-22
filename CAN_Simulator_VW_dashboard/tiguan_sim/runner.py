"""Offline-only generator: MQBevo reference layout, simulated measurements and faults.

Frames containing checksum-like signals have placeholder bytes and must not be
replayed to a real automotive bus. They exist for hex/DBC exploration only.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json

from .dbc_codec import load_dbc, encode, decode
from .scenarios import SCENARIOS, DURATION, DT, GROUND_TRUTH, vehicle_state
from .detector import infer_events, derive_dtcs

ROOT = Path(__file__).resolve().parent.parent
DBC_PATH = ROOT/'dbc'/'vw_mqbevo_reference_subset.dbc'
OBS_ROOT = ROOT/'output'/'observations'
EVAL_ROOT = ROOT/'output'/'evaluation'


def write_jsonl(path: Path, rows: list[dict]):
    path.write_text(''.join(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n' for row in rows),encoding='utf-8')


def build_frames(states: list[dict], dbc: dict):
    frames=[]
    for i,s in enumerate(states):
        t=s['t_s']
        specs = [
          ('Motor_04',{'MO_Istgang':s['gear'],'MO_Sollgang':s['gear'],
                       'MO_Oeldruck':2.8,'MO_Anzeigedrehz':s['rpm'],
                       'MO_Ladedruck':1.3+s['speed']/200}),
          ('Getriebe_11',{'CHECKSUM':0,'COUNTERXX':i%16,'GE_Fahrstufe':8,
                          'GE_Schaltvorgang':0,'GE_Status_Kupplung':1,'GE_Zielgang':s['gear']}),
        ]
        if s['abs_online']:
            specs.append(('ESP_NEW_1',{
               'XCHECKSUM':0,'COUNTER':i%16,
               'WHEEL_SPEED_FL':s['wheel_fl'],'WHEEL_SPEED_FR':s['wheel_fr'],
               'WHEEL_SPEED_RL':s['wheel_rl'],'WHEEL_SPEED_RR':s['wheel_rr'],
            }))
        for name,values in specs:
            msg=dbc[name]
            raw=encode(msg,values)
            decoded=decode(msg,raw)
            frames.append({'t_s':t,'can_id':f'0x{msg.can_id:03X}','data_hex':raw.hex().upper(),
               'message':name,'ecu':msg.ecu,'is_fd':len(raw)>8,
               'length':len(raw),'signals':decoded,
               'format_provenance':'OpenDBC MQBevo subset; 2025 Tiguan mapping unconfirmed',
               'crc_validated':None if name=='Motor_04' else False,
               'bus_injectable':False})
    return frames


def run_scenario(scenario: str, output_root: Path=OBS_ROOT, evaluation_root: Path=EVAL_ROOT):
    if scenario not in SCENARIOS: raise ValueError('Unknown scenario')
    dbc=load_dbc(DBC_PATH)
    states=[vehicle_state(i*DT,scenario) for i in range(int(DURATION/DT)+1)]
    events=infer_events(states)
    dtcs=derive_dtcs(events)
    frames=build_frames(states,dbc)
    out=output_root/scenario
    out.mkdir(parents=True,exist_ok=True)
    write_jsonl(out/'frames.jsonl',frames)
    # No hidden injection metadata in observation files!
    visible=[{k:v for k,v in row.items() if k not in ('scenario','fault_type')} for row in states]
    write_jsonl(out/'telemetry.jsonl',visible)
    write_jsonl(out/'events.jsonl',events)
    write_jsonl(out/'dtcs.jsonl',dtcs)
    (out/'candump.log').write_text(''.join(f'({1700000000+f["t_s"]:.6f}) vcan0 {f["can_id"][2:]}{"##0" if f["is_fd"] else "#"}{f["data_hex"]}\n' for f in frames),encoding='utf-8')
    summary={
      'scenario':scenario,'duration_s':DURATION,'frames_sent':len(frames),
      'fd_frames':sum(1 for f in frames if f['is_fd']),
      'events_detected':[e['type'] for e in events],
      'confirmed_dtcs':[x['code'] for x in dtcs],
      'source':'synthetic_mqbevo_reference_subset',
      'dbc_name':DBC_PATH.name,'dbc_sha256':hashlib.sha256(DBC_PATH.read_bytes()).hexdigest(),
      'real_vehicle_capture':False,'oem_checksum_implemented':False,
      'vehicle_compatibility_verified':False,
    }
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    truth={'scenario':scenario,'injected_faults':GROUND_TRUTH[scenario],
           'injection_starts_s':22,'internal_only':True}
    folder=evaluation_root/scenario
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'ground_truth.json').write_text(json.dumps(truth,ensure_ascii=False,indent=2),encoding='utf-8')
    return summary


def main():
    import argparse
    p=argparse.ArgumentParser(description='Tiguan 2025 TDI 4MOTION offline diagnostic demonstrator')
    p.add_argument('--scenario',choices=[*SCENARIOS,'all'],default='all')
    p.add_argument('--backend',choices=['offline'],default='offline')
    a=p.parse_args()
    for scenario in (SCENARIOS if a.scenario=='all' else [a.scenario]):
        result=run_scenario(scenario)
        print(f'{scenario}: {result["frames_sent"]} CAN frames; events={result["events_detected"]}; simulated DTCs={result["confirmed_dtcs"]}')

if __name__=='__main__':main()
