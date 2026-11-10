#!/usr/bin/env python3
"""Generate hw/pdlvds_rx.kicad_sch (KiCad 8) from hw/circuit.py.

Clean-room, machine-generated schematic with a human-style layout:
symbols are rectangles with pins at coordinates defined here (the STM32
pin NAME->NUMBER map is parsed from the installed KiCad symbol library,
ST's own symbol data; no other library-symbol geometry is relied on).

Layout: one framed, titled region per subsystem (the `group` field in
circuit.py), parts shelf-packed inside their region in circuit.py
order. Connections whose pins all live in one region are DRAWN WIRES,
routed orthogonally on the 1.27 mm grid by an exact-obstacle A* that
may cross other nets' wires (no junction = no connection in KiCad) but
never overlaps them collinearly and never touches a foreign pin.
Power-rail pins get a local power symbol at the pin (GND and +5V are
the stock KiCad symbols; the other rails use generated symbols of the
same form). Only nets that LEAVE a region use a net label, placed on a
short stub at the pin like a human's off-sheet tag. Correctness is
proven downstream by diffing the kicad-cli netlist export against
circuit.py (hw/check_netlist.py) and against a canonical snapshot of
the pre-redraw netlist (hw/schematic_snapshot.py).

All layout arithmetic is done in integer grid units (GU = 1.27 mm) in
sheet coordinates (x right, y down) and converted at emission; symbol
definitions flip y (KiCad symbol space is y-up) exactly once, in
symdef().
"""
import sys, uuid, re, math, heapq
sys.path.insert(0, 'hw')
import circuit

# KiCad's schematic connection grid is 1.27 mm (50 mil). Every symbol
# placement, pin offset, wire endpoint, label anchor and no-connect
# marker MUST land exactly on it: KiCad 8 ERC flags off-grid endpoints
# ([endpoint_off_grid]) and off-grid no-connect markers stop coinciding
# exactly with their pins. All layout below is in integer GU.
GRID = 1.27
def snap(v):
    return round(round(v / GRID) * GRID, 2)

def mm(gu):
    """Grid units -> mm string, exact hundredths."""
    return f"{gu * GRID:.2f}".rstrip('0').rstrip('.') if gu else "0"

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

def flag_nets():
    """Nets that get a PWR_FLAG, computed from circuit.py pin data:
    a net is flagged iff it contains at least one power_in pin and
    NO power_out pin. A PWR_FLAG presents a power_out to ERC — that
    is its whole job — so flagging a net that already has a genuine
    power_out puts two power outputs on one net: [pin_to_pin]
    "Power output and Power output connected", the 2 ERC errors on
    +VA (U13 OUT) and +3V3A (U14 OUT) in the main CI run on 264d58b,
    once round 3 made the flags electrically live. Conversely a net
    with no power_in pins (APD_K: only passive pins) has nothing for
    a flag to drive. The old hardcoded list (every POWER_NETS entry
    plus the two PHY rails appended by hand) violated both halves.
    The PHY rails now fall out of the rule on their own: they are
    the USB3300's internal-regulator outputs whose only pins are
    power_in loads on U7 itself. Order is deterministic: POWER_NETS
    order first, then first-appearance order in the pin census."""
    census, order = {}, []
    for part in circuit.PARTS:
        for _num, (_name, ktype, net) in part_pins(part).items():
            if net is None:
                continue
            if net not in census:
                census[net] = set()
                order.append(net)
            census[net].add(ktype)
    want = {n for n, ts in census.items()
            if "power_in" in ts and "power_out" not in ts}
    return ([n for n in circuit.POWER_NETS if n in want]
            + [n for n in order
               if n in want and n not in circuit.POWER_NETS])

# ---------- net classification ----------
# Nets whose pins get a local power symbol instead of a wire/label:
# the true rails. Other rails that are local to one region (+3V3D_CDR
# in cdr, PHY_1V8 / PHY_1V8A in usb) fall out of the intra-region rule
# and are drawn as wires, like a human draws a local decoupling loop.
# APD_K stays a signal for drawing purposes (it is the APD cathode
# node, drawn/labelled, not a rail symbol).
POWER_SYMBOL_NETS = {"GND", "+5V", "+3V3D", "+3V3A", "+VA", "-VA", "NEG_RAW"}
# chevron direction for generated rail symbols: -1 = points down
POWER_DOWN = {"-VA", "NEG_RAW"}

def numkey(n):
    return (0, int(n)) if str(n).isdigit() else (1, str(n))

def build_net_groups():
    g = {}
    for part in circuit.PARTS:
        for _num, (_name, _t, net) in part_pins(part).items():
            if net:
                g.setdefault(net, set()).add(part["group"])
    return g

NET_GROUPS = build_net_groups()

def pin_class(part, net):
    """How a pin is connected in the drawing: power / wire / label / nc."""
    if net is None:
        return "nc"
    if net in POWER_SYMBOL_NETS:
        return "power"
    if len(NET_GROUPS[net]) == 1:
        return "wire"
    return "label"

# Nominal region centres (mm), used ONLY to decide which side of a box
# symbol a pin belongs on (pins face the subsystem their net runs to).
NOMINAL = {"afe": (140, 140), "hv": (430, 140), "pwr": (740, 140),
           "cdr": (140, 430), "mcu": (430, 430), "usb": (740, 430),
           "mech": (110, 720), "cap": (330, 720), "dac": (580, 720),
           "misc": (850, 720)}

