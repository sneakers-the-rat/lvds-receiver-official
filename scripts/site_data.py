#!/usr/bin/env python3
"""Pre-build data step for the Jekyll project site.

    python3 scripts/site_data.py

The site skeleton is Jekyll (website/); this script is ONLY the data
and asset staging step that runs before `jekyll build` (locally and
in CI's build-site job). It ports, behaviour-for-behaviour, the data
half of the retired scripts/build_site.py:

  - website/_data/status.json  — the build-status panel data: CI job
    rows from .site-status/<job>/ (artefacts downloaded by CI;
    absent locally) plus the per-check verdicts read from results/.
    The KiCad DRC row keeps the CI-signal wording exactly: counts
    are BOARD STATE against ci/drc-baseline.json, FAIL only for a
    tool-health breakage, REGRESSION above baseline + the recorded
    jitter tolerance, PASS only at a 0/0 baseline with 0/0 counts.
    This script only DISPLAYS the gate's numbers; the gate itself
    (scripts/drc_gate.py, scripts/erc_gate.py) is untouched.
  - website/_data/tokens.json  — token-usage totals computed from
    the committed metrics/*.csv export (same arithmetic as the old
    generator: sums over token_series.csv, scope split from
    agents.csv). No export -> available: false, never a fake total.
  - website/_data/bom.json     — BOM table data from hw/fab/bom.csv.
  - website/_data/sims.json    — simulation summary blocks: the key
    lines of each results/*.txt, or the file's absence.
  - website/_data/board.json   — which board assets exist (top /
    bottom renders, the all-layers composite, per-layer SVGs,
    schematic SVG/PDF).
  - Board render SVGs staged into website/assets/gen/ (the fab
    renders and the per-pass history renders) get a dark background
    rect baked in — see inject_svg_background() — so a render
    opened on its own (new tab, direct link) stands on the same
    #111 ground the site's CSS panels paint behind it. The source
    SVGs (hw/fab/, history/) stay pristine KiCad output.
  - website/_data/downloads.json — the fabrication downloads list.
  - website/assets/, website/downloads/ — staged copies of the fab
    renders, results plots, metrics charts, per-pass history renders
    (assets/history/<dir>/), the matplotlib TIA plot and the
    kicad-cli schematic SVG (both best-effort, exactly as before:
    a failure warns and the page shows "not generated").
  - website/_includes/docs/    — docs/01, docs/02, docs/05 copied
    for Jekyll {% include %} + markdownify, heading levels shifted
    one deeper (the old converter rendered a doc's '#' as an h2
    because the page title slot holds the h1).

Everything tolerates missing inputs the way build_site.py did:
absent artefacts become explicit "not available" data, never a
failed step and never an invented value.

The generated files are gitignored (website/_data/*.json,
website/assets/, website/downloads/, website/_includes/docs/);
the committed sources of truth stay where they always were:
results/, metrics/, hw/fab/, history/, docs/.
"""
import csv, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "website")
DATA = os.path.join(WEB, "_data")
ASSETS = os.path.join(WEB, "assets", "gen")  # generated only;
# committed static assets (assets/css/) live outside this tree
DOWNLOADS = os.path.join(WEB, "downloads")
INCLUDES_DOCS = os.path.join(WEB, "_includes", "docs")


def read(path):
    p = os.path.join(ROOT, path)
    return open(p).read() if os.path.exists(p) else None


def write_json(name, obj):
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, name), "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def copy_into(src, dst_dir, name=None):
    p = os.path.join(ROOT, src)
    if not os.path.exists(p):
        return None
    name = name or os.path.basename(src)
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(p, os.path.join(dst_dir, name))
    return name


# --------------------------------------------- SVG background bake
# The dark colour the site paints behind renders (website/assets/
# css/main.css: .composite, .layergrid img and .refview all use
# #111). KiCad's SVG exports carry no background of their own, so a
# staged render opened outside the page (new tab, direct link) lost
# the panel and showed the artwork on white/transparent. Staging
# bakes the same colour into the file instead.
SVG_BG = "#111"
SVG_BG_ID = "site-bg"


