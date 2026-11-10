#!/usr/bin/env python3
"""Phase B extractor — script recovery, corrected scope (REDO).

Extracts every .py/.sh file written by EXACTLY the 94 sessions listed in
scratch/recovered/MANIFEST.md (Phase A set), from their session JSONL files
under /home/hatch/agents/. Nothing else is a source: membership is the
manifest list, full stop.

Method
- Records: {"type":"item","seq":N,"created_at":ISO,"item":{"type":
  "function_call","call_id":...,"name":"write|edit|exec","arguments":JSON}}.
- Ownership: child session files carry fork copies of ancestor transcripts
  (original seq + call_id preserved, created_at re-stamped to fork time).
  For each call_id, the instance with the earliest created_at across the
  94 files is the owner's genuine record. Calls owned by the root agent
  (4925d244..., NOT in the set) are excluded via an oracle pass over the
  root session file's call_ids (exclusion only — nothing is extracted
  from it; same census technique Phase A used for the main-chat session).
- Per session, owned write/edit/exec-heredoc ops on .py/.sh paths are
  replayed in timestamp order to session-final content:
  write(overwrite) sets content; write(append) appends; edit replaces the
  first occurrence of old_text; a heredoc (cat/tee with > or >>) sets or
  appends verbatim body text. An edit whose old_text is absent, an edit or
  append on an unknown base, or a truncated record makes the path's final
  state PARTIAL (content = last good state) or UNRECOVERABLE (no state),
  with the divergence named.
- Candidates are deduplicated by sha256 against every .py/.sh blob in
  origin/main's history plus every .py/.sh file in the split worktree.

Outputs (under /tmp/phaseb/):
- staging/<sha256>          candidate contents (whole and partial)
- extract.json               full metadata: candidates, partials,
                             unrecoverable, diagnostics
Local files only. No muse.db.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

REPO = os.path.expanduser("~/workspace/pdlvds-split")
MANIFEST = os.path.join(REPO, "scratch/recovered/MANIFEST.md")
AGENTS_DIR = "/home/hatch/agents"
ROOT_AGENT = "4925d244-018c-4b4f-9fad-7b3ad78af7c1"
OUT = "/tmp/phaseb"
STAGING = os.path.join(OUT, "staging")
HOME = "/home/hatch"

HEREDOC_RE = re.compile(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")
CD_RE = re.compile(r"(?:^|&&|;|\|\|)\s*cd\s+([^\s;&|]+)")
TARGET_REDIR_RE = re.compile(r"(>>?)\s*([^\s;|&<>]+)")
CATTEE_RE = re.compile(r"\b(?:cat|tee)\b([^<>|;&\n]*)")


def session_ids():
    ids = []
    for line in open(MANIFEST):
        m = re.match(r"\| \d+ \| `([0-9a-f-]{36})`", line)
        if m:
            ids.append(m.group(1))
    return ids


def session_path(agent):
    return os.path.join(AGENTS_DIR, "agent-" + agent, "sessions", agent + ".jsonl")


def iter_calls(path):
    """Yield (line_no, seq, created_at, call_id, name, arguments_str)."""
    with open(path, "rb") as f:
        for line_no, raw in enumerate(f):
            if b'"function_call"' not in raw:
                continue
            try:
                r = json.loads(raw)
            except Exception:
                continue
            it = r.get("item") or {}
            if it.get("type") != "function_call":
                continue
            yield (line_no, r.get("seq"), r.get("created_at"),
                   it.get("call_id"), it.get("name"), it.get("arguments"))


def oracle_call_ids():
    ids = set()
    p = session_path(ROOT_AGENT)
    if os.path.exists(p):
        for (_ln, _seq, _ts, cid, _nm, _args) in iter_calls(p):
            if cid:
                ids.add(cid)
    return ids


def norm_path(p, cwd=None):
    p = p.strip().strip("'\"")
    if p.startswith("~/"):
        p = os.path.join(HOME, p[2:])
    elif p == "~":
        p = HOME
    elif not p.startswith("/"):
        p = os.path.join(cwd or HOME, p)
    return os.path.normpath(p)


def parse_heredocs(command):
    """Return list of (target_raw, append_bool, body, cwd) for heredocs
    whose command segment invokes cat/tee with a resolvable target."""
    out = []
    lines = command.split("\n")
    i = 0
    cwd = None
    while i < len(lines):
        line = lines[i]
        for cd in CD_RE.finditer(line):
            cwd = norm_path(cd.group(1), cwd)
        m = HEREDOC_RE.search(line)
        if not m:
            i += 1
            continue
        delim = m.group(1)
        seg = line[:m.start()]
        if not re.search(r"\b(?:cat|tee)\b", seg):
            i += 1
            continue
        append = False
        target = None
        rm = TARGET_REDIR_RE.search(seg)
        if rm:
            append = rm.group(1) == ">>"
            target = rm.group(2)
        else:
            cm = CATTEE_RE.search(seg)
            if cm:
                toks = [t for t in cm.group(1).split() if not t.startswith("-")]
                if toks:
                    target = toks[0]
                if re.search(r"\btee\b[^<>|;&\n]*\s-a\b", seg) or \
                   re.search(r"\btee\s+-\w*a", seg):
                    append = True
        body_lines = []
        j = i + 1
        while j < len(lines) and lines[j].strip() != delim:
            body_lines.append(lines[j])
            j += 1
        if target and j < len(lines):
            body = "".join(l + "\n" for l in body_lines)
            out.append((target, append, body, cwd))
            i = j + 1
        else:
            i += 1
    return out


def main():
    os.makedirs(STAGING, exist_ok=True)
    ids = session_ids()
    print("set size:", len(ids))
    oracle = oracle_call_ids()
    print("root-owned call_ids in oracle:", len(oracle))

    # ---- pass 1: ownership resolution across the 94 files
    best = {}          # call_id -> (ts, agent, line_no, seq, name, args)
    parse_fail_lines = {}
    for agent in ids:
        p = session_path(agent)
        fails = 0
        with open(p, "rb") as f:
            raw_lines = f.readlines()
        for line_no, raw in enumerate(raw_lines):
            if b'"function_call"' in raw:
                try:
                    json.loads(raw)
                except Exception:
                    fails += 1
        parse_fail_lines[agent] = fails
        for (line_no, seq, ts, cid, name, args) in iter_calls(p):
            if cid is None or name not in ("write", "edit", "exec"):
                continue
            cur = best.get(cid)
            if cur is None or (ts or "") < cur[0]:
                best[cid] = (ts, agent, line_no, seq, name, args)
    owned = {}
    n_root_owned = 0
    for cid, (ts, agent, line_no, seq, name, args) in best.items():
        if cid in oracle:
            n_root_owned += 1
            continue
        owned.setdefault(agent, []).append(
            {"ts": ts, "line": line_no, "seq": seq, "name": name,
             "args": args, "call_id": cid})
    print("owned ops kept:", sum(len(v) for v in owned.values()),
          "| root-owned excluded:", n_root_owned)

    # ---- pass 2: per-session replay
    candidates = {}    # sha -> {content_meta...}
    partials = {}      # sha -> meta (content is last-good state)
    unrecoverable = [] # {agent, path, reason, seq}
    diag = {"heredoc_unresolved": 0, "ops": 0, "paths_touched": 0}

    def register(state, agent, path):
        content = state["content"]
        sha = hashlib.sha256(content.encode()).hexdigest()
        kind = "partial" if state["diverged"] else "whole"
        book = partials if state["diverged"] else candidates
        ent = book.setdefault(sha, {"sha256": sha, "paths": set(),
                                    "records": []})
        ent["paths"].add(path)
        ent["records"].append({
            "agent": agent, "path": path,
            "seq": state["last_seq"], "line": state["last_line"],
            "ts": state["last_ts"], "kind": kind,
            "reconstruction": state["label"],
            "divergence": state["divergence"]})
        with open(os.path.join(STAGING, sha), "w") as f:
            f.write(content)

    for agent in ids:
        ops = sorted(owned.get(agent, []),
                     key=lambda o: (o["ts"] or "", o["seq"] or 0, o["line"]))
        states = {}    # path -> state dict
        for op in ops:
            diag["ops"] += 1
            try:
                args = json.loads(op["args"]) if op["args"] else {}
            except Exception:
                args = None
            if op["name"] in ("write", "edit"):
                if args is None:
                    m = re.search(r'"path"\s*:\s*"([^"]+)"', op["args"] or "")
                    if m and (m.group(1).endswith(".py") or
                              m.group(1).endswith(".sh")):
                        pth = norm_path(m.group(1))
                        st = states.setdefault(pth, blank_state())
                        st["diverged"] = True
                        st["divergence"] = ("record truncated in transcript "
                                            "(arguments unparseable)")
                        st.update(last_of(op))
                    continue
                raw_path = args.get("path") or ""
                if not (raw_path.endswith(".py") or raw_path.endswith(".sh")):
                    continue
                pth = norm_path(raw_path)
                st = states.setdefault(pth, blank_state())
                if op["name"] == "write":
                    content = args.get("content")
                    if content is None:
                        st["diverged"] = True
                        st["divergence"] = "write record missing content"
                        st.update(last_of(op))
                        continue
                    if args.get("mode") == "append":
                        if st["content"] is None:
                            st["diverged"] = True
                            st["divergence"] = "append on unknown base"
                        else:
                            st["content"] += content
                            st["label"] = join_label(st["label"], "append")
                    else:
                        st["content"] = content
                        st["diverged"] = False
                        st["divergence"] = None
                        st["label"] = "muse.write"
                    st.update(last_of(op))
                else:  # edit
                    old, new = args.get("old_text"), args.get("new_text")
                    if st["content"] is None:
                        st["diverged"] = True
                        st["divergence"] = "edit on unknown base"
                        st.update(last_of(op))
                    elif old is None or old not in st["content"]:
                        st["diverged"] = True
                        st["divergence"] = ("edit old_text not found in "
                                            "replayed state")
                        st.update(last_of(op))
                    else:
                        st["content"] = st["content"].replace(old, new, 1)
                        st["label"] = bump_edit(st["label"])
                        st.update(last_of(op))
            else:  # exec -> heredocs
                cmd = (args or {}).get("command") if args else None
                if not cmd:
                    continue
                for (target, append, body, cwd) in parse_heredocs(cmd):
                    if not (target.endswith(".py") or target.endswith(".sh")):
                        continue
                    pth = norm_path(target, cwd)
                    st = states.setdefault(pth, blank_state())
                    if append:
                        if st["content"] is None:
                            st["diverged"] = True
                            st["divergence"] = "heredoc append on unknown base"
                        else:
                            st["content"] += body
                            st["label"] = join_label(st["label"],
                                                     "heredoc append")
                    else:
                        st["content"] = body
                        st["diverged"] = False
                        st["divergence"] = None
                        st["label"] = "exec heredoc"
                    st.update(last_of(op))
        diag["paths_touched"] += len(states)
        for pth, st in states.items():
            if st["content"] is None:
                unrecoverable.append({
                    "agent": agent, "path": pth,
                    "reason": st["divergence"] or "no establishing write",
                    "seq": st.get("last_seq"), "line": st.get("last_line"),
                    "ts": st.get("last_ts")})
            else:
                register(st, agent, pth)

    # ---- dedupe against committed corpus
    committed = committed_hashes()
    print("committed corpus (.py/.sh sha256):", len(committed))
    result = {"candidates": [], "partials": [], "already_committed": [],
              "unrecoverable": unrecoverable, "diagnostics": diag,
              "parse_fail_lines": parse_fail_lines,
              "root_owned_excluded": n_root_owned}
    for book, key in ((candidates, "candidates"), (partials, "partials")):
        for sha, ent in book.items():
            ent["paths"] = sorted(ent["paths"])
            ent["records"].sort(key=lambda r: (r["ts"] or ""))
            if sha in committed:
                result["already_committed"].append(ent)
            else:
                result[key].append(ent)
    with open(os.path.join(OUT, "extract.json"), "w") as f:
        json.dump(result, f, indent=1)
    print("distinct whole contents:", len(candidates),
          "| partial contents:", len(partials),
          "| already committed:", len(result["already_committed"]),
          "| landed whole:", len(result["candidates"]),
          "| landed partial:", len(result["partials"]),
          "| unrecoverable paths:", len(unrecoverable))
    print("diagnostics:", diag)


def blank_state():
    return {"content": None, "diverged": False, "divergence": None,
            "label": None, "last_seq": None, "last_line": None,
            "last_ts": None}


def last_of(op):
    return {"last_seq": op["seq"], "last_line": op["line"],
            "last_ts": op["ts"]}


def join_label(label, kind):
    return (label + " + " + kind) if label else kind


def bump_edit(label):
    if not label:
        return "edit"
    m = re.search(r"\+ (\d+) edits? replayed", label)
    if m:
        return label[:m.start()] + "+ %d edits replayed" % (int(m.group(1)) + 1)
    return label + " + 1 edit replayed"


def committed_hashes():
    hashes = set()
    out = subprocess.run(
        ["git", "-C", REPO, "rev-list", "--objects", "origin/main"],
        capture_output=True, text=True, check=True).stdout
    blob_ids = []
    for line in out.splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2 and (parts[1].endswith(".py") or
                                parts[1].endswith(".sh")):
            blob_ids.append(parts[0])
    print("history .py/.sh blobs:", len(blob_ids))
    if blob_ids:
        proc = subprocess.Popen(
            ["git", "-C", REPO, "cat-file", "--batch"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        for bid in blob_ids:
            proc.stdin.write((bid + "\n").encode())
            proc.stdin.flush()
            header = proc.stdout.readline().decode().split()
            if len(header) < 3 or header[1] != "blob":
                continue
            size = int(header[2])
            data = proc.stdout.read(size)
            proc.stdout.read(1)
            hashes.add(hashlib.sha256(data).hexdigest())
        proc.stdin.close()
        proc.wait()
    n_disk = 0
    for root, dirs, files in os.walk(REPO):
        if ".git" in root.split(os.sep):
            continue
        dirs[:] = [d for d in dirs if d != ".git"]
        for fn in files:
            if fn.endswith(".py") or fn.endswith(".sh"):
                with open(os.path.join(root, fn), "rb") as f:
                    hashes.add(hashlib.sha256(f.read()).hexdigest())
                n_disk += 1
    print("worktree .py/.sh files hashed:", n_disk)
    return hashes


if __name__ == "__main__":
    sys.exit(main())
