#!/usr/bin/env python3
"""Regression test: commit_pass.py must never audit/render a board
the pass did not produce.

Defect (pass 80, first attempt): commit_pass.py defaulted --board
to hw/pdlvds_rx.kicad_pcb — the pre-expansion base board — so a
pass committed with no --board recorded an audit of a board that
was not the pass's board (83 nets / 64 violations against the base
board, superseding record kept in the pass-80 commit). The fix:
--board defaults to None; resolve_board() auto-selects the newest
hw/pdlvds_rx.exp<N>.kicad_pcb (the board the latest work produced)
or refuses. It NEVER falls back to the base board silently; the
base board remains selectable only by explicit --board.

Run: python3 hw/tests/test_commit_pass_board.py
Pre-fix: FAIL (resolve_board / parse_args do not exist).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                '..', '..', 'scripts'))
import commit_pass  # noqa: E402

fails = []

def check(name, cond):
    print(('PASS' if cond else 'FAIL'), name)
    if not cond:
        fails.append(name)

def touch(d, name):
    p = os.path.join(d, name)
    open(p, 'w').close()
    return p

with tempfile.TemporaryDirectory() as d:
    base = touch(d, 'pdlvds_rx.kicad_pcb')
    touch(d, 'pdlvds_rx.exp16.kicad_pcb')
    newest = touch(d, 'pdlvds_rx.exp21.kicad_pcb')
    touch(d, 'pdlvds_rx.exp6n.kicad_pcb')
    touch(d, 'pdlvds_rx.expanded.kicad_pcb')
    got = commit_pass.resolve_board(None, d)
    check('omitted --board auto-selects newest exp board',
          got == os.path.abspath(newest))
    check('explicit --board is honoured verbatim',
          commit_pass.resolve_board(base, d) == os.path.abspath(base))

with tempfile.TemporaryDirectory() as d:
    touch(d, 'pdlvds_rx.kicad_pcb')
    try:
        commit_pass.resolve_board(None, d)
        check('base-board-only tree refuses', False)
    except SystemExit:
        check('base-board-only tree refuses', True)

check('argparse default for --board is None',
      commit_pass.parse_args(['x']).board is None)

print('FAILURES:', fails if fails else 'none')
sys.exit(1 if fails else 0)
