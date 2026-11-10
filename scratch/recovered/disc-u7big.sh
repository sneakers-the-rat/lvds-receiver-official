#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
D=$HOME/workspace/pdlvds-v6run
cd $R
export DISPLAY=:99
L=$R/results/disc-u7big.log
echo "=== disc u7big start $(date -u +%H:%M:%S) ===" >> $L
SRC=hw/pdlvds_rx.fr59.kicad_pcb
for i in 1 2 3 4 5 6 7 8; do
  O=$D/disc-u7big-$i.kicad_pcb
  python3 -u hw/clear_disc.py $SRC $O 30 61 5.5 25 "" 2>&1 | grep -v 'swig/python' | python3 -u $D/tswrap.py >> $L 2>&1
  SRC=$O
done
cp $SRC hw/pdlvds_rx.fr61.kicad_pcb
echo "=== disc u7big cleared $(date -u +%H:%M:%S) ===" >> $L
