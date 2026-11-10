#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
B=$R/hw/pdlvds_rx.fr16.kicad_pcb
LOG=$R/results/ckpt-watch16.log
n=0; last=""
while true; do
  if [ -f "$B" ]; then
    s1=$(stat -c '%s-%Y' "$B")
    sleep 5
    s2=$(stat -c '%s-%Y' "$B")
    if [ "$s1" = "$s2" ] && [ "$s1" != "$last" ]; then
      n=$((n+1))
      cp "$B" "$R/hw/pdlvds_rx.fr16.ckpt$n.kicad_pcb"
      echo "$(date -u +%H:%M:%S) ckpt$n saved ($s1)" >> $LOG
      last=$s1
    fi
  fi
  sleep 10
done
