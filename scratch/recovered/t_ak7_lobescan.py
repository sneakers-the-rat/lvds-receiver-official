"""t_ak7: SE-lobe margin landscape for an XO d0.5 dive under a few
variable combos of the t_ak6 model. Reports best points + blockers."""
import sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ak')
from t_ai_lib import pt_margin, in_box_pool, fmt_it
import importlib.util
spec = importlib.util.spec_from_file_location(
    't6', 'scratch/work/ak/t_ak6_solve.py')
# t_ak6 runs its search at import; instead re-implement minimal pieces:
