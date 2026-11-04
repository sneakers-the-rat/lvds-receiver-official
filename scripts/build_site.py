#!/usr/bin/env python3
"""Build the self-contained static project site into site/.

No external assets, no CDN, no JavaScript frameworks: one index.html
with inline CSS plus local files under assets/ and downloads/.
Content is assembled from the repo's own verified artefacts:
  - docs/01 (requirements), docs/02 (architecture), docs/05 (test plan)
    rendered from Markdown by the small converter below,
  - hw/fab/ board renders + per-layer SVGs + Gerber zip + BOM + CPL,
  - results/ simulation outputs and plots,
  - results/schematic.pdf (+ schematic SVG if kicad-cli can export it).
Anything missing is shown as "not generated" rather than faked.
Run scripts/ci.sh and scripts/make_fab.sh first for a complete site.
"""
import csv, html, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
ASSETS = os.path.join(SITE, "assets")
DOWNLOADS = os.path.join(SITE, "downloads")

# ---------------------------------------------------------------- markdown
def md_inline(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s

def md_to_html(text):
    out, para, lst, code, table = [], [], None, None, []

    def flush_para():
        if para:
            out.append("<p>" + md_inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_list():
        nonlocal lst
        if lst:
            out.append("</" + lst + ">")
            lst = None

    def flush_table():
        if not table:
            return
        rows = [[c.strip() for c in r.strip().strip("|").split("|")]
                for r in table]
        rows = [r for r in rows
                if not all(set(c) <= set("-: ") for c in r)]
        if rows:
            out.append("<table><thead><tr>" + "".join(
                f"<th>{md_inline(c)}</th>" for c in rows[0]) +
                "</tr></thead><tbody>")
            for r in rows[1:]:
                out.append("<tr>" + "".join(
                    f"<td>{md_inline(c)}</td>" for c in r) + "</tr>")
            out.append("</tbody></table>")
        table.clear()

    for line in text.splitlines():
        if code is not None:
            if line.strip().startswith("```"):
                out.append("<pre>" + html.escape("\n".join(code)) + "</pre>")
                code = None
            else:
                code.append(line)
            continue
        if line.strip().startswith("```"):
            flush_para(); flush_list(); flush_table(); code = []; continue
        if line.strip().startswith("|") and line.strip().endswith("|"):
            flush_para(); flush_list(); table.append(line); continue
        flush_table()
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            flush_para(); flush_list()
            lvl = len(m.group(1)) + 1  # page H1 is the doc title slot
            out.append(f"<h{lvl}>{md_inline(m.group(2))}</h{lvl}>")
            continue
        if re.match(r"^\s*---+\s*$", line):
            flush_para(); flush_list(); out.append("<hr>"); continue
        m = re.match(r"^\s*[-*]\s+(.*)", line)
        if m:
            flush_para()
            if lst != "ul":
                flush_list(); out.append("<ul>"); lst = "ul"
            out.append("<li>" + md_inline(m.group(1)) + "</li>"); continue
        m = re.match(r"^\s*\d+[.)]\s+(.*)", line)
        if m:
            flush_para()
            if lst != "ol":
                flush_list(); out.append("<ol>"); lst = "ol"
            out.append("<li>" + md_inline(m.group(1)) + "</li>"); continue
        if line.strip().startswith(">"):
            flush_para(); flush_list()
            out.append("<blockquote>" + md_inline(line.strip()[1:].strip())
                       + "</blockquote>"); continue
        if not line.strip():
            flush_para(); flush_list(); continue
        para.append(line.strip())
    if code is not None:
        out.append("<pre>" + html.escape("\n".join(code)) + "</pre>")
    flush_para(); flush_list(); flush_table()
    return "\n".join(out)

# ---------------------------------------------------------------- helpers
def read(path):
    p = os.path.join(ROOT, path)
    return open(p).read() if os.path.exists(p) else None

def copy_into(src, dst_dir, name=None):
    p = os.path.join(ROOT, src)
    if not os.path.exists(p):
        return None
    name = name or os.path.basename(src)
    shutil.copy2(p, os.path.join(dst_dir, name))
    return name

def key_lines(path, keys):
    txt = read(path)
    if txt is None:
        return None
    picked = [ln for ln in txt.splitlines()
              if any(k in ln for k in keys)]
    return picked

# ------------------------------------------------------- build status
def job_status():
    """Status JSONs recorded by the CI validation jobs and downloaded
    by the build-site job into .site-status/<job>/. Absent on a local
    build (nothing downloaded) — the panel then says so."""
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
    """The DRC row of the status panel, worded as BOARD STATE
    (CI signal fix, 2026-11-03): while routing is unfinished the
    counts are reported against ci/drc-baseline.json — never as
    "DRC passed" and no longer as a bare FAIL either. The row is
    FAIL only for a tool-health breakage, REGRESSION when a count
    rises above baseline, and PASS only once the board is finished
    and the baseline is 0/0 (the hard-gate end state).

    Counts come from the kicad-validate job's status JSON when the
    site is built by CI (scripts/drc_gate.py's numbers, merged in
    by the workflow), else from a local results/drc-report.txt; the
    baseline falls back to ci/drc-baseline.json in the checkout."""
    kj = next((j for j in job_status()
               if j.get("job") == "kicad-validate"), None)
    if kj is not None and kj.get("drc_verdict") == "TOOL FAILURE":
        return ("KiCad DRC (native)", "FAIL",
                kj.get("drc_board_state") or "DRC tool failure (see CI log)")
    v = u = bv = bu = None
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
        # Same real-format fix as scripts/drc_gate.py (round 2):
        # KiCad 8's report file frames the lines in '**' and counts
        # unconnected PADS, not items.
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
            except Exception:
                bv = bu = None
    if bv is None:
        return ("KiCad DRC (native)", "BOARD STATE",
                f"{v} violations, {u} unconnected items "
                "(no baseline recorded)")
    if regression is None:
        regression = v > bv or u > bu
    if v == 0 and u == 0 and bv == 0 and bu == 0:
        return ("KiCad DRC (native)", "PASS",
                "0 violations, 0 unconnected — baseline 0/0 (hard gate)")
    if regression:
        return ("KiCad DRC (native)", "REGRESSION",
                f"DRC REGRESSION: {v} violations, {u} unconnected "
                f"— above baseline {bv}/{bu}")
    return ("KiCad DRC (native)", "BOARD STATE",
            f"DRC (board in progress): {v} violations, {u} unconnected "
            f"— baseline {bv}/{bu}, no regression")

def check_status():
    """(name, status, detail) per verification, from results/ files.
    status is PASS, FAIL or 'not run' (file absent). A present file
    with no PASS verdict counts as FAIL — that is what the file's own
    verdict line is for."""
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

def status_panel():
    jobs = job_status()
    if jobs:
        jrows = "".join(
            "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(str(j.get("job", "?"))),
                html.escape(str(j.get("ci_outcome", "?"))),
                html.escape(str(j.get("sha", ""))[:10] +
                            (f" · run {j['run_id']}"
                             if j.get("run_id") else "")))
            for j in jobs)
        job_html = (f"<table><thead><tr><th>CI job</th><th>check step "
                    f"outcome</th><th>commit</th></tr></thead><tbody>"
                    f"{jrows}</tbody></table>")
    else:
        job_html = ("<p><em>No CI job status reported for this build "
                    "(local build, or the status artefacts were not "
                    "available).</em></p>")
    def badge(st):
        cls = {"PASS": "pass", "FAIL": "fail",
               "REGRESSION": "fail"}.get(st, "notrun")
        return f'<span class="badge {cls}">{html.escape(st)}</span>'
    crows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            html.escape(name), badge(st), html.escape(detail))
        for name, st, detail in check_status())
    return (f"<h3>Build status</h3>{job_html}"
            f"<table><thead><tr><th>Check</th><th>Status</th>"
            f"<th>Detail</th></tr></thead><tbody>{crows}</tbody>"
            f"</table>"
            f"<p>Status is read from the result files available to "
            f"this build (the validation jobs' fresh uploads when the "
            f"site is built by CI); anything missing is shown as "
            f"<em>not run</em>, never as passed.</p>")

