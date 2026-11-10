"""t_bb26: rip ALL ULPI_DIR copper (14 tracks + 7 vias, per the
t_bb25 census) from exp256 -> exp257work, for sequential groute
(XI first through the freed corridor, DIR re-routed second)."""
import wx
_app = wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp256.kicad_pcb'
DST = 'hw/pdlvds_rx.exp257work.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
MM = pcbnew.FromMM

def mm(v):
    return v / 1e6

nc = b.GetNetcodeFromNetname('ULPI_DIR')
trks = [t for t in list(b.GetTracks())
        if t.GetNetCode() == nc and t.Type() == pcbnew.PCB_TRACE_T]
vias = [t for t in list(b.GetTracks())
        if t.GetNetCode() == nc and t.Type() == pcbnew.PCB_VIA_T]
print(f'DIR tracks {len(trks)} (expect 14), vias {len(vias)} (expect 7)')
assert len(trks) == 14 and len(vias) == 7, 'count mismatch — STOP'
for t in trks + vias:
    b.Remove(t)
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(DST)
print('saved', DST)
b2 = pcbnew.LoadBoard(DST)
left = [t for t in b2.GetTracks() if t.GetNetCode() == nc]
print('DIR items remaining after reload:', len(left))
