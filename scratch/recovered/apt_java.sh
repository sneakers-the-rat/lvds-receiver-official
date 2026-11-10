#!/bin/bash
exec > /tmp/apt-java.log 2>&1
set -x
apt-get -o Acquire::Languages=none -o Acquire::http::Timeout=25 -o Acquire::https::Timeout=25 update
DEBIAN_FRONTEND=noninteractive apt-get -o Acquire::Languages=none install -y default-jre-headless xauth
echo "APT_JAVA_DONE rc=$?"
