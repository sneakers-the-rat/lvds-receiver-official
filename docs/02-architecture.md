# 02 — Architecture and part selection (decisions, with reasons)

Signal chain (main, bit-transparent path — no decoding in the LVDS path):
  APD -> transimpedance amplifier -> AC couple + baseline restore ->
  high-speed comparator with DAC-set threshold (the "adaptive digitizer") ->
  LVDS output pair (comparator has native LVDS outputs)
Verification / control path (tap, does not touch the LVDS path):
  comparator LVDS out -> CDR (clock+data recovery) -> MCU (USB-HS) -> host
  MCU also: APD bias DAC + monitor, threshold DAC, temperature, BIST LED driver,
  electrical test-pattern injection, status LEDs.

## Detector — Excelitas C30737LH-500-90 (primary population)
Si APD, SMD leadless ceramic carrier. Datasheet values (datasheets/):
  active dia 0.5 mm; peak sensitivity 900 nm; spectral range 500-1000 nm;
  responsivity 55 typ / 60 max A/W at 900 nm at M=100 (=> 0.55 A/W at M=1);
  capacitance 1.0 pF typ; dark current 0.1 typ / 1 nA max (at operating gain);
  noise current 0.1 pA/rtHz; rise/fall 0.9 ns; cutoff 380 MHz (RL=50 ohm);
  breakdown 180-260 V; tempco of Vbr 1.3 V/degC.
Why this part:
  * One device covers both paper channels: at 630 nm Si responsivity is still
    ~0.35-0.40 A/W (M=1, from the datasheet spectral curve), at 740 nm ~0.50 A/W.
    A SiPM's PDE falls steeply past 700 nm and the C15522 module's electronics
    are fixed; a linear APD + our own TIA removes both limits.
  * 1 pF terminal capacitance is what makes a >=50 MHz TIA with useful gain
    and noise possible (see link budget). Large-area APDs (2-3 mm) have
    11-22 pF and would need 400 V bias (Hamamatsu S8664 family) for less
    bandwidth; the area loss is recovered optically (below).
  * SMD package -> reproducible assembly, no TO-can hand soldering, and the
    optical centre can be put exactly on the board axis.
Alternate footprint (same optical centre, populate one only):
  Hamamatsu S8664-20K TO-5, dia 2.0 mm, Ct 11 pF, fc 280 MHz, Vbr ~400 V —
  for users who need bare-detector field of view over sensitivity/bias ease.
  Its bias requirement is why the HV supply is designed to 420 V.
Optics:
  * Bare: FOV set by package, like the original bare SiPM modules.
  * Lens mode: board carries an M25x0.5 / 25.4 mm holder footprint and standoff
    holes for a 25 mm dia, f=25 mm plano-convex lens (Thorlabs LA1951-A class,
    AR 350-700... use -B 650-1050 nm coating variant for the NIR channel) with
    the APD placed 17 mm behind the lens (deliberately defocused: spot ~3x the
    APD, trading peak gain for alignment tolerance and ~+/-2 deg acceptance).
    Collection area 5.1 cm2 vs APD 0.002 cm2 — see link budget for the honest
    etendue accounting; the lens buys ~14 dB at the design geometry, not 34 dB.
  * Filter: 12.5 mm dia bandpass in the same holder stack (630/10 or 740/10),
    as the paper's per-channel filtering.

## TIA — TI OPA657 (single, 5 V, FET input)
1.6 GHz gain-bandwidth, 4.8 nV/rtHz voltage noise, 1.3 fA/rtHz current noise class,
decompensated (stable for TIA gains >= ~1k). Chosen over an integrated fibre TIA
(MAX3658 etc.) because (a) it is simulatable from its published model, (b) the
feedback network is ours to optimise for a 1 pF APD instead of a fibre PIN diode,
(c) through-hole-friendly SOIC-8 hand assembly. Design: Rf = 3.3 kohm,
Cf = 0.35 pF (0.2 pF discrete + parasitics), predicted f-3dB ~ 90 MHz,
transimpedance 3.3 kV/A before the post stage. Full calc + ngspice in sim/.
Post-amplifier: OPA657's output drives the comparator directly through AC
coupling at the design point (54 mV from -34 dBm — see budget); a jumper-selected
x5 gain stage (THS4304, unity-gain stable SOT-23) is fitted for bench work at
lower levels. NOTE recorded as a risk: comparator overdrive dispersion at
<20 mV overdrive — mitigated by the post stage; see docs/04-risks.md (to come).

