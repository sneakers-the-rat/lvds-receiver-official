#!/usr/bin/env python3
"""Tests for host/cdc_transport.py against FakeSerial, a Python model
of the firmware's usb_app_process (firmware/src/usb_app.c) behind a
CDC byte pipe. No pytest dependency (house style, cf. test_codec.py):
run directly or under pytest.
  python3 host/test_transport.py
  python3 -m pytest host/test_transport.py -q
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdc_transport as ct


class FakeSerial:
    """Duck-typed pyserial stand-in running the firmware protocol
    model. read() honours chunk_limit to simulate partial reads."""
    def __init__(self, interlock_ok=True, chunk_limit=None):
        self.rx = bytearray()
        self.chunk_limit = chunk_limit
        self.timeout = 2.0
        self.interlock_ok = interlock_ok
        self.threshold_counts = 0
        self.bias_v = 0.0
        self.streaming = False
        self.ber = None            # dict while a BER test runs
        self.writes = []

    def _respond(self, opcode, status, payload=b""):
        self.rx += bytes([opcode | 0x80, status]) + payload

    def write(self, frame):
        self.writes.append(bytes(frame))
        op = frame[0]
        if op == ct.OP_GET_INFO:
            self._respond(op, 0, b"PDRX" + struct.pack("<H", 1) + b"\x01")
        elif op == ct.OP_SET_BIAS:
            if not self.interlock_ok:
                self._respond(op, 3)
            else:
                self.bias_v = struct.unpack_from("<f", frame, 1)[0]
                self._respond(op, 0)
        elif op == ct.OP_SET_THRESHOLD:
            self.threshold_counts = struct.unpack_from("<H", frame, 1)[0]
            self._respond(op, 0)
        elif op == ct.OP_GET_STATUS:
            p = struct.pack("<6B2H", 0, 1 if self.bias_v > 0 else 0,
                            1 if self.interlock_ok else 0, 0, 0, 1,
                            self.threshold_counts, 1234)
            p += struct.pack("<3f", 24.5, self.bias_v, self.bias_v)
            p += struct.pack("<2I", 0, self.ber["buffers"]
                             if self.ber else 0)
            self._respond(op, 0, p)
        elif op == ct.OP_BER_TEST_START:
            self.ber = {"start": struct.unpack_from("<I", frame, 1)[0],
                        "buffers": 0}
            self._respond(op, 0)
        elif op == ct.OP_BER_TEST_STOP:
            n = self.ber["buffers"] if self.ber else 0
            self.ber = None
            self._respond(op, 0,
                          struct.pack("<3I", 3, n * 40256, 1 if n else 0))
        elif op == ct.OP_STREAM_START:
            self.streaming = True
            self._respond(op, 0)
        elif op == ct.OP_STREAM_STOP:
            self.streaming = False
            self._respond(op, 0)
        else:
            self._respond(op, 2)
        return len(frame)

    def push_stream(self, data):
        assert self.streaming
        self.rx += data

    def read(self, n):
        if not self.rx:
            return b""
        if self.chunk_limit is not None:
            n = min(n, self.chunk_limit)
        out = bytes(self.rx[:n])
        del self.rx[:n]
        return out


def board(**kw):
    return ct.CDCBoard(FakeSerial(**kw), port_label="FAKE")


def expect_raises(exc, fn, *args):
    try:
        fn(*args)
    except exc as e:
        return e
    raise AssertionError(f"{exc.__name__} not raised")


def test_get_info():
    info = board().get_info()
    assert info["firmware"] == "rxfw 0.1"
    assert info["protocol"] == 1


def test_set_bias_and_interlock():
    b = board()
    assert b.set_bias(200.0)["bias_set_v"] == 200.0
    expect_raises(ValueError, b.set_bias, 300.0)
    e = expect_raises(ct.BoardStatusError,
                      board(interlock_ok=False).set_bias, 100.0)
    assert e.status == 3 and "J5" in str(e)


def test_set_threshold_counts():
    b = board()
    r = b.set_threshold(1250.0)
    assert abs(r["threshold_set_counts"] - 32768) <= 1
    assert b.ser.threshold_counts == r["threshold_set_counts"]
    expect_raises(ValueError, b.set_threshold, 2600.0)


def test_get_status_layout():
    b = board()
    b.set_bias(231.5)
    st = b.get_status()
    assert st["hv_on"] is True and st["interlock_ok"] is True
    assert st["temp_c"] == 24.5
    assert abs(st["bias_commanded_v"] - 231.5) < 1e-4
    assert st["hv_dac_counts"] == 1234


def test_partial_reads_assemble():
    b = board(chunk_limit=1)
    assert b.get_info()["protocol"] == 1


def test_timeout_raises():
    class Dead:
        timeout = 0.1
        def write(self, f): return len(f)
        def read(self, n): return b""
    expect_raises(ct.TransportError, ct.CDCBoard(Dead()).get_info)


def test_ber_roundtrip():
    b = board()
    b.ber_start(0)
    b.ser.ber["buffers"] = 10       # model: firmware scored 10 buffers
    r = b.ber_stop()
    assert r["bits_checked"] == 10 * 40256
    assert r["bit_errors"] == 3 and r["packets_failed"] == 1


def test_stream_bytes_are_raw():
    b = board()
    b.stream_start()
    payload = bytes(range(256)) * 32          # one 8192-byte buffer
    b.ser.push_stream(payload)
    assert b.stream_read(len(payload)) == payload
    b.stream_stop()


def test_find_ports_without_pyserial_or_board():
    assert isinstance(ct.find_ports(), list)


_TESTS = [v for k, v in sorted(globals().items())
          if k.startswith("test_") and callable(v)]

if __name__ == "__main__":
    for t in _TESTS:
        t()
        print(f"PASS {t.__name__}")
    print(f"PASS: all {len(_TESTS)} transport tests passed")
