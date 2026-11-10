#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
cd $R
export DISPLAY=:99
echo "=== repair6 on fr1 start $(date -u +%H:%M:%S) ===" >> $R/results/repair6-fr1.log
python3 -u hw/repair6.py hw/pdlvds_rx.fr1.kicad_pcb hw/pdlvds_rx.fr1r.kicad_pcb 2>&1 | python3 -u /tmp/tswrap.py >> $R/results/repair6-fr1.log 2>&1
echo "=== repair6 exit $(date -u +%H:%M:%S) ===" >> $R/results/repair6-fr1.log
