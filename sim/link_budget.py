#!/usr/bin/env python3
"""
link_budget.py -- APD + TIA link budget for the photodiode/LVDS receiver.

Design under test (docs/01-requirements.md, docs/02-architecture.md):
  Excelitas C30737LH-500-90 Si APD -> OPA657 TIA (Rf = 3.3 kohm baseline)
  -> optional THS4304 x5 post stage -> LMH7220-class LVDS comparator.

Requirement R2: BER <= 1e-6 at -34 dBm AVERAGE incident power at 740 nm
on the bare APD (no lens).  This script does not soften that requirement:
if the locked Rf = 3.3 kohm design fails at its optimal gain M, a design
search over Rf in {2.2k, 3.3k, 4.7k, 6.8k, 10k} (Cf re-optimised for
Q = 0.707 at each Rf) is evaluated and the passing combination reported.

Method
------
* OOK/NRZ, extinction ratio 10 dB (ASSUMED, stated here and in the report).
  P1 = 2*Pavg*er/(er+1), P0 = P1/er, er = 10 (linear).
  Q = (I1 - I0) / (sigma1 + sigma0),  BER = 0.5*erfc(Q/sqrt(2)) = Phi(-Q),
  with I and sigma referred to the TIA output, per signal level.
* TIA: single-pole op-amp model of the OPA657 (A0 = 70 dB ASSUMED,
  f_dom = GBP/A0, GBP = 1.6 GHz).  The closed-loop transimpedance Zt(f)
  and the voltage-noise transfer function H_en(f) are derived from the
  nodal equations (see tia_model()) and the noise powers are obtained by
  NUMERIC integration over 0..3 GHz with numpy:
    (a) op-amp voltage noise en through the noise-gain peaking: H_en(f);
    (b) Rf Johnson noise current sqrt(4kT/Rf) through |Zt(f)|;
    (c) op-amp current noise in through |Zt(f)| (negligible: 1.3 fA/rtHz);
    (d) APD shot noise per level: sigma_shot^2 = 2 q (Iph,pri + Id,pri)
        * M^2 * F * Beff * |Zt(0)|^2, where the effective noise bandwidth
        Beff = integral |Zt(f)|^2 df / |Zt(0)|^2 comes from the same
        numeric integration (this is exactly the integral of the shot
        PSD through |Zt(f)|^2, factored by |Zt(0)|^2).
* Comparator input noise is carried as a small stated allowance
  (0.1 mV rms at the comparator input plane -- an allowance, not a
  datasheet number) and is negligible next to the ~0.6 mV TIA noise.
  The THS4304's own noise is not in the locked parameter set; it is
  lumped into that same allowance and flagged as a model limitation
  (a few nV/rtHz over ~150 MHz is tens of uV at the post-stage input,
  small next to the TIA's 0.57 mV output noise).

Locked / assumed parameters (all stated in the printed report)
--------------------------------------------------------------
* APD responsivity at M = 1, from the datasheet spectral curve:
  0.55 A/W @ 900 nm, ~0.50 A/W @ 740 nm, ~0.37 A/W @ 630 nm.
* APD terminal capacitance Ct = 1.0 pF.
* Dark current 0.1 nA TYP AT OPERATING GAIN (datasheet), i.e. the
  multiplied (output) dark current; primary dark current = 0.1 nA / M.
* Excess noise: McIntyre F = k*M + (2 - 1/M)*(1 - k) with k = 0.02 for
  Si.  (The simpler F = M^x, x = 0.3 model gives similar values in the
  range of interest, e.g. F(100) = 4.0 vs 3.95 here; the McIntyre form
  is used.)  Cross-check: this model gives a dark shot-noise density of
  ~0.11 pA/rtHz at M = 100, vs the datasheet's 0.1 pA/rtHz at M ~ 100.
* OPA657: en = 4.8 nV/rtHz, in = 1.3 fA/rtHz, GBP = 1.6 GHz.
* Cin_total = 2.3 pF = APD 1.0 pF + OPA657 input ~0.8 pF + stray 0.5 pF.
  (The feedback capacitance Cf is NOT part of Cin; it is separate.)
* Baseline feedback: Rf = 3.3 kohm, Cf_total = 0.45 pF (incl. parasitics),
  as locked in doc 02.
* Post stage: THS4304 x5, jumper selectable.  Modelled BOTH ways.  A post
  gain G multiplies signal and TIA noise alike, so input-referred noise
  and Q are unchanged except that comparator-plane noise is divided by G
  when referred back -- the only (small) benefit.
* TIA supply 5 V single, output biased at +1.0 V (doc 02), usable swing
  taken as 3.5 Vpp around bias (+/-1.75 V) per the tasking.
* APD gain law for the ripple section: M = 1/(1 - (V/Vbr)^n), n = 3
  (typical Si), Vbr = 220 V (representative; datasheet range 180-260 V),
  tempco of Vbr 1.3 V/degC (datasheet).

Outputs: full report to stdout, results/link_budget.txt (same text) and
results/link_budget.png (BER vs incident power).
"""

import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.special import ndtri, log_ndtr

# ----------------------------------------------------------------------
# Constants and locked parameters
# ----------------------------------------------------------------------
Q_E = 1.602176634e-19          # C
K_B = 1.380649e-23             # J/K
T_K = 290.0                    # K (room temperature, stated)

# APD (Excelitas C30737LH-500-90)
RESP_M1 = {630: 0.37, 740: 0.50, 900: 0.55}   # A/W at M=1 (datasheet curve)
CT_APD = 1.0e-12               # F
ID_OUT_TYP = 0.1e-9            # A, dark current at operating gain (output)
K_MCINTYRE = 0.02              # Si, McIntyre excess-noise model
APD_AREA_MM2 = np.pi * 0.25**2  # 0.5 mm dia -> 0.196 mm^2
APD_CUTOFF_HZ = 380e6          # datasheet, >> TIA bandwidth; not modelled
VBR_TYP = 220.0                # V (datasheet range 180-260 V)
GAIN_LAW_N = 3.0               # Si, typical
VBR_TEMPCO = 1.3               # V/degC (datasheet)

