import re
from collections import Counter

def clearance_items(path):
    txt = open(path).read()
    items = []
    for b in re.split(r'\n(?=\[)', txt):
        if not b.startswith('[clearance]'):
            continue
        m = re.search(r"netclass '(\w+)' clearance ([\d.]+) mm; actual ([\d.]+) mm", b)
        lines = [l for l in b.splitlines() if l.strip().startswith('@(')]
        nets = []
        kinds = []
        for l in lines:
            nm = re.search(r"\[([^\]]+)\]", l)
            nets.append(nm.group(1) if nm else '?')
            kinds.append(l.split('):', 1)[1].strip().split(' [')[0])
        pts = tuple(re.findall(r"@\(([\d.]+) mm, ([\d.]+) mm\)", b))
        items.append((m.group(1), tuple(nets), float(m.group(3)),
                      tuple(kinds), pts))
    return items

old = clearance_items('scratch/work/finish/sh1/drc_d6d.txt')
new = clearance_items('scratch/work/finish/sh1/drc_e.txt')
print('exp275-d6d:', len(old), ' exp275-e:', len(new))

def key(it):
    return (it[0], tuple(sorted(it[1])), it[3])

co, cn = Counter(map(key, old)), Counter(map(key, new))
print()
print('--- NEW or GREW: old -> new  (class, nets, item kinds) ---')
for k in sorted(set(co) | set(cn)):
    if cn[k] > co[k]:
        print('%3d -> %3d' % (co[k], cn[k]), k)
print()
print('--- GONE or SHRANK ---')
for k in sorted(set(co) | set(cn)):
    if cn[k] < co[k]:
        print('%3d -> %3d' % (co[k], cn[k]), k)
print()
print('--- full detail of the delta items on exp275 ---')
delta_keys = {k for k in set(co) | set(cn) if cn[k] > co[k]}
for it in new:
    if key(it) in delta_keys:
        print(it[0], 'actual', it[2], it[1], it[3], it[4])
