#!/usr/bin/env bash
# t_ah4_groute_chain.sh -- run t_ab2_groute one job at a time over the
# district rip (rip2), chaining outputs g1..g9, stopping at first failure.
# Each step's board is kept so a failed step leaves the last good board.
set -u
cd ~/workspace/pdlvds-route
G=scratch/work/t_ab2_groute.py
W=scratch/work/ah
BOX="64 84 0 22"
JOBS=(
  "PHY_1V8A:U7.29:C23.1"
  "XO:U7.27:C21.1"
  "+3V3A:U7.31:U7.30"
  "+3V3A:U7.30:U7.16"
  "+3V3A:U7.16:C24.1"
  "+3V3A:U7.25:U7.16"
  "+3V3A:U7.6:U7.31"
  "ULPI_CK:U7.14:U6.41"
  "I2C_SCL:R20.1:U9.1"
)
prev=$W/rip2.kicad_pcb
i=0
for job in "${JOBS[@]}"; do
  i=$((i+1))
  out=$W/g$i.kicad_pcb
  echo "=== step $i: $job  ($prev -> $out)"
  if xvfb-run -a python3 $G "$prev" "$out" "$job" $BOX > $W/g$i.log 2>&1; then
    tail -2 $W/g$i.log
    prev=$out
  else
    echo "STEP $i FAILED ($job); log tail:"
    tail -5 $W/g$i.log
    echo "LAST GOOD BOARD: $prev"
    exit 1
  fi
done
echo "ALL 9 JOBS ROUTED. FINAL: $prev"