# Copper-layer palette for the routing-history composite + legend;
# must match LAYER_PALETTE in scripts/snapshot_route.py.
LAYER_ORDER = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
LAYER_PALETTE = {"F.Cu": "#FF3B30", "In1.Cu": "#FF9500",
                 "In2.Cu": "#34C759", "B.Cu": "#0A84FF"}


def routing_history():
    """Render the routing-evolution gallery from history/index.json.

    Snapshot assets (history/<ts>_<hash>/*.svg) are copied into
    assets/history/<dir>/ so the built site is self-contained. Entries
    without renders (attempts whose board was never committed) show an
    explicit note instead of an image. Stats that were never recorded
    show as "not recorded" — never interpolated. With no history at
    all, the section still builds with a placeholder line."""
    idx_path = os.path.join(ROOT, "history", "index.json")
    if not os.path.exists(idx_path):
        return ("<p><em>No routing snapshots recorded yet — run "
                "<code>scripts/snapshot_route.py</code> after a routing "
                "attempt.</em></p>")
    try:
        entries = json.load(open(idx_path))
    except Exception as e:
        return f"<p><em>history/index.json unreadable ({e}).</em></p>"
    if not entries:
        return ("<p><em>No routing snapshots recorded yet — run "
                "<code>scripts/snapshot_route.py</code> after a routing "
                "attempt.</em></p>")
    hist_assets = os.path.join(ASSETS, "history")
    os.makedirs(hist_assets, exist_ok=True)

    def nr(v):
        return "not recorded" if v is None else str(v)

    out = ["<p>Every routing attempt, in order — including the ones "
           "that failed. Snapshots live in <code>history/</code> in the "
           "repository, one directory per attempt, made by "
           "<code>scripts/snapshot_route.py</code>. The renders are "
           "route-only: tracks, vias and pads, with zone fills (the "
           "opaque GND pours) removed — each snapshot is exported "
           "from a temp copy of the board with its zones deleted, so "
           "every layer's routes stay visible. All renders are "
           "presented light-on-dark — bright layer colours on dark "
           "panels, the presentation the project owner asked for; "
           "drill holes are drawn in the panel tone so they read "
           "as holes in the pads around them.</p>"]
    for e in entries:
        st = e.get("stats") or {}
        nets = nr(st.get("nets_routed"))
        if st.get("nets_routed") is not None and st.get("nets_total"):
            nets = f"{st['nets_routed']} of {st['nets_total']}"
        rows = "".join([
            f"<tr><td>Nets fully routed</td><td>{nets}</td></tr>",
            f"<tr><td>Pins failed</td><td>{nr(st.get('pins_failed'))}"
            "</td></tr>",
            "<tr><td>Clearance violations</td><td>"
            f"{nr(st.get('clearance_violations'))}</td></tr>",
            f"<tr><td>Unconnected nets</td>"
            f"<td>{nr(st.get('unconnected_nets'))}</td></tr>",
            f"<tr><td>Audit verdict</td>"
            f"<td>{nr(st.get('audit_verdict'))}</td></tr>",
        ])
        renders = e.get("renders")
        layer_html = ""
        if renders and e.get("dir"):
            dst_dir = os.path.join(hist_assets, e["dir"])
            os.makedirs(dst_dir, exist_ok=True)
            # per-layer renders: composite stack + individual panels
            layers = e.get("layers") or {}
            copied = {}
            for layer in LAYER_ORDER:
                fn = layers.get(layer)
                src = os.path.join(ROOT, "history", e["dir"], fn) \
                    if fn else None
                if src and os.path.exists(src):
                    shutil.copy2(src, os.path.join(dst_dir, fn))
                    copied[layer] = fn
            if copied:
                stack = ""
                for i, layer in enumerate(
                        [l for l in LAYER_ORDER if l in copied]):
                    cls = "" if i == 0 else ' class="stack"'
                    stack += (f'<img{cls} src="assets/history/'
                              f'{e["dir"]}/{copied[layer]}" '
                              f'alt="{layer} layer">')
                legend = " ".join(
                    f'<span class="sw" style="background:'
                    f'{LAYER_PALETTE[layer]}"></span> {layer}'
                    for layer in LAYER_ORDER if layer in copied)
                panels = "".join(
                    f'<figure><img src="assets/history/{e["dir"]}/'
                    f'{copied[layer]}" alt="{layer} layer">'
                    f"<figcaption>{layer} — "
                    f"{LAYER_PALETTE[layer]}</figcaption></figure>"
                    for layer in LAYER_ORDER if layer in copied)
                layer_html = (
                    "<h4>Routes — all copper layers, stacked</h4>"
                    f'<div class="composite">{stack}</div>'
                    f'<p class="legend">{legend}</p>'
                    "<h4>Routes — each copper layer</h4>"
                    f'<div class="layergrid">{panels}</div>')
            imgs = ""
            for side in ("top", "bottom"):
                fn = renders.get(side)
                src = os.path.join(ROOT, "history", e["dir"], fn) \
                    if fn else None
                if src and os.path.exists(src):
                    shutil.copy2(src, os.path.join(dst_dir, fn))
                    imgs += (f"<h4>{side.capitalize()}</h4>"
                             f'<img class="refview" '
                             f'src="assets/history/{e["dir"]}/{fn}" '
                             f'alt="{html.escape(e.get("label", ""))} '
                             f'— {side}">')
                else:
                    imgs += (f"<p><em>{side} render missing from the "
                             "snapshot.</em></p>")
        else:
            imgs = ("<p><em>No board render — no board was committed "
                    "for this attempt (see note).</em></p>")
        note = (f"<p>{html.escape(e['note'])}</p>"
                if e.get("note") else "")
        out.append(
            f'<div class="attempt"><h3>{html.escape(e.get("label", ""))}'
            f"</h3><p>{html.escape(e.get('timestamp', ''))} UTC · "
            f"commit <code>{html.escape(e.get('short_hash', ''))}"
            f"</code> (<code>{html.escape(e.get('hash', ''))}</code>)"
            f"</p><table><tbody>{rows}</tbody></table>"
            f"{layer_html}{imgs}{note}"
            "</div>")
    return "\n".join(out)


