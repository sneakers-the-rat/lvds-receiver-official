#!/usr/bin/env python3
"""Secrets screen for the Phase B landing set (gate 1).

Screens EXACTLY the files about to be landed (the to-land sha256 set from
/tmp/phaseb/extract.json, staged under /tmp/phaseb/staging/) for
credential shapes BEFORE any push:

- Tier 1 (hard shapes): ghp_, github_pat_, AKIA..., xox[baprs]-,
  sk-, AIza..., PEM private-key blocks. Any hit stops the landing.
- Tier 2 (named assignments): a long literal assigned to a
  TOKEN/SECRET/PASSWORD/API_KEY-named variable. Reported as variable
  name + value length + entropy class only — the value itself is never
  printed. A tier-2 hit that does not look like a placeholder/test
  string also stops the landing.

Also produces a keyword census (files merely mentioning token/secret/
password/api-key) for the manifest's screen section, and writes that
section to /tmp/phaseb/screen_section.md.

Exit code 0 = clear to land; 1 = STOP (hits listed, values never shown).
"""
import hashlib
import json
import math
import os
import re
import sys

STAGING = "/tmp/phaseb/staging"
EXTRACT = "/tmp/phaseb/extract.json"

TIER1 = [
    ("ghp_token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("openai_style_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_-]{20,}")),
    ("private_key_block", re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH |PGP |DSA )?PRIVATE KEY-----")),
]
TIER2 = re.compile(
    r"(?i)(token|secret|password|passwd|api[_-]?key|auth[_-]?key|"
    r"access[_-]?key)\s*[:=]\s*['\"]([^'\"]{16,})['\"]")
KEYWORD = re.compile(r"(?i)token|secret|password|passwd|api[_-]?key|"
                     r"credential|bearer")
PLACEHOLDER = re.compile(
    r"(?i)example|test|dummy|changeme|your[_-]|xxx|placeholder|sample|"
    r"redacted|todo|none|null|fake|mock")


def entropy(s):
    if not s:
        return 0.0
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def main():
    d = json.load(open(EXTRACT))
    shas = [e["sha256"] for e in d["candidates"]] + \
           [e["sha256"] for e in d["partials"]]
    tier1_hits, tier2_flags, keyword_files = [], [], {}
    for sha in shas:
        text = open(os.path.join(STAGING, sha), encoding="utf-8",
                    errors="replace").read()
        names = set()
        for e in d["candidates"] + d["partials"]:
            if e["sha256"] == sha:
                names = {os.path.basename(p) for p in e["paths"]}
        label = "/".join(sorted(names)) or sha[:8]
        for cls, rx in TIER1:
            if rx.search(text):
                tier1_hits.append((label, cls))
        for m in TIER2.finditer(text):
            var, val = m.group(1), m.group(2)
            ph = bool(PLACEHOLDER.search(val))
            ent = entropy(val)
            tier2_flags.append((label, var, len(val), round(ent, 2), ph))
        kw = len(KEYWORD.findall(text))
        if kw:
            keyword_files[label] = kw
    lines = []
    lines.append("Screened the exact landing set (%d files) before any "
                 "push." % len(shas))
    lines.append("- Tier-1 credential shapes (ghp_, github_pat_, AKIA, "
                 "xox*, sk-, AIza, private-key blocks): **%d hits**."
                 % len(tier1_hits))
    for label, cls in tier1_hits:
        lines.append("  - HIT %s — %s" % (label, cls))
    real_t2 = [t for t in tier2_flags if not t[4] and t[3] >= 3.0]
    lines.append("- Tier-2 named-variable long literals: %d found, %d "
                 "placeholder/test-class, %d requiring stop-and-report."
                 % (len(tier2_flags), len(tier2_flags) - len(real_t2),
                    len(real_t2)))
    for label, var, ln, ent, ph in tier2_flags:
        lines.append("  - %s — variable `%s`, literal length %d, entropy "
                     "%.2f, %s" % (label, var, ln, ent,
                                   "placeholder-class" if ph else
                                   "REVIEWED-STOP" if (label, var, ln, ent, ph) in real_t2 or (not ph and ent >= 3.0) else "low-entropy"))
    lines.append("- Keyword-level mentions (code referring to tokens/"
                 "secrets, no credential value): %d files — %s"
                 % (len(keyword_files),
                    ", ".join(sorted(keyword_files)) or "none"))
    section = "\n".join(lines) + "\n"
    with open("/tmp/phaseb/screen_section.md", "w") as f:
        f.write(section)
    print(section)
    if tier1_hits or real_t2:
        print("STOP: shape hits present — do not land.")
        return 1
    print("SCREEN CLEAR.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