def inject_svg_background(path):
    """Insert a full-canvas background rect into a staged SVG.

    The rect goes immediately after the opening <svg> tag, i.e. it
    is the first PAINTED element (<title>/<desc> siblings do not
    paint); its size is the SVG's viewBox, falling back to the
    width/height attributes. Idempotent: a file already carrying
    the marker id is left alone. Anything unparseable is left
    untouched — a render without the baked background still builds,
    exactly as before this step existed."""
    try:
        with open(path, encoding="utf-8") as f:
            txt = f.read()
    except OSError:
        return
    if f'id="{SVG_BG_ID}"' in txt:
        return
    m = re.search(r"<svg\b[^>]*>", txt)
    if not m:
        return
    tag = m.group(0)
    box = None
    vb = re.search(r'viewBox\s*=\s*"([^"]+)"', tag)
    if vb:
        parts = [p for p in re.split(r"[\s,]+", vb.group(1).strip()) if p]
        if len(parts) == 4:
            box = parts
    if box is None:
        wm = re.search(r'width\s*=\s*"([0-9]*\.?[0-9]+)', tag)
        hm = re.search(r'height\s*=\s*"([0-9]*\.?[0-9]+)', tag)
        if wm and hm:
            box = ["0", "0", wm.group(1), hm.group(1)]
    if box is None:
        return
    rect = (f'<rect id="{SVG_BG_ID}" x="{box[0]}" y="{box[1]}" '
            f'width="{box[2]}" height="{box[3]}" fill="{SVG_BG}"/>')
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt[:m.end()] + "\n" + rect + txt[m.end():])


def key_lines(path, keys):
    txt = read(path)
    if txt is None:
        return None
    return [ln for ln in txt.splitlines()
            if any(k in ln for k in keys)]


# ------------------------------------------------------- build status
def job_status():
    """Status JSONs recorded by the CI validation jobs and downloaded
    by the build-site job into .site-status/<job>/. Absent on a local
    build — the panel then says so."""
    out = []
    for sub, fn in [("kicad", "kicad-validate.json"),
                    ("sim", "sim-and-firmware.json")]:
        p = os.path.join(ROOT, ".site-status", sub, fn)
        if os.path.exists(p):
            try:
                with open(p) as f:
                    out.append(json.load(f))
            except Exception as e:
                print(f"warning: unreadable status file {p} ({e})")
    return out