def tia_plot():
    """Render the ngspice TIA AC response to PNG from its CSV, if the
    CSV exists (matplotlib is a declared project dependency)."""
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
        freq = data[cols[0]]
        mag = data[cols[1]]
        fig, ax = plt.subplots(figsize=(7, 3.2), dpi=130)
        ax.semilogx(freq / 1e6, mag)
        ax.axhline(-3, color="r", ls="--", lw=0.8)
        ax.set_xlabel("frequency (MHz)")
        ax.set_ylabel("gain (dB)")
        ax.set_title("OPA657 TIA AC response (ngspice macromodel)")
        ax.grid(True, which="both", alpha=0.3)
        out = os.path.join(ASSETS, "tia_ac.png")
        fig.savefig(out, bbox_inches="tight")
        plt.close(fig)
        return "tia_ac.png"
    except Exception as e:  # plot is decorative; never fail the build
        print(f"warning: TIA plot skipped ({e})")
        return None

def schematic_svg():
    dst = os.path.join(ASSETS, "schematic.svg")
    try:
        subprocess.run(["kicad-cli", "sch", "export", "svg", "-o", ASSETS,
                        os.path.join(ROOT, "hw", "pdlvds_rx.kicad_sch")],
                       check=True, capture_output=True, timeout=180)
        for f in os.listdir(ASSETS):
            if f.endswith(".svg") and "schematic" not in f:
                os.rename(os.path.join(ASSETS, f), dst)
        return "schematic.svg" if os.path.exists(dst) else None
    except Exception as e:
        print(f"warning: schematic SVG export skipped ({e})")
        return None

