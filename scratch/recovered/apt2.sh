#!/bin/bash
exec > /tmp/apt2.log 2>&1
set -x
apt-get -o Acquire::Languages=none -o Acquire::http::Timeout=25 -o Acquire::https::Timeout=25 update
DEBIAN_FRONTEND=noninteractive apt-get -o Acquire::Languages=none install -y kicad xvfb ngspice gcc-arm-none-eabi
echo "APT2_DONE rc=$?"