def drc_row():
    """The DRC row of the status panel, worded as BOARD STATE.
    Ported verbatim (logic + wording) from build_site.py; see its
    docstring there and docs/00-status.md "CI signal fix"."""
    kj = next((j for j in job_status()
               if j.get("job") == "kicad-validate"), None)
    if kj is not None and kj.get("drc_verdict") == "TOOL FAILURE":
        return ("KiCad DRC (native)", "FAIL",
                kj.get("drc_board_state") or "DRC tool failure (see CI log)")
    if kj is not None and kj.get("drc_verdict") == "WITHIN JITTER TOLERANCE":
        return ("KiCad DRC (native)", "BOARD STATE",
                kj.get("drc_board_state")
                or "DRC counts above baseline, within checker "
                   "jitter tolerance (see CI log)")
    v = u = bv = bu = None
    tv = tu = 0
    regression = None
    if kj is not None and "drc_violations" in kj:
        v, u = kj["drc_violations"], kj["drc_unconnected"]
        bv = kj.get("drc_baseline_violations")
        bu = kj.get("drc_baseline_unconnected")
        regression = kj.get("drc_regression")
    if v is None:
        drc = read("results/drc-report.txt")
        if drc is None:
            return ("KiCad DRC (native)", "not run",
                    "no DRC report or status (needs a KiCad 8 CI run)")
        mv = re.search(r"(?:\*\*\s*)?Found (\d+) DRC violations(?:\s*\*\*)?", drc)
        mu = re.search(
            r"(?:\*\*\s*)?Found (\d+) unconnected (?:pads|items)(?:\s*\*\*)?", drc)
        if mv is None or mu is None:
            return ("KiCad DRC (native)", "FAIL",
                    "DRC report present but unparseable (tool health)")
        v, u = int(mv.group(1)), int(mu.group(1))
    if bv is None:
        base = read("ci/drc-baseline.json")
        if base is not None:
            try:
                bj = json.loads(base)
                bv, bu = bj["violations"], bj["unconnected"]
                tv = bj.get("tolerance_violations", 0)
                tu = bj.get("tolerance_unconnected", 0)
            except Exception:
                bv = bu = None
    if bv is None:
        return ("KiCad DRC (native)", "BOARD STATE",
                f"{v} violations, {u} unconnected items "
                "(no baseline recorded)")
    if bv == 0 and bu == 0:
        tv = tu = 0  # finished-board hard gate, as in drc_gate.py
    if regression is None:
        regression = v > bv + tv or u > bu + tu
    if v == 0 and u == 0 and bv == 0 and bu == 0:
        return ("KiCad DRC (native)", "PASS",
                "0 violations, 0 unconnected — baseline 0/0 (hard gate)")
    if regression:
        return ("KiCad DRC (native)", "REGRESSION",
                f"DRC REGRESSION: {v} violations, {u} unconnected "
                f"— above baseline {bv}/{bu} + jitter tolerance "
                f"+{tv}/+{tu}")
    if v > bv or u > bu:
        over = []
        if v > bv:
            over.append(f"+{v - bv} violations")
        if u > bu:
            over.append(f"+{u - bu} unconnected")
        return ("KiCad DRC (native)", "BOARD STATE",
                f"DRC (board in progress): {v} violations, "
                f"{u} unconnected — within checker jitter tolerance "
                f"({', '.join(over)} over baseline {bv}/{bu}, "
                f"tolerance +{tv}/+{tu})")
    return ("KiCad DRC (native)", "BOARD STATE",
            f"DRC (board in progress): {v} violations, {u} unconnected "
            f"— baseline {bv}/{bu}, no regression")


def check_status():
    """(name, status, detail) per verification, from results/ files.
    Ported verbatim from build_site.py."""
    def verdict(path, pass_markers, fail_markers=()):
        txt = read(path)
        if txt is None:
            return ("not run", "no result file")
        if any(m in txt for m in fail_markers):
            return ("FAIL", "")
        if any(m in txt for m in pass_markers):
            return ("PASS", "")
        return ("FAIL", "no PASS verdict in file")
    rows = [
        ("Link budget (R2 sensitivity)",) + verdict(
            "results/link_budget.txt",
            ["R2 VERDICT: PASS"], ["R2 VERDICT: FAIL"]),
        ("TIA ngspice simulation",) + verdict(
            "results/tia_sim.txt",
            ["VERDICT: PASS"], ["VERDICT: FAIL"]),
        ("HV flyback simulation",) + verdict(
            "results/hv_sim.txt", ["PASS"], ["FAIL"]),
        ("Digital simulation (codec / PRBS-15)",) + verdict(
            "results/digital_sim.txt",
            ["PASS: digital_sim -- all checks passed"], ["FAIL"]),
        ("Impedance calculation",) + verdict(
            "results/impedance.txt", ["VERDICT: PASS"], ["VERDICT: FAIL"]),
        ("Schematic netlist check",) + verdict(
            "results/netlist-check.txt",
            ["PASS: netlist matches"], ["FAIL"]),
    ]
    erc = read("results/erc-report.txt")
    if erc is None:
        rows.append(("KiCad ERC (native)", "not run",
                     "no ERC report (needs a KiCad 8 CI run)"))
    else:
        ne, nw = erc.count("; error"), erc.count("; warning")
        rows.append(("KiCad ERC (native)",
                     "PASS" if ne == 0 else "FAIL",
                     f"{ne} errors, {nw} warnings"))
    rows.append(drc_row())
    return rows


