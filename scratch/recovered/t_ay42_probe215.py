import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])   # gives pool, make_astar, helpers
import t_ai_lib as L
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp251.kicad_pcb')
fresh = L.load_items(b)
pool.clear()
pool.update(fresh)
print('pool rebound to exp251 as-built', flush=True)

def padpos(ref, num):
    for fp in b.GetFootprints():
        if fp.GetReference() == ref:
            for p in fp.Pads():
                if p.GetNumber() == str(num):
                    return tuple(round(v, 3)
                                 for v in pcbnew.ToMM(p.GetPosition()))
    return None

for ref, num in (('U7', 28), ('U7', 9), ('U7', 15), ('U6', 40),
                 ('X1', 1), ('X1', 2), ('C20', 1), ('C22', 1)):
    print(f'pad {ref}.{num}:', padpos(ref, num), flush=True)

astar = make_astar((58.0, -30.0, 96.0, 34.0), 0.25)

def probe(net, starts, goals, hw=0.1):
    for (sl, sx, sy) in starts:
        for (gl, gx, gy) in goals:
            r = astar(net, ((sl,), sx, sy), (gl, gx, gy), hw)
            print(f'  {net} ({sx},{sy})L{sl} -> ({gx},{gy})L{gl}:',
                  'FOUND len %.2f' % r[1] if r else 'NONE', flush=True)

xi28 = padpos('U7', 28)
print('PHY_1V8 C22-feed probes:')
probe('PHY_1V8',
      [(0, 72.02, 18.0), (0, 71.375, 17.625)],
      [(0, 77.25, 16.4375), (2, 77.9, 10.08), (0, 77.9, 10.08),
       (1, 77.9, 10.08), (2, 77.8, 16.2), (2, 76.95, 13.0)])
print('XI probes (goal U7.28 at', xi28, '):')
probe('XI', [(0, 75.72, 18.75), (0, 75.625, 18.625)],
      [(0, xi28[0], xi28[1])])
print('USB_RST probes (start U7.9, goals = south prep via area):')
probe('USB_RST', [(0, 74.25, 16.4375)],
      [(0, 88.6, -17.9), (2, 88.6, -17.9), (1, 88.6, -17.9),
       (2, 77.5, 6.0), (1, 77.5, 6.0)])
