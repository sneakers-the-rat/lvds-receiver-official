#!/usr/bin/env python3
"""Generate hw/pdlvds_rx.kicad_sch (KiCad 7) from hw/circuit.py.

Clean-room, machine-generated schematic: every symbol is a rectangle with
pins at coordinates defined here (no library-symbol geometry is relied
on), interconnected with global labels on short wire stubs.  The STM32
pin NAME->NUMBER map is parsed from the installed KiCad symbol library
(ST's own symbol data).  Correctness is proven downstream by diffing the
kicad-cli netlist export against circuit.py (hw/check_netlist.py).
"""
import sys, uuid, re
sys.path.insert(0, 'hw')
import circuit

TYPEMAP = {"in":"input","out":"output","bidir":"bidirectional",
           "passive":"passive","pwr_in":"power_in","pwr_out":"power_out",
           "oc":"open_collector","nc":"no_connect"}
def U(): return str(uuid.uuid4())
SHEET_UUID = U()
def q(s): return '"' + str(s).replace('\\','\\\\').replace('"','\\"') + '"'

# ---------- STM32 pin name -> number from KiCad library symbol ----------

def balanced(txt, i):
    """Return txt[i:j] spanning the balanced s-expr starting at i
    (string-aware: parens inside quotes are ignored)."""
    d = 0; j = i; instr = False
    while j < len(txt):
        c = txt[j]
        if instr:
            if c == '\\': j += 1
            elif c == '"': instr = False
        elif c == '"': instr = True
        elif c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: return txt[i:j+1]
        j += 1
    raise ValueError("unbalanced")

def stm32_pinmap():
    txt = open('/usr/share/kicad/symbols/MCU_ST_STM32H7.kicad_sym').read()
    i = txt.index('(symbol "STM32H723ZGTx"')
    block = balanced(txt, i)
    pins = {}
    pos = 0
    while True:
        try: i = block.index('(pin ', pos)
        except ValueError: break
        pb = balanced(block, i)
        mn = re.search(r'\(name "([^"]+)"', pb)
        mb = re.search(r'\(number "([^"]+)"', pb)
        if mn and mb: pins.setdefault(mn.group(1), []).append(mb.group(1))
        pos = i + 5
    return pins

ST_PINS = stm32_pinmap()

def stm32_all_pins(part):
    """Return {number: (name, type, net)} for the MCU."""
    out = {}
    sig = part["pins"]
    vcap_count = 0
    for name, nums in ST_PINS.items():
        base = name.split('(')[0]
        for num in nums:
            if base in sig:
                out[num] = (name, "bidir", sig[base]); continue
            if name in sig:
                out[num] = (name, "bidir", sig[name]); continue
            if name == "VCAP":
                vcap_count += 1
                out[num] = (name, "passive", f"VCAP{vcap_count}")
            elif name == "VDD": out[num] = (name, "pwr_in", "+3V3D")
            elif name == "VSS": out[num] = (name, "pwr_in", "GND")
            elif name == "VDDA": out[num] = (name, "pwr_in", "+3V3A")
            elif name == "VSSA": out[num] = (name, "pwr_in", "GND")
            elif name == "VREF+": out[num] = (name, "pwr_in", "+3V3A")
            elif name == "VREF-": out[num] = (name, "pwr_in", "GND")
            elif name == "VBAT": out[num] = (name, "pwr_in", "+3V3D")
            elif name == "NRST": out[num] = (name, "in", "NRST")
            elif name == "BOOT0": out[num] = (name, "in", "BOOT0")
            elif name == "PDR_ON": out[num] = (name, "in", "+3V3D")
            else: out[num] = (name, "nc", None)
    return out

def part_pins(part):
    """{number_str: (name, kicad_type, net)}"""
    if part["sym"] == "stm32":
        return {n: (nm, TYPEMAP[t], net) for n, (nm, t, net)
                in stm32_all_pins(part).items()}
    return {n: (nm, TYPEMAP[t], net) for n, (nm, t, net) in part["pins"].items()}

