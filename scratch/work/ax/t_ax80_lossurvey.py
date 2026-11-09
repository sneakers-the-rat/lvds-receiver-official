import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp248.kicad_pcb')
fr = fragsets(pool, 'CDR_LOS', (40, 100, -30, 50))
print(f'CDR_LOS fragments: {len(fr)}', flush=True)
for i, f in enumerate(fr):
    ts = sorted(set((l, tuple(round(v, 3) for v in p))
                    for (l, p) in f['terms']))
    print(f'  frag{i}: {len(f["items"])} items, terms {ts[:10]}',
          flush=True)
print('LOS items near U4.22 (68.6875,36.5):', flush=True)
for l in range(3):
    for it in pool[l]:
        if it[1] == 'CDR_LOS' and abs(it[2][0] - 68.6875) < 4 \
                and abs(it[2][1] - 36.5) < 4:
            print(f'  L{l} {L.fmt_it(it)}', flush=True)
print('LOS items near U6.75 (92.6625,1.75):', flush=True)
for l in range(3):
    for it in pool[l]:
        if it[1] == 'CDR_LOS' and abs(it[2][0] - 92.6625) < 4 \
                and abs(it[2][1] - 1.75) < 4:
            print(f'  L{l} {L.fmt_it(it)}', flush=True)
