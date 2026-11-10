#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
LOG=$R/results/freerouting-relief.log
echo "=== relief chain start $(date -u +%H:%M:%S) ===" >> $LOG
for i in $(seq 1 90); do
  if DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends openjdk-25-jre-headless >> $R/results/jre25-install.log 2>&1; then
    echo "jre25 installed on attempt $i $(date -u +%H:%M:%S)" >> $LOG; break
  fi
  sleep 20
done
/usr/lib/jvm/java-25-openjdk-amd64/bin/java -version >> $LOG 2>&1
cd $R && timeout 3300 /usr/lib/jvm/java-25-openjdk-amd64/bin/java -Djava.awt.headless=true -jar $HOME/workspace/tools/freerouting/freerouting-2.5.0.jar -de $R/results/relief.dsn -do $R/results/relief.ses -mp 40 >> $LOG 2>&1
echo "FREEROUTING_EXIT=$? $(date -u +%H:%M:%S)" >> $LOG
