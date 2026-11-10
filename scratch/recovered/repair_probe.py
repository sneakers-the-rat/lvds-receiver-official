import sys, time, resource
sys.path.insert(0, 'hw')

def rss():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024

import importlib.util
spec = importlib.util.spec_from_file_location('repair', 'hw/repair.py')
rep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rep)
import pcbnew
t0 = time.time()
board = pcbnew.LoadBoard('/tmp/board_test.kicad_pcb')
print(f"load: {time.time()-t0:.1f}s RSS={rss()}MB", flush=True)
items, pad_cells = rep.build_items(board)
print(f"build_items: {time.time()-t0:.1f}s RSS={rss()}MB nets={len(pad_cells)}", flush=True)
g = rep.compute_groups(board)
multi = {n: len(gs) for n, gs in g.items() if len(gs) > 1}
print(f"compute_groups: {time.time()-t0:.1f}s RSS={rss()}MB multi={len(multi)}", flush=True)
print("top multi:", sorted(multi.items(), key=lambda kv: -kv[1])[:8], flush=True)
