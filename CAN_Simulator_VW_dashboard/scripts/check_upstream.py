"""Check selected signal layouts against the downloaded OpenDBC full DBC."""
from pathlib import Path
from tiguan_sim.dbc_codec import load_dbc

reference=load_dbc(Path('dbc/vw_mqbevo_reference_subset.dbc'))
upstream=load_dbc(Path('dbc/upstream/vw_mqbevo.dbc'))
diff=[]
for name,msg in reference.items():
    original=upstream.get(name)
    if not original or (original.can_id,original.size)!=(msg.can_id,msg.size):
        diff.append(f'{name}: CAN ID sau lungime diferită')
        continue
    for sig, spec in msg.signals.items():
        actual=original.signals.get(sig)
        if actual is None or (spec.start,spec.length,spec.factor,spec.offset)!=(actual.start,actual.length,actual.factor,actual.offset):
            diff.append(f'{name}.{sig}: definiție diferită')
if diff:
    print('DIFERENȚE:',*diff,sep='\n  ')
    raise SystemExit(1)
print('OK: subset-ul de layout coincide cu definițiile selectate din OpenDBC.')
print('Atenție: compatibilitatea exactă cu Tiguan 2025 rămâne neverificată.')
