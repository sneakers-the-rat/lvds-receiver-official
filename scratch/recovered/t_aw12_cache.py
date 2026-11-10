# t_aw12: checkpoint the post-X2-links model state for join-2 iterations
import pickle
state = dict(pool=pool, NEW=NEW, JOURNEYS=JOURNEYS, NET_HW=NET_HW,
             RIP_ADD=RIP_ADD, B=B, new_pads=new_pads,
             base_v3_len=len(base_v3), base_clk_len=len(base_clk),
             base_dm_len=len(base_dm), base_ref_len=len(base_ref))
with open('scratch/work/aw/state_aw.pkl', 'wb') as fh:
    pickle.dump(state, fh)
print('STATE CACHED: pool sizes', [len(x) for x in pool],
      'NEW sizes', [len(x) for x in NEW], flush=True)
print('T_AW12 CACHE COMPLETE', flush=True)
