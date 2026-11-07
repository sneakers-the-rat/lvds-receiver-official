import sys, collections
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

def counts(path):
    b = pcbnew.LoadBoard(path)
    c = collections.Counter()
    for t in b.GetTracks():
        c[t.GetNetname()] += 1
    return c

base = counts('hw/pdlvds_rx.exp216.kicad_pcb')
cand = counts('scratch/work/exp217cand2.kicad_pcb')
allnets = sorted(set(base) | set(cand))
diffs = []
for n in allnets:
    if base[n] != cand[n]:
        diffs.append((n, base[n], cand[n], cand[n] - base[n]))
for d in diffs:
    print('DIFF', d)
print('nets changed:', len(diffs))
# expected: D4: -11 ripped segs... board objects: D4 rip 4F+3In2 segs+1 via=8,
# add 3 stub segs+1 via+1 In2 seg=+5 -> net -3. D6 rip 7F+3In2+1=11,
# add 7 stub+1 via+1 In2=+9 -> net -2. D5: add 4 stub+1 via=+5.
