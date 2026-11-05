#!/usr/bin/env python3
"""HV clamp + SHDN re-ratio derivation — PDLVDS-RX rev A fix.

All inputs are primary-record values:
  * LT3757 datasheet (ADI Rev. F) Electrical Characteristics:
      VFBX(REG)      1.569 / 1.6 / 1.631 V   (full temp range)
      FBX pin current at VFBX=1.6 V: 70 typ / 100 max nA (into pin)
      SHDN/UVLO falling threshold: 1.17 / 1.22 / 1.27 V (full range)
      SHDN input-low voltage: 0.4 V
      SHDN pin bias current (pin in 0.7..1.22 V band): 1.7/2/2.5 uA
        pull-down (IS1); pin functions text: IS1 active above 0.7 V.
  * Docs/03 network (old): R31 7.68M / R32 49.9k / R33 71.5k,
    V_DAC in [0, 2.5] V (DAC8562 internal ref, gain x1).
  * C30737 (docs/07): VBR 180..260 V at 22 C, tempco 1.3 V/C,
    operating range -20..+60 C.
  * VBUS (docs/03): 4.75..5.25 V.
Transfer (KCL at the FBX node, V_FBX servoed to V_REF):
  V_HV = V_REF*(1 + R31/R32 + R31/R33) - (R31/R33)*V_DAC + R31*I_FBX
  (I_FBX term: pin sinks current, divider must supply it via R31.)
"""

VREF_T, VREF_L, VREF_H = 1.6, 1.569, 1.631
I_FBX_MAX = 100e-9
VDAC_FS = 2.5

def transfer(r31, r32, r33, vref=VREF_T, tol=0.0, ifbx=0.0):
    """Return (A, S): V_HV = A - S*V_DAC. tol>0 = worst-high stack."""
    a = (r31 * (1 + tol)) / (r32 * (1 - tol))
    b = (r31 * (1 + tol)) / (r33 * (1 - tol))
    A = vref * (1 + a + b) + r31 * (1 + tol) * ifbx
    S = b  # volts per DAC volt (at vref nominal slope scaling ignored:
           # slope term scales with r31/r33 only, vref enters via A)
    return A, S

def show(name, r31, r32, r33):
    A, S = transfer(r31, r32, r33)
    print(f"{name}: R31={r31/1e6}M R32={r32/1e3}k R33={r33/1e3}k")
    print(f"  nominal:  A={A:.2f} V (V_DAC=0), mid(1.25)={A - S*1.25:.2f} V,"
          f" L(2.5)={A - S*2.5:.2f} V, slope={S:.3f} V/V")
    for tol, tag in ((0.001, "0.1% (as specified)"), (0.01, "1% (sensitivity)")):
        Aw, _ = transfer(r31, r32, r33, vref=VREF_H, tol=tol, ifbx=I_FBX_MAX)
        Al, _ = transfer(r31, r32, r33, vref=VREF_L, tol=-tol)
        print(f"  worst-high A [{tag}]: {Aw:.2f} V   worst-low A: {Al:.2f} V")
    print()

print("=== FB set-point network ===")
show("OLD (S8664 variant values)", 7.68e6, 49.9e3, 71.5e3)
show("NEW (C30737 fit)", 7.68e6, 75.0e3, 140e3)

# Coverage of the C30737 envelope by the NEW nominal range
A, S = transfer(7.68e6, 75.0e3, 140e3)
L = A - S * VDAC_FS
cold_min_unit = 180 - 1.3 * (22 - (-20))   # min-VBR unit at -20 C
print(f"Coverage: cold corner (180 V unit at -20 C) needs {cold_min_unit:.1f} V;"
      f" new low end {L:.2f} V -> margin {cold_min_unit - L:.2f} V")
# low end worst-high corner: A high, slope low, DAC full-scale low (-0.5% ref allowance)
Aw, _ = transfer(7.68e6, 75.0e3, 140e3, vref=VREF_H, tol=0.001, ifbx=I_FBX_MAX)
S_low = (7.68e6 * 0.999) / (140e3 * 1.001)
L_wc = Aw - S_low * (VDAC_FS * 0.995)
print(f"  low end, stacked worst-high corner: {L_wc:.2f} V (need <= {cold_min_unit:.1f})")
print(f"  VBR span 180..260: nominal range {L:.1f}..{A:.1f} V covers all but the"
      f" top {260 - A:.1f} V sliver (units with VBR > {A:.0f} V at warm temps)")

print()
print("=== SHDN/UVLO divider (PC7 high-Z = idle/absent-jumper state) ===")
TH_FALL_MIN = 1.17
def shdn(name, r25, r26, tol=0.01):
    for vbus in (4.75, 5.0, 5.25):
        k = r26 / (r25 + r26)
        print(f"  {name}: VBUS={vbus}: node={vbus * k:.3f} V", end="")
        kw = (r26 * (1 + tol)) / (r25 * (1 - tol) + r26 * (1 + tol))
        rth = (r25 * (1 - tol) * r26 * (1 + tol)) / (r25 * (1 - tol) + r26 * (1 + tol))
        node_w = vbus * kw
        leak = 1e-6 * rth  # 1 uA MCU pin leakage design allowance
        print(f" | worst-high(+{tol*100:.0f}% tol)={node_w:.3f} V,"
              f" +1uA leak={node_w + leak:.3f} V,"
              f" margin vs 1.17 = {TH_FALL_MIN - node_w - leak:.3f} V")
    k = r26 / (r25 + r26)
    vin_fall = 1.22 / k
    verdict = ("divider alone enables at normal VBUS" if vin_fall < 5.25
               else "above max VBUS 5.25 -> divider alone can never enable")
    print(f"  {name}: divider-only VIN falling point (typ 1.22 V ref) = {vin_fall:.2f} V"
          f" ({verdict})")
    print()

shdn("OLD", 100e3, 33e3)
shdn("NEW", 143e3, 33e3)
print("PC7 drive states (both designs): LOW -> node ~0 V (<= 0.4 V input-low);")
print("HIGH -> 3.3 V push-pull, above 1.27 V threshold max; sources"
      " ~(3.3/33k - (5-3.3)/143k) = 88 uA into the NEW divider.")

print()
print("=== Firmware DAC mapping spot values (NEW transfer) ===")
for v in (0.0, 116.07, 150.0, 184.64, 200.0, 250.0, 253.21):
    vdac = min(max((A - v) / S, 0.0), VDAC_FS)
    counts = int(vdac / VDAC_FS * 65535 + 0.5)
    print(f"  V_req={v:7.2f} -> V_DAC={vdac:.4f} V -> counts={counts}")
