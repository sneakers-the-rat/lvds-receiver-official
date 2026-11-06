#!/usr/bin/env python3
"""Group builder for the pass-65 expansion (survey only, no moves).

Membership for each seed (U7, U4, U9, U10):
  tier A: BFS over SIGNAL nets from the seed's pads (GND and the rail
          nets in RAIL_NETS excluded), restricted to footprints whose
          centre lies within RADIUS[seed] of the seed centre;
  tier B: any footprint within DECOUPLE_R (10 mm) of the seed centre
          that shares a non-GND net with the seed (decoupling and
          other tight local parts the signal BFS misses).
Frozen parts are never claimed. A part claimed by two seeds goes to
the nearer seed. Prints groups with claim evidence and pad-extent
bounding boxes.

Usage: xvfb-run -a python3 hw/groups_expand.py <board> <out.txt>
"""
import sys
import pcbnew

RAIL_NETS = {"GND", "+5V", "+3V3D", "+3V3D_CDR", "+3V3A", "+VA", "-VA",
             "NEG_RAW", "VBUS_RAW", "PHY_1V8", "PHY_1V8A",
             "HV_RAW", "HV_SEC", "APD_K"}
FROZEN = {"J1", "J2", "J3", "J4", "RJ1", "RJ2", "D1", "U1", "R1", "SH1",
          "MH1", "MH2", "MH3", "MH4", "MH5", "MH6", "U6"}
SEEDS = {"U7": 17.0, "U4": 17.0, "U9": 13.0, "U10": 28.0}
DECOUPLE_R = 10.0


def mm(v):
    return pcbnew.ToMM(v)


def main():
    board_path, out_path = sys.argv[1], sys.argv[2]
    b = pcbnew.LoadBoard(board_path)
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}

    def centre(ref):
        p = fps[ref].GetPosition()
        return mm(p.x), mm(p.y)

    def nets_of(ref):
        return {pad.GetNetname() for pad in fps[ref].Pads()
                if pad.GetNetname()}

    def dist(a, b_):
        return ((a[0] - b_[0]) ** 2 + (a[1] - b_[1]) ** 2) ** 0.5

    # net -> refs (for BFS over footprints sharing a net)
    net_refs = {}
    for ref in fps:
        for n in nets_of(ref):
            net_refs.setdefault(n, set()).add(ref)

    claims = {}   # ref -> (seed, tier, via_net, dist_to_seed)
    for seed, radius in SEEDS.items():
        sc = centre(seed)
        # tier A: BFS over signal nets
        web = set(nets_of(seed)) - RAIL_NETS
        frontier = {seed}
        seen = {seed}
        changed = True
        while changed:
            changed = False
            for n in list(web):
                for ref in net_refs.get(n, ()):
                    if ref in seen or ref in FROZEN:
                        continue
                    if dist(centre(ref), sc) > radius:
                        continue
                    seen.add(ref)
                    frontier.add(ref)
                    new = nets_of(ref) - RAIL_NETS - web
                    if new:
                        web |= new
                        changed = True
        for ref in seen:
            if ref == seed:
                continue
            via = sorted((nets_of(ref) & web) - RAIL_NETS)
            d = dist(centre(ref), sc)
            if ref not in claims or d < claims[ref][3]:
                claims[ref] = (seed, "A", ",".join(via[:3]), d)
        # tier B: decoupling-radius parts sharing any non-GND net
        seed_nets = nets_of(seed) - {"GND"}
        for ref in fps:
            if ref == seed or ref in FROZEN:
                continue
            d = dist(centre(ref), sc)
            if d > DECOUPLE_R:
                continue
            shared = nets_of(ref) & seed_nets
            if not shared:
                continue
            if ref not in claims or d < claims[ref][3]:
                claims[ref] = (seed, "B", ",".join(sorted(shared)[:3]), d)

    lines = []
    for seed in SEEDS:
        members = sorted((r for r, c in claims.items() if c[0] == seed),
                         key=lambda r: claims[r][3])
        allrefs = [seed] + members
        xs, ys = [], []
        for r in allrefs:
            for pad in fps[r].Pads():
                xs.append(mm(pad.GetPosition().x))
                ys.append(mm(pad.GetPosition().y))
        lines.append("GROUP %s: %d parts, pad-extent x %.2f..%.2f "
                     "y %.2f..%.2f" % (seed, len(allrefs),
                                       min(xs), max(xs), min(ys), max(ys)))
        lines.append("  %s (seed)" % seed)
        for r in members:
            s, t, via, d = claims[r]
            x, y = centre(r)
            lines.append("  %-6s @(%6.2f,%6.2f) tier %s via %-28s d=%.1f"
                         % (r, x, y, t, via, d))
    unclaimed_near = []
    for seed in SEEDS:
        sc = centre(seed)
        for ref in fps:
            if ref in claims or ref in FROZEN or ref == seed:
                continue
            d = dist(centre(ref), sc)
            if d <= SEEDS[seed]:
                unclaimed_near.append("%s near %s d=%.1f" % (ref, seed, d))
    lines.append("UNCLAIMED within seed radii: %s"
                 % (", ".join(sorted(set(unclaimed_near))) or "none"))
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
