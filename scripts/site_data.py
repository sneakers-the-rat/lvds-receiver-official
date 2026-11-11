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
  - website/_data/bom.json     — BOM table data, REGENERATED at
    build time from a netlist exported from the current schematic
    (kicad-cli), falling back to the committed results/netlist.xml
    and then to a staged hw/fab/bom.csv; the source used is named
    in the JSON (and on the BOM page).
  - website/_data/sims.json    — simulation summary blocks: the key
    lines of each results/*.txt (plus the file's mtime, shown on
    the page — the sims themselves are NOT re-run by the site
    build; CI refreshes results/ via the sim job's artefact), or
    the file's absence.
  - website/_data/board.json   — which board assets exist (top /
    bottom renders, the all-layers composite, per-layer SVGs,
    schematic SVG/PDF) plus provenance: the board file the renders
    were exported from and how each schematic asset was obtained.
    The board renders are EXPORTED AT BUILD TIME from the current
    frontier board — the newest hw/pdlvds_rx.exp<N>.kicad_pcb,
    selected by commit_pass.resolve_board, the pass system's own
    rule (SITE_BOARD overrides it, for testing / reproducing an
    older build). Only when no build-time export is possible (no
    kicad-cli — CI's build-site job) does staging fall back to the
    hw/fab/ copies, which CI's kicad-validate job regenerates from
    the same frontier board on every run (scripts/make_fab.sh) and
    ships as the fab-outputs artefact; board.json says which path
    produced the renders, and board.md prints it.
  - Board render SVGs staged into website/assets/gen/ (the fab
    renders and the per-pass history renders) get a dark background
    rect baked in — see inject_svg_background() — so a render
    opened on its own (new tab, direct link) stands on the same
    #111 ground the site's CSS panels paint behind it. The source
    SVGs (hw/fab/, history/) stay pristine KiCad output.
  - website/_data/downloads.json — the fabrication downloads list.
  - website/assets/, website/downloads/ — the board renders
    exported at build time (above), staged copies of the remaining
    fab downloads, results plots, metrics charts, per-pass history
    renders (assets/history/<dir>/), the matplotlib TIA plot and
    the kicad-cli schematic SVG/PDF (all best-effort, exactly as
    before: a failure warns and the page shows "not generated",
    with the fallback source named where one was used).
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
results/, metrics/, history/, docs/ (hw/fab/ is a CI artefact
staging area, regenerated per run — never a source of truth).
"""
import csv, json, os, re, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone

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


# --------------------------------------------- current sources
# The current-information pages (board, schematic, BOM, downloads)
# derive from CURRENT sources at build time — never from a manually
# refreshed staging directory. Board renders used to be staged from
# hw/fab/, which only scripts/make_fab.sh regenerates, so /board
# silently showed a long-dead board state (and make_fab exported
# the pre-expansion BASE board at that). Now: this step exports
# from the frontier board itself when kicad-cli is available
# (local builds), and CI's kicad-validate job — the one place in
# that pipeline with KiCad — regenerates hw/fab/ from the same
# frontier board every run for the build-site job to stage.

def frontier_board():
    """Absolute path of the board the current-info pages render:
    the newest hw/pdlvds_rx.exp<N>.kicad_pcb, selected by
    commit_pass.resolve_board — the pass system's own rule, reused
    verbatim, never reimplemented here and never the base board.
    SITE_BOARD (a path) overrides it, for testing and for
    reproducing an older build. None when no exp board exists
    (tolerated: staging falls back to hw/fab/ and says so)."""
    override = os.environ.get("SITE_BOARD")
    if override:
        p = os.path.abspath(override)
        if os.path.exists(p):
            return p
        print(f"warning: SITE_BOARD={override} does not exist; "
              f"ignoring the override")
    try:
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import commit_pass
        return commit_pass.resolve_board(
            None, os.path.join(ROOT, "hw"))
    except SystemExit:
        return None
    except Exception as e:  # selection must never fail the build
        print(f"warning: frontier board selection failed ({e})")
        return None


def have_kicad():
    return shutil.which("kicad-cli") is not None


def run_kicad(args, timeout=300):
    """One kicad-cli invocation, best-effort: True iff it ran and
    exited 0. A missing binary or a failed export warns and returns
    False — the caller falls back and names the fallback."""
    if not have_kicad():
        return False
    try:
        r = subprocess.run(["kicad-cli"] + args,
                           capture_output=True, timeout=timeout)
        if r.returncode != 0:
            print(f"warning: kicad-cli {' '.join(args[:3])}... "
                  f"exited {r.returncode}")
            return False
        return True
    except Exception as e:
        print(f"warning: kicad-cli {' '.join(args[:3])}... "
              f"failed ({e})")
        return False


# The /board gallery's export specs — layer lists and crop flags
# identical to scripts/make_fab.sh's, so a build-time render and a
# fab render of the same board are the same picture. A test
# (hw/tests/test_site_data_board.py) pins the two together.
BOARD_SVG_SPECS = [
    ("board-layers.svg",
     "F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,B.SilkS,Edge.Cuts"),
    ("board-top.svg", "F.Cu,F.SilkS,Edge.Cuts"),
    ("board-bottom.svg", "B.Cu,B.SilkS,Edge.Cuts"),
]
BOARD_LAYER_SVGS = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu",
                    "F.SilkS", "Edge.Cuts"]
BOARD_PDF_LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu"


def export_board_renders(board, assets_dir, downloads_dir):
    """Export the /board gallery (composite, top, bottom, one SVG
    per layer in BOARD_LAYER_SVGS) and the board-layers.pdf
    download from `board` into the staging dirs. Best-effort per
    file. Returns (svg_names:set, layers:dict, pdf_ok:bool)."""
    svgs, layers, pdf_ok = set(), {}, False
    for name, spec in BOARD_SVG_SPECS:
        out = os.path.join(assets_dir, name)
        if run_kicad(["pcb", "export", "svg", "--layers", spec,
                      "--page-size-mode", "2",
                      "--exclude-drawing-sheet",
                      "-o", out, board]) \
                and os.path.exists(out):
            svgs.add(name)
    for layer in BOARD_LAYER_SVGS:
        name = f"layer-{layer}.svg"
        out = os.path.join(assets_dir, name)
        if run_kicad(["pcb", "export", "svg", "--layers", layer,
                      "--page-size-mode", "2",
                      "--exclude-drawing-sheet",
                      "-o", out, board]) \
                and os.path.exists(out):
            layers[layer] = name
    out = os.path.join(downloads_dir, "board-layers.pdf")
    if run_kicad(["pcb", "export", "pdf", "--layers",
                  BOARD_PDF_LAYERS, "-o", out, board]) \
            and os.path.exists(out):
        pdf_ok = True
    return svgs, layers, pdf_ok


def export_schematic_pdf(dst):
    """Export the schematic PDF from the CURRENT schematic at
    build time (kicad-cli). True iff dst now holds the export."""
    if run_kicad(["sch", "export", "pdf", "-o", dst,
                  os.path.join(ROOT, "hw", "pdlvds_rx.kicad_sch")]) \
            and os.path.exists(dst):
        return True
    return False


# ------------------------------------------------------- bom build
_BOM_CACHE = None


def parse_bom_netlist(path):
    """BOM (header, rows) from a KiCad XML netlist — the grouping
    scripts/make_fab.sh has always used: group components by
    (value, footprint), refs space-joined in document order,
    groups sorted by first ref. Rows are [Refs, Qty, Value,
    Footprint] strings, header first."""
    groups = defaultdict(list)
    tree = ET.parse(path)
    for comp in tree.getroot().iter("comp"):
        fp = comp.findtext("footprint") or ""
        groups[(comp.findtext("value"), fp)].append(comp.get("ref"))
    rows = [[" ".join(refs), str(len(refs)), val, fp]
            for (val, fp), refs in
            sorted(groups.items(), key=lambda kv: kv[1][0])]
    return ["Refs", "Qty", "Value", "Footprint"], rows


def bom_table():
    """(header, rows, source) for the BOM page + bom.csv download,
    regenerated at build time. Source, best first: a netlist
    exported from the current schematic right now (kicad-cli);
    the committed results/netlist.xml; a staged hw/fab/bom.csv.
    Cached — bom_data() and stage_assets() share one computation.
    (None, None, reason) when no source exists at all."""
    global _BOM_CACHE
    if _BOM_CACHE is not None:
        return _BOM_CACHE
    result = (None, None, "no netlist or fab BOM available")
    sch_rel = "hw/pdlvds_rx.kicad_sch"
    tmp = None
    try:
        if have_kicad():
            tmp = tempfile.mkdtemp(prefix="site-bom-")
            nl = os.path.join(tmp, "netlist.xml")
            if run_kicad(["sch", "export", "netlist",
                          "--format", "kicadxml", "-o", nl,
                          os.path.join(ROOT, sch_rel)]):
                header, rows = parse_bom_netlist(nl)
                result = (header, rows,
                          f"netlist exported from {sch_rel} at "
                          f"build time")
        if result[0] is None and \
                os.path.exists(os.path.join(ROOT,
                                            "results/netlist.xml")):
            header, rows = parse_bom_netlist(
                os.path.join(ROOT, "results/netlist.xml"))
            result = (header, rows,
                      "committed results/netlist.xml (schematic "
                      "netlist export; not regenerated this build)")
        if result[0] is None:
            fab_bom = os.path.join(ROOT, "hw", "fab", "bom.csv")
            if os.path.exists(fab_bom):
                with open(fab_bom) as f:
                    all_rows = list(csv.reader(f))
                if all_rows:
                    result = (all_rows[0], all_rows[1:],
                              "staged hw/fab/bom.csv (CI fab "
                              "artefact; not regenerated this build)")
    except Exception as e:
        print(f"warning: BOM regeneration failed ({e}); "
              f"falling back")
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    _BOM_CACHE = result
    return result


def file_mtime_iso(path):
    """A file's mtime as an ISO UTC string ('' when absent) — the
    honest freshness stamp for inputs the site build cannot
    regenerate (simulation results)."""
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return ""
    return datetime.fromtimestamp(
        os.path.getmtime(p), timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


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
# Presentation names for the cost tables: the data files carry the
# providers' full API names and the models' catalogue ids; the tables
# use the plain names below. Anything unmapped falls back to the
# string in the data file.
COST_PROVIDER_DISPLAY = {
    "Meta - Muse (Meta Model API)": "Meta",
    "Anthropic - Claude API": "Anthropic",
    "OpenAI API": "OpenAI",
}
COST_MODEL_DISPLAY = {
    "muse-wonder-1.0": "Muse Wonder 1.0",
    "muse-spark-1.3": "Muse Spark 1.3",
    "claude-opus-5-5": "Opus 5.5",
    "claude-sonnet-5-5": "Sonnet 5.5",
    "gpt-6-astra": "GPT-6 Astra",
    "gpt-6.1-sol": "GPT-6.1 Sol",
}
COST_SCOPE_DISPLAY = {
    "main_chat": "Main chat",
    "subagents": "Subagents",
    "checkpoint_cron": "Checkpoint cron",
}
COST_SCOPES = ("main_chat", "subagents", "checkpoint_cron")


def _usd(value):
    return f"${float(value):,.2f}"


def _usd_rate(value):
    return f"${float(value):.2f}"


def cost_data():
    """Cost tables for the token page, generated from the metrics
    data files: the rates table from metrics/api_rates.json and the
    cost tables from metrics/cost_summary.csv (both produced by the
    metrics step; see metrics/README.md). The files are OPTIONAL:
    when either is absent from the tree the token page simply has no
    cost section. No cost figure is computed or invented here — the
    staging only selects, orders and formats the generator's rows."""
    csv_path = os.path.join(ROOT, "metrics", "cost_summary.csv")
    rates_path = os.path.join(ROOT, "metrics", "api_rates.json")
    if not (os.path.exists(csv_path) and os.path.exists(rates_path)):
        write_json("costs.json", {"available": False})
        return
    with open(rates_path) as f:
        rates_doc = json.load(f)
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or "providers" not in rates_doc:
        write_json("costs.json", {"available": False})
        return

    providers = [p["provider"] for p in rates_doc["providers"]]
    columns = [COST_PROVIDER_DISPLAY.get(p, p) for p in providers]

    # Rates table: each provider's flagship tier, then its step-down.
    rates = []
    for p in rates_doc["providers"]:
        prov = COST_PROVIDER_DISPLAY.get(p["provider"], p["provider"])
        rates.append({
            "provider": prov,
            "model": COST_MODEL_DISPLAY.get(p["model"], p["model"]),
            "input": _usd_rate(p["input_usd_per_mtok"]),
            "cached": _usd_rate(p["cached_input_usd_per_mtok"]),
            "output": _usd_rate(p["output_usd_per_mtok"]),
        })
        rates.append({
            "provider": prov,
            "model": COST_MODEL_DISPLAY.get(
                p["stepdown_model"], p["stepdown_model"]),
            "input": _usd_rate(p["stepdown_input_usd_per_mtok"]),
            "cached": _usd_rate(p["stepdown_cached_input_usd_per_mtok"]),
            "output": _usd_rate(p["stepdown_output_usd_per_mtok"]),
        })

    def cells_for(model_label, scope):
        """One formatted cell per provider, in api_rates.json order,
        from the cost_summary.csv row with this model label + scope;
        empty string where a provider has no such row."""
        cells = []
        for prov in providers:
            match = [r for r in rows if r["provider"] == prov
                     and r["model"] == model_label
                     and r["scope"] == scope]
            cells.append(_usd(match[0]["total_cost_usd"]) if match else "")
        return cells

    # Main cost table: the all-uncached tier-matched rows, scopes
    # then Total.
    costs = []
    for scope in COST_SCOPES:
        costs.append({"label": COST_SCOPE_DISPLAY[scope], "total": False,
                      "cells": cells_for("all-uncached (tier-matched)",
                                         scope)})
    costs.append({"label": "Total", "total": True,
                  "cells": cells_for("all-uncached (tier-matched)",
                                     "all")})

    # Second table: the other whole-volume costs.
    extras = []
    for label in ("all-cached (tier-matched)",
                  "cache-adjusted (pessimistic estimate)",
                  "cache-adjusted (optimistic estimate)",
                  "cache-adjusted (assumed 95% share)"):
        cells = cells_for(label, "all")
        if any(cells):
            extras.append({"label": label[0].upper() + label[1:],
                           "cells": cells})

    if not all(costs[-1]["cells"]) or not rates:
        write_json("costs.json", {"available": False})
        return
    write_json("costs.json", {"available": True, "columns": columns,
                              "rates": rates, "costs": costs,
                              "extras": extras})


# ------------------------------------------------------- bom + sims
def bom_data():
    header, rows, source = bom_table()
    if not rows:
        write_json("bom.json", {"available": False,
                                "source": source})
        return
    n_parts = sum(int(r[1]) for r in rows if r and r[1].isdigit())
    write_json("bom.json", {"available": True, "header": header,
                            "rows": rows, "n_lines": len(rows),
                            "n_parts": n_parts, "source": source})


def sim_data():
    def block(title, path, keys):
        return {"title": title, "path": path,
                "lines": key_lines(path, keys),
                "updated": file_mtime_iso(path)}
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
        # ngspice's wrdata output is whitespace-delimited with no
        # header, despite the .csv name: two columns, Hz and dB.
        data = np.loadtxt(csv_path)
        if data.ndim != 2 or data.shape[1] < 2:
            raise ValueError(f"unexpected TIA data shape {data.shape}")
        fig, ax = plt.subplots(figsize=(7, 3.2), dpi=130)
        ax.semilogx(data[:, 0] / 1e6, data[:, 1])
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

    # ---- current board: export the /board renders + the layers
    # PDF from the frontier board at build time. Fall back to the
    # hw/fab staging copies (CI's fab artefact, regenerated from
    # the same board by kicad-validate) only for whatever the
    # build-time export did not produce.
    board = frontier_board()
    board_rel = os.path.relpath(board, ROOT) if board else None
    exp_svgs, exp_layers, exp_pdf = set(), {}, False
    if board and have_kicad():
        exp_svgs, exp_layers, exp_pdf = export_board_renders(
            board, ASSETS, DOWNLOADS)
    if exp_svgs or exp_layers:
        renders_source = (f"exported at build time from "
                          f"{board_rel}")
    elif board:
        renders_source = (f"staged from hw/fab (CI fab artefact, "
                          f"generated from {board_rel}; no "
                          f"build-time export this build)")
    else:
        renders_source = ("staged from hw/fab (no frontier board "
                          "found this build)")

    dl = {}
    # schematic.pdf: regenerated from the current schematic at
    # build time; else the CI fab artefact's copy; else the
    # committed results/ copy (named as such — it is NOT
    # regenerated by anything and predates schematic changes).
    sch_pdf_src = None
    if export_schematic_pdf(os.path.join(DOWNLOADS,
                                         "schematic.pdf")):
        dl["schematic.pdf"] = "schematic.pdf"
        sch_pdf_src = ("exported at build time from "
                       "hw/pdlvds_rx.kicad_sch")
    elif copy_into("hw/fab/schematic.pdf", DOWNLOADS,
                   "schematic.pdf"):
        dl["schematic.pdf"] = "schematic.pdf"
        sch_pdf_src = ("staged from hw/fab/schematic.pdf (CI fab "
                       "artefact, exported from the current "
                       "schematic by scripts/make_fab.sh)")
    elif copy_into("results/schematic.pdf", DOWNLOADS,
                   "schematic.pdf"):
        dl["schematic.pdf"] = "schematic.pdf"
        sch_pdf_src = ("staged from committed results/schematic.pdf "
                       "(not regenerated — no kicad-cli this build "
                       "and no CI fab artefact present)")
    # bom.csv: the build-time-regenerated table (see bom_table);
    # the hw/fab copy only when regeneration had no source at all.
    bom_header, bom_rows, _bom_src = bom_table()
    if bom_rows:
        with open(os.path.join(DOWNLOADS, "bom.csv"), "w",
                  newline="") as f:
            w = csv.writer(f)
            w.writerow(bom_header)
            w.writerows(bom_rows)
        dl["bom.csv"] = "bom.csv"
    # board-layers.pdf: the build-time export above, else staged.
    if exp_pdf:
        dl["board-layers.pdf"] = "board-layers.pdf"
    for src, name in [("hw/fab/gerbers.zip", "gerbers.zip"),
                      ("hw/fab/bom.csv", "bom.csv"),
                      ("hw/fab/cpl.csv", "cpl.csv"),
                      ("hw/fab/board-layers.pdf", "board-layers.pdf"),
                      ("metrics/README.md", "token-metrics-README.md")]:
        if name not in dl and copy_into(src, DOWNLOADS, name):
            dl[name] = name
    img = {}
    for name in ("board-top.svg", "board-bottom.svg",
                 "board-layers.svg"):
        if name in exp_svgs:
            img[name] = name
    for src, name in [("hw/fab/board-top.svg", "board-top.svg"),
                      ("hw/fab/board-bottom.svg", "board-bottom.svg"),
                      ("hw/fab/board-layers.svg", "board-layers.svg"),
                      ("results/link_budget.png", "link_budget.png"),
                      ("results/digital_sim.png", "digital_sim.png"),
                      ("metrics/token_per_message.svg",
                       "token_per_message.svg"),
                      ("metrics/progress_vs_tokens.svg",
                       "progress_vs_tokens.svg")]:
        if name not in img and copy_into(src, ASSETS, name):
            img[name] = name
    layers = dict(exp_layers)
    fab = os.path.join(ROOT, "hw", "fab")
    if os.path.isdir(fab):
        for f in sorted(os.listdir(fab)):
            if f.startswith("layer-") and f.endswith(".svg") \
                    and f[6:-4] not in layers:
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
    sch_svg_src = None
    if sch:
        img[sch] = sch
        sch_svg_src = ("exported at build time from "
                       "hw/pdlvds_rx.kicad_sch")
    elif copy_into("hw/fab/schematic.svg", ASSETS, "schematic.svg"):
        sch = "schematic.svg"
        img[sch] = sch
        sch_svg_src = ("staged from hw/fab/schematic.svg (CI fab "
                       "artefact, exported from the current "
                       "schematic by scripts/make_fab.sh)")
    # board-3d.glb: the interactive 3D model. Exported at build time
    # from the frontier board when KiCad is available (via
    # scripts/export_glb.sh, which resolves every component model
    # from the repo's hw/models3d mirror); otherwise staged from the
    # fab package CI's kicad-validate job regenerated.
    model3d = False
    model3d_src = None
    glb_dst = os.path.join(ASSETS, "board-3d.glb")
    if board and have_kicad():
        try:
            r = subprocess.run(
                ["bash", os.path.join(ROOT, "scripts", "export_glb.sh"),
                 board, glb_dst],
                capture_output=True, text=True, timeout=600)
            if r.returncode == 0 and os.path.exists(glb_dst):
                model3d = True
                model3d_src = ("exported at build time from "
                               + (board_rel or "the frontier board"))
            else:
                print("warning: export_glb failed: "
                      + (r.stderr or r.stdout or "")[-300:])
        except Exception as e:
            print(f"warning: export_glb failed ({e})")
    if not model3d and copy_into("hw/fab/board-3d.glb", ASSETS,
                                 "board-3d.glb"):
        model3d = True
        model3d_src = ("staged from hw/fab/board-3d.glb (CI fab "
                       "artefact, exported from the current board "
                       "by scripts/make_fab.sh)")
    if copy_into("hw/fab/board-3d.glb", DOWNLOADS, "board-3d.glb"):
        dl["board-3d.glb"] = "board-3d.glb"
    write_json("board.json", {
        "top": "board-top.svg" in img,
        "bottom": "board-bottom.svg" in img,
        "composite": "board-layers.svg" in img,
        "model3d": model3d,
        "model3d_source": model3d_src,
        "layers": [{"name": k, "file": v}
                   for k, v in sorted(layers.items())],
        "has_link_budget_plot": "link_budget.png" in img,
        "has_tia_plot": tia is not None,
        "has_digital_plot": "digital_sim.png" in img,
        "has_schematic_svg": sch is not None,
        "has_schematic_pdf": "schematic.pdf" in dl,
        "board_file": board_rel,
        "renders_source": renders_source,
        "schematic_svg_source": sch_svg_src,
        "schematic_pdf_source": sch_pdf_src,
    })
    labels = {"gerbers.zip": "gerbers.zip", "bom.csv": "bom.csv",
              "cpl.csv": "cpl.csv",
              "board-layers.pdf": "board-layers.pdf",
              "schematic.pdf": "schematic.pdf",
              "board-3d.glb": "board-3d.glb (interactive 3D model)",
              "token-metrics-README.md": "token-metrics-README.md"}
    write_json("downloads.json", {
        "files": [{"name": labels.get(n, n), "file": f}
                  for n, f in sorted(dl.items())],
        "board_file": board_rel,
        "fab_source": ("gerbers.zip and cpl.csv are staged from "
                       "hw/fab — in CI, regenerated from "
                       f"{board_rel or 'the frontier board'} on "
                       "every run by scripts/make_fab.sh "
                       "(kicad-validate job); a local build without "
                       "a fab export stages the last local copy, if "
                       "any")})


# ------------------------------------------------------- docs includes
def stage_docs():
    """Copy docs/01, docs/02, docs/05, docs/14 into _includes/docs/
    with heading levels shifted one deeper (page title holds the h1,
    exactly as the old markdown converter arranged it)."""
    if os.path.exists(INCLUDES_DOCS):
        shutil.rmtree(INCLUDES_DOCS)
    os.makedirs(INCLUDES_DOCS)
    for src, name in [("docs/01-requirements.md", "requirements.md"),
                      ("docs/02-architecture.md", "architecture.md"),
                      ("docs/05-test-plan.md", "test-plan.md"),
                      ("docs/14-build-guide.md", "build-guide.md")]:
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
