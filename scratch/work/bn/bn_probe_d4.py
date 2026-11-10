import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bn')
exec(open('scratch/work/bn/bn_fix3_search3.py').read().split("o4 = [")[0])

def solo_named(trks, vias):
    out = []
    for (net, layer, a, b, hw) in trks:
        for (m, d) in BG.margin_trk(a, b, layer, net, local, hw=hw):
            if m < 0.05: out.append((m, f'pool: trk {a}->{b} vs {d}'))
        for (n2, l2, a2, b2, h2) in FIXED:
            if net != n2 and layer == l2:
                m = BG.seg_seg(a, b, a2, b2) - hw - h2 - 0.20
                if m < 0.05: out.append((m, f'fixed-trk: {a}->{b} vs {n2} {a2}->{b2}'))
        for (n2, at) in FIXED_VIA:
            if net != n2:
                m = BG.pt_seg(at, a, b) - hw - 0.25 - 0.20
                if m < 0.05: out.append((m, f'fixed-via: {a}->{b} vs {n2} {at}'))
    for (net, at) in vias:
        for (m, d) in BG.margin_via(at, net, local, r=0.25):
            if m < 0.05: out.append((m, f'pool: via {at} vs {d}'))
        for (n2, l2, a2, b2, h2) in FIXED:
            if net != n2:
                m = BG.pt_seg(at, a2, b2) - h2 - 0.25 - 0.20
                if m < 0.05: out.append((m, f'fixed-trk: via {at} vs {n2} {a2}->{b2}'))
        for (n2, at2) in FIXED_VIA:
            if net != n2:
                m = ((at[0] - at2[0]) ** 2 + (at[1] - at2[1]) ** 2) ** 0.5 - 0.70
                if m < 0.05: out.append((m, f'fixed-via-via: {at} vs {n2} {at2}'))
    return sorted(out)

for v4 in [(80.5, 14.25), (80.45, 14.15), (80.4, 14.2), (80.6, 14.1), (80.35, 14.3)]:
    t, v = d4(v4)
    print(f'== V4={v4}')
    for m, d in solo_named(t, v)[:5]:
        print(f'   {m:+.3f}  {d}')
