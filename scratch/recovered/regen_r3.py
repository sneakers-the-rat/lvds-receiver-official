import json, subprocess, sys, os
ROOT = "/home/hatch/workspace/pdlvds-cifix"
MAIN = "/home/hatch/workspace/photodiode-lvds-rx"
entries = json.load(open("/tmp/index-before-r3.json"))
stat_flags = [("nets_routed","--nets-routed"),("nets_total","--nets-total"),
              ("pins_failed","--pins-failed"),
              ("clearance_violations","--clearance-violations"),
              ("unconnected_nets","--unconnected-nets"),
              ("audit_verdict","--audit-verdict")]
for e in entries:
    if not e.get("renders"):
        print(f"skip {e['short_hash']} (no board)"); continue
    board = f"/tmp/regen-{e['short_hash']}.kicad_pcb"
    with open(board, "wb") as f:
        r = subprocess.run(["git","-C",MAIN,"show",f"{e['hash']}:hw/pdlvds_rx.kicad_pcb"],
                           stdout=f)
    assert r.returncode == 0, e['hash']
    cmd = ["python3", os.path.join(ROOT,"scripts/snapshot_route.py"),
           "--board", board, "--label", e["label"], "--hash", e["hash"],
           "--timestamp", e["timestamp"], "--note", e.get("note",""),
           "--no-parse"]
    for key, flag in stat_flags:
        v = (e.get("stats") or {}).get(key)
        if v is not None:
            cmd += [flag, str(v)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("FAILED", e['short_hash'], r.stderr); sys.exit(1)
print("regen complete")
