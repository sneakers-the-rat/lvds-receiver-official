"""Connected-group census for given nets (or all nets with unconnected pads).
Usage: groups.py BOARD [NET ...]
Uses pcbnew connectivity: two pads are in one group if connected via copper.
"""
import sys
sys.path.insert(0, 'hw')
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.ToMM
conn = board.GetConnectivity()

pads_by_net = {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        net = pad.GetNetname()
        if not net:
            continue
        p = pad.GetPosition()
        pads_by_net.setdefault(net, []).append(
            (f"{ref}.{pad.GetNumber()}", pad, MM(p.x), MM(p.y)))

want = sys.argv[2:] or None
for net, lst in sorted(pads_by_net.items()):
    if want and net not in want:
        continue
    # union-find over pads via connectivity
    parent = list(range(len(lst)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    for i, (_, pad_i, _, _) in enumerate(lst):
        items = conn.GetConnectedItems(pad_i, pcbnew.CT_ITEM_MASK)
        ids = {it.m_Uid for it in items}
        for j, (_, pad_j, _, _) in enumerate(lst):
            if i != j and pad_j.m_Uid in ids:
                union(i, j)
    groups = {}
    for i, (desc, _, x, y) in enumerate(lst):
        groups.setdefault(find(i), []).append(f"{desc}@({x:.1f},{y:.1f})")
    if len(groups) > 1 or want:
        print(f"NET {net}: {len(groups)} group(s)")
        for g in groups.values():
            print("   ", ", ".join(g))
