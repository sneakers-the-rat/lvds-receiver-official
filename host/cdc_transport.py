#!/usr/bin/env python3
"""
cdc_transport.py - real hardware transport for rxhost.py.

The board enumerates as a TinyUSB CDC ACM device (firmware/src/
usb_device_tinyusb.c; VID 0x1209 / PID 0xD723, unregistered
placeholder ids - see firmware/BRINGUP.md). The application protocol
is firmware/src/usb_app.h, unchanged:

  command:  [opcode][payload...]
  response: [opcode | 0x80][status][payload...]   status 0 = OK

Framing contract: the firmware's main loop hands each CDC read to
usb_app_process as ONE frame, so the host must send each command as
a single write() and must finish reading a command's response before
issuing the next command. Response payload lengths are fixed per
opcode by protocol version 1 (GET_INFO 7, GET_STATUS 30,
BER_TEST_STOP 12, all others 0), so the host reads exactly
2 + payload_len bytes.

The one shared-channel hazard: while capture streaming is armed, the
firmware also sends raw 8192-byte capture buffers on the same CDC
channel (main.c). Commands are therefore only issued while streaming
is stopped; stream reads are raw byte reads with no framing.

The serial object is duck-typed (write(bytes)->int, read(n)->bytes,
timeout attribute), which is pyserial's interface; tests substitute
a fake running a Python model of usb_app_process.
"""
import struct

VID, PID = 0x1209, 0xD723

OP_GET_INFO = 0x01
OP_SET_BIAS = 0x02
OP_SET_THRESHOLD = 0x03
OP_GET_STATUS = 0x04
OP_BER_TEST_START = 0x05
OP_BER_TEST_STOP = 0x06
OP_STREAM_START = 0x07
OP_STREAM_STOP = 0x08

STATUS_NAMES = {
    0: "OK", 1: "BAD_FRAME", 2: "BAD_OPCODE", 3: "INTERLOCK",
    4: "IO_ERROR", 5: "BAD_STATE",
}

# Fixed response payload lengths, protocol version 1 (usb_app.c).
RESP_PAYLOAD_LEN = {
    OP_GET_INFO: 7, OP_SET_BIAS: 0, OP_SET_THRESHOLD: 0,
    OP_GET_STATUS: 30, OP_BER_TEST_START: 0, OP_BER_TEST_STOP: 12,
    OP_STREAM_START: 0, OP_STREAM_STOP: 0,
}

CAPTURE_BUF_BYTES = 8192          # firmware/src/capture.h
DAC_FULL_SCALE_MV = 2500.0        # DAC8562 internal ref, docs/03
DAC_COUNTS = 65535.0
BIAS_MAX_V = 253.21               # docs/07 hardware ceiling (C30737 fit)


class TransportError(Exception):
    """The board did not answer as the protocol requires."""


class BoardStatusError(TransportError):
    """The board answered with a non-OK status byte."""
    def __init__(self, opcode, status):
        self.opcode = opcode
        self.status = status
        name = STATUS_NAMES.get(status, f"status {status}")
        hint = ""
        if status == 3:
            hint = (" (SET_BIAS refused: HV interlock jumper J5 absent "
                    "or HV fault - see firmware/BRINGUP.md)")
        super().__init__(
            f"board returned {name} for opcode 0x{opcode:02X}{hint}")


