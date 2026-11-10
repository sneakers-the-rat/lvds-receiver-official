#!/bin/bash
# Chunked download of freerouting-2.5.0.jar via HTTP ranges.
URL="https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-2.5.0.jar"
cd ~/workspace/tools/freerouting
TOTAL=67108864   # upper bound probe; real size learned from first range response
CHUNK=8388608    # 8 MiB
rm -f jar.part.*
i=0; start=0
while :; do
  end=$((start + CHUNK - 1))
  f=$(printf "jar.part.%03d" $i)
  code=$(curl -sL -w "%{http_code}" -o "$f" -r ${start}-${end} --retry 5 --retry-all-errors --max-time 600 "$URL")
  sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
  echo "chunk $i bytes $start-$end http=$code size=$sz"
  if [ "$sz" -eq 0 ]; then echo "CHUNK_FAIL at $i"; exit 1; fi
  if [ "$sz" -lt "$CHUNK" ]; then echo "LAST_CHUNK $i"; break; fi
  start=$((start + CHUNK)); i=$((i + 1))
  if [ $i -gt 40 ]; then echo "TOO_MANY_CHUNKS"; exit 1; fi
done
cat jar.part.* > freerouting-2.5.0.jar
ls -la freerouting-2.5.0.jar
sha256sum freerouting-2.5.0.jar
