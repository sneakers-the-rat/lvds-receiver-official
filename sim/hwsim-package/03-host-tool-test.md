# Host test against the emulated device

## A fact about the host tool, stated plainly

`host/rxhost.py` in this revision cannot talk to any device, real or
emulated: its hardware transport is a stub. Without `--simulate`, `main()`
prints "Hardware present-check not implemented in this revision; use
--simulate" and exits 1; with `--simulate` it runs against `SimBoard`, an
in-process Python model — not against firmware. Closing that transport gap
(a serial backend for the CDC endpoint) is named remaining work for the
project independent of this package.

So the acid test here drives the **protocol itself** — the exact frames
the firmware implements (`firmware/src/usb_app.h`) — against the bridged
endpoint, with the checker the host tool's hardware backend will reuse.

## Sequence

1. Boot the device (README steps 1–4) and note the bridged endpoint path
   (a PTY path from the Renode session, e.g. `/dev/pts/N`).
2. From this folder:
   `python3 drive_protocol.py /dev/pts/N`
3. The driver runs, in order: GET_INFO (expects the `PDRX` magic in the
   reply), SET_THRESHOLD 0x1234 then GET_STATUS (the value must read
   back), SET_BIAS 200 V (an INTERLOCK refusal is the CORRECT answer
   while the interlock is open — the driver prints the status byte and
   does not fail on it), BER_TEST_START/STOP (counters must return),
   STREAM_START, STREAM_START again (must be refused, BAD_STATE),
   STREAM_STOP.
4. Save the full transcript (the driver prints every frame both ways)
   under `captures/<date>/` per the README.

## Scoring

Per the README: Stage B is CONFIRMED only when this sequence passes end
to end against the emulated firmware. A failure at a named step is a
finding — record the step, the frames, and the Renode log around it.
