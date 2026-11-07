# check_pcb clearance-census drift — reconciliation (2026-11-07, pass 188 session)

**Verdict: the divergence is a rule-set difference, not copper
defects. No pair in the census is a KiCad DRC violation.**

## The fact pattern
- KiCad DRC clearance has held **0** on every pass while
  check_pcb's clearance census grew 71 → 109.
- The current census (109 pairs) decomposes as **97 pairs at
  "need 1.0 mm" (HV surface-creepage class) + 12 pairs at
  "need 0.25 mm" (power class). Zero pairs at 0.2 or 0.3.**
- check_pcb imposes per-class clearances derived from its own
  voltage census (HV 1.0 mm surface / 0.3 buried-only, power
  0.25, default 0.2). The board/project file defines exactly
  ONE netclass — Default, 0.2 mm, no assignments — so KiCad
  DRC enforces flat 0.2 everywhere, including across the
  259 V bias domain (the standing netclasses-owed debt).
- Therefore any copper laid DRC-legally (gap ≥ 0.20) that
  passes an HV-class net at < 1.0 mm or a power-class net at
  < 0.25 mm registers pairs in check_pcb's census and nowhere
  in DRC. A track passing a staircase registers one pair per
  nearby segment, so one physical adjacency can add many
  pairs.

## Attribution of every increment (from history/pass-NNNN
## audits, diffed pairwise; each jump coincides with a pass
## that CONNECTED a net near HV/power copper)
- 166→167 (+22, census 71→93): HV_VC + HV_VC2 connected.
  All 22 are HV-class (need 1.0): HV_VC2's new track/via vs
  the HV_R29M staircase, HV_RAW (R29.1) vs HV_VC tracks.
- 168→169 (+2, 93→95): SET_P + ILIM_A connected; +5V power
  class (need 0.25).
- 169→170 (+1, 95→96): DAC_VREF connected; +3V3A vs
  DAC_VREF via (need 0.25).
- 170→171 (+5, 96→101): APD_A + APD_K connected; HV class
  (need 1.0) around D1.
- 173→174 (+3, 101→104): REFCLKN + +3V3D_CDR (C14/C15 nudge,
  CF re-land); power class (need 0.25).
- 175→176 (+1, 104→105): I2C_SDA work; +3V3A (U9.5) vs
  I2C_SDA via (need 0.25).
- 176→177 (+3, 105→108): C48 move + ULPI_D1/D2 re-fanout;
  GND/NRST (C19 pads) vs the new +3V3D feed track/via at
  (81.0,12.6)/(81.625,10.9) (need 0.25).
- 184→185 (+1, 108→109): ULPI_NXT connected. The measured
  pair: pass 185's new GND mouth-tie segment
  (71.000,0.270)->(69.600,0.250) passes U6.32 (+3V3A) with
  an exact copper gap of **0.230 mm** (t_ag9_drift.py) —
  ≥ KiCad's 0.20 (DRC silent, correctly), < the 0.25 power
  class. On exp214 the segment does not exist; the pair is
  born with it.

## Consequence
The census is a *class-band adjacency count*, not a defect
count. It will keep growing by a few pairs whenever a
connection lands near HV/power copper at DRC-legal spacing,
and it cannot be driven to zero by routing alone at the
board's current density — it goes to zero only when the
classes are written into the board/project file as
netclasses + custom rules (the owed board-file work, pending
the user's decision), at which point KiCad DRC itself
becomes the referee for them and check_pcb's census should
be retired or re-based. Until then, KiCad DRC remains the
authoritative checker (user ruling), and census deltas are
reported per pass with their causing connection named.
