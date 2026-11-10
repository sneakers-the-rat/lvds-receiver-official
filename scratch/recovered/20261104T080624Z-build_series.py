#!/usr/bin/env python3
"""Expand /tmp/series_rows.csv (short ids) to metrics/token_series.csv and
verify per-agent sums against the bounded aggregate query (created_at <=
1793779463) run separately via muse.db. R = root agent."""
import csv, sys
from datetime import datetime, timezone

ROOT = '4925d244-018c-4b4f-9fad-7b3ad78af7c1'
FULL = {
 '6b643e67':'6b643e67-3b72-4a34-a4e4-cb88906fc170','04d878b8':'04d878b8-e46d-47c3-a3e8-19842ed9ea6c',
 '6ff926cd':'6ff926cd-6c17-4a41-8909-98b586b5f440','6f4d20c5':'6f4d20c5-47b4-4bf6-8065-beccf060eb00',
 '8cd3872d':'8cd3872d-6d1a-4019-a2ec-2fc4eaf8ba32','a3e40860':'a3e40860-2586-4cf9-82a8-2a75ddc66333',
 '24e0eb6c':'24e0eb6c-44aa-4edb-b20b-5aa162bbbee9','3c689d8e':'3c689d8e-9bcc-47b0-a096-4767120a160c',
 '666e7905':'666e7905-566f-4542-b7c8-e3a635056245','5c02f48f':'5c02f48f-e810-477e-a1a5-b0e051554599',
 '263d02bd':'263d02bd-2694-4be4-a34b-d020557c1979','ef183183':'ef183183-61a9-4861-924b-f734c2af0d40',
 'e6df4119':'e6df4119-7d10-4878-bda3-f7028100059a','00079813':'00079813-c48a-433e-bd73-476dd6ede479',
 'fbee6d75':'fbee6d75-6e0b-4c8a-a720-6ef52d21c0d2','ff0c75ad':'ff0c75ad-4e6c-4321-bfa3-a2ca61b971bc',
 '7f6dd3c0':'7f6dd3c0-90bf-4b74-9767-641daf60ab88','d5e5d654':'d5e5d654-fe3e-40d4-95d4-8b6dc95f990a',
 '17cf59bf':'17cf59bf-8385-4af3-b3d2-68307731e9ae','e3e498fa':'e3e498fa-2d0f-4ea0-896f-06f51051aa22',
 '6a97695b':'6a97695b-6751-4abd-9929-f5f37e468e68','702cfae9':'702cfae9-6d8c-406b-82a2-813949aadb2b',
 '85d4defd':'85d4defd-603f-4301-993d-8d2d3551c8ea','0425f4c8':'0425f4c8-b441-42cd-b0c1-45614475590c',
 '211e6068':'211e6068-5645-443d-821c-d965a1288a6c','e7c8284e':'e7c8284e-984b-4ac2-a44b-93088cb7c38e',
 'b3484ddd':'b3484ddd-409f-4eb0-bc21-c912679c6b5d','13c2bc99':'13c2bc99-3cf3-4499-a01f-dda273939356',
 'f619171e':'f619171e-4521-4863-b1d1-15245f6f2fa3','f733d408':'f733d408-fc0f-4f72-bad0-e8122c5005dc',
 'b785e77a':'b785e77a-5ae4-47b7-a4a9-61508885fa25','f495395a':'f495395a-2b18-40e9-9b68-0ec796786ae1',
 '01f324ab':'01f324ab-0034-4376-92f0-6d70e32d9a32','56fcfcc3':'56fcfcc3-9f6e-4c4a-920b-ff977d6e1bc4',
 'c85c9228':'c85c9228-2542-4b64-a2a4-57fa956a0576','d4391ab4':'d4391ab4-4e7c-4d77-9067-46dde4939300',
 '2e0c24c3':'2e0c24c3-50b8-43e3-b1b4-29100617c5f2','a8dba706':'a8dba706-0be9-4395-80a9-73b16c43d91e',
 'b763af74':'b763af74-d05d-4a08-adb7-d169eca32540','b86bfcad':'b86bfcad-e748-48fb-888c-37c6c390ac86',
 '47385b29':'47385b29-ea4b-4e6a-8b39-0be1ff54def1','dee33dc9':'dee33dc9-3fdc-4561-bef6-9869699d6401',
 '114e9629':'114e9629-7982-4555-bf09-37914c8a9ee3','270d1279':'270d1279-1c15-4987-8933-fd315926044c',
 '6608b8a8':'6608b8a8-96c5-4a91-9bb7-9c620fc1e56b','91a6bfe2':'91a6bfe2-2e01-45f6-81f6-9f41461c757d',
}
# Expected per-agent (rows, input, output) from the bounded aggregate query.
EXPECTED = {
 '4925d244':(97,49411439,137679),'00079813':(1,3740528,16143),'01f324ab':(1,914622,5423),
 '0425f4c8':(1,47268,533),'04d878b8':(1,3089221,53683),'114e9629':(1,536647,4242),
 '13c2bc99':(1,3641257,23380),'17cf59bf':(1,68917,662),'211e6068':(1,2224018,8136),
 '24e0eb6c':(1,53120,411),'263d02bd':(1,6039766,36647),'270d1279':(1,55992,710),
 '2e0c24c3':(1,836329,4456),'3c689d8e':(1,9121511,45386),'47385b29':(1,1171590,7943),
 '56fcfcc3':(1,528135,3285),'5c02f48f':(1,59495,904),'6608b8a8':(1,538689,3629),
 '666e7905':(1,601811,6128),'6a97695b':(1,733884,4162),'6b643e67':(1,788734,34177),
 '6f4d20c5':(1,385384,3511),'6ff926cd':(1,2116475,39013),'702cfae9':(1,58878,800),
 '7f6dd3c0':(1,3755916,11915),'85d4defd':(1,545512,2883),'8cd3872d':(1,595395,5733),
 '91a6bfe2':(1,66851,588),'a3e40860':(1,505296,4190),'a8dba706':(1,763530,5384),
 'b3484ddd':(1,3087268,23626),'b763af74':(1,680079,4136),'b785e77a':(1,2443726,17957),
 'b86bfcad':(1,582384,3732),'c85c9228':(1,860684,4746),'d4391ab4':(1,488528,4784),
 'd5e5d654':(1,733431,5133),'dee33dc9':(1,440334,3392),'e3e498fa':(1,5960096,18709),
 'e6df4119':(1,65065,720),'e7c8284e':(1,677487,5299),'ef183183':(1,538374,4207),
 'f495395a':(1,520135,3269),'f619171e':(1,477726,4236),'f733d408':(1,59212,435),
 'fbee6d75':(1,4949062,19301),'ff0c75ad':(1,8545955,29044),
}
rows=[]
with open('/tmp/series_rows.csv') as f:
    for line in f:
        line=line.strip()
        if not line: continue
        ts,aid,inp,out = line.split(',')
        full = ROOT if aid=='R' else FULL[aid]
        rows.append((int(ts), full, int(inp), int(out)))
rows.sort(key=lambda r:(r[0], r[1]))
assert len(rows)==143, len(rows)
# verify per-agent
from collections import defaultdict
agg=defaultdict(lambda:[0,0,0])
for ts,aid,i,o in rows: agg[aid[:8]][0]+=1; agg[aid[:8]][1]+=i; agg[aid[:8]][2]+=o
bad=[]
for k,(n,i,o) in EXPECTED.items():
    a=agg.get(k)
    if not a or a[0]!=n or a[1]!=i or a[2]!=o: bad.append((k,(n,i,o),a))
if bad:
    print('MISMATCHES:', bad); sys.exit(1)
print('per-agent verification: all', len(EXPECTED), 'agents match the bounded aggregate query')
ti=sum(v[1] for v in EXPECTED.values()); to=sum(v[2] for v in EXPECTED.values())
print('TOTAL rows=143 input=%d output=%d total=%d' % (ti,to,ti+to))
import os
os.makedirs('/home/hatch/workspace/pdlvds-cifix/metrics', exist_ok=True)
ci=co=0
with open('/home/hatch/workspace/pdlvds-cifix/metrics/token_series.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['ts_epoch','ts_utc','agent_id','input_tokens','output_tokens','cum_input_tokens','cum_output_tokens','cum_total_tokens'])
    for ts,aid,i,o in rows:
        ci+=i; co+=o
        w.writerow([ts, datetime.fromtimestamp(ts,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), aid, i, o, ci, co, ci+co])
print('wrote metrics/token_series.csv; final cum input=%d output=%d' % (ci,co))
