"""Check a freshly downloaded OpenDBC full DBC against bundled example fields.

This checks only DBC layouts. It cannot prove Tiguan 2025 compatibility.
"""
from pathlib import Path
from tiguan_sim.dynamic_dbc import Catalog, DEFAULT_DBC

subset = Catalog.open(DEFAULT_DBC)
full_path = Path('dbc/upstream/vw_mqbevo.dbc')
full = Catalog.open(full_path)
existing = {m.name:m for m in full.messages}
problems=[]
for reference in subset.messages:
    upstream=existing.get(reference.name)
    if upstream is None:
        problems.append(f'{reference.name}: message not found')
        continue
    if (subset.can_id(reference),subset.length(reference)) != (full.can_id(upstream),full.length(upstream)):
        problems.append(f'{reference.name}: frame ID / length mismatch')
        continue
    signals={s.name:full.signal_info(s) for s in full.signals(upstream)}
    for s in subset.signals(reference):
        expected=subset.signal_info(s)
        actual=signals.get(s.name)
        if not actual:
            problems.append(f'{reference.name}.{s.name}: signal not found')
        elif any(float(expected[k])!=float(actual[k]) if k in ('scale','offset') else expected[k]!=actual[k]
                 for k in ('start','length','scale','offset')):
            problems.append(f'{reference.name}.{s.name}: layout mismatch')
print(f'Upstream catalog: {full.meta()["messages"]} messages, {full.meta()["signals"]} signals')
print(f'DBC SHA-256: {full.meta()["dbc_sha256"]}')
if problems:
    print('Reference subset mismatches (important for interpretation):')
    for p in problems: print(' -',p)
    print('WARNING: Using the full upstream DBC remains possible, but do not assume the bundled subset matches it.')
print('Selected subset message layouts match the downloaded DBC.')
print('NOTE: No exact compatibility validation with VW Tiguan CT 2025 has been performed.')
