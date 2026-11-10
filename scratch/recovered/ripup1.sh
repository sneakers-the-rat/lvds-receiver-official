#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
cd $R
export DISPLAY=:99
echo "=== ripup batch start $(date -u +%H:%M:%S) ===" >> $R/results/ripup-fr2.log
python3 -u hw/ripup.py hw/pdlvds_rx.fr1r.s2.kicad_pcb hw/pdlvds_rx.fr2.kicad_pcb 12 2>&1 | python3 -u /tmp/tswrap.py >> $R/results/ripup-fr2.log 2>&1
echo "=== ripup batch exit $(date -u +%H:%M:%S) ===" >> $R/results/ripup-fr2.log
