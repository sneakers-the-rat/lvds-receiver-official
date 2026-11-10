"""t_az8: exact item dumps for the design phase."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')
LN = {0: 'F', 1: 'In2', 2: 'B'}


def dump(title, pred):
    print(f'##### {title}')
    for l in range(3):
        for it in pool[l]:
            if pred(l, it):
                print(f'  {LN[l]} {L.fmt_it(it)} clr={it[3]}')


def ctr_in(x0, x1, y0, y1):
    def f(l, it):
        p = C(it)
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    return f


dump('+3V3A In2 web x[76,79] y[9,17]',
     lambda l, it: it[1] == '+3V3A' and l == 1
     and ctr_in(76.0, 79.0, 9.0, 17.0)(l, it))
dump('PHY_1V8A all x[70,78] y[9,16]',
     lambda l, it: it[1] == 'PHY_1V8A' and ctr_in(70, 78, 9, 16)(l, it))
dump('ULPI_DIR In2 x[70,80] y[12,20]',
     lambda l, it: it[1] == 'ULPI_DIR' and l == 1
     and ctr_in(70, 80, 12, 20)(l, it))
dump('ULPI_NXT In2 x[70,80] y[12,20]',
     lambda l, it: it[1] == 'ULPI_NXT' and l == 1
     and ctr_in(70, 80, 12, 20)(l, it))
dump('ULPI_CK In2 x[70,80] y[5,20]',
     lambda l, it: it[1] == 'ULPI_CK' and l == 1
     and ctr_in(70, 80, 5, 20)(l, it))
dump('XO all x[74,78] y[8,13]',
     lambda l, it: it[1] == 'XO' and ctr_in(74, 78, 8, 13)(l, it))
dump('ULPI_STP In2 x[70,80] y[9,20]',
     lambda l, it: it[1] == 'ULPI_STP' and l == 1
     and ctr_in(70, 80, 9, 20)(l, it))
dump('south band B x[64,92] y[-2,8] (non-GND segs/vias)',
     lambda l, it: l == 2 and it[0] in ('seg', 'via') and it[1] != 'GND'
     and ctr_in(64, 92, -2, 8)(l, it))
dump('south band In2 x[64,92] y[-2,8] (non-GND segs/vias)',
     lambda l, it: l == 1 and it[0] in ('seg', 'via') and it[1] != 'GND'
     and ctr_in(64, 92, -2, 8)(l, it))
print('=== done ===')