GROUP_TITLES = {
    "afe": "ANALOG FRONT END - APD / TIA / COMPARATOR",
    "cdr": "CLOCK + DATA RECOVERY - ADN2813",
    "cap": "LVDS -> CMOS CAPTURE + LVDS OUTPUT",
    "mcu": "MCU - STM32H723",
    "usb": "USB - USB3300 PHY + USB-C",
    "dac": "DAC + TEMPERATURE - DAC8562 / TMP117",
    "hv": "HV BIAS - LT3757 FLYBACK",
    "pwr": "POWER - BUCKS + LDOs",
    "misc": "LEDS / MISC",
    "mech": "MECHANICAL",
}
GROUP_ORDER = [["afe", "hv", "pwr"], ["cdr", "mcu", "usb"],
               ["mech", "cap", "dac", "misc"]]
# target content widths per region, GU
REGION_W = {"afe": 235, "hv": 245, "pwr": 245, "cdr": 205, "mcu": 250,
            "usb": 235, "cap": 165, "dac": 195, "misc": 145, "mech": 125}
# preferred home region for each PWR_FLAG (fallback: busiest region)
FLAG_HOME = {"GND": "pwr", "+5V": "pwr", "+3V3D": "pwr", "-VA": "pwr",
             "NEG_RAW": "pwr", "+3V3D_CDR": "cdr", "PHY_1V8": "usb",
             "PHY_1V8A": "usb"}

# ---------- per-part geometry ----------
# A layout is a dict:
#   kind: "box" | "2h" | "2v"
#   w, h: body size in GU
#   pins: {num: (dx, dy, dirx, diry)} connection-point offset from the
#         part centre in GU (sheet coords, y down) + outward direction
#   ext: (L, R, T, B) footprint extents from centre in GU, including
#        stubs, label text, power symbols and ref/value text zones
#   body: (bx, by) half-extents of the obstacle rectangle (body + pin
#        lines; pin connection points sit on its boundary)

def text_gu(s):
    """Approximate rendered width of a 1.27 mm-font string, in GU."""
    return int(math.ceil(len(s) * 0.85)) + 2

