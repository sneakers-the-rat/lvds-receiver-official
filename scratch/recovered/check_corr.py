import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import check_pcb
check_pcb.HV_NETS = {"APD_K", "HV_RAW", "HV_SEC", "TP_HV", "HV_R29M",
                     "HV_R30M", "HV_R31A", "HV_R31B", "HV_OVP1", "HV_OVP2"}
check_pcb.main(sys.argv[1])
