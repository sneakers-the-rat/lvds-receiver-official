#!/usr/bin/env python3
import csv
from collections import defaultdict
from datetime import datetime, timezone

M='metrics/'
series=list(csv.DictReader(open(M+'token_series.csv')))
per=defaultdict(lambda:{'rows':0,'in':0,'out':0,'first':None,'last':None})
for r in series:
    a=per[r['agent_id']]; a['rows']+=1; a['in']+=int(r['input_tokens']); a['out']+=int(r['output_tokens'])
    a['first']=r['ts_utc'] if a['first'] is None else min(a['first'],r['ts_utc'])
    a['last']=r['ts_utc'] if a['last'] is None else max(a['last'],r['ts_utc'])

TREE={
 '4925d244-018c-4b4f-9fad-7b3ad78af7c1':('main agent (root of this chat: orchestration, pushes, CI merges, user reports)',''),
 '211e6068-5645-443d-821c-d965a1288a6c':('build coordinator #1 (router v1-v5, repair passes 1-4, stage 7b/7c start)',''),
 '04d878b8-e46d-47c3-a3e8-19842ed9ea6c':('coordinator #1 child worker','spawn prompt in agent.subagent_spawns'),
 '6b643e67-3b72-4a34-a4e4-cb88906fc170':('coordinator #1 child worker','spawn prompt in agent.subagent_spawns'),
 '6ff926cd-6c17-4a41-8909-98b586b5f440':('coordinator #1 child worker','spawn prompt in agent.subagent_spawns'),
 '3c689d8e-9bcc-47b0-a096-4767120a160c':('CI-fix worker, rounds 1-2',''),
 '263d02bd-2694-4be4-a34b-d020557c1979':('CI-fix worker, round 3',''),
 'fbee6d75-6e0b-4c8a-a720-6ef52d21c0d2':('CI-fix worker, round 4 (ERC)',''),
 '00079813-c48a-433e-bd73-476dd6ede479':('routing-history gallery worker, round 1',''),
 'ff0c75ad-4e6c-4321-bfa3-a2ca61b971bc':('routing-history gallery worker, round 2 (route-only renders)',''),
 'e3e498fa-2d0f-4ea0-896f-06f51051aa22':('routing-history gallery worker, round 3 (light-on-dark)',''),
 '7f6dd3c0-90bf-4b74-9767-641daf60ab88':('CI speed worker',''),
 'b3484ddd-409f-4eb0-bc21-c912679c6b5d':('CI-signal worker, round 1',''),
 '13c2bc99-3cf3-4499-a01f-dda273939356':('CI-signal worker, round 2',''),
 'b785e77a-5ae4-47b7-a4a9-61508885fa25':('CI-signal worker, round 3',''),
 '110e2372-a411-4917-9496-e2188176d9f6':('build coordinator #2 (router v6 + Freerouting lines)','RUNNING at snapshot: no usage row yet (rows land at completion) - excluded from totals'),
 '60e10a13-9832-4f5a-b861-c8112a74866b':('token-metrics worker (this export)','RUNNING at snapshot: no usage row yet - excluded from totals'),
}
# (worker_agent_id, history_agent_id, run scheduled ts) from scheduler.job_runs
RUNS=[
 ('24e0eb6c-44aa-4edb-b20b-5aa162bbbee9','a3e40860-2586-4cf9-82a8-2a75ddc66333',1793741956),
 ('20029001-796e-47cd-954c-3275a5ba1f49','8cd3872d-6d1a-4019-a2ec-2fc4eaf8ba32',1793740156),
 ('5c02f48f-e810-477e-a1a5-b0e051554599','666e7905-566f-4542-b7c8-e3a635056245',1793743756),
 ('e6df4119-7d10-4878-bda3-f7028100059a','ef183183-61a9-4861-924b-f734c2af0d40',1793745556),
 ('17cf59bf-8385-4af3-b3d2-68307731e9ae','d5e5d654-fe3e-40d4-95d4-8b6dc95f990a',1793747356),
 ('702cfae9-6d8c-406b-82a2-813949aadb2b','6a97695b-6751-4abd-9929-f5f37e468e68',1793749156),
 ('0425f4c8-b441-42cd-b0c1-45614475590c','85d4defd-603f-4301-993d-8d2d3551c8ea',1793750956),
 ('1960d6c4-e52f-4f1b-8a20-979b5eca273b','e7c8284e-984b-4ac2-a44b-93088cb7c38e',1793752756),
 ('f733d408-fc0f-4f72-bad0-e8122c5005dc','f619171e-4521-4863-b1d1-15245f6f2fa3',1793754556),
 ('8bca1620-a5e4-45bc-9317-c968fdc57d13','f495395a-2b18-40e9-9b68-0ec796786ae1',1793756356),
 ('c7a4e87c-3725-4588-8cf9-d8eb9365731c','01f324ab-0034-4376-92f0-6d70e32d9a32',1793758156),
 ('954f2fb0-37ef-45d3-8bb6-17a11f93d581','56fcfcc3-9f6e-4c4a-920b-ff977d6e1bc4',1793759956),
 ('fc82ce37-fd26-4628-bd0b-ee8562c23198','c85c9228-2542-4b64-a2a4-57fa956a0576',1793761756),
 ('18e4ad88-a14e-4dcc-949a-9be952075632','d4391ab4-4e7c-4d77-9067-46dde4939300',1793763556),
 ('7fa5c66c-a4a7-4422-a8bd-18e29bf7beee','2e0c24c3-50b8-43e3-b1b4-29100617c5f2',1793765356),
 ('b506df93-d341-44f6-abc2-a6ea85961130','a8dba706-0be9-4395-80a9-73b16c43d91e',1793767156),
 ('704a193a-d248-432c-b2a3-d40995da7da1','b763af74-d05d-4a08-adb7-d169eca32540',1793768956),
 ('a5c042f2-7da4-4c40-9402-d2ffbb94730e','b86bfcad-e748-48fb-888c-37c6c390ac86',1793770756),
 ('ae32c733-a578-486c-b7a8-3806eda1dc93','47385b29-ea4b-4e6a-8b39-0be1ff54def1',1793772556),
 ('270d1279-1c15-4987-8933-fd315926044c','114e9629-7982-4555-bf09-37914c8a9ee3',1793776156),
 ('91a6bfe2-2e01-45f6-81f6-9f41461c757d','6608b8a8-96c5-4a91-9bb7-9c620fc1e56b',1793777956),
 ('dc0bfe1a-e481-4e4a-9fe4-7fc9ba02a4c9','dee33dc9-3fdc-4561-bef6-9869699d6401',1793774356),
 ('e1d5b58c-f788-4aa1-9682-171cbfbbe165','6f4d20c5-47b4-4bf6-8065-beccf060eb00',1793738356),
]
def ts(t): return datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
out=[]
for aid,(role,note) in TREE.items():
    a=per.get(aid,{'rows':0,'in':0,'out':0,'first':'','last':''})
    out.append([aid,'chat-tree',role,a['rows'],a['in'],a['out'],a['first'] or '',a['last'] or '',note])
for w,h,t in RUNS:
    for aid,role in ((h,'pdlvds-progress checkpoint worker (cron job pdlvds-progress)'),
                     (w,'pdlvds-progress run/delivery agent (cron job pdlvds-progress)')):
        a=per.get(aid,{'rows':0,'in':0,'out':0,'first':'','last':''})
        note=f'run scheduled {ts(t)}' + ('' if aid in per else '; no usage row recorded')
        out.append([aid,'checkpoint-cron',role,a['rows'],a['in'],a['out'],a['first'] or '',a['last'] or '',note])
with open(M+'agents.csv','w',newline='') as f:
    wcsv=csv.writer(f); wcsv.writerow(['agent_id','scope','role','usage_rows','input_tokens','output_tokens','first_row_utc','last_row_utc','notes']); wcsv.writerows(out)
for scope in ('chat-tree','checkpoint-cron'):
    rows=[r for r in out if r[1]==scope]
    print(scope, 'agents:',len(rows), 'rows:',sum(r[3] for r in rows), 'input:',sum(r[4] for r in rows), 'output:',sum(r[5] for r in rows))
print('TOTAL agents listed:', len(out))
