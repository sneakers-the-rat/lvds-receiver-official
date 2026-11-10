#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
cd $R
export DISPLAY=:99
echo "=== ripup-all batch start $(date -u +%H:%M:%S) ===" >> $R/results/ripup-fr3.log
python3 -u hw/ripup.py hw/pdlvds_rx.fr2.kicad_pcb hw/pdlvds_rx.fr3.kicad_pcb 8 all 2>&1 | python3 -u /tmp/tswrap.py >> $R/results/ripup-fr3.log 2>&1
echo "=== ripup-all batch exit $(date -u +%H:%M:%S) ===" >> $R/results/ripup-fr3.log
