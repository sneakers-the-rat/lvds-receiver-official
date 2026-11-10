#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
cd $R
L=$R/results/freerouting-complete.log
echo "=== freerouting completion start $(date -u +%H:%M:%S) ===" >> $L
java -jar $HOME/workspace/tools/freerouting/freerouting-2.5.0.jar -de results/fr21-fr.dsn -do results/fr21.ses -mp 10 >> $L 2>&1
echo "FREEROUTING_EXIT=$? $(date -u +%H:%M:%S)" >> $L
ls -la results/fr21.ses >> $L 2>&1
