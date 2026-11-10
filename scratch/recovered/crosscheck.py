import json, os, re, subprocess, sys
C = os.path.expanduser("~/workspace/pdlvds-cifix")
old = json.loads(subprocess.run(["git", "-C", C, "show", "HEAD:history/index.json"],
                                capture_output=True, text=True).stdout)
new = json.load(open(os.path.join(C, "history/index.json")))
assert len(old) == len(new) == 6, (len(old), len(new))
PAL = {"F.Cu": "#FF3B30", "In1.Cu": "#FF9500", "In2.Cu": "#34C759", "B.Cu": "#0A84FF"}
THEME = {"#C83434", "#CE7D2C", "#7FC87F", "#4D7FC4"}
errors = []
for o, n in zip(old, new):
    for k in ("timestamp", "hash", "short_hash", "label", "dir", "renders", "stats", "note"):
        if o.get(k) != n.get(k):
            errors.append(f"{n['short_hash']}: field {k} changed: {o.get(k)!r} -> {n.get(k)!r}")
    d = os.path.join(C, "history", n["dir"])
    if not os.path.isdir(d):
        errors.append(f"{n['short_hash']}: dir missing"); continue
    layers = n.get("layers")
    if n["renders"]:
        if not layers or set(layers) != set(PAL):
            errors.append(f"{n['short_hash']}: layers map wrong: {layers}"); continue
        vbs = set()
        for layer, fn in layers.items():
            p = os.path.join(d, fn)
            if not os.path.exists(p):
                errors.append(f"{n['short_hash']}: {fn} missing"); continue
            size = os.path.getsize(p)
            if size < 10000:
                errors.append(f"{n['short_hash']}: {fn} trivial ({size} B)")
            txt = open(p).read()
            cols = {c.upper() for c in re.findall(r"#[0-9A-Fa-f]{6}", txt)}
            if PAL[layer] not in cols:
                errors.append(f"{n['short_hash']}: {fn} lacks palette {PAL[layer]}")
            bad = cols & THEME
            if bad:
                errors.append(f"{n['short_hash']}: {fn} still has theme colours {bad}")
            vbs.add(re.search(r'viewBox="([^"]*)"', txt).group(1))
        if len(vbs) != 1:
            errors.append(f"{n['short_hash']}: viewBoxes differ across layers: {vbs}")
        print(f"{n['short_hash']}: 4 layer files OK, viewBox {vbs.pop()}, "
              f"sizes " + ",".join(str(os.path.getsize(os.path.join(d, layers[l]))) for l in PAL))
    else:
        if layers:
            errors.append(f"{n['short_hash']}: board-less entry gained layers")
        print(f"{n['short_hash']}: board-less, no layers (correct)")
disk = sorted(d for d in os.listdir(os.path.join(C, "history"))
              if os.path.isdir(os.path.join(C, "history", d)))
idx = sorted(e["dir"] for e in new)
assert disk == idx, (disk, idx)
print("index dirs == disk dirs:", len(disk))
if errors:
    print("ERRORS:"); [print(" -", e) for e in errors]; sys.exit(1)
print("CROSS-CHECK PASS: stats/labels/notes/timestamps identical to pre-regen index for all 6 entries")
