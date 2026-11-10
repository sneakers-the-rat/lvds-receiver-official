import glob, re, collections, sys
def lum(hexs):
    r,g,b = (int(hexs[i:i+2],16)/255 for i in (1,3,5))
    f = lambda c: c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b)
DESIGNATED = {"#111111"}  # panel tone: CSS panel bg + drill holes by design
bad_total = 0
for path in sorted(glob.glob("history/2026-*/*.svg")):
    counts = collections.Counter(t.upper() for t in re.findall(r"#[0-9A-Fa-f]{6}\b", open(path).read()))
    nearblack = {c:n for c,n in counts.items() if lum(c) < 0.08 and c not in DESIGNATED}
    bad_total += sum(nearblack.values())
    print(f"{path.split('history/')[1]:58s} colours={len(counts)} "
          f"#000000={counts.get('#000000',0)} #FFFFFF={counts.get('#FFFFFF',0)} "
          f"#111111={counts.get('#111111',0)} #9E9E9E={counts.get('#9E9E9E',0)} "
          f"#ECECEC={counts.get('#ECECEC',0)} #F2EDA1={counts.get('#F2EDA1',0)} "
          f"near-black-unexplained={nearblack}")
print("TOTAL unexplained near-black tokens:", bad_total)
sys.exit(1 if bad_total else 0)