def status_data():
    jobs = [{"job": str(j.get("job", "?")),
             "ci_outcome": str(j.get("ci_outcome", "?")),
             "sha": str(j.get("sha", "")),
             "run_id": str(j.get("run_id", ""))}
            for j in job_status()]
    checks = [{"name": n, "status": s, "detail": d}
              for n, s, d in check_status()]
    write_json("status.json", {"jobs": jobs, "checks": checks})


# ------------------------------------------------------- token usage
def token_data():
    series = os.path.join(ROOT, "metrics", "token_series.csv")
    agents_p = os.path.join(ROOT, "metrics", "agents.csv")
    if not (os.path.exists(series) and os.path.exists(agents_p)):
        write_json("tokens.json", {"available": False})
        return
    with open(series) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        write_json("tokens.json", {"available": False})
        return
    last = rows[-1]
    tin = sum(int(r["input_tokens"]) for r in rows)
    tout = sum(int(r["output_tokens"]) for r in rows)
    with open(agents_p) as f:
        ag = list(csv.DictReader(f))
    n_with = sum(1 for a in ag if int(a["usage_rows"]) > 0)
    by_scope = {}
    for a in ag:
        s = by_scope.setdefault(a["scope"], [0, 0])
        s[0] += int(a["input_tokens"])
        s[1] += int(a["output_tokens"])
    scope_names = {"chat-tree": "design chat tree (main chat + its subagents)",
                   "checkpoint-cron": "checkpoint cron (pdlvds-progress)"}
    scopes = [{"key": k, "label": scope_names.get(k, k),
               "input": v[0], "output": v[1], "gross": v[0] + v[1]}
              for k, v in sorted(by_scope.items())]
    write_json("tokens.json", {
        "available": True,
        "total_in": tin, "total_out": tout, "total_gross": tin + tout,
        "n_messages": len(rows),
        "n_agents_with": n_with, "n_agents_scope": len(ag),
        "snapshot_utc": last["ts_utc"],
        "scopes": scopes,
        "has_chart": os.path.exists(
            os.path.join(ROOT, "metrics", "token_per_message.svg")),
        "has_progress": os.path.exists(
            os.path.join(ROOT, "metrics", "progress_vs_tokens.svg")),
    })


