#!/usr/bin/env python3
"""
hv_design.py — analytical design of the APD bias flyback (stage 4b, part 1).

Topology: LT3757 current-mode controller, single-switch flyback, DCM,
5 V in -> 150..420 V out, DAC-injected feedback (see docs/02).
All numbers are analytical (hand-calc grade, formulas stated inline);
the companion ngspice averaged simulation is sim/hv_flyback.cir.

Design rules checked (PASS/FAIL printed):
  * every semiconductor voltage/current stress < 80% of its rating
  * output ripple at the APD < 20 mVpp (R9) after the RC post-filter
  * bleeder discharges 420 V -> <60 V in < 10 s (R9)
  * duty cycle < 0.85 at worst case (min Vin, max Vout)
Ratings assumed (VERIFY against datasheets at bring-up, see MANIFEST):
  MOSFET 100 V / 2 A class (primary switch sees only Vin + reflected
  Vout = ~26 V — a 600 V part would be wasted Rds(on) here),
  secondary diode 1000 V ultrafast, output caps 630 V film/ceramic class.
"""
import math

# ---------------- design inputs ----------------
Vin_nom, Vin_min, Vin_max = 5.0, 4.75, 5.25
Vout_max, Vout_min = 420.0, 150.0
I_apd_max = 200e-6          # APD current worst case (docs/02: < 200 uA)
R_bleed = 4.7e6             # bleeder resistor
I_load = I_apd_max + Vout_max / R_bleed
P_out = Vout_max * I_load
eta = 0.70                  # assumed flyback efficiency at this power level
P_in = P_out / eta
f_sw = 250e3
N = 20.0                    # Ns/Np turns ratio
Lp = 47e-6                  # primary inductance, H
C_out = 47e-9               # effective output capacitance (HV ceramic, derated)
R_filt, C_filt = 10e3, 100e-9   # RC post-filter before the APD

print("=== APD bias flyback — analytical design (LT3757, DCM) ===")
print(f"Load: APD {I_apd_max*1e6:.0f} uA + bleeder {Vout_max/R_bleed*1e6:.0f} uA "
      f"= {I_load*1e6:.0f} uA  -> P_out = {P_out*1e3:.0f} mW, "
      f"P_in(eta={eta}) = {P_in*1e3:.0f} mW")

# DCM: P_in = 0.5 * Lp * Ipk^2 * f_sw  ->  Ipk
Ipk_pri = math.sqrt(2 * P_in / (Lp * f_sw))
Vor = Vout_max / N                       # reflected output voltage
D_worst = Vor / (Vor + Vin_min)          # ton/(ton+toff) in DCM boundary form
t_on = Lp * Ipk_pri / Vin_min
t_off = Lp * Ipk_pri / Vor
print(f"Turns ratio 1:{N:.0f}, Lp = {Lp*1e6:.0f} uH, f_sw = {f_sw/1e3:.0f} kHz")
print(f"Primary peak current Ipk = {Ipk_pri:.2f} A, t_on = {t_on*1e6:.2f} us, "
      f"t_off = {t_off*1e6:.2f} us, period = {1/f_sw*1e6:.2f} us "
      f"(DCM: t_on+t_off = {(t_on+t_off)*1e6:.2f} us < period: "
      f"{'OK' if t_on+t_off < 1/f_sw else 'NOT DCM!'})")
print(f"Reflected voltage Vor = {Vor:.1f} V, worst-case duty = {D_worst:.3f}")

# stresses
Vds_mos = Vin_max + Vor
Vds_spike = Vin_max + 1.8 * Vor          # leakage spike allowance 1.8x Vor
Id_rms = Ipk_pri * math.sqrt(D_worst / 3)
V_diode = Vout_max + Vin_max * N
Ipk_sec = Ipk_pri / N
print(f"MOSFET: Vds = {Vds_mos:.1f} V, with spike allowance {Vds_spike:.1f} V "
      f"vs 100 V rating -> {100*Vds_spike/100:.0f}% ; Irms = {Id_rms:.2f} A vs 2 A")
print(f"Secondary diode: Vrev = {V_diode:.0f} V vs 1000 V -> "
      f"{100*V_diode/1000:.0f}% ; Ipk_sec = {Ipk_sec*1e3:.0f} mA")
print(f"Output caps see {Vout_max:.0f} V vs 630 V class -> {100*Vout_max/630:.0f}%")

# ripple: raw (charge packet / load droop between packets) then RC filter
ripple_raw = I_load / (f_sw * C_out)
att = 1.0 / math.sqrt(1 + (2 * math.pi * f_sw * R_filt * C_filt) ** 2)
ripple_apd = ripple_raw * att
drop_filt = I_load * R_filt
print(f"Ripple at converter output ~ {ripple_raw*1e3:.1f} mVpp; RC post-filter "
      f"({R_filt/1e3:.0f} kohm x {C_filt*1e9:.0f} nF, attenuation {att:.2e}) "
      f"-> {ripple_apd*1e6:.1f} uVpp at APD; filter drop {drop_filt:.1f} V "
      f"(absorbed by DAC setpoint range)")

# bleeder discharge: Ceq ~ C_out + C_filt on the APD side of R_filt is C_filt;
# the converter-side cap discharges through R_bleed + path — use total C.
Ceq = C_out + C_filt
tau = R_bleed * Ceq
t_60 = tau * math.log(Vout_max / 60.0)
print(f"Bleeder: tau = {tau:.2f} s, 420 V -> 60 V in {t_60:.2f} s")

checks = [
    ("MOSFET V stress (incl. spike) < 80% of 100 V", Vds_spike < 0.8 * 100),
    ("MOSFET I_rms < 80% of 2 A", Id_rms < 0.8 * 2.0),
    ("Diode V stress < 80% of 1000 V", V_diode < 0.8 * 1000),
    ("Output cap V stress < 80% of 630 V", Vout_max < 0.8 * 630),
    ("Duty cycle < 0.85 worst case", D_worst < 0.85),
    ("DCM maintained (t_on+t_off < period)", t_on + t_off < 1 / f_sw),
    ("Ripple at APD < 20 mVpp (R9)", ripple_apd < 20e-3),
    ("Bleeder 420->60 V in < 10 s (R9)", t_60 < 10.0),
]
print("\n--- checks ---")
ok = True
for name, passed in checks:
    print(f"{'PASS' if passed else 'FAIL'}  {name}")
    ok &= passed
print(f"\nHV DESIGN VERDICT: {'PASS' if ok else 'FAIL'}")
with open("results/hv_design.txt", "w") as f:
    f.write("See stdout capture in results/hv_design_run.txt\n")
