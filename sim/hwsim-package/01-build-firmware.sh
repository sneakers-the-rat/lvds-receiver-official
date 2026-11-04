#!/bin/sh
# Build the receiver's production firmware exactly as the project builds it.
# Output: ../../firmware/build/rxfw.elf (the binary the simulation boots).
set -eu
cd "$(dirname "$0")/../../firmware"
make arm
ls -l build/rxfw.elf
arm-none-eabi-size build/rxfw.elf
echo "Firmware built: firmware/build/rxfw.elf"