# ---------- symbol layout ----------
def layout(part):
    """Assign each pin a side and local (x,y). Returns (pins_layout, w, h).
    Local frame: x right, y DOWN (KiCad file convention), origin centre."""
    pins = part_pins(part)
    def numkey(n):
        return (0, int(n)) if str(n).isdigit() else (1, str(n))
    left, right = [], []
    for n in sorted(pins, key=numkey):
        name, t, net = pins[n]
        if t in ("output", "power_out"): right.append(n)
        else: left.append(n)
    rows = max(len(left), len(right), 1)
    h = max(7.62, (rows - 1) * 2.54 + 5.08)
    label = part["value"].split(" ")[0]
    w = max(15.24, min(40.0, 2 * (len(label) * 1.1 + 6)))
    if part["sym"] in ("R","C","L","D","LED"):
        w, h = 10.16, 5.08
        lay = {}
        ns = sorted(pins, key=numkey)
        lay[ns[0]] = (-w/2 - 2.54, 0, -1)   # pin stub point + side
        lay[ns[1]] = ( w/2 + 2.54, 0, 1)
        return lay, w, h, pins
    lay = {}
    for i, n in enumerate(left):
        lay[n] = (-w/2 - 2.54, -h/2 + 2.54 + i * 2.54 + 1.27, -1)
    for i, n in enumerate(right):
        lay[n] = ( w/2 + 2.54, -h/2 + 2.54 + i * 2.54 + 1.27, 1)
    return lay, w, h, pins

