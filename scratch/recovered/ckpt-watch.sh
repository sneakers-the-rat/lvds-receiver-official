#!/bin/bash
# Copy each repair6 checkpoint state to its own file so every saved
# state survives for its own pass commit. A copy is taken only when
# the board file's size+mtime have been stable for >4 s (never mid-save).
R=$HOME/workspace/photodiode-lvds-rx
LOG=$R/results/repair6-fr1.log
OUT=$R/hw/pdlvds_rx.fr1r.kicad_pcb
copied=2   # ckpt1, ckpt2 already copied+committed by hand
while true; do
  n=$(grep -c 'checkpoint:' $LOG 2>/dev/null || echo 0)
  if [ "$n" -gt "$copied" ]; then
    s1=$(stat -c '%s %Y' $OUT); sleep 4; s2=$(stat -c '%s %Y' $OUT)
    if [ "$s1" = "$s2" ]; then
      copied=$((copied+1))
      cp $OUT $R/hw/pdlvds_rx.fr1r.ckpt${copied}.kicad_pcb
      echo "$(date -u +%H:%M:%S) copied ckpt${copied}" >> $R/results/ckpt-watch.log
    fi
  fi
  grep -q 'repair6 done' $LOG && break
  sleep 5
done
echo "$(date -u +%H:%M:%S) watcher exit" >> $R/results/ckpt-watch.log