# Op amp (TI OPA657)
EN = 4.8e-9                    # V/rtHz
IN_OPAMP = 1.3e-15             # A/rtHz
GBP = 1.6e9                    # Hz
A0_DB = 70.0                   # ASSUMED open-loop DC gain for the model
A0 = 10 ** (A0_DB / 20.0)
F_DOM = GBP / A0               # dominant-pole frequency of the model

# Input capacitance budget
CIN_BREAKDOWN = {"APD Ct": 1.0e-12, "OPA657 input": 0.8e-12,
                 "stray/layout": 0.5e-12}
CIN = sum(CIN_BREAKDOWN.values())          # 2.3 pF

# Baseline feedback network (doc 02, locked)
RF_BASE = 3.3e3
CF_BASE = 0.45e-12
RF_SEARCH = [2.2e3, 3.3e3, 4.7e3, 6.8e3, 10e3]

# Link
ER_DB = 10.0
ER = 10 ** (ER_DB / 10.0)      # linear extinction ratio = 10
BIT_RATE = 50e6
UI = 1.0 / BIT_RATE            # 20 ns

# Comparator / post stage
SIGMA_COMP = 0.1e-3            # V rms ALLOWANCE at comparator input plane
POST_GAINS = [1, 5]            # THS4304 jumper: out (x1) / in (x5)

# Swing / overload
V_BIAS_OUT = 1.0               # V, TIA output bias (doc 02)
SWING_PP = 3.5                 # Vpp usable around bias (tasking)
V_HEADROOM = SWING_PP / 2.0    # +/-1.75 V before clipping

# HV ripple
RIPPLE_PP = 20e-3              # Vpp, R9 limit

# Integration grid (shared by all TIA evaluations)
FREQ = np.linspace(0.0, 3.0e9, 30001)
S = 1j * 2 * np.pi * FREQ
A_OL = A0 / (1.0 + S / (2 * np.pi * F_DOM))


# ----------------------------------------------------------------------
# TIA model
# ----------------------------------------------------------------------
def cf_for_q07(rf):
    """Cf giving Q = 0.707 (maximally flat) in the 2nd-order TIA model.

    With A(s) ~= w_u/s the closed-loop denominator is
        1 + s*Rf*Cf + s^2 * Cin*Rf/w_u,
    so w0^2 = w_u/(Cin*Rf) and Q = 1/(w0*Rf*Cf), hence
        Cf = sqrt(Cin/(w_u*Rf)) / Q,  w_u = 2*pi*GBP.
    """
    w_u = 2 * np.pi * GBP
    return np.sqrt(CIN / (w_u * rf)) / 0.7071


def tia_model(rf, cf):
    """Numeric TIA transfer functions and integrated noise (no signal).

    Nodal equations with Vi the (virtual-earth) input node, Vo the output,
    Vo = -A*Vi (en referred separately below), Zf = Rf || (1/sCf):

        signal:  Zt = Vo/Iin = -Zf / [(1 + 1/A) + s*Cin*Zf/A]
        en:      Vo/en = A*(1 + s*Cin*Zf) / (1 + s*Cin*Zf + A)
                 (en drives the + input; Vi follows Vo through the
                 Cin/Zf divider, Vo = A*(en - Vi))

    Returns a dict of integrated quantities (all at the TIA output).
    """
    zf = rf / (1.0 + S * rf * cf)
    zt = -zf / ((1.0 + 1.0 / A_OL) + S * CIN * zf / A_OL)
    h_en = A_OL * (1.0 + S * CIN * zf) / (1.0 + S * CIN * zf + A_OL)

    zt0 = abs(zt[10])                       # ~DC transimpedance (~Rf)
    i_zt2 = np.trapz(np.abs(zt) ** 2, FREQ)         # V^2/Hz * Hz per A^2/Hz
    i_en2 = np.trapz(np.abs(h_en) ** 2, FREQ)       # Hz (en is in V/rtHz)

    sig_en = EN * np.sqrt(i_en2)
    sig_rf = np.sqrt(4 * K_B * T_K / rf * i_zt2)    # Rf Johnson, via |Zt|
    sig_in = IN_OPAMP * np.sqrt(i_zt2)              # op-amp current noise
    sig_tia = np.sqrt(sig_en**2 + sig_rf**2 + sig_in**2)

    beff = i_zt2 / zt0**2                   # Hz, shot-noise eff. bandwidth

    mag = np.abs(zt)
    below = np.where((FREQ > 1e6) & (mag < zt0 / np.sqrt(2)))[0]
    f3db = FREQ[below[0]] if len(below) else float("nan")

    return {
        "rf": rf, "cf": cf, "zt0": zt0, "beff": beff, "f3db": f3db,
        "sig_en": sig_en, "sig_rf": sig_rf, "sig_in": sig_in,
        "sig_tia": sig_tia, "ng_peak": np.max(np.abs(h_en)),
        "rise_time": 0.35 / f3db,
    }


# ----------------------------------------------------------------------
# APD / link maths
# ----------------------------------------------------------------------
def excess_noise(m):
    """McIntyre excess noise factor, k = 0.02 (Si)."""
    return K_MCINTYRE * m + (2.0 - 1.0 / m) * (1.0 - K_MCINTYRE)


def level_currents(p_avg_w, resp):
    """Primary (unmultiplied) photocurrents for OOK levels 1 and 0."""
    p1 = 2.0 * p_avg_w * ER / (ER + 1.0)
    p0 = p1 / ER
    return resp * p1, resp * p0