# ------------------------------------------------------- cost summary
def cost_data():
    """Cost summary from metrics/cost_summary.csv (list-price
    equivalents per API, per scope — produced by a separate metrics
    step; see metrics/README.md). The file is OPTIONAL: when it is
    absent from the tree the token page simply has no cost section.
    The CSV is staged verbatim (header + rows, as strings); no cost
    figure is computed or invented here."""
    p = os.path.join(ROOT, "metrics", "cost_summary.csv")
    if not os.path.exists(p):
        write_json("costs.json", {"available": False})
        return
    with open(p, newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        write_json("costs.json", {"available": False})
        return
    write_json("costs.json", {"available": True, "header": rows[0],
                              "rows": rows[1:]})


# ------------------------------------------------------- bom + sims
def bom_data():
    bom_path = os.path.join(ROOT, "hw", "fab", "bom.csv")
    rows = []
    if os.path.exists(bom_path):
        with open(bom_path) as f:
            rows = list(csv.reader(f))
    if not rows:
        write_json("bom.json", {"available": False})
        return
    n_parts = sum(int(r[1]) for r in rows[1:] if r and r[1].isdigit())
    write_json("bom.json", {"available": True, "header": rows[0],
                            "rows": rows[1:], "n_lines": len(rows) - 1,
                            "n_parts": n_parts})


def sim_data():
    def block(title, path, keys):
        return {"title": title, "path": path,
                "lines": key_lines(path, keys)}
    write_json("sims.json", {"blocks": [
        block("Link budget (requirement R2)", "results/link_budget.txt",
              ["SENSITIVITY", "sensitivity", "VERDICT", "f-3dB", "margin"]),
        block("TIA ngspice", "results/tia_sim.txt",
              ["f-3dB", "peaking", "noise", "VERDICT", "PASS", "FAIL"]),
        block("HV flyback", "results/hv_sim.txt",
              ["PASS", "FAIL", "ripple", "regulat"]),
        block("Digital simulation", "results/digital_sim.txt",
              ["PASS", "FAIL"]),
        block("Schematic netlist verification", "results/netlist-check.txt",
              ["PASS", "FAIL", "nets", "pins"]),
    ]})


# ------------------------------------------------------- assets
def tia_plot():
    """Render the ngspice TIA AC response to PNG from its CSV
    (best-effort, as in build_site.py)."""
    csv_path = os.path.join(ROOT, "results", "tia_ac.csv")
    if not os.path.exists(csv_path):
        return None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        data = np.genfromtxt(csv_path, delimiter=",", names=True)
        cols = data.dtype.names
        fig, ax = plt.subplots(figsize=(7, 3.2), dpi=130)
        ax.semilogx(data[cols[0]] / 1e6, data[cols[1]])
        ax.axhline(-3, color="r", ls="--", lw=0.8)
        ax.set_xlabel("frequency (MHz)")
        ax.set_ylabel("gain (dB)")
        ax.set_title("OPA657 TIA AC response (ngspice macromodel)")
        ax.grid(True, which="both", alpha=0.3)
        os.makedirs(ASSETS, exist_ok=True)
        out = os.path.join(ASSETS, "tia_ac.png")
        fig.savefig(out, bbox_inches="tight")
        plt.close(fig)
        return "tia_ac.png"
    except Exception as e:  # plot is decorative; never fail the build
        print(f"warning: TIA plot skipped ({e})")
        return None


def schematic_svg():
    """Export the schematic SVG via kicad-cli (best-effort, as in
    build_site.py — only files THIS export produced are collapsed
    onto schematic.svg)."""
    dst = os.path.join(ASSETS, "schematic.svg")
    try:
        os.makedirs(ASSETS, exist_ok=True)
        before = set(os.listdir(ASSETS))
        subprocess.run(["kicad-cli", "sch", "export", "svg", "-o", ASSETS,
                        os.path.join(ROOT, "hw", "pdlvds_rx.kicad_sch")],
                       check=True, capture_output=True, timeout=180)
        for f in os.listdir(ASSETS):
            if (f not in before and f.endswith(".svg")
                    and "schematic" not in f):
                os.rename(os.path.join(ASSETS, f), dst)
        return "schematic.svg" if os.path.exists(dst) else None
    except Exception as e:
        print(f"warning: schematic SVG export skipped ({e})")
        return None


def stage_assets():
    for d in (ASSETS, DOWNLOADS):
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)
    dl = {}
    for src, name in [("hw/fab/gerbers.zip", "gerbers.zip"),
                      ("hw/fab/bom.csv", "bom.csv"),
                      ("hw/fab/cpl.csv", "cpl.csv"),
                      ("hw/fab/board-layers.pdf", "board-layers.pdf"),
                      ("results/schematic.pdf", "schematic.pdf"),
                      ("metrics/README.md", "token-metrics-README.md")]:
        if copy_into(src, DOWNLOADS, name):
            dl[name] = name
    img = {}
    for src, name in [("hw/fab/board-top.svg", "board-top.svg"),
                      ("hw/fab/board-bottom.svg", "board-bottom.svg"),
                      ("hw/fab/board-layers.svg", "board-layers.svg"),
                      ("results/link_budget.png", "link_budget.png"),
                      ("results/digital_sim.png", "digital_sim.png"),
                      ("metrics/token_per_message.svg",
                       "token_per_message.svg"),
                      ("metrics/progress_vs_tokens.svg",
                       "progress_vs_tokens.svg")]:
        if copy_into(src, ASSETS, name):
            img[name] = name
    layers = {}
    fab = os.path.join(ROOT, "hw", "fab")
    if os.path.isdir(fab):
        for f in sorted(os.listdir(fab)):
            if f.startswith("layer-") and f.endswith(".svg"):
                if copy_into(os.path.join("hw/fab", f), ASSETS, f):
                    layers[f[6:-4]] = f
    # per-pass history renders (committed image files, never
    # re-rendered — the build-matrix property of the pass system)
    pj_path = os.path.join(ROOT, "history", "passes.json")
    if os.path.exists(pj_path):
        try:
            entries = json.load(open(pj_path))["passes"]
        except Exception as e:
            print(f"warning: passes.json unreadable ({e})")
            entries = []
        for e in entries:
            d = e.get("dir")
            if not d:
                continue
            files = set()
            for fn in (e.get("renders") or {}).values():
                if fn:
                    files.add(fn)
            for fn in (e.get("layers") or {}).values():
                if fn:
                    files.add(fn)
            for fn in sorted(files):
                if copy_into(os.path.join("history", d, fn),
                             os.path.join(ASSETS, "history", d), fn) \
                        and fn.endswith(".svg"):
                    inject_svg_background(
                        os.path.join(ASSETS, "history", d, fn))
    # fab board renders (top / bottom / all-layers composite /
    # per-layer) get the same baked-in background as the history
    # renders above, so every board render SVG the site serves
    # stands alone on #111.
    for name in ("board-top.svg", "board-bottom.svg", "board-layers.svg"):
        if name in img:
            inject_svg_background(os.path.join(ASSETS, name))
    for f in layers.values():
        inject_svg_background(os.path.join(ASSETS, f))
    tia = tia_plot()
    if tia:
        img[tia] = tia
    sch = schematic_svg()
    if sch:
        img[sch] = sch
    write_json("board.json", {
        "top": "board-top.svg" in img,
        "bottom": "board-bottom.svg" in img,
        "composite": "board-layers.svg" in img,
        "layers": [{"name": k, "file": v}
                   for k, v in sorted(layers.items())],
        "has_link_budget_plot": "link_budget.png" in img,
        "has_tia_plot": tia is not None,
        "has_digital_plot": "digital_sim.png" in img,
        "has_schematic_svg": sch is not None,
        "has_schematic_pdf": "schematic.pdf" in dl,
    })
    labels = {"gerbers.zip": "gerbers.zip", "bom.csv": "bom.csv",
              "cpl.csv": "cpl.csv",
              "board-layers.pdf": "board-layers.pdf",
              "schematic.pdf": "schematic.pdf",
              "token-metrics-README.md": "token-metrics-README.md"}
    write_json("downloads.json", {
        "files": [{"name": labels.get(n, n), "file": f}
                  for n, f in sorted(dl.items())]})