# ---------------------------------------------------------------- build
def main():
    if os.path.exists(SITE):
        shutil.rmtree(SITE)
    os.makedirs(ASSETS); os.makedirs(DOWNLOADS)

    dl = {}
    for src, name in [("hw/fab/gerbers.zip", "gerbers.zip"),
                      ("hw/fab/bom.csv", "bom.csv"),
                      ("hw/fab/cpl.csv", "cpl.csv"),
                      ("hw/fab/board-layers.pdf", "board-layers.pdf"),
                      ("results/schematic.pdf", "schematic.pdf")]:
        got = copy_into(src, DOWNLOADS, name)
        if got:
            dl[name] = got

    img = {}
    for src, name in [("hw/fab/board-top.svg", "board-top.svg"),
                      ("hw/fab/board-bottom.svg", "board-bottom.svg"),
                      ("results/link_budget.png", "link_budget.png"),
                      ("results/digital_sim.png", "digital_sim.png")]:
        got = copy_into(src, ASSETS, name)
        if got:
            img[name] = got
    layers = {}
    fab = os.path.join(ROOT, "hw", "fab")
    if os.path.isdir(fab):
        for f in sorted(os.listdir(fab)):
            if f.startswith("layer-") and f.endswith(".svg"):
                if copy_into(os.path.join("hw/fab", f), ASSETS, f):
                    layers[f[6:-4]] = f
    tia_png = tia_plot()
    if tia_png:
        img[tia_png] = tia_png
    sch_svg = schematic_svg()
    if sch_svg:
        img[sch_svg] = sch_svg

    # BOM table from the fab BOM CSV
    bom_html = "<p><em>BOM not generated — run scripts/make_fab.sh.</em></p>"
    bom_path = os.path.join(ROOT, "hw", "fab", "bom.csv")
    rows = []
    if os.path.exists(bom_path):
        with open(bom_path) as f:
            rows = list(csv.reader(f))
    if rows:
        n_parts = sum(int(r[1]) for r in rows[1:] if r and r[1].isdigit())
        t = ["<table><thead><tr>" + "".join(f"<th>{html.escape(c)}</th>"
             for c in rows[0]) + "</tr></thead><tbody>"]
        for r in rows[1:]:
            t.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>"
                                      for c in r) + "</tr>")
        t.append("</tbody></table>")
        bom_html = (f"<p>{len(rows) - 1} line items, {n_parts} placed "
                    f"parts.</p>" + "\n".join(t))

    # simulation / verification summary from results/
    def block(title, path, keys):
        lines = key_lines(path, keys)
        if not lines:
            return (f"<h3>{title}</h3><p><em>result file {path} not "
                    f"generated yet.</em></p>")
        body = "\n".join(html.escape(ln) for ln in lines)
        return f"<h3>{title}</h3><pre>{body}</pre>"

    sim_html = "\n".join([
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
    ])

    panel_html = status_panel()
    history_html = routing_history()

    req_html = md_to_html(read("docs/01-requirements.md")
                          or "_requirements doc missing_")
    arch_html = md_to_html(read("docs/02-architecture.md")
                           or "_architecture doc missing_")
    test_html = md_to_html(read("docs/05-test-plan.md")
                           or "_test plan missing_")

    def img_tag(name, alt):
        return (f'<img src="assets/{name}" alt="{alt}">'
                if name in img else
                f"<p><em>{alt} render not generated — run "
                f"scripts/make_fab.sh.</em></p>")

    layer_links = " · ".join(
        f'<a href="assets/{f}">{html.escape(lname)}</a>'
        for lname, f in sorted(layers.items())) or \
        "<em>per-layer SVGs not generated</em>"
    dl_links = " · ".join(
        f'<a href="downloads/{f}">{html.escape(n)}</a>'
        for n, f in sorted(dl.items())) or "<em>no downloads yet</em>"
    sch_link = ('<p><a href="downloads/schematic.pdf">Schematic PDF</a></p>'
                if "schematic.pdf" in dl else
                "<p><em>schematic PDF not generated</em></p>")
    sch_inline = (f'<img src="assets/schematic.svg" alt="schematic">'
                  if sch_svg else "")

    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PDLVDS-RX — photodiode LVDS receiver</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 0; color: #1a1a1a; }}