def part_layout(part):
    pins = part_pins(part)
    cls = {n: pin_class(part, pins[n][2]) for n in pins}
    if part["sym"] in ("R", "C", "L", "D", "LED") and len(pins) == 2:
        ns = sorted(pins, key=numkey)
        nets = [pins[n][2] for n in ns]
        if (nets[0] == "GND") != (nets[1] == "GND"):
            # vertical: non-GND pin up, GND pin down (the classic
            # shunt/decoupling orientation)
            top = ns[0] if nets[1] == "GND" else ns[1]
            bot = ns[1] if nets[1] == "GND" else ns[0]
            geo = {top: (0, -6, 0, -1), bot: (0, 6, 0, 1)}
            lay = dict(kind="2v", w=4, h=8, pins=geo, body=(2, 6))
        else:
            geo = {ns[0]: (-6, 0, -1, 0), ns[1]: (6, 0, 1, 0)}
            lay = dict(kind="2h", w=8, h=4, pins=geo, body=(6, 2))
    else:
        sides = pin_sides(part, pins)
        rows = {-1: 0, 1: 0}
        for s in sides.values():
            rows[s] += 1
        nrows = max(rows[-1], rows[1], 1)
        h = max(6, (nrows - 1) * 2 + 4)
        label = part["value"].split(" ")[0]
        w_mm = max(15.24, min(40.64,
                   math.ceil((2 * (len(label) * 1.1 + 6)) / 2.54) * 2.54))
        w = int(round(w_mm / GRID))
        geo = {}
        # deterministic: walk pins in numeric order per side
        perside = {-1: [], 1: []}
        for n in sorted(pins, key=numkey):
            perside[sides[n]].append(n)
        for s, lst in perside.items():
            for i, n in enumerate(lst):
                geo[n] = (s * (w // 2 + 2), -h // 2 + 2 + i * 2, s, 0)
        lay = dict(kind="box", w=w, h=h, pins=geo, body=(w // 2 + 2, h // 2))
    # footprint extents
    bx, by = lay["body"]
    ext = [bx, bx, by, by]  # L, R, T, B
    for n, (dx, dy, dirx, diry) in lay["pins"].items():
        c = cls[n]
        net = pins[n][2]
        if c == "wire":
            need = 1
        elif c == "label":
            need = 4 + text_gu(net)
        elif c == "power":
            need = 2 + 10
        else:
            need = 0
        if dirx < 0: ext[0] = max(ext[0], bx + need)
        if dirx > 0: ext[1] = max(ext[1], bx + need)
        if diry < 0: ext[2] = max(ext[2], by + need)
        if diry > 0: ext[3] = max(ext[3], by + need)
    # ref/value text zones
    if lay["kind"] == "2v":
        ext[1] = max(ext[1], 4 + text_gu(part["value"].split(" ")[0]) + 2)
    else:
        ext[2] = max(ext[2], by + 2)   # reference line above
        ext[3] = max(ext[3], by + 3)   # value line below
    lay["ext"] = tuple(ext)
    lay["cls"] = cls
    lay["pinsinfo"] = pins
    return lay

def pin_sides(part, pins):
    """Side (-1 left / +1 right) for every pin of a box symbol.
    Signal pins face the region their net runs to (ties and intra-net
    pins fall back to the classic in-left / out-right); power and
    no-connect pins balance the two columns."""
    g = part["group"]
    gx = NOMINAL[g][0]
    counts = {-1: 0, 1: 0}
    sides = {}
    deferred = []
    for n in sorted(pins, key=numkey):
        _name, t, net = pins[n]
        if net is None or net in POWER_SYMBOL_NETS:
            deferred.append(n)
            continue
        dest = NET_GROUPS[net] - {g}
        if not dest:
            side = 1 if t in ("output", "power_out") else -1
        else:
            score = sum((NOMINAL[d][0] > gx) - (NOMINAL[d][0] < gx)
                        for d in dest)
            if score < 0: side = -1
            elif score > 0: side = 1
            else: side = 1 if t in ("output", "power_out") else -1
        sides[n] = side
        counts[side] += 1
    for n in deferred:
        side = -1 if counts[-1] <= counts[1] else 1
        sides[n] = side
        counts[side] += 1
    return sides

# ---------- symbol definitions ----------
def symdef(part, lay):
    """Emit the (lib) symbol definition. Symbol space is y-UP: a pin
    whose sheet-space offset is (dx, dy) is written at (dx, -dy), and
    its rotation is the direction from the connection point TOWARD
    the body in symbol space."""
    name = "PD_" + re.sub(r'[^A-Za-z0-9]+', '_',
                          part["ref"] + "_" + part["value"].split(" ")[0])
    ref_letter = re.match(r'[A-Za-z]+', part["ref"]).group(0)
    w, h = lay["w"], lay["h"]
    s = [f'(symbol {q(name)} (pin_names (offset 1.016)) (in_bom yes) (on_board yes)']
    s.append(f'  (property "Reference" {q(ref_letter)} (at 0 {-h*GRID/2-2.54:.2f} 0) (effects (font (size 1.27 1.27))))')
    s.append(f'  (property "Value" {q(part["value"])} (at 0 {h*GRID/2+2.54:.2f} 0) (effects (font (size 1.27 1.27))))')
    s.append('  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    s.append('  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    s.append(f'  (symbol {q(name+"_0_1")} (rectangle (start {-w*GRID/2:.2f} {-h*GRID/2:.2f}) (end {w*GRID/2:.2f} {h*GRID/2:.2f}) (stroke (width 0.254) (type default)) (fill (type background))))')
    pl = [f'  (symbol {q(name+"_1_1")}']
    for n, (dx, dy, dirx, diry) in lay["pins"].items():
        pname, ptype, _net = lay["pinsinfo"][n]
        # toward-body direction in symbol space: -(dirx, -diry)
        tx, ty = -dirx, diry
        rot = {(1, 0): 0, (-1, 0): 180, (0, 1): 90, (0, -1): 270}[(tx, ty)]
        pl.append(f'    (pin {ptype} line (at {dx*GRID:.2f} {-dy*GRID:.2f} {rot}) (length 2.54) (name {q(pname)} (effects (font (size 1.0 1.0)))) (number {q(n)} (effects (font (size 1.0 1.0)))))')
    pl.append('  )')
    s.append("\n".join(pl))
    s.append(')')
    return name, "\n".join(s)

def power_symdef(net):
    """Generated power symbol for a custom rail: same form as the
    stock chevron symbols in power.kicad_sym. Pin at origin, length
    0; the net name is carried by the instance Value (KiCad power
    symbol rule), the pin name is "~" exactly like the stock lib."""
    name = "PWR_" + re.sub(r'[^A-Za-z0-9]+', '_', net)
    down = net in POWER_DOWN
    sgn = -1 if down else 1
    pts = [(-0.762, sgn * 1.27), (0, sgn * 2.54), (0.762, sgn * 1.27)]
    lines = []
    lines.append(f'    (polyline (pts (xy {pts[0][0]} {pts[0][1]}) (xy {pts[1][0]} {pts[1][1]})) (stroke (width 0) (type default)) (fill (type none)))')
    lines.append(f'    (polyline (pts (xy 0 0) (xy 0 {sgn*2.54})) (stroke (width 0) (type default)) (fill (type none)))')
    lines.append(f'    (polyline (pts (xy {pts[1][0]} {pts[1][1]}) (xy {pts[2][0]} {pts[2][1]})) (stroke (width 0) (type default)) (fill (type none)))')
    rot = 270 if down else 90
    out = [f'(symbol {q(name)} (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom no) (on_board no)',
           f'  (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))',
           f'  (property "Value" {q(net)} (at 0 {sgn*3.556} 0) (effects (font (size 1.27 1.27))))',
           '  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           '  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'  (symbol {q(name+"_0_1")}'] + lines + [
           '  )',
           f'  (symbol {q(name+"_1_1")} (pin power_in line (at 0 0 {rot}) (length 0) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27))))))',
           ')']
    return name, "\n".join(out)

# ---------- region packing ----------
def pack_region(parts, flag_list):
    """Shelf-pack one region's parts. Returns dict with frame size,
    placed parts [(part, lay, cx, cy)] in region-local GU, and flag
    strip slots [(net, sx, sy)] in region-local GU. Content origin is
    (0,0); the frame is drawn around it with margins by the caller."""
    target = REGION_W[parts[0]["group"]]
    placed = []
    x = 0
    y = 0
    shelf_h = 0
    used_w = 0
    for part in parts:
        lay = part_layout(part)
        eL, eR, eT, eB = lay["ext"]
        fw, fh = eL + eR, eT + eB
        if x > 0 and x + fw > target:
            used_w = max(used_w, x - 6)
            x = 0
            y += shelf_h + 8
            shelf_h = 0
        placed.append((part, lay, x + eL, y + eT))
        x += fw + 6
        shelf_h = max(shelf_h, fh)
    used_w = max(used_w, x - 6)
    content_h = y + shelf_h
    slots = []
    if flag_list:
        sy = content_h + 12
        sx = 2
        for net in flag_list:
            slots.append((net, sx, sy))
            sx += 22
        used_w = max(used_w, sx - 22 + 18)
        content_h = sy + 10
    return dict(w=used_w, h=content_h, placed=placed, slots=slots)

def compute_frames(flag_homes):
    """Lay out all regions on the sheet. Returns
    {group: dict(rx, ry, w, h, placed=[(part, lay, cx, cy)], slots)}
    in absolute sheet GU. Frame w/h include margins + title zone."""
    by_group = {}
    for part in circuit.PARTS:
        by_group.setdefault(part["group"], []).append(part)
    frames = {}
    y = 8
    max_x = 0
    for row in GROUP_ORDER:
        x = 8
        row_h = 0
        for g in row:
            pk = pack_region(by_group[g], flag_homes.get(g, []))
            w = pk["w"] + 14
            h = pk["h"] + 19
            placed = [(p, l, cx + x + 7, cy + y + 13)
                      for (p, l, cx, cy) in pk["placed"]]
            slots = [(n, sx + x + 7, sy + y + 13)
                     for (n, sx, sy) in pk["slots"]]
            frames[g] = dict(rx=x, ry=y, w=w, h=h, placed=placed,
                             slots=slots)
            x += w + 10
            row_h = max(row_h, h)
        max_x = max(max_x, x - 10)
        y += row_h + 12
    frames["_extent"] = (max_x, y - 12)
    return frames

# ---------- wire router (per region, exact-obstacle A*) ----------
def route_region(frame, net_pins, blocked, pincell, wiremap, soft=None):
    """Route every net in net_pins ({net: [(gx,gy), ...]}, absolute
    sheet GU) inside the frame. blocked: set of forbidden cells.
    pincell: {cell: net-or-None} for every pin in the region (all are
    in blocked; a routed net may enter only its own pin cells).
    wiremap: {cell: [net, axis_mask]} of foreign stub wires; mutated
    with each routed net's segments. Crossing a foreign wire at a
    single point is legal in KiCad (no junction, no connection);
    running along it is not. Returns {net: (segments, junctions)}
    with segments as (x1, y1, x2, y2) GU tuples."""
    rx, ry, rw, rh = frame["rx"], frame["ry"], frame["w"], frame["h"]
    dom = (rx + 2, ry + 2, rx + rw - 2, ry + rh - 2)
    near = set()
    for (x, y) in blocked:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                c = (x + dx, y + dy)
                if c not in blocked:
                    near.add(c)
    out = {}
    for net in sorted(net_pins, key=lambda n: (-len(net_pins[n]), n)):
        pins = sorted(set(net_pins[net]))
        # seed tree at the pin nearest the centroid
        cx = sum(p[0] for p in pins) / len(pins)
        cy = sum(p[1] for p in pins) / len(pins)
        seed = min(pins, key=lambda p: (abs(p[0] - cx) + abs(p[1] - cy), p))
        tree = {seed}
        segs = []
        todo = [p for p in pins if p != seed]
        todo.sort(key=lambda p: abs(p[0] - seed[0]) + abs(p[1] - seed[1]))
        for pin in todo:
            if pin in tree:
                continue
            path = _astar(pin, tree, dom, blocked, set(pins), pincell,
                          wiremap, net, near, soft or set())
            if path is None:
                raise RuntimeError(f"no route for net {net} pin {pin}")
            for cell in path:
                tree.add(cell)
            new_segs = _compress(path)
            segs += new_segs
            for (x1, y1, x2, y2) in new_segs:
                mask = 1 if y1 == y2 else 2
                for cell in _seg_cells((x1, y1, x2, y2)):
                    e = wiremap.setdefault(cell, [net, 0])
                    e[1] |= mask
        out[net] = _subdivide(segs, pins)
    return out

def _seg_cells(seg):
    x1, y1, x2, y2 = seg
    if x1 == x2:
        return [(x1, y) for y in range(min(y1, y2), max(y1, y2) + 1)]
    return [(x, y1) for x in range(min(x1, x2), max(x1, x2) + 1)]

def _compress(path):
    """Path (list of cells) -> maximal straight segments."""
    segs = []
    start = path[0]
    prev = path[0]
    pdir = None
    for cell in path[1:]:
        d = (cell[0] - prev[0], cell[1] - prev[1])
        if pdir is not None and d != pdir:
            segs.append((start[0], start[1], prev[0], prev[1]))
            start = prev
        pdir = d
        prev = cell
    segs.append((start[0], start[1], prev[0], prev[1]))
    return segs

def _on_seg(p, s):
    x1, y1, x2, y2 = s
    if x1 == x2:
        return p[0] == x1 and min(y1, y2) <= p[1] <= max(y1, y2)
    return p[1] == y1 and min(x1, x2) <= p[0] <= max(x1, x2)

def _subdivide(segs, pins):
    """Split a net's segments at every point where the net touches
    itself (another segment's endpoint, a crossing, or a pin lying
    on a segment) and return (atomic_segments, junction_points).

    This is load-bearing, not cosmetic: KiCad 8's file-based netlist
    extraction connects wires ONLY at shared endpoints — a wire
    ending mid-segment of another wire does not join it, with or
    without a junction dot (proven with minimal probe schematics:
    split-at-join connects, T+dot and cross+dot do not). Junction
    dots are therefore emitted purely as the human visual marker,
    at vertices of degree >= 3 in the subdivided graph."""
    splits = [set() for _ in segs]
    for i, s in enumerate(segs):
        splits[i].add((s[0], s[1]))
        splits[i].add((s[2], s[3]))
    for i, s in enumerate(segs):
        for j, t in enumerate(segs):
            if i == j:
                continue
            for p in ((t[0], t[1]), (t[2], t[3])):
                if _on_seg(p, s):
                    splits[i].add(p)
            if (s[1] == s[3]) != (t[1] == t[3]):  # one H, one V
                p = (t[0], s[1]) if s[1] == s[3] else (s[0], t[1])
                if _on_seg(p, s) and _on_seg(p, t):
                    splits[i].add(p)
                    splits[j].add(p)
    for p in pins:
        for i, s in enumerate(segs):
            if _on_seg(p, s):
                splits[i].add(p)
    atomic = set()
    for i, s in enumerate(segs):
        pts = sorted(splits[i],
                     key=lambda p: (p[0] if s[0] != s[2] else p[1]))
        for a, b in zip(pts, pts[1:]):
            if a != b:
                atomic.add((a[0], a[1], b[0], b[1]))
    deg = {}
    for (x1, y1, x2, y2) in atomic:
        deg[(x1, y1)] = deg.get((x1, y1), 0) + 1
        deg[(x2, y2)] = deg.get((x2, y2), 0) + 1
    jpts = sorted(p for p, d in deg.items() if d >= 3)
    return sorted(atomic), jpts

def _astar(start, goals, dom, blocked, own_pins, pincell, wiremap,
           net, near, soft):
    """A* from start to any cell of goals. Returns path cells or None."""
    x0, y0, x1, y1 = dom
    gx0 = min(g[0] for g in goals); gx1 = max(g[0] for g in goals)
    gy0 = min(g[1] for g in goals); gy1 = max(g[1] for g in goals)
    def h(c):
        # Manhattan distance to the goals' bounding box: admissible
        # (every goal lies inside it) and O(1) per step.
        dx = max(gx0 - c[0], 0, c[0] - gx1)
        dy = max(gy0 - c[1], 0, c[1] - gy1)
        return dx + dy
    opens = [(h(start), 0, start, (0, 0))]
    came = {start: None}
    gs = {start: 0}
    DIRS = [(1, 0, 1), (-1, 0, 1), (0, 1, 2), (0, -1, 2)]
    while opens:
        _f, g, cell, pdir = heapq.heappop(opens)
        if cell in goals and cell != start:
            path = [cell]
            while came[path[-1]] is not None:
                path.append(came[path[-1]])
            return path[::-1]
        for dx, dy, axis in DIRS:
            nb = (cell[0] + dx, cell[1] + dy)
            if not (x0 <= nb[0] <= x1 and y0 <= nb[1] <= y1):
                continue
            if nb in blocked and nb not in own_pins and nb not in goals:
                continue
            pn = pincell.get(nb, net)
            if pn != net:
                continue
            step = 1
            wm = wiremap.get(nb)
            if wm is not None and wm[0] != net:
                if wm[1] & axis:
                    continue
                step += 12
            if nb in soft:
                step += 6
            if nb in near:
                step += 1
            if pdir != (0, 0) and (dx, dy) != pdir:
                step += 2
            ng = g + step
            if ng < gs.get(nb, 1 << 30):
                gs[nb] = ng
                came[nb] = cell
                heapq.heappush(opens, (ng + h(nb), ng, nb, (dx, dy)))
    return None

def net_label_anchor(segs, jpts, name, zones, others):
    """Pick a point on a net's longest (preferably horizontal)
    segment for its naming label. The point must be junction-free,
    must not touch any other net's wire or stub (a label anchored
    exactly on a foreign crossing attaches to the wrong graph —
    proven by DP_PHY losing its name that way), and its text zone
    should not collide with labels already placed in this region
    (closely parallel wires — J1's DP_CON/DN_CON — otherwise stack
    their labels illegibly)."""
    cand = sorted(segs, key=lambda s: (s[1] != s[3],
                                       -(abs(s[2] - s[0]) + abs(s[3] - s[1]))))
    tw = int(len(name) * 1.15) + 3
    fallback = None
    for s in cand[:4]:
        x1, y1, x2, y2 = s
        L = abs(x2 - x1) + abs(y2 - y1)
        if L < 2:
            continue
        rot = 0 if y1 == y2 else 90
        for frac in (0.5, 0.3, 0.7, 0.15, 0.85):
            t = max(1, min(L - 1, int(L * frac)))
            p = (x1 + (0 if x2 == x1 else (1 if x2 > x1 else -1)) * t,
                 y1 + (0 if y2 == y1 else (1 if y2 > y1 else -1)) * t)
            if p in jpts:
                continue
            if any(_on_seg(p, o) for o in others):
                continue
            if rot == 0:
                zone = (p[0] - 1, p[1] - 3, p[0] + tw, p[1] + 1)
            else:
                zone = (p[0] - 3, p[1] - tw, p[0] + 1, p[1] + 1)
            if fallback is None:
                fallback = (p, rot, zone)
            if any(not (zone[2] < z[0] or zone[0] > z[2]
                        or zone[3] < z[1] or zone[1] > z[3])
                   for z in zones):
                continue
            zones.append(zone)
            return p, rot
    if fallback is not None:
        zones.append(fallback[2])
        return fallback[0], fallback[1]
    s = cand[0]
    return (s[0], s[1]), (0 if s[1] == s[3] else 90)

# ---------- power symbol instance geometry ----------
# Stock GND points DOWN at rotation 0; stock +5V and the generated
# rail symbols point UP at rotation 0. KiCad instance rotation is
# counterclockwise on screen.
ROT_DOWN_NATURAL = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}
ROT_UP_NATURAL = {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270}

def stock_power_def(name):
    txt = open('/usr/share/kicad/symbols/power.kicad_sym').read()
    i = txt.index(f'(symbol "{name}"')
    return balanced(txt, i).replace(f'(symbol "{name}"',
                                     f'(symbol "power:{name}"', 1)

def main():
    FLAG_NETS = flag_nets()
    # home each flag: preferred region, else the region with most pins
    pin_count = {}
    for part in circuit.PARTS:
        for _n, (_nm, _t, net) in part_pins(part).items():
            if net:
                pin_count.setdefault(net, {})
                pin_count[net][part["group"]] = \
                    pin_count[net].get(part["group"], 0) + 1
    flag_homes = {}
    for net in FLAG_NETS:
        home = FLAG_HOME.get(net)
        if home is None or pin_count[net].get(home, 0) == 0:
            home = max(pin_count[net].items(), key=lambda kv: kv[1])[0]
        flag_homes.setdefault(home, []).append(net)
    frames = compute_frames(flag_homes)
    ex, ey = frames.pop("_extent")
    if ex > 920 or ey > 645:
        raise RuntimeError(f"layout overflows A0: extent {ex} x {ey} GU")

    defs, instances, wires, labels, ncs = [], [], [], [], []
    junctions, graphics = [], []
    stats = {"wire_pins": 0, "label_pins": 0, "power_pins": 0,
             "wire_segs": 0, "junctions": 0, "routed_nets": 0,
             "net_labels": 0}
    pwr_seq = [0]
    flg_seq = [0]

    def emit_power_instance(lib_id, net, gx, gy, rot, value_at):
        pwr_seq[0] += 1
        ref = f"#PWR{pwr_seq[0]:03d}"
        x, y = mm(gx), mm(gy)
        vx, vy = mm(value_at[0]), mm(value_at[1])
        instances.append(
            f'(symbol (lib_id {q(lib_id)}) (at {x} {y} {rot}) (unit 1) '
            f'(in_bom no) (on_board no) (dnp no) (uuid {q(U())}) '
            f'(property "Reference" {q(ref)} (at {x} {y} 0) '
            f'(effects (font (size 1.27 1.27)) hide)) '
            f'(property "Value" {q(net)} (at {vx} {vy} 0) '
            f'(effects (font (size 1.27 1.27)))) '
            f'(property "Footprint" "" (at {x} {y} 0) '
            f'(effects (font (size 1.27 1.27)) hide)) '
            f'(property "Datasheet" "" (at {x} {y} 0) '
            f'(effects (font (size 1.27 1.27)) hide)) '
            f'(instances (project "pdlvds_rx" (path "/{SHEET_UUID}" '
            f'(reference {q(ref)}) (unit 1)))))')

    def power_lib(net):
        if net == "GND":
            return "power:GND"
        if net == "+5V":
            return "power:+5V"
        return "pdlvds:PWR_" + re.sub(r'[^A-Za-z0-9]+', '_', net)

    # symbol definitions for parts + generated rail symbols
    custom_power = {}
    for net in sorted(POWER_SYMBOL_NETS | set(FLAG_NETS)):
        if net in ("GND", "+5V"):
            continue
        nm, sd = power_symdef(net)
        custom_power[net] = (nm, sd)
    placed_frames = frames
    for g, fr in placed_frames.items():
        # frame + title (graphic items)
        rx, ry, rw, rh = fr["rx"], fr["ry"], fr["w"], fr["h"]
        graphics.append(
            f'(rectangle (start {mm(rx)} {mm(ry)}) (end {mm(rx+rw)} {mm(ry+rh)}) '
            f'(stroke (width 0.35) (type default)) (fill (type none)) (uuid {q(U())}))')
        graphics.append(
            f'(text {q(GROUP_TITLES[g])} (at {mm(rx+7)} {mm(ry+7)} 0) '
            f'(effects (font (size 3.81 3.81)) (justify left)) (uuid {q(U())}))')
        blocked = set()
        soft = set()
        pincell = {}
        wiremap = {}
        stub_segs = []
        net_pins = {}
        # title zone + flag strip are off-limits to the router
        for xx in range(rx + 1, rx + rw):
            for yy in range(ry + 1, ry + 10):
                blocked.add((xx, yy))
        for (net, sx, sy) in fr["slots"]:
            for xx in range(sx - 3, sx + 16):
                for yy in range(sy - 9, sy + 10):
                    blocked.add((xx, yy))
        # place parts; register obstacles, pins, stubs
        for (part, lay, cx, cy) in fr["placed"]:
            name, sd = symdef(part, lay)
            sd = sd.replace('(symbol "' + name + '"',
                            '(symbol "pdlvds:' + name + '"', 1)
            defs.append(sd)
            bx, by = lay["body"]
            # Obstacle model: the SOLID body (border included) and
            # each pin's line cells are walls, but the pin-point
            # column/row at non-pin positions is a legal bus channel
            # — a pin's only non-body exit is along its axis, and if
            # a foreign wire takes that cell the pin is sealed unless
            # it can first slip sideways along the pin-point line.
            # (KiCad connects pins at their point only; the channel
            # cells touch no pin point and no pin line.)
            if lay["kind"] == "2v":
                for xx in range(cx - bx, cx + bx + 1):
                    for yy in range(cy - by + 2, cy + by - 1):
                        blocked.add((xx, yy))
            else:
                for xx in range(cx - bx + 2, cx + bx - 1):
                    for yy in range(cy - by, cy + by + 1):
                        blocked.add((xx, yy))
            for n2, (dx2, dy2, dirx2, diry2) in lay["pins"].items():
                for k in (0, 1):
                    blocked.add((cx + dx2 - dirx2 * k,
                                 cy + dy2 - diry2 * k))
            # ref / value text zones: SOFT router obstacles (cost,
            # not walls). They are not part of the footprint extents
            # (a long value string is wider than its part), so as
            # hard walls they reach across neighbours and seal pins —
            # the TP_HV seal. As costs, wires avoid text when they
            # reasonably can and cross only when they must.
            vw = text_gu(part["value"]) + 4
            if lay["kind"] == "2v":
                for xx in range(cx + 3, cx + 4 + vw):
                    for yy in range(cy - 4, cy + 5):
                        soft.add((xx, yy))
            elif lay["kind"] == "2h":
                # value sits below the part, left-justified at its
                # left edge in a smaller font (see valat below)
                vw2 = int(len(part["value"]) * 0.85) + 3
                for xx in range(cx - lay["w"] // 2,
                                cx - lay["w"] // 2 + vw2):
                    for yy in (cy + lay["h"] // 2 + 2,
                               cy + lay["h"] // 2 + 3,
                               cy + lay["h"] // 2 + 4):
                        soft.add((xx, yy))
            else:
                for xx in range(cx - vw // 2, cx + vw // 2 + 1):
                    for yy in (cy + lay["h"] // 2 + 1,
                               cy + lay["h"] // 2 + 2,
                               cy + lay["h"] // 2 + 3):
                        soft.add((xx, yy))
                rw2 = text_gu(part["ref"]) + 2
                for xx in range(cx - lay["w"] // 2 - 2,
                                cx - lay["w"] // 2 + rw2):
                    for yy in (cy - lay["h"] // 2 - 3,
                               cy - lay["h"] // 2 - 2,
                               cy - lay["h"] // 2 - 1):
                        soft.add((xx, yy))
            fplib, fpname = part["fp"]
            if lay["kind"] == "2v":
                refat = (mm(cx + 5), mm(cy - 2))
                valat = (mm(cx + 5), mm(cy + 3))
                valeff = '(font (size 1.27 1.27))'
            elif lay["kind"] == "2h":
                # Long spec-note values on adjacent horizontal parts
                # (the HV divider chain) collide when centred; run
                # them left-justified from the part's left edge in a
                # 1.0 mm font so a 40-char value fits a normal pitch.
                refat = (mm(cx - lay["w"] // 2), mm(cy - lay["h"] // 2 - 2))
                valat = (mm(cx - lay["w"] // 2), mm(cy + lay["h"] // 2 + 3))
                valeff = '(font (size 1.0 1.0)) (justify left)'
            else:
                refat = (mm(cx - lay["w"] // 2), mm(cy - lay["h"] // 2 - 2))
                valat = (mm(cx), mm(cy + lay["h"] // 2 + 2))
                valeff = '(font (size 1.27 1.27))'
            inst = [f'(symbol (lib_id {q("pdlvds:"+name)}) (at {mm(cx)} {mm(cy)} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {q(U())})']
            inst.append(f'  (property "Reference" {q(part["ref"])} (at {refat[0]} {refat[1]} 0) (effects (font (size 1.27 1.27))))')
            inst.append(f'  (property "Value" {q(part["value"])} (at {valat[0]} {valat[1]} 0) (effects {valeff}))')
            inst.append(f'  (property "Footprint" {q(fplib+":"+fpname)} (at {mm(cx)} {mm(cy)} 0) (effects (font (size 1.27 1.27)) hide))')
            inst.append('  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
            inst.append(f'  (instances (project "pdlvds_rx" (path "/{SHEET_UUID}" (reference {q(part["ref"])}) (unit 1))))')
            inst.append(')')
            instances.append("\n".join(inst))
            for n, (dx, dy, dirx, diry) in lay["pins"].items():
                _pname, ptype, net = lay["pinsinfo"][n]
                px, py = cx + dx, cy + dy
                pincell[(px, py)] = net
                c = lay["cls"][n]
                if net is None:
                    # no-connect markers: see the long note in git
                    # history — pins whose type is already no_connect
                    # carry the declaration in their type; a marker on
                    # top is a double declaration KiCad 8 flags both
                    # ways. Markers stay for the other net-None pins.
                    if ptype != "no_connect":
                        ncs.append(f'(no_connect (at {mm(px)} {mm(py)}) (uuid {q(U())}))')
                elif c == "power":
                    ex, ey2 = px + dirx * 2, py + diry * 2
                    stub_segs.append((px, py, ex, ey2))
                    wires.append(f'(wire (pts (xy {mm(px)} {mm(py)}) (xy {mm(ex)} {mm(ey2)})) (stroke (width 0) (type default)) (uuid {q(U())}))')
                    mask = 1 if diry == 0 else 2
                    for cell in _seg_cells((px, py, ex, ey2)):
                        e = wiremap.setdefault(cell, [net, 0])
                        e[1] |= mask
                    if net == "GND":
                        rot = ROT_DOWN_NATURAL[(dirx, diry)]
                    else:
                        rot = ROT_UP_NATURAL[(dirx, diry)]
                    vat = (ex + dirx * 5, ey2 + diry * 5)
                    emit_power_instance(power_lib(net), net, ex, ey2,
                                        rot, vat)
                    # glyph obstacle zone: the glyph itself is ~2 GU
                    # wide; block a +-1 GU swath along its axis. Any
                    # wider and the zone seals the exit rows of the
                    # part's own neighbouring pins (pin rows are 2 GU
                    # apart) — that was the APD_A seal on U1. The
                    # value text is NOT an obstacle (a rare wire
                    # strike through text is cosmetic; a sealed pin
                    # is fatal).
                    for k in range(0, 9):
                        for s_ in (-1, 0, 1):
                            blocked.add((ex + dirx * k + (s_ if diry else 0),
                                         ey2 + diry * k + (s_ if dirx else 0)))
                    stats["power_pins"] += 1
                elif c == "label":
                    ex, ey2 = px + dirx * 4, py + diry * 4
                    stub_segs.append((px, py, ex, ey2))
                    wires.append(f'(wire (pts (xy {mm(px)} {mm(py)}) (xy {mm(ex)} {mm(ey2)})) (stroke (width 0) (type default)) (uuid {q(U())}))')
                    mask = 1 if diry == 0 else 2
                    for cell in _seg_cells((px, py, ex, ey2)):
                        e = wiremap.setdefault(cell, [net, 0])
                        e[1] |= mask
                    lrot = {(1, 0): 0, (-1, 0): 180, (0, -1): 90,
                            (0, 1): 270}[(dirx, diry)]
                    just = {(1, 0): "left", (-1, 0): "right",
                            (0, -1): "left", (0, 1): "left"}[(dirx, diry)]
                    labels.append(f'(global_label {q(net)} (shape input) (at {mm(ex)} {mm(ey2)} {lrot}) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {just})) (uuid {q(U())}) (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {mm(ex)} {mm(ey2)} {lrot}) (effects (font (size 1.27 1.27)) hide)))')
                    # label text zone is a router obstacle
                    tw = text_gu(net)
                    if dirx:
                        xs = range(ex, ex + dirx * tw, dirx)
                        for xx in xs:
                            for yy in (ey2 - 1, ey2, ey2 + 1):
                                blocked.add((xx, yy))
                    else:
                        ys = range(ey2, ey2 + diry * tw, diry)
                        for yy in ys:
                            for xx in (ex - 1, ex, ex + 1):
                                blocked.add((xx, yy))
                    stats["label_pins"] += 1
                else:  # wire
                    net_pins.setdefault(net, []).append((px, py))
                    stats["wire_pins"] += 1
        # flag strip: power symbol + wire + PWR_FLAG per homed net
        for (net, sx, sy) in fr["slots"]:
            emit_power_instance(power_lib(net), net, sx, sy,
                                0, (sx, sy - 6))
            wires.append(f'(wire (pts (xy {mm(sx)} {mm(sy)}) (xy {mm(sx+6)} {mm(sy)})) (stroke (width 0) (type default)) (uuid {q(U())}))')
            flg_seq[0] += 1
            fref = f"#FLG{flg_seq[0]:02d}"
            fx, fy = mm(sx + 6), mm(sy)
            instances.append(f'(symbol (lib_id "power:PWR_FLAG") (at {fx} {fy} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {q(U())}) (property "Reference" {q(fref)} (at {fx} {fy} 0) (effects (font (size 1.27 1.27)) hide)) (property "Value" "PWR_FLAG" (at {fx} {fy} 0) (effects (font (size 1.27 1.27)) hide)) (property "Footprint" "" (at {fx} {fy} 0) (effects (font (size 1.27 1.27)) hide)) (property "Datasheet" "" (at {fx} {fy} 0) (effects (font (size 1.27 1.27)) hide)) (instances (project "pdlvds_rx" (path "/{SHEET_UUID}" (reference {q(fref)}) (unit 1)))))')
        # route the intra-region nets
        routed = route_region(fr, net_pins, blocked, pincell, wiremap, soft)
        label_zones = []
        for net, (segs, jpts) in routed.items():
            stats["routed_nets"] += 1
            for (x1, y1, x2, y2) in segs:
                wires.append(f'(wire (pts (xy {mm(x1)} {mm(y1)}) (xy {mm(x2)} {mm(y2)})) (stroke (width 0) (type default)) (uuid {q(U())}))')
                stats["wire_segs"] += 1
            for (jx, jy) in jpts:
                junctions.append(f'(junction (at {mm(jx)} {mm(jy)}) (diameter 0) (color 0 0 0 0) (uuid {q(U())}))')
                stats["junctions"] += 1
            # One global label ON the net's longest segment names the
            # net (drawn wires alone would leave it with a generated
            # Net-(...) name; a local label would name it "/NAME",
            # sheet-prefixed — both break the netlist identity, a
            # global label gives the bare name, probe-verified).
            others = [s2 for n2, (sg2, _j2) in routed.items()
                      if n2 != net for s2 in sg2] + stub_segs
            (ax, ay), arot = net_label_anchor(segs, set(jpts), net,
                                              label_zones, others)
            labels.append(f'(global_label {q(net)} (shape input) (at {mm(ax)} {mm(ay)} {arot}) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify left)) (uuid {q(U())}) (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {mm(ax)} {mm(ay)} {arot}) (effects (font (size 1.27 1.27)) hide)))')
            stats["net_labels"] += 1

    out = ['(kicad_sch (version 20230121) (generator "pdlvds-gen")', f'(uuid {SHEET_UUID})',
           '(paper "A0")', '(title_block (title "PDLVDS-RX rev A — photodiode LVDS receiver") (rev "A"))',
           '(lib_symbols']
    out += defs
    for _nm, sd in custom_power.values():
        sdx = sd.replace('(symbol "' + _nm + '"',
                         '(symbol "pdlvds:' + _nm + '"', 1)
        out.append(sdx)
    out.append(stock_power_def("GND"))
    out.append(stock_power_def("+5V"))
    # PWR_FLAG definition copied from the KiCad power library, with
    # the library-prefixed name — see git history for why the bare
    # name leaves every flag electrically inert.
    out.append(stock_power_def("PWR_FLAG"))
    out.append(')')
    out += graphics + instances + wires + junctions + labels + ncs
    out.append('(sheet_instances (path "/" (page "1")))')
    out.append(')')
    text = "\n".join(out) + "\n"
    text = re.sub(r'\(uuid "([0-9a-f-]{36})"\)', r'(uuid \1)', text)
    open('hw/pdlvds_rx.kicad_sch', 'w').write(text)
    # also write the symbol library file (same defs) for sym-lib-table
    lib = ['(kicad_symbol_lib (version 20211014) (generator "pdlvds-gen")'] + defs + \
          [sd.replace('(symbol "' + nm + '"', '(symbol "pdlvds:' + nm + '"', 1)
           for nm, sd in custom_power.values()] + [')']
    open('hw/pdlvds.kicad_sym', 'w').write("\n".join(lib) + "\n")
    print(f"schematic written: {len(circuit.PARTS)} parts, "
          f"{stats['routed_nets']} nets drawn with "
          f"{stats['wire_segs']} wire segments + {stats['junctions']} junctions "
          f"+ {stats['net_labels']} on-wire net labels, "
          f"{stats['wire_pins']} wire pins, {stats['label_pins']} label pins, "
          f"{stats['power_pins']} power-symbol pins, {len(ncs)} no-connects")

if __name__ == "__main__":
    main()
