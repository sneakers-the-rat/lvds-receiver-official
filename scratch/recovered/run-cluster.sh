#!/bin/bash
# usage: run-cluster.sh NAME IN OUT CX CY R KEEP TARGETS...
R=$HOME/workspace/photodiode-lvds-rx
D=$HOME/workspace/pdlvds-v6run
cd $R
export DISPLAY=:99
NAME=$1; IN=$2; OUT=$3; CX=$4; CY=$5; RAD=$6; KEEP=$7; shift 7
L=$R/results/cluster-$NAME.log
echo "=== cluster $NAME start $(date -u +%H:%M:%S) ===" >> $L
SRC=$IN
for i in 1 2 3 4 5 6; do
  O=$D/disc-$NAME-$i.kicad_pcb
  python3 -u hw/clear_disc.py $SRC $O $CX $CY $RAD 25 $KEEP 2>&1 | grep -v 'swig/python' | python3 -u $D/tswrap.py >> $L 2>&1
  SRC=$O
done
cp $SRC $OUT
python3 -u hw/cluster.py $OUT $OUT 0 0 0 "$@" 2>&1 | grep -v 'swig/python' | python3 -u $D/tswrap.py >> $L 2>&1
python3 -u hw/check_pcb.py $OUT > results/audit-$NAME.txt 2>/dev/null
head -3 results/audit-$NAME.txt >> $L
echo "=== cluster $NAME exit $(date -u +%H:%M:%S) ===" >> $L
