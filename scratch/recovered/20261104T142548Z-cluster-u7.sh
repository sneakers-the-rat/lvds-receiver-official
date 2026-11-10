#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
cd $R
export DISPLAY=:99
L=$R/results/cluster-u7.log
echo "=== cluster U7 v2 start $(date -u +%H:%M:%S) ===" >> $L
SRC=hw/pdlvds_rx.fr2.kicad_pcb
for i in 1 2 3 4; do
  OUT=/tmp/disc$i.kicad_pcb
  python3 -u hw/clear_disc.py $SRC $OUT 30.3 57.6 3.4 25 +3V3A,PHY_1V8,PHY_1V8A 2>/dev/null | python3 -u /tmp/tswrap.py >> $L 2>&1
  SRC=$OUT
done
cp $SRC hw/pdlvds_rx.fr4.kicad_pcb
python3 -u hw/cluster.py hw/pdlvds_rx.fr4.kicad_pcb hw/pdlvds_rx.fr4.kicad_pcb 0 0 0 +3V3A:U7.25,U7.30,U7.31 PHY_1V8:U7.26 PHY_1V8A:U7.29 2>&1 | grep -v 'swig/python' | python3 -u /tmp/tswrap.py >> $L 2>&1
echo "=== cluster U7 v2 exit $(date -u +%H:%M:%S) ===" >> $L