header {{ background: #14304d; color: #fff; padding: 1.2rem 2rem; }}
nav {{ background: #e8eef4; padding: .5rem 2rem; }}
nav a {{ margin-right: 1rem; }}
main {{ max-width: 62rem; margin: 0 auto; padding: 1rem 2rem 3rem; }}
img {{ max-width: 100%; border: 1px solid #ccc; }}
table {{ border-collapse: collapse; margin: .8rem 0; font-size: .92rem; }}
th, td {{ border: 1px solid #bbb; padding: .3rem .55rem; text-align: left; }}
th {{ background: #eef3f8; }}
pre {{ background: #f4f4f4; padding: .7rem; overflow-x: auto; }}
code {{ background: #f0f0f0; padding: 0 .25rem; }}
blockquote {{ border-left: 3px solid #99b; margin-left: 0;
  padding-left: 1rem; color: #444; }}
.badge {{ font-weight: 600; padding: .05rem .45rem; border-radius: .5rem; }}
.badge.pass {{ background: #d9ead3; color: #274e13; }}
.badge.fail {{ background: #f4cccc; color: #7a1f1f; }}
.badge.notrun {{ background: #e0e0e0; color: #555; }}
.composite {{ position: relative; background: #111; line-height: 0; }}
.composite img {{ display: block; width: 100%; border: none; }}
.composite img.stack {{ position: absolute; inset: 0; height: 100%;
  mix-blend-mode: screen; opacity: .55; }}
.legend .sw {{ display: inline-block; width: .8em; height: .8em;
  margin-left: .8em; }}
.legend .sw:first-child {{ margin-left: 0; }}
.layergrid {{ display: flex; flex-wrap: wrap; gap: .6rem; }}
.layergrid figure {{ flex: 1 1 9rem; margin: 0; }}
.layergrid img {{ background: #111; border: none; width: 100%;
  display: block; }}
.refview {{ background: #111; border: 1px solid #444; display: block;
  width: 100%; box-sizing: border-box; }}
.layergrid figcaption {{ font-size: .85rem; padding-top: .25rem; }}
</style></head><body>
<header><h1>PDLVDS-RX — photodiode LVDS receiver</h1>
<p>Clean-room receiver for the Miniscope Zero optical uplink:
Excelitas C30737LH Si APD → OPA657 TIA → LMH7220 comparator (LVDS out,
DAC-set threshold) → ADN2813 CDR → STM32H723 + USB3300 USB-HS.
50 Mbps line rate, 8b/10b (40 Mbps payload); legacy 8 Mbps Manchester
mode. LT3757 flyback APD bias 150–420 V. USB-C powered; verify on any
laptop over USB, no FPGA attached.</p></header>
<nav>
<a href="#summary">Summary</a><a href="#board">Board</a>
<a href="#routing-history">Routing history</a>
<a href="#schematic">Schematic</a><a href="#stackup">Stackup</a>
<a href="#bom">BOM</a><a href="#sims">Simulations</a>
<a href="#testplan">Bench test plan</a><a href="#downloads">Downloads</a>
</nav>
<main>
<section id="summary"><h2>Project summary</h2>
<p>Design status and stage-by-stage evidence live in the repository
(<code>docs/00-status.md</code>); open risks and the bring-up plan in
<code>docs/04-risks.md</code>. Everything on this page is generated
from the repository's own verified artefacts by
<code>scripts/build_site.py</code>.</p>
{panel_html}
{req_html}
{arch_html}
</section>
<section id="board"><h2>PCB — top and bottom</h2>
<h3>Top</h3>{img_tag("board-top.svg", "PCB top")}
<h3>Bottom</h3>{img_tag("board-bottom.svg", "PCB bottom")}
<p>Per-layer SVG: {layer_links}</p>
</section>
<section id="routing-history"><h2>Routing history</h2>
{history_html}
</section>
<section id="schematic"><h2>Schematic</h2>
{sch_link}{sch_inline}
</section>
<section id="stackup"><h2>Stackup and impedance</h2>
<table><thead><tr><th>Layer</th><th>Use</th><th>Notes</th></tr></thead>
<tbody>
<tr><td>F.Cu</td><td>signals + GND pour</td>
<td>50 Ω SE width 0.405 mm</td></tr>
<tr><td>In1.Cu</td><td>solid GND plane</td><td>reference for all routing</td></tr>
<tr><td>In2.Cu</td><td>signals</td>
<td>100 Ω diff pairs: W 0.300 mm / gap 0.349 mm</td></tr>
<tr><td>B.Cu</td><td>signals + GND pour</td><td></td></tr>
</tbody></table>
<p>Stackup: JLCPCB JLC04161H-7628, 4-layer, 1.6 mm, Er 4.4,
prepreg height 0.2104 mm. Geometry from <code>sim/impedance.py</code>
(Hammerstad–Jansen / Wadell); propagation delay 6.02 ps/mm, length
matching within 0.5 mm on LVDS pairs.</p>
</section>
<section id="bom"><h2>Bill of materials</h2>
{bom_html}
</section>
<section id="sims"><h2>Simulation and verification results</h2>
{sim_html}
<h3>Link budget — BER vs incident power</h3>
{img_tag("link_budget.png", "link budget plot")}
<h3>TIA AC response (ngspice)</h3>
{img_tag("tia_ac.png", "TIA AC response")}
<h3>Digital simulation</h3>
{img_tag("digital_sim.png", "digital simulation plot")}
</section>
<section id="testplan"><h2>Bench test plan</h2>
{test_html}
</section>
<section id="downloads"><h2>Fabrication downloads</h2>
<p>{dl_links}</p>
<p>Gerbers + drill are in <code>gerbers.zip</code>; BOM and CPL
(position) CSVs are the same files tabulated above.</p>
</section>
</main></body></html>"""
    with open(os.path.join(SITE, "index.html"), "w") as f:
        f.write(page)
    total = 0
    for dirpath, _, files in os.walk(SITE):
        for fn in files:
            total += os.path.getsize(os.path.join(dirpath, fn))
    print(f"site built: {SITE} ({total/1024:.0f} KiB, "
          f"{len(img)} images, {len(dl)} downloads)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
