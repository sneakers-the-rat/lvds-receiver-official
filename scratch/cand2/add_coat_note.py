import pcbnew
p = 'scratch/cand2/pdlvds_rx.kicad_pcb'
b = pcbnew.LoadBoard(p)
t = pcbnew.PCB_TEXT(b)
t.SetLayer(pcbnew.Dwgs_User)
t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(2.0), pcbnew.FromMM(-38.0)))
t.SetText("FAB/ASSEMBLY NOTE: CONFORMAL COAT REQUIRED over the HV bias\n"
          "island (APD + boost converter area, west side) after assembly.\n"
          "HV spacing design basis: IPC-2221B Table 6-1 B4 (coated).\n"
          "See docs/14-build-guide.md.")
t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.5), pcbnew.FromMM(1.5)))
b.Add(t)
b.Save(p)
print('coat note added on Dwgs.User')
