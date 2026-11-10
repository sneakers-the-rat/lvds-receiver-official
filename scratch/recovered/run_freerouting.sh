#!/bin/bash
# Freerouting completion attempt on the pass-75 (exp12) board.
# Precedent: results/alt-paths/work/run_freerouting2.sh (jar 2.5.0,
# OpenJDK 25, -de/-do/-mp). Differences, deliberate:
#   -mp 10 (not 20): fr21 precedent showed ~460 s/pass on this class
#     of board; 20 passes would overrun the 90-min budget and a
#     killed run writes NO ses (fr21 exit 143 evidence). 10 passes
#     is sized to finish inside the budget so a session file exists
#     to import and audit.
#   timeout 5400 (90 min) hard cap per the task brief; on expiry the
#     wrapper records the state and stops the jar (TERM, then KILL).
set -u
cd "$(dirname "$0")"
LOG=freerouting.log
HB=freerouting-heartbeat.log
STATUS=freerouting.status
JAVA=/usr/lib/jvm/java-25-openjdk-amd64/bin/java
JAR=$HOME/workspace/tools/freerouting/freerouting-2.5.0.jar
echo "$(date -Is) fr-attempt wrapper start pid=$$" >> "$LOG"
( while true; do
    sleep 60
    echo "$(date -Is) heartbeat ses=$(test -f exp12.ses && echo yes || echo no) jarlog_lines=$(wc -l < "$LOG")" >> "$HB"
  done ) &
HBPID=$!
timeout --signal=TERM --kill-after=30 5400 \
  "$JAVA" -jar "$JAR" -de exp12.dsn -do exp12.ses -mp 10 >> "$LOG" 2>&1
RC=$?
kill "$HBPID" 2>/dev/null
echo "$(date -Is) java exited rc=$RC ses=$(test -f exp12.ses && echo yes || echo no)" >> "$LOG"
echo "rc=$RC finished=$(date -Is)" > "$STATUS"
ls -la exp12.ses >> "$STATUS" 2>/dev/null || echo "no ses file" >> "$STATUS"
