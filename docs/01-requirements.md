# 01 — Requirements derived from the source paper

Source: Sasatani et al., "Miniscope Zero", bioRxiv 10.64898/2026.09.05.745822v1
(full text via PMC13622490). Quotes are from the Methods, "Optical data I/O modules"
and "Data stream packet structure" sections.

## What the existing system does (facts from the paper)
- Optical uplink: 8 Mbps imaging data + metadata, 200x200 px, 20 fps, 8-bit.
- Encoding: Manchester, generated in hardware by XOR of data and clock
  (Nexperia 74LV1T86GXH). Manchester embeds the clock; no separate clock channel.
- Emitters (head-mounted transmitter):
  - Red channel: Wurth Elektronik 150060RS75003, 0603 LED, peak 630 nm,
    dominant 625 nm, 530 mcd @ 20 mA, 140 deg viewing angle.
  - NIR channel (2nd animal): QT Brightek QBLP601-IR4 family, 0603 IR LED,
    peak 740 nm (730-750 nm), 0.6 min / 1.7 typ mW/sr @ 20 mA.
    NOTE: the "-2IR4" variant in the paper is the 740 nm part, NOT 940 nm.
  - Emitter driver: GaN FET modulator (EPC EPC2038) — i.e. the LED is pulsed
    at currents well above the 20 mA datasheet point.
- Receiver (the unit being replaced):
  - Hamamatsu C15522-3010SA SiPM (MPPC) module, modules placed above/around arena.
  - Custom CNC aluminium enclosure per frontend (EMI from the 6.63 MHz QSCR
    wireless-power field).
  - Custom high-gain amplifier + adaptive digitizer (threshold adapts to received
    intensity, which varies with animal position / head orientation / line of sight).
  - Opal Kelly XEM7310 FPGA does clock recovery, Manchester decode, packet recovery;
    decoded data go to the PC over USB.
  - Optical bandpass filters matched to the channel in use; WDM separation of the
    red and NIR channels for two-animal work.
- Packet structure: dummy 32-bit words, fixed preamble, 11-word (32-bit) header
  (frame index, global packet index, packet index in frame, device timestamp,
  pixel count, raw battery voltage, raw input voltage), payload of 5,032 bytes;
  a 200x200 frame = 8 packets.
- PER test mode in the original: PRBS-15 (x^15+x^14+1), reseeded per buffer as
  seed=(buffer_count mod 2^15)|1, 40,256 payload bits per buffer; a packet fails
  if any payload bit differs.
- Environment: strong 6.63 MHz magnetic field (QSCR power), behavioural
  illumination as optical interference, free-space path over a 50x50 cm arena,
  receiver above/around the arena.

## Customer target for this replacement (supersedes the paper's rates)
- Line rate 50 Mbps, 8b/10b, payload 40 Mbps, UI = 20 ns.
- Photodiode receiver with LVDS output.
- SiPM is disfavoured: limited custom electronics, limited bandwidth in the
  large-area module form, poor NIR response. APD is explicitly acceptable.
- A user with a random laptop must be able to plug the module in over USB,
  program it, and verify it — with no FPGA attached. (So: programming and
  full-rate verification must work over USB alone.)
- Progress reports with decisions and stage.

## Derived engineering requirements (our derivation, argued in doc 02)
R1  Analog front end -3 dB bandwidth >= 50 MHz (0.7/UI rule gives 35 MHz for
    NRZ; 50 MHz target keeps rise time <= 7 ns = 0.35 UI), low-frequency cutoff
    <= 500 kHz (8b/10b max run length 5 UI -> lowest fundamental 5 MHz for a
    repeating pattern, Manchester legacy is DC-balanced by construction;
    AC-coupling / baseline restoration must not droop over 5 UI).
R2  Sensitivity design point: BER <= 1e-6 at -34 dBm average incident power at
    740 nm on the bare APD (no lens), improving to <= -44 dBm effective with the
    specified 25 mm collection lens fitted. Derivation: sim/link_budget.py.
R3  Overload: no damage and recovery within 10 UI at +0 dBm on the APD.
R4  Output: LVDS data pair, TIA/EIA-644-A (250-450 mV diff into 100 ohm,
    1.125-1.375 V common mode), on U.FL pair + 100-ohm-terminated pin header;
    plus LVDS recovered-clock pair in CDR mode. Jitter added by the module
    (excluding source) < 2 ns pk-pk (0.1 UI) at the design point.
R5  Wavelengths: useful response at 630 nm and 740 nm from one detector;
    filter holder accepts 12.5 mm bandpass filters for channel separation,
    as in the paper.
R6  Verification without FPGA: on-board CDR (10 Mbps..1.25 Gbps, so it locks
    both to 50 Mbps 8b/10b and to the 16 Mbaud Manchester chip stream) +
    Cortex-M7 MCU with USB high-speed (480 Mbps) streaming decoded payload to
    the host at >= 40 Mbps sustained; on-board PRBS-15 checker compatible with
    the paper's PER test mode, plus 8b/10b decode and Manchester decode in
    firmware. Host tool reports BER/PER, eye/threshold margin scan.
R7  Programming without a dongle: MCU in ROM DFU / USB bootloader mode from
    any laptop (STM32 system bootloader over USB DFU), plus SWD pads for rescue.
R8  Adaptive digitizer (as the original): slicing threshold set by a DAC under
    MCU control, with an automatic baseline/peak tracking mode in firmware and
    a manual override from the host.
R9  APD bias: programmable over the full range of the fitted APD, resolution
    <= 0.5 V, ripple <= 20 mVpp after filtering, hardware current limit,
    temperature compensation using the APD tempco and an on-board temperature
    sensor, hardware over-voltage clamp independent of firmware, HV enable
    interlock, bleeder so the rail falls below 60 V within 10 s of disable.
R10 EMI: metal enclosure / shield can over the analog frontend, frontend ground
    partitioning and supply filtering sized for the 6.63 MHz QSCR field
    environment described in the paper.
R11 USB-C connector, bus powered (5 V, <= 900 mA USB-C default with CC
    advertisement; total budget in doc 02), ESD protection on all external
    connectors.
R12 Board: 4-layer, controlled impedance 50 ohm SE / 100 ohm differential,
    fab outputs + BOM + placement from the repo, DRC/ERC clean.
