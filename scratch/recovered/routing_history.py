def routing_history():
    """Render the routing-evolution gallery from history/passes.json.

    One entry per layout pass, in pass order. Each pass's renders are
    the image files committed with that pass (history/<dir>/) copied
    into assets/history/<dir>/ — the site never re-renders an old
    board with current code, so this section builds identically from
    any commit's tree alone. Passes without committed renders show an
    explicit note instead of an image. Stats that were never recorded
    show as "not recorded" — never interpolated. With no pass log at
    all, the section still builds with a placeholder line."""
    pj_path = os.path.join(ROOT, "history", "passes.json")
    if not os.path.exists(pj_path):
        return ("<p><em>No passes recorded yet — run "
                "<code>scripts/commit_pass.py</code> when a routing "
                "run produces a new board state.</em></p>")
    try:
        doc = json.load(open(pj_path))
        entries = doc["passes"]
    except Exception as e:
        return f"<p><em>history/passes.json unreadable ({e}).</em></p>"
    if not entries:
        return ("<p><em>No passes recorded yet — run "
                "<code>scripts/commit_pass.py</code> when a routing "
                "run produces a new board state.</em></p>")
    hist_assets = os.path.join(ASSETS, "history")
    os.makedirs(hist_assets, exist_ok=True)

    def nr(v):
        return "not recorded" if v is None else str(v)

    out = ["<p>Every layout pass, in order — one counter for the "
           "whole project, including the passes that failed. Strategy "
           "changes are the changelog lines under each pass number. "
           "Passes live in <code>history/</code> in the repository, "
           "one directory per pass, committed by "
           "<code>scripts/commit_pass.py</code> at the moment the "
           "board state existed; the renders below are those "
           "committed image files, never re-rendered. The renders are "
           "route-only: tracks, vias and pads, with zone fills (the "
           "opaque GND pours) removed — each snapshot is exported "
           "from a temp copy of the board with its zones deleted, so "
           "every layer's routes stay visible. All renders are "
           "presented light-on-dark — bright layer colours on dark "
           "panels, the presentation the project owner asked for; "
           "drill holes are drawn in the panel tone so they read "
           "as holes in the pads around them. Runs whose boards were "
           "never committed hold no pass number — they are listed as "
           "gaps in <code>history/PASSES.md</code>.</p>"]
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
                             f'alt="Pass {e.get("pass", "")} '
                             f'— {side}">')
                else:
                    imgs += (f"<p><em>{side} render missing from the "
                             "snapshot.</em></p>")
        else:
            imgs = ("<p><em>No renders were committed for this "
                    "pass.</em></p>")
        desc = (f"<p>{html.escape(e['description'])}</p>"
                if e.get("description") else "")
        note = (f"<p>{html.escape(e['note'])}</p>"
                if e.get("note") else "")
        out.append(
            f'<div class="attempt"><h3>Pass {e.get("pass", "")}</h3>'
            f"<p>{html.escape(e.get('timestamp', ''))} UTC · "
            f"commit <code>{html.escape(e.get('short_hash') or '')}"
            f"</code> (<code>{html.escape(e.get('hash') or '')}"
            f"</code>)</p>{desc}"
            f"<table><tbody>{rows}</tbody></table>"
            f"{layer_html}{imgs}{note}"
            "</div>")
    return "\n".join(out)