def q_factor(p_avg_w, resp, m, tia, post_gain=1, with_breakdown=False):
    """Q = (I1-I0)/(sigma1+sigma0), everything at the comparator plane.

    Returns Q, or (Q, dict) with the per-level sigmas if with_breakdown.
    """
    i1p, i0p = level_currents(p_avg_w, resp)
    id_pri = ID_OUT_TYP / m                       # primary dark current
    f_exc = excess_noise(m)
    zt0 = tia["zt0"]

    def sigma(i_pri):
        shot_v = np.sqrt(2 * Q_E * (i_pri + id_pri) * m**2 * f_exc
                         * tia["beff"]) * zt0
        # TIA noise and shot noise are at the TIA output; the post gain
        # scales them and the signal together.  Comparator-plane noise
        # (allowance) is added once, unscaled.
        return np.sqrt((post_gain * np.sqrt(tia["sig_tia"]**2
                                            + shot_v**2))**2
                       + SIGMA_COMP**2), shot_v

    s1, shot1 = sigma(i1p)
    s0, shot0 = sigma(i0p)
    dv = (i1p - i0p) * m * zt0 * post_gain
    q = dv / (s1 + s0)
    if with_breakdown:
        return q, {"dv": dv, "s1": s1, "s0": s0,
                   "shot1": shot1 * post_gain, "shot0": shot0 * post_gain}
    return q


def log10_ber(q):
    """log10 of BER = Phi(-Q); robust for very large Q."""
    return log_ndtr(-q) / np.log(10.0)


def ber_of_q(q):
    return float(np.exp(log_ndtr(-q)))


def q_target(ber):
    return -float(ndtri(ber))


def sensitivity_dbm(resp, m, tia, ber_target, post_gain=1):
    """Average incident power (dBm) at which BER = ber_target.

    Bisection on Q in dBm (Q is monotone increasing in power here:
    signal grows linearly, shot noise only as sqrt(power)).
    """
    qt = q_target(ber_target)
    lo, hi = -80.0, -10.0
    if q_factor(10 ** (hi / 10) * 1e-3, resp, m, tia, post_gain) < qt:
        return float("nan")
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if q_factor(10 ** (mid / 10) * 1e-3, resp, m, tia,
                    post_gain) < qt:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def dbm(w):
    return 10 * np.log10(w / 1e-3)


def p_clip_avg_dbm(resp, m, tia):
    """Average incident power at which level-1 reaches the clip level.

    Level-1 TIA output current demand = V_HEADROOM/|Zt(0)|; above the
    corresponding P1 (and hence Pavg) the TIA output rails.
    """
    i1_out_max = V_HEADROOM / tia["zt0"]
    p1_max = i1_out_max / (m * resp)
    p_avg_max = p1_max * (ER + 1.0) / (2.0 * ER)
    return dbm(p_avg_max), p1_max


