#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
D=$HOME/workspace/pdlvds-v6run
cd $R
export DISPLAY=:99
L=$R/results/repairg-fr20.log
echo "=== repairg fr20 start $(date -u +%H:%M:%S) ===" >> $L
python3 -u hw/repairg.py hw/pdlvds_rx.fr19.kicad_pcb hw/pdlvds_rx.fr20.kicad_pcb 2>&1 | grep -v 'swig/python' | python3 -u $D/tswrap.py >> $L 2>&1
echo "=== repairg fr20 exit $(date -u +%H:%M:%S) ===" >> $L
