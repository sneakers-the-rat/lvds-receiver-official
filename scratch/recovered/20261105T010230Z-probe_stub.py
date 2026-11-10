import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp6.kicad_pcb')
MM = pcbnew.ToMM

def pad_of(ref, num):
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            for p in fp.Pads():
                if p.GetNumber() == num:
                    return p
    return None

for ref, num in [('U6', '36'), ('U6', '37'), ('U4', '16'), ('U3', '3')]:
    p = pad_of(ref, num)
    pos = p.GetPosition()
    bb = p.GetBoundingBox()
    print(f"{ref}.{num}: pos=({MM(pos.x):.3f},{MM(pos.y):.3f}) "
          f"bbox=({MM(bb.GetLeft()):.3f},{MM(bb.GetTop()):.3f})-"
          f"({MM(bb.GetRight()):.3f},{MM(bb.GetBottom()):.3f}) "
          f"size=({MM(p.GetSize().x):.3f}x{MM(p.GetSize().y):.3f}) "
          f"layer={p.GetLayer()} orient={p.GetOrientationDegrees()}")
    # tracks of the same net starting near the pad
    net = p.GetNetname()
    for t in board.GetTracks():
        if t.GetNetname() != net or isinstance(t, pcbnew.PCB_VIA):
            continue
        s = t.GetStart()
        if abs(MM(s.x) - MM(pos.x)) < 3 and abs(MM(s.y) - MM(pos.y)) < 3:
            sh = t.GetEffectiveShape()
            ps = p.GetEffectiveShape()
            print(f"   track start=({MM(s.x):.3f},{MM(s.y):.3f}) "
                  f"collide0={ps.Collide(sh, 0)} width={MM(t.GetWidth()):.3f}")