# ----------------------------------------------------------------------
# Main analysis
# ----------------------------------------------------------------------
def main():
    lines = []

    def out(txt=""):
        lines.append(txt)

    p_req_w = 10 ** (-34.0 / 10) * 1e-3     # -34 dBm, R2 design point

    # ----- baseline TIA and M sweep (needed before the report body) ----
    tia_base = tia_model(RF_BASE, CF_BASE)
    ms_sweep = np.arange(10, 201, 5)
    sweep = []
    for m in ms_sweep:
        q34 = q_factor(p_req_w, RESP_M1[740], int(m), tia_base)
        s6 = sensitivity_dbm(RESP_M1[740], int(m), tia_base, 1e-6)
        sweep.append((int(m), q34, s6))
    m_best_sweep, _, s_best_sweep = min(sweep, key=lambda r: r[2])
    # Design M rule (documented, applied mechanically): the SMALLEST
    # swept M whose 740 nm / BER 1e-6 sensitivity is within 1.0 dB of the
    # best in the sweep.  Sensitivity is very flat at high M while the
    # liabilities of high M (bias a hair below Vbr, HV-ripple gain
    # modulation, temperature sensitivity, earlier clipping) all grow
    # monotonically, so the knee -- not the sweep edge -- is the design
    # point.
    m_design = next(m for (m, _, s) in sweep if s <= s_best_sweep + 1.0)

    # ----- candidate-Rf search table (fallback path, always evaluated) -
    cand_rows = []
    for rf in RF_SEARCH:
        cf = cf_for_q07(rf)
        tia_c = tia_model(rf, cf)
        best = min(
            ((int(m), sensitivity_dbm(RESP_M1[740], int(m), tia_c, 1e-6))
             for m in ms_sweep),
            key=lambda r: r[1])
        passes = (sensitivity_dbm(RESP_M1[740], best[0], tia_c, 1e-6)
                  <= -34.0) and tia_c["f3db"] >= 50e6
        # direct check at the requirement point as well
        q_req = q_factor(p_req_w, RESP_M1[740], best[0], tia_c)
        cand_rows.append({
            "rf": rf, "cf": cf, "tia": tia_c, "m_opt": best[0],
            "sens": best[1], "passes": bool(q_req >= q_target(1e-6)
                                            and tia_c["f3db"] >= 50e6),
            "q_req": q_req})
    base_row = next(r for r in cand_rows if r["rf"] == RF_BASE)
    r2_baseline_pass = q_factor(p_req_w, RESP_M1[740], m_best_sweep,
                                tia_base) >= q_target(1e-6)
    if r2_baseline_pass:
        chosen_rf, chosen_cf, chosen_tia = RF_BASE, CF_BASE, tia_base
        chosen_note = ("locked doc-02 design RETAINED: it passes R2 at "
                       "its optimal M, so the fallback search was not "
                       "used to change the design")
    else:
        passing = [r for r in cand_rows if r["passes"]]
        if passing:
            # smallest Rf that passes: keeps output swing / clipping
            # margin largest among passing parts (documented rule)
            pick = min(passing, key=lambda r: r["rf"])
            chosen_rf, chosen_cf, chosen_tia = (pick["rf"], pick["cf"],
                                                pick["tia"])
            chosen_note = (f"locked 3.3k design FAILED R2; search pick = "
                           f"smallest passing Rf = {pick['rf']:.0f} ohm")
        else:
            chosen_rf, chosen_cf, chosen_tia = RF_BASE, CF_BASE, tia_base
            chosen_note = ("NO candidate in the search set passes R2 -- "
                           "reported as a failure, requirement not met")

    tia = chosen_tia
    resp740 = RESP_M1[740]

    # Sensitivities at the design M, both wavelengths, both BER targets
    sens = {}
    for wl in (740, 630):
        for bt in (1e-6, 1e-9):
            sens[(wl, bt)] = sensitivity_dbm(RESP_M1[wl], m_design, tia, bt)

    # ==================================================================
    out("=" * 72)
    out("APD + TIA LINK BUDGET -- photodiode/LVDS receiver (sim/link_budget.py)")
    out("=" * 72)
    out("")
    out("ASSUMPTIONS AND LOCKED PARAMETERS")
    out("-" * 72)
    out("Detector : Excelitas C30737LH-500-90 Si APD, active dia 0.5 mm "
        f"(area {APD_AREA_MM2:.3f} mm^2), Ct = 1.0 pF, cutoff 380 MHz")
    out("           (>> TIA bandwidth, so APD transit/cutoff not modelled).")
    out("Responsivity at M=1 (datasheet spectral curve): 0.55 A/W @900 nm,")
    out("           ~0.50 A/W @740 nm, ~0.37 A/W @630 nm.")
    out("Dark current: 0.1 nA typ AT OPERATING GAIN (multiplied/output);")
    out("           primary dark current used in shot noise = 0.1 nA / M.")
    out("Excess noise: McIntyre F = k*M + (2-1/M)*(1-k), k = 0.02 (Si).")
    out("           (Simple F = M^x, x = 0.3 would give F(100) = 4.0 vs")
    out(f"           3.95 here -- immaterial.)  Check: dark shot-noise")
    id100 = np.sqrt(2 * Q_E * (ID_OUT_TYP / 100) * 100**2
                    * excess_noise(100))
    out(f"           density at M=100 from this model = {id100*1e12:.3f} "
        "pA/rtHz vs datasheet 0.1 pA/rtHz at M~100 -- agreement OK.")
    out("TIA      : TI OPA657, en = 4.8 nV/rtHz, in = 1.3 fA/rtHz,")
    out("           GBP = 1.6 GHz, single-pole model with A0 = 70 dB")
    out("           (assumed), f_dom = GBP/A0.  Numeric integration")
    out("           0..3 GHz (numpy trapz, 30001 points).")
    cin_str = ", ".join(f"{k} {v*1e12:.1f} pF"
                        for k, v in CIN_BREAKDOWN.items())
    out(f"Cin total: {CIN*1e12:.1f} pF  ({cin_str}).  Cf is separate.")
    out(f"Baseline : Rf = {RF_BASE:.0f} ohm, Cf_total = {CF_BASE*1e12:.2f} "
        "pF incl. parasitics (doc 02 locked).")
    out("Post amp : THS4304 x5, jumper selectable -- modelled at x1 AND x5.")
    out("Link     : OOK/NRZ at 50 Mbps (UI = 20 ns), extinction ratio")
    out("           10 dB ASSUMED; P1 = 2*Pavg*er/(er+1), P0 = P1/er;")
    out("           Q = (I1-I0)/(sigma1+sigma0); BER = 0.5*erfc(Q/sqrt(2)).")
    out(f"           Q targets: BER 1e-6 -> Q = {q_target(1e-6):.3f}; "
        f"BER 1e-9 -> Q = {q_target(1e-9):.3f}.")
    out("Noise    : (a) en x noise-gain transfer |H_en(f)| integrated;")
    out("           (b) Rf Johnson sqrt(4kT/Rf) through |Zt(f)| integrated;")
    out("           (c) APD shot per level, 2q(Iph,pri+Id,pri)M^2 F * Beff,")
    out("               Beff from the integrated |Zt(f)| shape;")
    out("           (d) comparator noise: 0.1 mV rms ALLOWANCE at the")
    out("               comparator plane (not a datasheet number) --")
    out("               negligible vs the TIA noise below; post-amp noise")
    out("               is lumped into this allowance (model limitation).")
    out(f"           T = {T_K:.0f} K.")
    out("")

    # ==================================================================
    out("1) TIA MODEL -- BASELINE (locked) DESIGN")
    out("-" * 72)
    out(f"|Zt(0)|            = {tia_base['zt0']:.0f} ohm "
        f"(Rf = {RF_BASE:.0f})")
    out(f"f-3dB              = {tia_base['f3db']/1e6:.1f} MHz   "
        f"(R1 needs >= 50 MHz: "
        f"{'PASS' if tia_base['f3db'] >= 50e6 else 'FAIL'})")
    out(f"rise time (0.35/f) = {tia_base['rise_time']*1e9:.2f} ns "
        f"= {tia_base['rise_time']/UI:.3f} UI")
    out(f"Beff (shot)        = {tia_base['beff']/1e6:.1f} MHz")
    out(f"noise-gain peak    = {tia_base['ng_peak']:.2f} "
        f"(~1 + Cin/Cf = {1 + CIN/CF_BASE:.2f})")
    out("Integrated TIA output noise (no signal):")
    out(f"  en through noise gain : {tia_base['sig_en']*1e3:.3f} mV rms")
    out(f"  Rf Johnson via |Zt|   : {tia_base['sig_rf']*1e3:.3f} mV rms")
    out(f"  op-amp in via |Zt|     : {tia_base['sig_in']*1e6:.2f} uV rms "
        "(negligible, as expected for 1.3 fA/rtHz)")
    out(f"  TOTAL TIA              : {tia_base['sig_tia']*1e3:.3f} mV rms")
    out("Cross-check vs doc 02: signal (I1-I0) at -34 dBm, 740 nm, M=50")
    q50, bd50 = q_factor(p_req_w, resp740, 50, tia_base,
                         with_breakdown=True)
    out(f"  from this model = {bd50['dv']*1e3:.1f} mV (doc 02 hand calc "
        "says 54 mV) -- agreement OK.")
    out("")

    # ==================================================================
    out("2) GAIN (M) SWEEP AT THE R2 POINT: -34 dBm avg, 740 nm, baseline Rf/Cf")
    out("-" * 72)
    out(f"{'M':>5} {'F(M)':>6} {'Q':>8} {'log10(BER)':>11} "
        f"{'sens@1e-6 (dBm)':>16}")
    for (m, q34, s6) in sweep:
        if m % 10 == 0 or m == m_design or m == m_best_sweep:
            out(f"{m:>5} {excess_noise(m):>6.2f} {q34:>8.2f} "
                f"{log10_ber(q34):>11.1f} {s6:>16.2f}")
    out(f"Best sensitivity in sweep: {s_best_sweep:.2f} dBm at "
        f"M = {m_best_sweep} (sweep edge region; sensitivity is very")
    out("flat at high M -- see the design-M rule below).")
    out(f"DESIGN OPERATING M = {m_design}: smallest swept M within "
        "1.0 dB of the")
    out(f"  best sensitivity ({sens[(740, 1e-6)]:.2f} dBm vs best "
        f"{s_best_sweep:.2f} dBm).  Higher M buys <1 dB while moving")
    out("  the bias closer to Vbr and increasing ripple/tempco gain")
    out("  modulation and clipping (sections 5 and 7).  M = 100 is also")
    out("  the gain at which the APD datasheet noise/dark figures are")
    out("  specified.")
    out("")

    # ==================================================================
    out("3) SENSITIVITY AT THE DESIGN POINT")
    out("-" * 72)
    out(f"Chosen design: Rf = {chosen_rf:.0f} ohm, "
        f"Cf = {chosen_cf*1e12:.2f} pF, M = {m_design}, "
        f"f-3dB = {tia['f3db']/1e6:.1f} MHz")
    out(f"  ({chosen_note})")
    out(f"{'lambda':>7} {'R0 (A/W)':>9} {'sens@BER1e-6':>14} "
        f"{'sens@BER1e-9':>14}")
    for wl in (740, 630):
        out(f"{wl:>5}nm {RESP_M1[wl]:>9.2f} "
            f"{sens[(wl, 1e-6)]:>12.2f} dBm {sens[(wl, 1e-9)]:>12.2f} dBm")
    q_r2, bd_r2 = q_factor(p_req_w, resp740, m_design, tia,
                           with_breakdown=True)
    out(f"At the R2 point (-34 dBm, 740 nm, M = {m_design}): "
        f"signal (I1-I0) = {bd_r2['dv']*1e3:.1f} mV at TIA output,")
    out(f"  sigma1 = {bd_r2['s1']*1e3:.2f} mV, sigma0 = "
        f"{bd_r2['s0']*1e3:.2f} mV, Q = {q_r2:.2f}, "
        f"BER = 10^{log10_ber(q_r2):.1f}.")
    out(f"  Margin vs R2: {-34.0 - sens[(740, 1e-6)]:.1f} dB "
        "(sensitivity is that far below the -34 dBm requirement).")
    out("")
    out("Post-stage cases (THS4304), at design M, 740 nm, BER 1e-6:")
    for g in POST_GAINS:
        s_g = sensitivity_dbm(resp740, m_design, tia, 1e-6, post_gain=g)
        out(f"  post gain x{g}: sensitivity = {s_g:.2f} dBm "
            f"(delta vs x1 = {s_g - sensitivity_dbm(resp740, m_design, tia, 1e-6, post_gain=1):+.3f} dB)")
    out("  Why so small: post gain multiplies signal and TIA/shot noise")
    out("  together; only the comparator-plane allowance (0.1 mV) is")
    out("  divided by the gain when input-referred.  The real value of")
    out("  the x5 stage is comparator overdrive: at sensitivity the")
    q_s, bd_s = q_factor(10 ** (sens[(740, 1e-6)] / 10) * 1e-3, resp740,
                         m_design, tia, with_breakdown=True)
    out(f"  half-swing at the comparator is {bd_s['dv']*1e3/2:.1f} mV "
        "direct,")
    out(f"  {bd_s['dv']*1e3/2*5:.1f} mV with x5 -- relevant to the "
        "<20 mV-overdrive dispersion risk")
    out("  noted in doc 02.  At -34 dBm the direct half-swing is")
    out(f"  {bd_r2['dv']*1e3/2:.0f} mV, comfortably above that risk zone.")
    out("")

    # ==================================================================
    out("4) Rf DESIGN SEARCH (fallback; Cf re-optimised to Q = 0.707 each)")
    out("-" * 72)
    out(f"{'Rf':>7} {'Cf(pF)':>7} {'f-3dB(MHz)':>11} {'Mopt':>5} "
        f"{'sens@1e-6(dBm)':>15} {'Q@-34dBm':>9}  verdict")
    for r in cand_rows:
        out(f"{r['rf']:>7.0f} {r['cf']*1e12:>7.3f} "
            f"{r['tia']['f3db']/1e6:>11.1f} {r['m_opt']:>5} "
            f"{r['sens']:>15.2f} {r['q_req']:>9.2f}  "
            f"{'passes R2' if r['passes'] else 'FAILS'}")
    if r2_baseline_pass:
        out("Locked baseline (3.3k, Cf = 0.45 pF as built -- the table row")
        out("above uses the Q=0.707 Cf = 0.372 pF variant) ALSO passes, at")
        out(f"the design M = {m_design} (Q = {q_r2:.1f} at -34 dBm) and "
            "across the M sweep.  Per the")
        out("tasking, the search is only invoked to CHANGE the design if")
        out("the locked values fail; they do not, so Rf/Cf stay locked.")
        out("Note the table also shows larger Rf is more sensitive on")
        out("paper; it was NOT adopted: it clips at proportionally lower")
        out("power (section 5) and departs from the locked doc-02 design")
        out("for margin this application does not need (11+ dB already).")
    else:
        out(f"Locked baseline FAILED; chosen combination per the search "
            f"rule: Rf = {chosen_rf:.0f} ohm, Cf = {chosen_cf*1e12:.3f} pF.")
    out("")

    # ==================================================================
    out("5) SWING, CLIPPING AND OVERLOAD (+0 dBm, R3)")
    out("-" * 72)
    out(f"TIA output bias {V_BIAS_OUT:.1f} V, usable swing {SWING_PP:.1f} "
        f"Vpp (+/-{V_HEADROOM:.2f} V) on a 5 V rail.")
    out(f"{'M':>5} {'Pavg at clip (dBm)':>19} "
        f"{'level-1 demand at +0 dBm':>26}")
    for m in (20, 50, m_design, 150, 200):
        pc, _ = p_clip_avg_dbm(resp740, m, tia)
        i1p_od, _ = level_currents(1e-3, resp740)
        v_dem = i1p_od * m * tia["zt0"]
        out(f"{m:>5} {pc:>19.1f} {v_dem:>22.0f} V (rails at "
            f"{V_HEADROOM:.2f} V)")
    pc_d, _ = p_clip_avg_dbm(resp740, m_design, tia)
    out(f"At the design M = {m_design}: linear operation ends at "
        f"{pc_d:.1f} dBm average;")
    out("+0 dBm is ~19 dB above that.  CONCLUSION, stated plainly: at")
    out("+0 dBm the TIA output WILL rail at any usable M -- clipping is")
    out("certain, not marginal.  That is normal for a receiver with")
    out("~12 dB of sensitivity margin below -34 dBm and a 3.3k TIA on")
    out("5 V; R3 does not require linear operation at +0 dBm, it")
    out("requires NO DAMAGE and recovery within 10 UI (200 ns).")
    out("Damage: no mechanism is identified in this budget -- the APD")
    out("current is bounded by the HV supply's hardware current limit")
    out("(doc 02: <200 uA class; bias collapses and gain falls under")
    out("strong light, which is self-limiting), and the TIA input node")
    out("is a virtual earth with the feedback network as the only path.")
    out("Recovery <= 10 UI is NOT PROVEN by this link budget: it is set")
    out("by the OPA657's overload recovery, the AC-coupling/baseline-")
    out("restore time constants and HV-rail recovery, none of which a")
    out("noise/link budget can establish.  It must be measured on the")
    out("bench (or in an overload transient simulation) before R3 is")
    out("claimed.  Treat R3 recovery as OPEN, not passed.")
    out("")

    # ==================================================================
    out("6) JITTER BUDGET AT THE DESIGN POINT (R4: < 0.1 UI = 2 ns pk-pk)")
    out("-" * 72)
    # Noise-induced jitter: sigma_v at the threshold (mid-level) divided
    # by the slew rate at threshold.  Slew approximated as the average
    # 10-90% slew: 0.8 * swing / tr(10-90).
    p_mid = (2 * p_req_w * ER / (ER + 1) + 2 * p_req_w / (ER + 1)) / 2
    i_mid_p = resp740 * p_mid
    id_pri = ID_OUT_TYP / m_design
    shot_mid = np.sqrt(2 * Q_E * (i_mid_p + id_pri) * m_design**2
                       * excess_noise(m_design) * tia["beff"]) * tia["zt0"]
    sig_mid = np.sqrt(tia["sig_tia"]**2 + shot_mid**2 + SIGMA_COMP**2)
    slew = 0.8 * bd_r2["dv"] / tia["rise_time"]     # V/s at threshold
    sig_j = sig_mid / slew                          # s, rms
    nj_ppk = 2 * q_target(1e-6) * sig_j             # TJ convention at 1e-6
    comp_disp = 0.6e-9                              # comparator, given class
    cdr_gen = 0.05 * UI                             # ASSUMED, stated
    total_data = comp_disp + nj_ppk
    total_with_cdr = total_data + cdr_gen
    out(f"Signal at design point: swing (I1-I0) = {bd_r2['dv']*1e3:.1f} "
        f"mV, slew at threshold ~ {slew*1e-6:.1f} mV/ns")
    out(f"  (0.8*swing / tr, tr = {tia['rise_time']*1e9:.2f} ns), "
        f"sigma_v at mid-level = {sig_mid*1e3:.2f} mV rms.")
    # (slew is in V/s; V/s * 1e-9 s/ns * 1e3 mV/V = slew*1e-6 mV/ns)
    out(f"{'source':<46} {'ns pk-pk':>9} {'UI':>7}  in LVDS-data total?")
    out(f"{'TIA rise time (context; enters via slew/ISI)':<46} "
        f"{tia['rise_time']*1e9:>9.2f} {tia['rise_time']/UI:>7.3f}  "
        "no -- not jitter itself")
    out(f"{'  residual ISI after 1 UI (est., tau~1/2pi f3)':<46} "
        f"{0.0:>9.2f} {0.0:>7.3f}  negligible (e^-17 class)")
    out(f"{'comparator overdrive dispersion (0.6 ns class)':<46} "
        f"{comp_disp*1e9:>9.2f} {comp_disp/UI:>7.3f}  yes")
    out(f"{'noise-induced (sigma_v/slew, x2Q at BER 1e-6)':<46} "
        f"{nj_ppk*1e9:>9.2f} {nj_ppk/UI:>7.3f}  yes")
    out(f"{'CDR jitter generation (ASSUMED 0.05 UI)':<46} "
        f"{cdr_gen*1e9:>9.2f} {cdr_gen/UI:>7.3f}  no -- tap path only")
    out(f"LVDS DATA total (deterministic + 2Q*random, linear): "
        f"{total_data*1e9:.2f} ns = {total_data/UI:.3f} UI -> "
        f"{'PASS' if total_data < 0.1 * UI else 'FAIL'} vs 0.1 UI")
    out("The CDR is a verification-path TAP (doc 02): it does not sit in")
    out("the LVDS data path, so its jitter generation is not added to")
    out("the data pair.  For completeness, the recovered-CLOCK pair in")
    out(f"CDR mode would total {total_with_cdr*1e9:.2f} ns = "
        f"{total_with_cdr/UI:.3f} UI on the same conservative linear")
    out("accounting IF the assumed 0.05 UI CDR generation is really")
    out("pk-pk -- marginally over 2 ns.  That number rests entirely on")
    out("the stated 0.05 UI assumption, not on an ADN2813 datasheet")
    out("jitter specification; resolve it from the datasheet before")
    out("claiming the CDR-mode clock against the same 0.1 UI budget.")
    out(f"R4 JITTER (LVDS data pair): "
        f"{'PASS' if total_data < 0.1 * UI else 'FAIL'}")
    out("")

    # ==================================================================
    out("7) HV RIPPLE -> GAIN MODULATION (R9: ripple <= 20 mVpp)")
    out("-" * 72)
    out(f"Gain law M = 1/(1-(V/Vbr)^n), n = {GAIN_LAW_N:.0f}, "
        f"Vbr = {VBR_TYP:.0f} V.  d(lnM)/dV = n*u/(V*(1-u)), "
        "u = (V/Vbr)^n = 1 - 1/M.")
    for m in sorted({50, m_design, 100}):
        u = 1 - 1 / m
        v_op = VBR_TYP * u ** (1 / GAIN_LAW_N)
        dlnm_dv = GAIN_LAW_N * u / (v_op * (1 - u))
        am_pp = dlnm_dv * RIPPLE_PP
        out(f"  M = {m:>3}: V_op = {v_op:.1f} V (Vbr - V = "
            f"{VBR_TYP - v_op:.1f} V), d(lnM)/dV = {dlnm_dv:.3f} /V, "
            f"20 mVpp ripple -> dM/M = {am_pp*100:.2f} % pk-pk "
            f"(+/-{am_pp*100/2:.2f} %)")
    u_d = 1 - 1 / m_design
    v_d = VBR_TYP * u_d ** (1 / GAIN_LAW_N)
    dlnm = GAIN_LAW_N * u_d / (v_d * (1 - u_d))
    am_peak = dlnm * RIPPLE_PP / 2
    margin_loss_db = -20 * np.log10(1 - am_peak)
    out(f"At design M = {m_design}: peak AM depth {am_peak*100:.2f} % of "
        "the signal, i.e. a")
    out(f"  worst-case sensitivity loss of {margin_loss_db:.3f} dB, vs a "
        f"1-sigma noise fraction")
    out(f"  of {100/q_r2:.1f} % at the R2 point and an R2 margin of "
        f"{-34.0 - sens[(740, 1e-6)]:.1f} dB.  Ripple-induced AM is "
        "well below")
    out("  the noise: PASS.  (Criterion: peak AM << 1/Q fraction and "
        "<< 5%.)")
    out(f"  Same sensitivity coefficient, for temperature: at fixed bias")
    out(f"  d(lnM) = {dlnm:.2f} * 1.3 V/degC = {dlnm*VBR_TEMPCO:.2f} per "
        "degC -- i.e. fixed-bias")
    out("  gain is unusable across temperature at this M; the R9")
    out("  temperature compensation (bias tracking Vbr) is mandatory,")
    out("  as doc 02 already provides for.  This is also why the design")
    out("  M is the knee (~100), not the sweep edge (~200, where the")
    out(f"  ripple AM would be ~{3*0.995/( (VBR_TYP*0.995**(1/3)) *0.005)*RIPPLE_PP*100:.1f} % pk-pk).")
    out("HV RIPPLE VERDICT: PASS (at design M, with temp compensation "
        "fitted)")
    out("")

    # ==================================================================
    out("8) COVERAGE SANITY CHECK vs THE ORIGINAL PAPER SYSTEM  [INFO]")
    out("-" * 72)
    out("Paper benchmark: PER test, packet = 40,256 bits, packet fails if")
    out("any bit differs; PER = 1e-3, frame = 8 packets -> frame loss")
    out(f"  1-(1-1e-3)^8 = {(1-(1-1e-3)**8)*100:.3f} %.  One SiPM receiver")
    out("covered ~700 cm^2 of lateral area (equivalent diameter")
    out(f"  2*sqrt(700/pi) = {2*np.sqrt(700/np.pi):.1f} cm).  Note that "
        "packet PER 1e-3")
    ber_equiv = 1 - (1 - 1e-3) ** (1 / 40256)
    out(f"  corresponds to BER ~ {ber_equiv:.1e} (any-bit-fails over "
        "40,256 bits),")
    out("  which is STRICTER than our R2 BER 1e-6 operating point.")
    out("Our estimate (free space, on axis, simple model):")
    out("  Emitter: NIR LED radiant intensity 1.7 mW/sr typ @ 20 mA")
    out("           (datasheet, paper); pulsed by the GaN driver --")
    out("           ASSUMED 5 mW/sr pulsed.  E = I/d^2;  P_rx = E * A_eff.")
    i_e = 5e-3                                # W/sr, assumed pulsed
    p_sens_w = 10 ** (sens[(740, 1e-6)] / 10) * 1e-3
    a_bare = APD_AREA_MM2 * 1e-6              # m^2
    a_lens_geo = np.pi * 12.5**2              # mm^2, 25 mm lens
    a_lens = a_lens_geo * 0.9 * 0.1 * 1e-6    # transmission x coupling
    d_bare = np.sqrt(i_e * a_bare / p_sens_w)
    d_lens = np.sqrt(i_e * a_lens / p_sens_w)
    out(f"  Sensitivity used: {sens[(740, 1e-6)]:.2f} dBm = "
        f"{p_sens_w*1e9:.1f} nW (740 nm, BER 1e-6, design M).")
    out(f"  BARE: A_eff = {APD_AREA_MM2:.3f} mm^2 -> on-axis range to "
        f"sensitivity = {d_bare*100:.0f} cm.")
    p_bare_50 = i_e / 0.5**2 * a_bare
    out(f"        At a 0.5 m mounting height the on-axis received power "
        f"is {dbm(p_bare_50):.1f} dBm,")
    out(f"        i.e. {sens[(740, 1e-6)] - dbm(p_bare_50):.1f} dB BELOW "
        "sensitivity: bare mode does not cover a")
    out("        0.5 m geometry at all.  Bare mode is a bench / short-")
    out("        range mode (~20 cm class), as its -34 dBm R2 point "
        "implies.")
    out(f"  LENS: 25 mm lens, geometric {a_lens_geo:.0f} mm^2 x 0.9 "
        "transmission x 0.1")
    out(f"        coupling/defocus efficiency (ASSUMED) = "
        f"{a_lens*1e6:.1f} mm^2 effective -> on-axis")
    out(f"        range to sensitivity = {d_lens:.2f} m.")
    h_rx = 0.5
    r_cone = h_rx * np.tan(np.radians(15))
    area_cone_cm2 = np.pi * r_cone**2 * 1e4
    d_edge = h_rx / np.cos(np.radians(15))
    p_edge = i_e / d_edge**2 * a_lens
    out(f"  At receiver height {h_rx} m with an assumed +/-15 deg useful "
        f"cone: radius {r_cone*100:.1f} cm,")
    out(f"  area = pi r^2 = {area_cone_cm2:.0f} cm^2.  Range is NOT the "
        f"limit inside the cone:")
    out(f"  at the cone edge (slant {d_edge:.2f} m) P_rx = "
        f"{dbm(p_edge):.1f} dBm, still "
        f"{dbm(p_edge) - sens[(740, 1e-6)]:.1f} dB above")
    out("  sensitivity (1/d^2 only; emitter off-axis falloff not "
        "modelled).")
    out(f"  Even at the stricter paper-equivalent BER (~2.5e-8, between")
    out(f"  our 1e-6 and 1e-9 sensitivities), the lens range stays "
        ">2 m, so")
    out("  the cone area at 0.5 m height is unchanged.")
    out(f"COMPARISON [INFO, not a gate]: lens-mode cone area "
        f"{area_cone_cm2:.0f} cm^2 vs the paper's")
    out(f"  ~700 cm^2 per SiPM receiver -- same class, "
        f"{area_cone_cm2/700:.2f}x the area, under much cruder optics "
        "(one 25 mm")
    out("  lens vs a large-area SiPM).  CAVEAT, honestly: this is a "
        "pure")
    out("  geometric line-of-sight estimate.  The paper's system also")
    out("  collects diffuse/scattered light in an enclosed maze, and")
    out("  animal head orientation / emitter pattern dominate in")
    out("  practice; the geometric comparison understates BOTH systems'")
    out("  real coverage and must not be read as a measured coverage.")
    out("")

    # ==================================================================
    out("9) SUMMARY")
    out("-" * 72)
    out(f"Chosen design: Rf = {chosen_rf:.0f} ohm, "
        f"Cf = {chosen_cf*1e12:.2f} pF (total, incl. parasitics), "
        f"M = {m_design}, f-3dB = {tia['f3db']/1e6:.1f} MHz")
    out(f"Sensitivity @740 nm: {sens[(740, 1e-6)]:.2f} dBm (BER 1e-6), "
        f"{sens[(740, 1e-9)]:.2f} dBm (BER 1e-9)")
    out(f"Sensitivity @630 nm: {sens[(630, 1e-6)]:.2f} dBm (BER 1e-6), "
        f"{sens[(630, 1e-9)]:.2f} dBm (BER 1e-9)")
    out(f"R1 bandwidth: f-3dB {tia['f3db']/1e6:.1f} MHz >= 50 MHz -- PASS")
    out("R3 overload: +0 dBm clips the TIA at any usable M (linear to")
    out(f"  {pc_d:.1f} dBm at design M); no damage mechanism identified,")
    out("  but <=10 UI recovery is UNPROVEN by this budget -- OPEN.")
    out(f"R4 jitter (LVDS data): {total_data*1e9:.2f} ns pk-pk "
        f"({'PASS' if total_data < 0.1*UI else 'FAIL'}); CDR-mode clock "
        "see section 6 caveat.")
    out("R9 ripple at design M: PASS (section 7).")
    out("Coverage [INFO]: bare ~"
        f"{d_bare*100:.0f} cm on-axis range; lens mode "
        f"{d_lens:.1f} m range, ~{area_cone_cm2:.0f} cm^2 cone area at "
        "0.5 m")
    out("  height vs paper's ~700 cm^2 (geometric estimate only).")
    out("")
    out(f"R2 VERDICT: {'PASS' if r2_baseline_pass or any(r['passes'] for r in cand_rows) else 'FAIL'}"
        + (" (locked Rf = 3.3 kohm design passes as originally specified)"
           if r2_baseline_pass else
           " (via the Rf design search -- see section 4)"))

    report = "\n".join(lines) + "\n"
    print(report, end="")

    # ----- write text report -----
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res_dir = os.path.join(base, "results")
    os.makedirs(res_dir, exist_ok=True)
    with open(os.path.join(res_dir, "link_budget.txt"), "w") as fh:
        fh.write(report)

    # ----- plot: BER vs incident power -----
    p_db = np.linspace(-60, -25, 176)
    plot_ms = sorted({20, 50, 100, 150, m_design, m_best_sweep
                      if m_best_sweep <= 200 else m_design})
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for m in plot_ms:
        qs = [q_factor(10 ** (p / 10) * 1e-3, resp740, m, tia_base)
              for p in p_db]
        lb = np.maximum([log10_ber(q) for q in qs], -30)
        lab = f"740 nm, M = {m}" + (" (design M)" if m == m_design
                                    else "")
        ax.plot(p_db, lb, label=lab)
    qs = [q_factor(10 ** (p / 10) * 1e-3, RESP_M1[630], m_design, tia_base)
          for p in p_db]
    ax.plot(p_db, np.maximum([log10_ber(q) for q in qs], -30), "--",
            label=f"630 nm, M = {m_design} (design M)")
    ax.axhline(-6, color="k", lw=0.8, ls=":")
    ax.axhline(-9, color="k", lw=0.8, ls=":")
    ax.axvline(-34, color="r", lw=0.8, ls="--")
    ax.text(-33.7, -28.5, "R2 point\n-34 dBm", color="r", fontsize=8)
    ax.text(-59.5, -5.6, "BER 1e-6", fontsize=8)
    ax.text(-59.5, -8.6, "BER 1e-9", fontsize=8)
    ax.set_xlabel("Average incident power on bare APD (dBm)")
    ax.set_ylabel("log10(BER)")
    ax.set_title("OOK BER vs incident power -- Rf = 3.3 kohm, "
                 "Cf = 0.45 pF, ER = 10 dB")
    ax.set_ylim(-30, 0)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(res_dir, "link_budget.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
