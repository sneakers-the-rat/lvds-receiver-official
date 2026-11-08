#!/bin/bash
# t_ai0: verify frontier baseline (exp219) with both referees before any edit.
set -u
cd ~/workspace/pdlvds-route
B=hw/pdlvds_rx.exp219.kicad_pcb
kicad-cli pcb drc --output scratch/work/ai/drc-exp219-baseline.json --format json "$B" 2>/dev/null
python3 - <<'EOF'
import json, collections
d = json.load(open('scratch/work/ai/drc-exp219-baseline.json'))
v = d.get('violations', [])
c = collections.Counter(x['type'] for x in v)
print('KiCad DRC violations:', len(v))
for k, n in sorted(c.items()):
    print(f'  {k}: {n}')
u = d.get('unconnected_items', [])
print('KiCad unconnected items:', len(u))
for x in u:
    print('  UNC:', x.get('description', x))
EOF
xvfb-run -a python3 hw/check_pcb.py "$B" > scratch/work/ai/check-exp219-baseline.txt 2>&1
grep -E "copper items|unconnected nets|clearance violations|courtyard|blind" scratch/work/ai/check-exp219-baseline.txt | head -20
grep -c "^  CLEARANCE" scratch/work/ai/check-exp219-baseline.txt || true
