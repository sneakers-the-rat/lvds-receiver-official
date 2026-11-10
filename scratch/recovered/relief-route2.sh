#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
LOG=$R/results/freerouting-relief2.log
echo "=== relief route run 2 (-mp 6, no timeout) start $(date -u +%H:%M:%S) ===" >> $LOG
cd $R && /usr/lib/jvm/java-25-openjdk-amd64/bin/java -Djava.awt.headless=true -jar $HOME/workspace/tools/freerouting/freerouting-2.5.0.jar -de $R/results/relief.dsn -do $R/results/relief.ses -mp 6 >> $LOG 2>&1
echo "FREEROUTING_EXIT=$? $(date -u +%H:%M:%S)" >> $LOG