class CDCBoard:
    """The receiver board over its CDC ACM serial port."""

    def __init__(self, ser, port_label=""):
        self.ser = ser
        self.port_label = port_label

    # -- framing ----------------------------------------------------
    def _command(self, opcode, payload=b""):
        frame = bytes([opcode]) + payload
        self.ser.write(frame)
        want = 2 + RESP_PAYLOAD_LEN[opcode]
        buf = bytearray()
        while len(buf) < want:
            chunk = self.ser.read(want - len(buf))
            if not chunk:
                raise TransportError(
                    f"timeout reading response to opcode 0x{opcode:02X} "
                    f"({len(buf)}/{want} bytes received)")
            buf += chunk
        if buf[0] != (opcode | 0x80):
            raise TransportError(
                f"response opcode 0x{buf[0]:02X} does not match request "
                f"0x{opcode:02X} (stream data interleaved? commands "
                f"must not be issued while streaming is armed)")
        status = buf[1]
        if status != 0:
            raise BoardStatusError(opcode, status)
        return bytes(buf[2:])

    # -- control plane (same method set as SimBoard) ----------------
    def get_info(self):
        p = self._command(OP_GET_INFO)
        if p[0:4] != b"PDRX":
            raise TransportError(f"bad GET_INFO magic {p[0:4]!r}")
        ver = struct.unpack_from("<H", p, 4)[0]
        return {"board": "PDLVDS-RX rev A (STM32H723 + ADN2813)",
                "firmware": f"rxfw {ver >> 8}.{ver & 0xFF}",
                "protocol": p[6],
                "transport": f"CDC ACM {self.port_label}".strip()}

    def set_bias(self, volts):
        if not (0.0 <= volts <= BIAS_MAX_V):
            raise ValueError(
                f"bias {volts} V outside 0..{BIAS_MAX_V} V range "
                f"(docs/07 hardware ceiling for the C30737 fit)")
        self._command(OP_SET_BIAS, struct.pack("<f", volts))
        return {"bias_set_v": volts,
                "note": "board acknowledged (interlock OK)"}

    def set_threshold(self, mv):
        """mv is the DAC output voltage in millivolts (0..2500);
        THR_DAC reaches the comparator through a 1k/100nF lowpass
        with no divider (hw/CONNECTIONS.md), so it is also the
        comparator threshold voltage."""
        if not (0.0 <= mv <= DAC_FULL_SCALE_MV):
            raise ValueError(
                f"threshold {mv} mV outside 0..{DAC_FULL_SCALE_MV:.0f} "
                f"mV DAC range")
        counts = round(mv / DAC_FULL_SCALE_MV * DAC_COUNTS)
        self._command(OP_SET_THRESHOLD, struct.pack("<H", counts))
        return {"threshold_set_counts": counts,
                "threshold_dac_mv": counts / DAC_COUNTS
                * DAC_FULL_SCALE_MV}

    def get_status(self):
        p = self._command(OP_GET_STATUS)
        (cap_state, hv_on, interlock_ok, hv_fault, los, temp_valid,
         thr_counts, hv_dac_counts) = struct.unpack_from("<6B2H", p, 0)
        temp_c, commanded_v, setpoint_v = struct.unpack_from("<3f", p, 10)
        overruns, buffers = struct.unpack_from("<2I", p, 22)
        return {"capture_state": cap_state, "hv_on": bool(hv_on),
                "interlock_ok": bool(interlock_ok),
                "hv_fault": bool(hv_fault), "cdr_los": bool(los),
                "temp_valid": bool(temp_valid),
                "threshold_counts": thr_counts,
                "hv_dac_counts": hv_dac_counts,
                "temp_c": temp_c, "bias_commanded_v": commanded_v,
                "bias_setpoint_v_at_25c": setpoint_v,
                "capture_overruns": overruns,
                "buffers_completed": buffers}

    # -- data plane ---------------------------------------------------
    def ber_start(self, start_buffer=0):
        self._command(OP_BER_TEST_START, struct.pack("<I", start_buffer))

    def ber_stop(self):
        p = self._command(OP_BER_TEST_STOP)
        errs, bits, failed = struct.unpack_from("<3I", p, 0)
        return {"bit_errors": errs, "bits_checked": bits,
                "packets_failed": failed}

    def stream_start(self):
        self._command(OP_STREAM_START)

    def stream_stop(self):
        self._command(OP_STREAM_STOP)

    def stream_read(self, nbytes):
        """Raw read of streamed capture bytes (no framing). May
        return short if the port times out."""
        buf = bytearray()
        while len(buf) < nbytes:
            chunk = self.ser.read(nbytes - len(buf))
            if not chunk:
                break
            buf += chunk
        return bytes(buf)


def find_ports():
    """[(device, description)] for ports matching the board's
    VID:PID. Empty list when pyserial is unavailable."""
    try:
        from serial.tools import list_ports
    except Exception:
        return []
    return [(p.device, p.description or "")
            for p in list_ports.comports()
            if p.vid == VID and p.pid == PID]


def open_board(port=None):
    """Open the board's CDC port. port=None auto-detects by VID:PID.
    Raises TransportError with a usable message otherwise."""
    try:
        import serial  # pyserial; lazily, so --simulate never needs it
    except Exception:
        raise TransportError(
            "pyserial is not installed; the hardware transport needs "
            "it (pip install pyserial). --simulate works without it.")
    if port is None:
        found = find_ports()
        if not found:
            raise TransportError(
                f"no board found (no CDC port with VID:PID "
                f"{VID:04X}:{PID:04X}); connect the board or pass "
                f"--port. (Enumeration is bench-verified only - "
                f"firmware/BRINGUP.md.)")
        if len(found) > 1:
            raise TransportError(
                f"multiple boards found ({', '.join(d for d, _ in found)}); "
                f"pass --port to choose")
        port = found[0][0]
    ser = serial.Serial(port, baudrate=115200, timeout=2.0)
    return CDCBoard(ser, port_label=port)
