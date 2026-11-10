#!/usr/bin/env python3
"""Chain 3: small-disc clear + immediate audit-exact stub, per site,
then a healing repairg run. Each site: clear_disc rounds of 25
until the disc is empty of foreign copper, then hand_stub the
site's targets on the cleared field (victims heal afterwards)."""
import subprocess, sys, os
os.chdir(os.path.expanduser('~/workspace/photodiode-lvds-rx'))
env = dict(os.environ, DISPLAY=':99')

def run(cmd, log):
    with open(log, 'a') as f:
        f.write('$ ' + ' '.join(cmd) + '\n')
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT,
                           env=env)
    return r.returncode

def clear(board_in, board_out, cx, cy, rad, log):
    src = board_in
    for i in range(8):
        out = f'/tmp/chain3-clear-{i}.kicad_pcb'
        run(['python3', '-u', 'hw/clear_disc.py', src, out,
             str(cx), str(cy), str(rad), '25', 'KEEP_NONE'], log)
        txt = open(log).read().strip().splitlines()
        last = [l for l in txt if 'clear_disc:' in l][-1]
        print(last, flush=True)
        src = out
        if 'removed 0' in last:
            break
    run(['cp', src, board_out], log)

def stub(board_in, board_out, targets, log):
    run(['python3', '-u', 'hw/hand_stub.py', board_in, board_out]
        + targets, log)

LOG = 'results/chain3.log'
open(LOG, 'w').write('chain3 start\n')
B = 'hw/pdlvds_rx.fr30.kicad_pcb'
def step(name, out, cx, cy, rad, targets):
    global B
    print(f'--- {name}: clear disc ({cx},{cy}) r{rad}', flush=True)
    clear(B, out, cx, cy, rad, LOG)
    print(f'--- {name}: stub {targets}', flush=True)
    stub(out, out, targets, LOG)
    B = out

step('u7east', 'hw/pdlvds_rx.fr31.kicad_pcb', 31.5, 63.4, 2.4,
     ['ULPI_NXT:U7.11', 'ULPI_STP:U7.13', 'ULPI_DIR:U7.12',
      'ULPI_CK:U7.14'])
step('u7south', 'hw/pdlvds_rx.fr32.kicad_pcb', 30.0, 58.5, 2.6,
     ['PHY_1V8A:U7.29', '+3V3A:U7.6'])
step('u6west', 'hw/pdlvds_rx.fr33.kicad_pcb', 84.5, 43.5, 2.5,
     ['USB_RST:U6.40', 'ULPI_D6:U6.74'])
step('u10', 'hw/pdlvds_rx.fr34.kicad_pcb', 16.0, 10.0, 3.0,
     ['HV_INTVCC:U10.8', 'HV_SS:U10.3'])
step('u4south', 'hw/pdlvds_rx.fr35.kicad_pcb', 52.5, 54.0, 2.6,
     ['THRADJ:U4.9', 'REFCLKN:U4.11'])
print('chain3 board steps done ->', B, flush=True)
