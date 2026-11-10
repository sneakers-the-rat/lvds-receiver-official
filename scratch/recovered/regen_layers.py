import json, os, subprocess, sys
CIFIX = os.path.expanduser("~/workspace/pdlvds-cifix")
MAIN = os.path.expanduser("~/workspace/photodiode-lvds-rx")
entries = json.load(open(os.path.join(CIFIX, "history/index.json")))
BOARD_HASHES = {"d0c0bca", "3ac1a43", "41d7196", "fb2acf7"}
FLAGMAP = [("nets_routed", "--nets-routed"), ("nets_total", "--nets-total"),
           ("pins_failed", "--pins-failed"),
           ("clearance_violations", "--clearance-violations"),
           ("unconnected_nets", "--unconnected-nets"),
           ("audit_verdict", "--audit-verdict")]
for e in entries:
    if e["short_hash"] not in BOARD_HASHES:
        continue
    board = f"/tmp/regen-{e['short_hash']}.kicad_pcb"
    with open(board, "wb") as f:
        subprocess.run(["git", "-C", MAIN, "show",
                        f"{e['hash']}:hw/pdlvds_rx.kicad_pcb"],
                       stdout=f, check=True)
    cmd = [sys.executable, "scripts/snapshot_route.py",
           "--board", board, "--label", e["label"],
           "--hash", e["hash"], "--timestamp", e["timestamp"],
           "--no-parse"]
    for key, flag in FLAGMAP:
        if e["stats"].get(key) is not None:
            cmd += [flag, str(e["stats"][key])]
    if e.get("note"):
        cmd += ["--note", e["note"]]
    r = subprocess.run(cmd, cwd=CIFIX, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("FAILED", e["short_hash"], r.stderr); sys.exit(1)
print("done")
