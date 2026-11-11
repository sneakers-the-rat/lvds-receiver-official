#!/usr/bin/env python3
"""HV converter reachability/stress proof for the WE-FLEX HV redesign.

Companion to sim/run_hv_clamp.py. The clamp checker proves the DAC/FBX
set-point bound (docs/07 condition (b): worst-case demand 259.40 V
<= 260 V). That bound is set by the feedback divider and does not
depend on the transformer. This checker proves the other half for the
docs/11 selection (Wurth WE-FLEX HV 749196518 replacing the custom
wind): that the converter built around the catalog part can actually
REACH every demanded voltage, inside the LT3757's duty envelope, the
transformer's saturation / volt-second limits, and every fitted
part's voltage rating — for both stuffing variants.

Topology proved (docs/12):
  N1 (pins 1-2)          primary, dot (pin 1) at +5 V
  N2..N6 in series       secondary, 5:1, dot-end of the string at GND,
                         far end = HV_SEC (positive during flyback)
  2-cell Cockcroft-Walton ladder on the secondary:
      a flyback secondary winding waveform swings -N*Vin (switch on)
      to +Vf (flyback), with volt-second balance Vf = N*Vin*D/(1-D).
      One CW cell delivers Vf + N*Vin = N*Vin/(1-D); m cells deliver
          Vout = m * N * Vin / (1 - D).
  R28 raised 0.05 -> 0.15 ohm: LT3757 peak current limit falls from
  the 2.4 A class to <= 0.80 A worst case (120 mV max sense
  threshold), matched to the catalog part's saturation figure.

Datasheet figures used (Wurth 749196518, rev 001.001 2023-09-20,
results/partsfix/datasheets/wurth-749196518.pdf):
  L_BASE 22.3 uH +/-20 % per winding; I_SAT BASE 0.93 A typ
  (|dL/L| < 10 %); volt-us base 123.4 Vus max; leakage 0.24 uH typ;
  RDC 102 mohm max; insulation test 1500 VAC all windings.
LT3757 figures (datasheet text in results/partsfix/datasheets):
  min on-time 220 ns typ, min off-time 220 ns typ -> at 250 kHz
  Dmax(typ) = 1 - 220 ns * 250 kHz = 0.945; current-sense threshold
  120 mV max (the figure behind docs/09's "2.4 A at 0.05 ohm").
"""

import sys

FAILS = []


def check(name, ok, detail):
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    if not ok:
        FAILS.append(name)


# --- fixed design data -------------------------------------------------
F_SW = 250e3            # Hz, R24 = 53.6 kohm (unchanged)
T_OFF_MIN = 220e-9      # LT3757 typ
T_ON_MIN = 220e-9       # LT3757 typ
DMAX = 1.0 - T_OFF_MIN * F_SW
N = 5                   # secondary windings in series (N2..N6)
M = 2                   # Cockcroft-Walton cells
LP = 22.3e-6            # per-winding inductance, nominal
LP_MIN = LP * 0.8       # -20 % tolerance
ISAT_BASE = 0.93        # A typ, conservative single-winding reading
VUS_BASE = 123.4        # V*us max per winding
R28 = 0.15              # ohm, redesigned sense resistor
VSENSE_MAX = 0.120      # V, LT3757 max current-sense threshold
VSENSE_TYP = 0.100      # V, typical
ILIM_MAX = VSENSE_MAX / R28
ILIM_TYP = VSENSE_TYP / R28
Q1_VDS = 60.0           # IRLML0060TRPBF
DIODE_VRRM = 600.0      # ES1J
CAP_VRATED = 630.0      # 100 nF ladder/reservoir class (as C32)

VINS = (4.75, 5.0, 5.25)          # USB +5 V +/-5 %
DEMANDS = {
    "C30737 min (DAC full-scale)": 116.07,
    "C30737 nominal max": 253.21,
    "C30737 worst-case max (docs/07)": 259.40,
    "S8664 variant max": 420.0,
}


def duty(vout, vin):
    """CCM duty for Vout = M*N*Vin/(1-D)."""
    return 1.0 - M * N * vin / vout


# --- 1. duty envelope --------------------------------------------------
worst_off = 1.0
for label, vout in DEMANDS.items():
    for vin in VINS:
        d = duty(vout, vin)
        t_off = (1.0 - d) / F_SW
        worst_off = min(worst_off, t_off)
        check(f"duty {label} @ Vin={vin}",
              0.0 < d < DMAX and t_off >= 2 * T_OFF_MIN,
              f"D={d:.3f} (Dmax typ {DMAX:.3f}), off-time {t_off*1e9:.0f} ns "
              f"vs min {T_OFF_MIN*1e9:.0f} ns typ")

