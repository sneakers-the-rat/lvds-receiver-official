import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
def nets_of(fp):
    s = set()
    for p in fp.Pads():
        n = p.GetNetname()
        if n: s.add(n)
    return s
def pos(fp):
    p = fp.GetPosition(); return (p.x/1e6, p.y/1e6)
for chip in ['U6','U7']:
    cn = nets_of(fps[chip]); cx, cy = pos(fps[chip])
    print(f"== companions of {chip} at ({cx},{cy}), {len(cn)} nets")
    for ref, fp in sorted(fps.items()):
        if ref == chip: continue
        fn = nets_of(fp) - {'GND',''}
        if not fn: continue
        x, y = pos(fp)
        d = ((x-cx)**2 + (y-cy)**2) ** 0.5
        if fn <= cn:
            print(f"  EXCLUSIVE {ref} at ({x:.1f},{y:.1f}) d={d:.1f} nets={sorted(fn)}")
    print(f"== U6/U7 pad nets for target nets:")
    break
# target net endpoints
for net in ['ULPI_D1','ULPI_D2','ULPI_D3','ULPI_D4','ULPI_D5','ULPI_D6','ULPI_NXT','ULPI_STP','ULPI_CLK','USB_RST','DP_PHY','DM_PHY','CAP_DATA','CDR_SQUELCH']:
    eps = []
    for ref, fp in fps.items():
        for p in fp.Pads():
            if p.GetNetname() == net:
                pp = p.GetPosition(); eps.append(f"{ref}.{p.GetNumber()}@({pp.x/1e6:.1f},{pp.y/1e6:.1f})")
    print(net, ' '.join(eps))
