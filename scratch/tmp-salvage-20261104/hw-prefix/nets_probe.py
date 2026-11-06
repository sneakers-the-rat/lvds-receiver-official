#!/usr/bin/env python3
"""Probe: print pad nets for a list of refs (supplement verification).
Usage: xvfb-run -a python3 hw/nets_probe.py <board> REF [REF ...]"""
import sys
import pcbnew


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    for ref in sys.argv[2:]:
        fp = fps[ref]
        pads = ["%s:%s" % (p.GetNumber(), p.GetNetname() or "-")
                for p in fp.Pads()]
        print("%-5s %s" % (ref, " ".join(pads)))


if __name__ == "__main__":
    main()