# --- 2. current limit vs saturation ------------------------------------
check("current limit vs I_SAT BASE (conservative reading)",
      ILIM_MAX < ISAT_BASE,
      f"Ilim max {ILIM_MAX:.2f} A (120 mV / {R28} ohm) < {ISAT_BASE} A typ; "
      f"ampere-turn reading gives a further 6x (six windings share one core)")

# --- 3. operating peak current at full C30737 load ---------------------
vout = 253.21
p_load = vout**2 * (1 / 7.68e6 + 1 / 4.7e6) + 0.5e-3   # divider+bleeder+APD
eta = 0.7
e_cyc = (p_load / eta) / F_SW
ipk_op = (2 * e_cyc / LP_MIN) ** 0.5
check("operating peak current", ipk_op < ILIM_TYP / 3,
      f"rail load {p_load*1e3:.1f} mW -> Ipk {ipk_op*1e3:.0f} mA "
      f"(Lp at -20 % tol, eta {eta})")

# --- 4. minimum on-time at the operating point -------------------------
t_on_op = LP_MIN * ipk_op / max(VINS)
check("on-time at operating point", t_on_op > T_ON_MIN,
      f"{t_on_op*1e9:.0f} ns > min on-time {T_ON_MIN*1e9:.0f} ns typ")

# --- 5. volt-seconds ----------------------------------------------------
vus_worst = 0.0
for label, v in DEMANDS.items():
    for vin in VINS:
        vus_worst = max(vus_worst, vin * duty(v, vin) / F_SW * 1e6)
check("primary volt-seconds", vus_worst < VUS_BASE / 2,
      f"worst {vus_worst:.1f} Vus < {VUS_BASE} Vus max (2x margin demanded)")

# --- 6. switch stress ----------------------------------------------------
for label, v in (("C30737 worst", 259.40), ("S8664 max", 420.0)):
    vin = max(VINS)
    vf = v / M - N * vin            # secondary flyback amplitude
    v_drain = vin + vf / N
    check(f"Q1 drain steady peak ({label})", v_drain < 0.75 * Q1_VDS,
          f"{v_drain:.1f} V vs {Q1_VDS:.0f} V rated "
          f"(leakage spike excluded — see docs/12; spike energy at the "
          f"new current limit is ~15x below the custom-wind design's)")

# --- 7. rectifier / ladder stresses --------------------------------------
v_half = max(DEMANDS.values()) / M
check("CW diode stress (ES1J)", v_half < DIODE_VRRM / 2,
      f"each diode blocks <= Vout/{M} = {v_half:.0f} V vs {DIODE_VRRM:.0f} V")
check("CW shunt/series cap stress", v_half < CAP_VRATED / 2,
      f"ladder caps stand at <= {v_half:.0f} V (first series cap only "
      f"N*Vin = {N*max(VINS):.1f} V) vs {CAP_VRATED:.0f} V class")
check("output reservoir stress", max(DEMANDS.values()) < CAP_VRATED,
      f"HV_RAW cap (C32 class) at <= {max(DEMANDS.values()):.0f} V "
      f"vs {CAP_VRATED:.0f} V")

# --- 8. startup charge time at the current limit -------------------------
c_tot = 1.45e-6     # C32 100n + C4 1u + 3 ladder caps + strays
e_rail = 0.5 * c_tot * 259.40**2
e_cyc_max = 0.5 * LP_MIN * ILIM_TYP**2
t_charge = e_rail / (e_cyc_max * F_SW)
check("startup charge", t_charge < 0.5,
      f"rail energy {e_rail*1e3:.0f} mJ charges in >= {t_charge*1e3:.0f} ms "
      f"at the typ current limit (soft-start ramp governs in practice)")

# --- 9. leakage, referred -----------------------------------------------
llk = 0.24e-6 + (N * 0.24e-6) / N**2  # primary term + secondary referred
check("referred leakage", llk <= 0.5e-6,
      f"~{llk*1e6:.2f} uH vs the custom-wind target <= 0.50 uH")

print()
if FAILS:
    print(f"RESULT: FAIL ({len(FAILS)} checks): {', '.join(FAILS)}")
    sys.exit(1)
print("RESULT: PASS — converter reaches every demanded rail inside "
      "all ratings, both stuffing variants")
