#!/bin/bash
# Freerouting run 2 (Path B): official jar 2.5.0 under OpenJDK 25,
# pass-10 DSN -> SES, 20 passes. Detached via setsid by the launcher.
# Progress: freerouting's own timestamped lines go to the jar log;
# this wrapper adds a 60 s heartbeat to fr2-heartbeat.log and a final
# status line to freerouting-run2.status.
set -u
cd "$(dirname "$0")"
LOG=freerouting-jar2.log
HB=fr2-heartbeat.log
STATUS=freerouting-run2.status
JAVA=/usr/lib/jvm/java-25-openjdk-amd64/bin/java
JAR=$HOME/workspace/tools/freerouting/freerouting-2.5.0.jar
echo "$(date -Is) run2 wrapper start pid=$$" >> "$LOG"
( while true; do
    sleep 60
    echo "$(date -Is) heartbeat ses=$(test -f pass10.ses && echo yes || echo no) jarlog_lines=$(wc -l < "$LOG")" >> "$HB"
  done ) &
HBPID=$!
"$JAVA" -jar "$JAR" -de pass10.dsn -do pass10.ses -mp 20 >> "$LOG" 2>&1
RC=$?
kill "$HBPID" 2>/dev/null
echo "$(date -Is) java exited rc=$RC ses=$(test -f pass10.ses && echo yes || echo no)" >> "$LOG"
echo "rc=$RC finished=$(date -Is)" > "$STATUS"
ls -la pass10.ses >> "$STATUS" 2>/dev/null || echo "no ses file" >> "$STATUS"
