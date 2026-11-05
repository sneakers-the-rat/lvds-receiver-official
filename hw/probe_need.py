import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp42.kicad_pcb')
for a, b in [('SET_P', '+5V'), ('SET_P', 'GND'), ('+3V3A', 'GND'),
             ('+5V', 'GND'), ('DP_PHY', 'GND'), ('SET_A', '+5V'),
             ('CC2', 'VBUS_RAW'), ('HV_INTVCC', 'GND'),
             ('+3V3D_CDR', 'GND'), ('CDR_PIN', 'CDR_NIN'),
             ('HV_SS', 'HV_FBX'), ('PHY_1V8', '+3V3A')]:
    print(f'need({a},{b}) surf={check_pcb.need_for(a, b, {pcbnew.F_Cu})} '
          f'clr({a})={check_pcb.clearance_for(a)} clr({b})={check_pcb.clearance_for(b)}')
print('HV_NETS has SET_P:', 'SET_P' in check_pcb.HV_NETS)
import re
print([n for n in check_pcb.HV_NETS if 'SET' in n or 'ILIM' in n])