## Quantizer — TI LMH7220 comparator, native LVDS output
2.9 ns propagation delay, 0.6 ns rise/fall, adjustable hysteresis, LVDS outputs
specified to TIA/EIA-644. This part IS the LVDS driver — no separate translator
stage adding jitter. Threshold from a DAC (below) into the inverting input
through the baseline-restoration network; hysteresis set to ~8 mV referred.

## CDR — Analog Devices ADN2813 (verification path)
Continuous-rate CDR with integrated limiting amplifier, 10 Mbps to 1.25 Gbps,
no reference clock required, I2C rate readback, LOS output. It locks to
50 Mbps 8b/10b NRZ and equally to the 16 Mbaud Manchester chip stream
(Manchester decoding itself is then a firmware function on the recovered
chips — exactly as the paper's FPGA decoded after clock recovery).
CML outputs AC-coupled to the MCU capture inputs.

## MCU — ST STM32H723ZG + Microchip USB3300 ULPI PHY (USB high-speed)
Why: USB FS (12 Mbps) cannot stream a 40 Mbps payload — this is the single
fact that rules out RP2040/RP2350/STM32F4-class parts for the "verify it from a
laptop, no FPGA" requirement. The H723 (550 MHz Cortex-M7, LQFP-144... design
uses the 100-pin ZG variant footprint class) has a USB OTG HS core; with the
USB3300 ULPI PHY it enumerates as USB-HS: bulk IN streaming of captured data,
CDC control channel. Capture: recovered data+clock from the CDR enter a timer/
SPI-slave DMA path (data sampled on recovered clock, DMA to SRAM, double
buffered) — no FPGA, the CDR does the timing-critical work.
Programming: STM32 ROM bootloader over USB (DFU) — BOOT button + USB-C, works
on any laptop with dfu-util / STM32CubeProgrammer; SWD pads fitted for rescue.
Control duties: bias DAC + HV enable, threshold DAC, ADN2813 I2C, temperature
(TMP117 + APD tempco compensation), BIST, status.

## DACs / monitoring
- Threshold + bias setpoint: TI DAC8562 (dual 16-bit, SPI) — one channel sets
  the comparator threshold (through a divider), one sets HV feedback.
- HV monitor + photocurrent monitor: MCU 16-bit ADC via precision dividers.
- Temperature: TI TMP117 (I2C, +/-0.1 C) placed 3 mm from the APD.

## APD bias supply — flyback, LT3757 controller
APD current is < 200 uA worst case, but voltage is 150-420 V (APD dependent).
A boost from 5 V cannot reach 84:1; a flyback can. Design: LT3757 in flyback
configuration, Wurth/Coilcraft-class 1:10 flyback transformer, 600 V MOSFET
and diode, output RC post-filter (ripple target < 20 mVpp at the APD after the
filter — APD gain sensitivity to ripple is computed in the link budget),
DAC-injected feedback for MCU control, hardware OVP zener clamp at 440 V,
primary current limit, bleeder + HV-present LED, creepage slots and >= 3 mm
clearance on the HV island, conformal-coat note in the fab drawing.
Safety: HV is generated only when the MCU asserts HV_EN after USB host sets a
bias AND the enclosure interlock jumper is fitted; default at power-up is OFF.

## Power tree (USB-C 5 V in, budget < 4.5 W)
5 V -> 3.3 V buck (TPS62130) for digital/CDR/LVDS; 5 V analog rail via low-noise
LDO (LT3042) for TIA/comparator analog; -5 V small inverter (LT1617 class) NOT
fitted in rev A: OPA657 runs single-supply 5 V with the APD cathode at HV and
anode at the TIA virtual ground biased at +1.0 V (see schematic notes).
HV flyback input from 5 V. Per-rail current budget table: docs/03-power.md (to come).

## Connectors
USB-C (data + power), LVDS out: 2x U.FL (data pair as two 50-ohm SE legs is NOT
used — LVDS pair is routed to a single Samtec/... ) — decision: LVDS on a
4-pin 2.54 header + on two SMA (P/N legs) for lab scopes + on a HDMI-style
differential footprint? NO — keep it simple and standard: LVDS data pair and
clock pair on a 2x4 100-mil shrouded header (100 ohm termination at the far
end is the user's receiver) AND data pair also on a pair of edge SMA for
measurement. BIST LED (630 nm, same part as the paper's emitter) facing the APD
position via a light-pipe hole for optical self-test. SMA test input for
electrical injection in parallel with the APD (AC-coupled, for bench verify
without light).
