#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
D=$HOME/workspace/pdlvds-v6run
cd $R
export DISPLAY=:99
L=$R/results/repair6-fr5.log
echo "=== repair fr5 start $(date -u +%H:%M:%S) ===" >> $L
python3 -u hw/repair6.py hw/pdlvds_rx.fr4.kicad_pcb hw/pdlvds_rx.fr5.kicad_pcb 2>&1 | grep -v 'swig/python' | python3 -u $D/tswrap.py >> $L 2>&1
echo "=== repair fr5 exit $(date -u +%H:%M:%S) ===" >> $L
