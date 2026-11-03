#!/usr/bin/env python3
"""
impedance.py — controlled-impedance geometry for the PCB (stage 4d).

Stackup: JLCPCB 4-layer 1.6 mm, stackup JLC04161H-7628 (state it — this is
the assumption; re-check before ordering a different stackup):
  L1 (signal, 1 oz = 35 um) -- prepreg 7628, h = 0.2104 mm, Er = 4.4 (1 GHz
  class value for 7628 prepreg; JLC publishes Er ~4.6 for the core, prepreg
  flows lower — sensitivity to Er is printed) -- L2 GND plane.
Surface microstrip formulas: Hammerstad & Jansen (closed-form, as collected
in Wadell, "Transmission Line Design Handbook"):

  eps_eff = (Er+1)/2 + (Er-1)/2 * (1 + 12h/W)^-1/2   (+ thickness correction
            terms neglected beyond the standard u=W/h formulation)
  Z0 = 120pi / ( sqrt(eps_eff) * (u + 1.393 + 0.667*ln(u+1.444)) )  u >= 1
  Z0 = 60/sqrt(eps_eff) * ln(8/u + u/4)                              u <  1
Differential (edge-coupled microstrip, Wadell):
  Zdiff = 2 * Z0 * (1 - 0.48 * exp(-0.96 * S / W))
where S is edge-to-edge gap. Both are standard published approximations,
good to a few percent vs a field solver; the fab house impedance coupon
remains the authority (stated in docs/05 test plan).

Outputs the geometry the PCB generator must use:
  50 ohm single-ended width, 100 ohm differential width/gap, and (for the
  ULPI 60 MHz and LVDS pairs) the same pair geometry is reused.
"""
import math

Er = 4.4
h = 0.2104      # mm, L1->L2 prepreg (7628)
t = 0.035       # mm copper


def z0_microstrip(W, Er=Er, h=h):
    u = W / h
    eps_eff = (Er + 1) / 2 + (Er - 1) / 2 * (1 + 12 / u) ** -0.5
    if u >= 1:
        return 120 * math.pi / (math.sqrt(eps_eff) *
                                (u + 1.393 + 0.667 * math.log(u + 1.444)))
    return 60 / math.sqrt(eps_eff) * math.log(8 / u + u / 4)


def solve_width(z_target, Er=Er):
    lo, hi = 0.02, 3.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if z0_microstrip(mid, Er) > z_target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def zdiff(W, S, Er=Er):
    return 2 * z0_microstrip(W, Er) * (1 - 0.48 * math.exp(-0.96 * S / W))


print("=== Impedance geometry — JLC04161H-7628 4L stackup ===")
print(f"L1-L2 dielectric h = {h} mm, Er = {Er}, copper t = {t*1000:.0f} um")

W50 = solve_width(50.0)
print(f"50 ohm SE:  W = {W50:.3f} mm  (check Z0 = {z0_microstrip(W50):.1f} ohm)")
for er in (4.2, 4.6):
    print(f"   sensitivity Er={er}: same W gives Z0 = "
          f"{z0_microstrip(W50, er):.1f} ohm; W for 50 ohm = {solve_width(50, er):.3f} mm")

# diff pair: choose a manufacturable width, solve gap for 100 ohm
for W in (0.25, 0.30, 0.35):
    lo, hi = 0.05, 2.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if zdiff(W, mid) < 100:
            lo = mid
        else:
            hi = mid
    S = (lo + hi) / 2
    print(f"100 ohm diff: W = {W:.2f} mm, gap S = {S:.3f} mm "
          f"(pitch {W+S:.3f} mm, check Zdiff = {zdiff(W, S):.1f} ohm)")

W_diff, S_diff = 0.30, None
lo, hi = 0.05, 2.0
for _ in range(80):
    mid = (lo + hi) / 2
    if zdiff(W_diff, mid) < 100:
        lo = mid
    else:
        hi = mid
S_diff = (lo + hi) / 2

# length / skew / loss sanity for the LVDS pair at 50 Mbps and ULPI at 60 MHz
eps_eff = (Er + 1) / 2 + (Er - 1) / 2 * (1 + 12 * h / W_diff) ** -0.5
vp = 299.79 / math.sqrt(eps_eff)     # mm/ns
print(f"\nPropagation: eps_eff = {eps_eff:.2f}, vp = {vp:.0f} mm/ns, "
      f"delay = {1000/vp:.2f} ps/mm")
print(f"Intra-pair skew budget: 1 mm length mismatch = {1000/vp:.1f} ps "
      f"= {1000/vp/20000*100:.3f}% of the 20 ns UI — length matching to "
      f"+/-0.5 mm is ample; rule adopted: match within 0.5 mm.")
print(f"UI = 20 ns -> one UI of trace = {vp*20/1000:.1f} m: board-scale "
      f"traces are electrically short; termination and geometry discipline "
      f"matter, serpentine tuning does not.")

chosen = [
    ("50 ohm single-ended (SMA test input, ULPI clock if routed SE)", W50),
]
ok = abs(z0_microstrip(W50) - 50) < 1.0 and abs(zdiff(W_diff, S_diff) - 100) < 1.0
print("\n--- PCB geometry to use (hw generator constants) ---")
print(f"SE50_W_MM   = {W50:.3f}")
print(f"DIFF_W_MM   = {W_diff:.3f}")
print(f"DIFF_GAP_MM = {S_diff:.3f}")
print(f"VERDICT: {'PASS' if ok else 'FAIL'} — closed-form solution converges "
      f"to 50.0 / 100.0 ohm within 1 ohm; fab coupon verification is in the "
      f"test plan (docs/05).")
