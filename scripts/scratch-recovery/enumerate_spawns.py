#!/usr/bin/env python3
"""Enumerate subagent.spawn lineage from session JSONL transcripts.

Phase A of the corrected script-recovery: build the set of sessions spawned
FOR the PCB project from spawn records alone (no muse.db; local JSONL only).

Usage: enumerate_spawns.py SESSION.jsonl [SESSION.jsonl ...]
Emits one JSON object per spawn to stdout:
  {parent, child, spawned_at, seq, brief}
where brief is the full spawn message text (the tasking brief).
Spawns whose result carried no agent_id are emitted with child=null.
"""
import json, sys, glob, os

def brief_of(args_raw):
    try:
        args = json.loads(args_raw)
    except Exception:
        return ""
    if isinstance(args.get("message"), str):
        return args["message"]
    items = args.get("items") or []
    parts = [it.get("text", "") for it in items if isinstance(it, dict) and it.get("type") == "text"]
    return "\n".join(p for p in parts if p)

def spawns_in(path):
    calls = {}   # call_id -> (created_at, seq, brief)
    order = []
    outs = {}    # call_id -> agent_id or None
    with open(path) as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            it = r.get("item") or {}
            if it.get("type") == "function_call" and it.get("name") == "subagent.spawn":
                calls[it["call_id"]] = (r.get("created_at"), r.get("seq"), brief_of(it.get("arguments") or ""))
                order.append(it["call_id"])
            elif it.get("type") == "function_call_output" and it.get("call_id") in calls or (
                it.get("type") == "function_call_output" and it.get("call_id") not in outs and it.get("call_id")):
                raw = it.get("output")
                aid = None
                if isinstance(raw, str):
                    try:
                        aid = json.loads(raw).get("agent_id")
                    except Exception:
                        aid = None
                if it.get("call_id") in calls:
                    outs[it["call_id"]] = aid
    parent = os.path.basename(path).replace(".jsonl", "")
    for cid in order:
        ts, seq, brief = calls[cid]
        yield {"parent": parent, "child": outs.get(cid), "spawned_at": ts, "seq": seq, "brief": brief}

def session_file(agent_id):
    hits = sorted(glob.glob(f"/home/hatch/agents/agent-{agent_id}/sessions/*.jsonl"))
    return hits[0] if hits else None

if __name__ == "__main__":
    for p in sys.argv[1:]:
        for row in spawns_in(p):
            print(json.dumps(row))