def symdef(part, lay, w, h, pins):
    name = "PD_" + re.sub(r'[^A-Za-z0-9]+', '_', part["ref"] + "_" + part["value"].split(" ")[0])
    ref_letter = re.match(r'[A-Za-z]+', part["ref"]).group(0)
    s = [f'(symbol {q(name)} (pin_names (offset 1.016)) (in_bom yes) (on_board yes)']
    s.append(f'  (property "Reference" {q(ref_letter)} (at 0 {-h/2-2.54} 0) (effects (font (size 1.27 1.27))))')
    s.append(f'  (property "Value" {q(part["value"])} (at 0 {h/2+2.54} 0) (effects (font (size 1.27 1.27))))')
    s.append('  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    s.append('  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    s.append(f'  (symbol {q(name+"_0_1")} (rectangle (start {-w/2} {-h/2}) (end {w/2} {h/2}) (stroke (width 0.254) (type default)) (fill (type background))))')
    pl = [f'  (symbol {q(name+"_1_1")}']
    for n, (x, y, side) in lay.items():
        pname, ptype, _ = pins[n]
        # KiCad convention: left-side pins rotation 0, right-side 180;
        # the (at) point is the electrical connection point.
        rot = 0 if side < 0 else 180
        pl.append(f'    (pin {ptype} line (at {x} {y} {rot}) (length 2.54) (name {q(pname)} (effects (font (size 1.0 1.0)))) (number {q(n)} (effects (font (size 1.0 1.0)))))')
    pl.append('  )')
    s.append("\n".join(pl))
    s.append(')')
    return name, "\n".join(s)

# ---------- sheet placement ----------
GROUP_X = {"afe": 40, "hv": 150, "pwr": 260, "cdr": 40, "cap": 150,
           "mcu": 210, "usb": 330, "dac": 330, "misc": 400, "mech": 400}
GROUP_Y = {"afe": 30, "cdr": 200, "cap": 200, "hv": 30, "pwr": 30,
           "mcu": 150, "usb": 30, "dac": 190, "misc": 300, "mech": 350}

def main():
    defs, instances, wires, labels, ncs = [], [], [], [], []
    cursors = {}
    placed = {}
    for part in circuit.PARTS:
        lay, w, h, pins = layout(part)
        name, sd = symdef(part, lay, w, h, pins)
        # embedded lib_symbols copies carry the library-prefixed name
        sd = sd.replace('(symbol "' + name + '"', '(symbol "pdlvds:' + name + '"', 1)
        defs.append(sd)
        g = part["group"]
        x0 = GROUP_X[g]; y = cursors.get(g, GROUP_Y[g])
        cx, cy = x0 + w/2 + 10, y + h/2
        cursors[g] = y + h + 12
        placed[part["ref"]] = (cx, cy)
        fplib, fpname = part["fp"]
        inst = [f'(symbol (lib_id {q("pdlvds:"+name)}) (at {cx} {cy} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {q(U())})']
        inst.append(f'  (property "Reference" {q(part["ref"])} (at {cx-w/2} {cy-h/2-2.54} 0) (effects (font (size 1.27 1.27))))')
        inst.append(f'  (property "Value" {q(part["value"])} (at {cx} {cy+h/2+2.54} 0) (effects (font (size 1.27 1.27))))')
        inst.append(f'  (property "Footprint" {q(fplib+":"+fpname)} (at {cx} {cy} 0) (effects (font (size 1.27 1.27)) hide))')
        inst.append('  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
        inst.append(f'  (instances (project "pdlvds_rx" (path "/{SHEET_UUID}" (reference {q(part["ref"])}) (unit 1))))')
        inst.append(')')
        instances.append("\n".join(inst))
        for n, (lx, ly, side) in lay.items():
            pname, ptype, net = pins[n]
            px, py = cx + lx, cy - ly   # KiCad symbol y is up, sheet y is down
            if net is None:
                ncs.append(f'(no_connect (at {px} {py}) (uuid {q(U())}))')
            else:
                # stub extends further outward from pin end
                dx = 5.08 * side
                ex = px + dx
                wires.append(f'(wire (pts (xy {px} {py}) (xy {ex} {py})) (stroke (width 0) (type default)) (uuid {q(U())}))')
                lrot = 0 if side > 0 else 180
                labels.append(f'(global_label {q(net)} (shape input) (at {ex} {py} {lrot}) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {"left" if lrot==0 else "right"})) (uuid {q(U())}) (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {ex} {py} {lrot}) (effects (font (size 1.27 1.27)) hide)))')
    # PWR_FLAGs: one per power net, parked at bottom, stub+label like others
    fx = 30.0
    for net in circuit.POWER_NETS:
        fy = 560.0
        wires.append(f'(wire (pts (xy {fx} {fy}) (xy {fx} {fy-5.08})) (stroke (width 0) (type default)) (uuid {q(U())}))')
        labels.append(f'(global_label {q(net)} (shape input) (at {fx} {fy-5.08} 270) (fields_autoplaced) (effects (font (size 1.27 1.27))) (uuid {q(U())}) (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {fx} {fy-5.08} 270) (effects (font (size 1.27 1.27)) hide)))')
        instances.append(f'(symbol (lib_id "power:PWR_FLAG") (at {fx} {fy} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {q(U())}) (property "Reference" {q("#FLG"+str(int(fx)))} (at {fx} {fy+2.54} 0) (effects (font (size 1.27 1.27)) hide)) (property "Value" "PWR_FLAG" (at {fx} {fy-2.54} 0) (effects (font (size 1.27 1.27)) hide)) (property "Footprint" "" (at {fx} {fy} 0) (effects (font (size 1.27 1.27)) hide)) (property "Datasheet" "" (at {fx} {fy} 0) (effects (font (size 1.27 1.27)) hide)) (instances (project "pdlvds_rx" (path "/{SHEET_UUID}" (reference {q("#FLG"+str(int(fx)))}) (unit 1)))))')
        fx += 25.0
    out = ['(kicad_sch (version 20230121) (generator "pdlvds-gen")', f'(uuid {SHEET_UUID})',
           '(paper "A1")', '(title_block (title "PDLVDS-RX rev A — photodiode LVDS receiver") (rev "A"))',
           '(lib_symbols']
    out += defs
    # embed PWR_FLAG definition copied from KiCad power library
    ptxt = open('/usr/share/kicad/symbols/power.kicad_sym').read()
    i = ptxt.index('(symbol "PWR_FLAG"')
    out.append(balanced(ptxt, i))
    out.append(')')
    out += instances + wires + labels + ncs
    out.append('(sheet_instances (path "/" (page "1")))')
    out.append(')')
    text = "\n".join(out) + "\n"
    text = re.sub(r'\(uuid "([0-9a-f-]{36})"\)', r'(uuid \1)', text)
    open('hw/pdlvds_rx.kicad_sch', 'w').write(text)
    # also write the symbol library file (same defs) for sym-lib-table
    lib = ['(kicad_symbol_lib (version 20211014) (generator "pdlvds-gen")'] + defs + [')']
    open('hw/pdlvds.kicad_sym', 'w').write("\n".join(lib) + "\n")
    print(f"schematic written: {len(circuit.PARTS)} parts, {len(labels)} labels, {len(ncs)} no-connects")

if __name__ == "__main__":
    main()
