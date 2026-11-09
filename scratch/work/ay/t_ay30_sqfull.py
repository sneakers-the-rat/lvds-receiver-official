import sys
sys.path.insert(0, 'scratch/work/ax')
H = {'__name__': 'ax252head'}
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0], H)
pool = H['pool']
# NOTE: this pool is the faithful exp250 load BEFORE head edits? No: the
# head already edited. SQUELCH untouched by head edits, so items are real.
for lay in (0, 1, 2):
    rows = [it for it in pool[lay] if it[1] == 'CDR_SQUELCH']
    print(f'layer {lay}: {len(rows)} SQUELCH items', flush=True)
    for it in sorted(rows, key=lambda t: str(t[2])):
        print('  ', it[0], it[2], flush=True)