# ------------------------------------------------------- docs includes
def stage_docs():
    """Copy docs/01, docs/02, docs/05 into _includes/docs/ with
    heading levels shifted one deeper (page title holds the h1,
    exactly as the old markdown converter arranged it)."""
    if os.path.exists(INCLUDES_DOCS):
        shutil.rmtree(INCLUDES_DOCS)
    os.makedirs(INCLUDES_DOCS)
    for src, name in [("docs/01-requirements.md", "requirements.md"),
                      ("docs/02-architecture.md", "architecture.md"),
                      ("docs/05-test-plan.md", "test-plan.md")]:
        txt = read(src)
        if txt is None:
            txt = f"_{src} missing_"
        out, in_code = [], False
        for line in txt.splitlines():
            if line.strip().startswith("```"):
                in_code = not in_code
            elif not in_code and re.match(r"^#{1,5}\s", line):
                line = "#" + line
            out.append(line)
        with open(os.path.join(INCLUDES_DOCS, name), "w") as f:
            f.write("\n".join(out) + "\n")


def main():
    os.makedirs(WEB, exist_ok=True)
    status_data()
    token_data()
    cost_data()
    bom_data()
    sim_data()
    stage_assets()
    stage_docs()
    print(f"site data staged: {WEB} "
          f"(_data/status.json, tokens.json, bom.json, sims.json, "
          f"board.json, downloads.json; assets/; downloads/; "
          f"_includes/docs/)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
