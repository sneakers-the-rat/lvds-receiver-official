# STP quadrant + D5 — fence proofs and trial record, 2026-11-06 (post-pass-186 session, exp216)

Board state unchanged this session: exp216, unconnected 19,
violations 154. No pass banked. What follows is proven, with the
arithmetic, so the next worker does not re-derive it.

## 1. The STP gate is sealed on F (extends the inherited fence proof)

Gate geometry (measured on exp216 this session): U7 south pads
0.25x0.88 at y16.438, rects y[15.998,16.878]. DIR via (75.5,17.521)
d0.5, CK via (76.625,17.5) d0.5, C20.1 pad rect x[75.275,76.175]
y[18.025,18.975], C20.2 rect x[76.825,77.725] same y.

- Dive via between DIR/CK: centre must be >=0.7 from both via
  centres (bisector x~76.06 forces |y-17.51|>=0.42 -> y>=17.94)
  and <=18.025-0.45=17.575 (C20.1 rect). Empty. Even d0.3
  microvia: y>=17.736 vs <=17.675 — still empty.
- F track south through the gate: the thread point (76.06,17.51)
  is legal (edge margins 0.21/0.215), but continuing south is
  impossible: CK-via centreline-exclusion disc r0.55 around
  (76.625,17.5) and C20.1's SE-corner disc r0.30 around
  (76.175,18.025) overlap (centres 0.691 apart < 0.85), and
  both overlap C20.2's NW-corner disc — a continuous barrier
  from the pad row to C20. The between-pads gap (x76.5 column,
  edges clear 0.225/0.225) is therefore unreachable.
- Quartet re-fanout: DIR via is pinned in a ~0.1 lens by NXT's
  exit thread (W), C20.1 (S), STP/CK (E). CK via east is pinned
  by PHY_1V8's stub (N) and C20.2 (S). Moving CK via to
  (76.7,17.45) IS legal (0.259 vs PHY stub) and widens the dive
  lens to y>=17.88 — still > 17.575. Dead.

## 2. C20 cannot move (all branches proven)

C20 must vacate pad rect (75.725,18.5): the dive needs its north
edge at y>=18.33 (centre >=18.805) or the rect out of
x[74.8,76.7].

- South: U5 courtyard north edge y19.505 caps centre at 18.73.
  Dead by 0.075.
- West (in-row): DM_PHY F vertical x74.125 (W) and GND via
  (77.25,18.375) d0.6 (E) leave pad1-centre window
  [73.675+... ] — empty by 0.15. With the full fallback packing
  (C22 west 0.7 to its C24-courtyard touch, DM escape re-laid
  to a dive at (73.85,17.5), C20 west): pad2's rect slides into
  the dive column; west branch then dead by 0.065–0.125.
- East: t_ae4_c20scan.py scanned x[58,95] y[-12,42] at 0.25 x 4
  rotations against repair.build_items: 66 pad-clear candidates,
  ALL courtyard-blocked (min total overlap 0.161 mm^2 vs U5 at
  (82.75,18.25)). Pinch: SDA via (80.625,18.375) d0.6 + SDA In2
  vertical x80.375 (W) vs X1 courtyard x>=83.105 (E).
- North row / NW: no pad-clear site exists (via fields:
  +3V3A via, I2C_SCL via at the (76.9,7.9) site — t_ae3 trial:
  222 violations, 32 shorting; the F leg (ii) at x79.33 also
  crosses the ULPI_D0–D6 F fanout, which point-sampled design
  missed — see trial record below).
- Swaps (C21/C24/C28 sites): the pad RECT is the fence, not the
  net. Any 0603 pad at (75.725,18.5) blocks the dive. Dead.

## 3. Surviving C20 options (decision above this lane)

(a) Shrink C20 0603 -> 0402 (33 pF C0G exists in 0402). Computed
    fit: C20 at (76.2,18.75), pads y[18.45,19.05]; dive via
    (76.06,17.99): DIR 0.730 / CK 0.748 pair distances, rect
    edge 0.21; courtyard gap to U5 0.105; XI staircase via
    (75.625,18.625) must be ripped (already required by any XI
    re-plan). Margins 0.01–0.05 — thin but positive. This is a
    footprint/BOM change: circuit.py + CONNECTIONS + docs/08
    must move with it.
(b) Far relocation (x<58 or y>42, outside the scan domain):
    XI becomes a 20 mm+ journey for a 24 MHz crystal load cap —
    a design regression in spirit.
(c) Leave the quadrant blocked; STP/XI/USB_RST stay unconnected.

## 4. USB_RST (analysis only, no landing)

South of U7.9 the F corridor is closed by DM_PHY's escape.
The hand dive sliver at (74.345,17.235) clears a straight-line
DM model by 0.004–0.013, but that DM line is itself illegal
(0.013 from C22.2's pad corner); every legal DM re-lay bulges
east into the dive field. Any USB_RST attempt must be a joint
(DM re-lay, RST dive) computational search over the exact item
model — not hand placement. Its U6.40 mouth at (74.75,4.662)
is in the sealed mouth braid (cf. §6).

## 5. ULPI_D5 escape is F-sealed; needs a joint re-fanout

U7 east face: D5 pad (78.438,14.75). D4's F polyline + via
(79.625,14.875) d0.6 walls the NE; D6's F polyline
(78.438,15.25)->via (80.625,14.875) walls the SE; the corridor
between D4's via disc and D6's y15.625 horizontal has 0.35 of
copper gap (needs 0.6). D5 via slots: between D4 via and D6's
In2 staircase the lens closes (best joint (D4v,D5v) margins
computed at 0.002–0.06 — not layable). A D4+D5 (possibly +D6)
joint re-fanout designed by computational search over the item
model is the remaining route. groute pad-to-pad: NO PATH
(t_ae7). D6's In2 staircase (80.625,14.875)->NE to (93.375,2.875)
is the journey template; D5's target U6.73 is (92.662,2.75).

## 6. Long-haul singles: groute refuses at the endpoints

t_ab2_groute on exp216, this session: SPI_SCK U8.7<->U6.111
NO PATH (61 s, box 66..94/-19..9); CAP_CLK U6.34<->U5.5 NO PATH
(40 s); CDR_LOS U4.22<->U6.75 NO PATH (94 s). SPI_MOSI and
CAP_DATA were not individually searched (groute aborts on the
first failure of each pair run). All five are endpoint-sealed
(U6 south face for SPI, U6 north mouth braid for CAP, U6.75
approach for LOS), not mid-field blocked.

## 7. Trial record (scripts in scratch/work/, boards alongside)

- t_ae1 (C20 -> (80.975,18.4)): +6 violations. Site designed
  against a head-truncated survey; C20.1 sat on I2C_SDA's via
  (80.625,18.375). Lesson restated: full dumps or the item
  model, never excerpts.
- t_ae2 (C20 -> (83.075,18.4)): shorts cured; courtyards_overlap
  1 (X1), dangling 1, silk +2. Not bankable (courtyard rule).
- t_ae3 (C20 -> (76.9,7.9) + hand XI legs): 222 violations,
  32 shorting — site sits on +3V3A/SCL vias; leg (ii) crosses
  the ULPI_D fanout. Point-sampled design fails the same way.
- t_ae4: the scan (§2). t_ae5: courtyard-machinery control
  (passes at C20's current site, as DRC requires).
