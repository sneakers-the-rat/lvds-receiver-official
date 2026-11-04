#!/usr/bin/env python3
"""Drive the receiver's command protocol against a serial endpoint.

Protocol (from firmware/src/usb_app.h — the authoritative source):
  command:  [opcode][payload...]
  response: [opcode | 0x80][status][payload...]     status 0 = OK
Payloads are little-endian, matching the firmware's C structs.

Usage: python3 drive_protocol.py /dev/pts/N   (or /dev/ttyACM0 for hardware)
Prints a verbatim transcript; exit 0 only if every check passes.
UNTESTED against the emulated device — see REFUSAL-RECORD.md in this folder.
"""
import os
import struct
import sys
import time

GET_INFO, SET_BIAS, SET_THRESHOLD, GET_STATUS = 0x01, 0x02, 0x03, 0x04
BER_START, BER_STOP, STREAM_START, STREAM_STOP = 0x05, 0x06, 0x07, 0x08


def exchange(fd, opcode, payload=b"", read_len=64, timeout=5.0):
    frame = bytes([opcode]) + payload
    print(f">> cmd 0x{opcode:02x} {payload.hex()}")
    os.write(fd, frame)
    deadline = time.time() + timeout
    buf = b""
    while time.time() < deadline and len(buf) < 2:
        try:
            chunk = os.read(fd, read_len)
        except BlockingIOError:
            time.sleep(0.05)
            continue
        if chunk:
            buf += chunk
            if len(buf) >= 2 and buf[0] == (opcode | 0x80):
                # status known; try to drain any payload briefly
                time.sleep(0.1)
                try:
                    buf += os.read(fd, read_len)
                except BlockingIOError:
                    pass
                break
    print(f"<< {buf.hex()}")
    return buf


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    return cond


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    fd = os.open(sys.argv[1], os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    ok = True
    r = exchange(fd, GET_INFO)
    ok &= check("GET_INFO answers with opcode|0x80, status OK",
                len(r) >= 2 and r[0] == 0x81 and r[1] == 0)
    ok &= check("GET_INFO payload carries the PDRX magic", b"PDRX" in r)
    r = exchange(fd, SET_THRESHOLD, struct.pack("<H", 0x1234))
    ok &= check("SET_THRESHOLD accepted", len(r) >= 2 and r[1] == 0)
    r = exchange(fd, GET_STATUS)
    ok &= check("GET_STATUS reports threshold 0x1234",
                struct.pack("<H", 0x1234) in r)
    r = exchange(fd, SET_BIAS, struct.pack("<f", 200.0))
    print(f"   SET_BIAS 200 V status byte: {r[1] if len(r) > 1 else 'none'}"
          " (INTERLOCK refusal is correct with the interlock open)")
    r = exchange(fd, BER_START, struct.pack("<I", 0))
    ok &= check("BER_TEST_START accepted", len(r) >= 2 and r[1] == 0)
    r = exchange(fd, BER_STOP)
    ok &= check("BER_TEST_STOP returns counters", len(r) >= 10)
    r = exchange(fd, STREAM_START)
    ok &= check("STREAM_START accepted", len(r) >= 2 and r[1] == 0)
    r = exchange(fd, STREAM_START)
    ok &= check("STREAM_START while armed refused (BAD_STATE)",
                len(r) >= 2 and r[1] != 0)
    r = exchange(fd, STREAM_STOP)
    ok &= check("STREAM_STOP accepted", len(r) >= 2 and r[1] == 0)
    print("RESULT:", "ALL CHECKS PASSED" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
