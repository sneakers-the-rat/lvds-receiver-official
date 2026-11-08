"""t_ai6: referee a candidate board against the exp219 baseline.
Usage: t_ai6_referee.py CANDIDATE TAG [net ...]
Runs kicad-cli DRC + check_pcb, diffs class tables, violation
description multisets, unconnected items, the check_pcb census line
set, courtyard/blind, and per-net track censuses vs exp219."""
import collections, json, subprocess, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

CAND, TAG = sys.argv[1], sys.argv[2]
NETS = sys.argv[3:]
BASE = 'hw/pdlvds_rx.exp220.kicad_pcb'
BD = 'scratch/work/ai/drc-exp220-baseline.json'
BC = 'scratch/work/ai/census-exp219.txt'
od = f'scratch/work/ai/drc-{TAG}.json'
oc = f'scratch/work/ai/check-{TAG}.txt'
subprocess.run(['kicad-cli', 'pcb', 'drc', '--output', od,
                '--format', 'json', CAND], capture_output=True)
subprocess.run(['xvfb-run', '-a', 'python3', 'hw/check_pcb.py', CAND],
               stdout=open(oc, 'w'), stderr=subprocess.DEVNULL)


def load(p):
    return json.load(open(p))


def vtab(d):
    return collections.Counter(x['type'] for x in d['violations'])


def vdesc(d):
    return collections.Counter(
        (x['type'], x.get('description', '')) for x in d['violations'])


bd_, cd_ = load(BD), load(od)
print(f'== KiCad DRC: baseline {sum(vtab(bd_).values())} -> '
      f'cand {sum(vtab(cd_).values())}')
for k in sorted(set(vtab(bd_)) | set(vtab(cd_))):
    mark = '' if vtab(bd_)[k] == vtab(cd_)[k] else '   <<<< DIFF'
    print(f'   {k}: {vtab(bd_)[k]} -> {vtab(cd_)[k]}{mark}')
new = vdesc(cd_) - vdesc(bd_)
gone = vdesc(bd_) - vdesc(cd_)
print(f'   violation descriptions: +{sum(new.values())} new, '
      f'-{sum(gone.values())} removed')
for (t, s), n in list(new.items())[:12]:
    print(f'     NEW {t}: {s} x{n}')
for (t, s), n in list(gone.items())[:6]:
    print(f'     GONE {t}: {s} x{n}')


def unc_items(d):
    out = []
    for x in d.get('unconnected_items', []):
        descs = []
        for it in x.get('items', []):
            p = it.get('pos', {})
            descs.append((it.get('description', ''),
                          round(p.get('x', 0), 2),
                          round(p.get('y', 0), 2)))
        out.append(tuple(sorted(descs)))
    return collections.Counter(out)


bu, cu = unc_items(bd_), unc_items(cd_)
print(f'== unconnected items: {sum(bu.values())} -> {sum(cu.values())}')
for k, n in (cu - bu).items():
    print(f'   NEW UNC {k} x{n}')
for k, n in (bu - cu).items():
    print(f'   GONE UNC {k} x{n}')

bl = {ln.strip() for ln in open(BC) if ln.strip()}
cl = set()
check_txt = open(oc).read()
for ln in check_txt.splitlines():
    if ln.startswith('  CLEARANCE'):
        cl.add(ln.strip())
print(f'== check_pcb census: {len(bl)} -> {len(cl)} '
      f'(+{len(cl - bl)} / -{len(bl - cl)})')
for ln in sorted(cl - bl)[:8]:
    print('   NEW PAIR', ln)
for ln in sorted(bl - cl)[:8]:
    print('   GONE PAIR', ln)
for probe in ('unconnected nets:', 'courtyard collisions:',
              'courtyard fallback pairs'):
    for ln in check_txt.splitlines():
        if probe in ln:
            print('   check:', ln.strip())
            break
for ln in check_txt.splitlines():
    if ln.startswith('  UNCONNECTED'):
        print('   ', ln.strip())


def census(path):
    b = pcbnew.LoadBoard(path)
    c = collections.Counter()
    for t in b.GetTracks():
        c[t.GetNetname()] += 1
    return c, sum(c.values())


bc2, bt = census(BASE)
cc2, ct = census(CAND)
print(f'== track census: total {bt} -> {ct}')
for n in NETS:
    print(f'   {n}: {bc2[n]} -> {cc2[n]} (delta {cc2[n] - bc2[n]:+d})')
others = {n: cc2[n] - bc2[n] for n in set(bc2) | set(cc2)
          if n not in NETS and cc2[n] != bc2[n]}
if others:
    print('   UNEXPECTED net deltas:', others)
else:
    print('   no other net deltas')
