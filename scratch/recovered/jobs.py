import json,sys,urllib.request,datetime
def get(url):
    req=urllib.request.Request(url, headers={'Accept':'application/vnd.github+json','User-Agent':'ci-diag'})
    return json.load(urllib.request.urlopen(req))
def ts(s):
    return datetime.datetime.fromisoformat(s.replace('Z','+00:00')) if s else None
def dur(a,b):
    if not a or not b: return None
    return int((ts(b)-ts(a)).total_seconds())
for run_id in sys.argv[1:]:
    d=get(f'https://api.github.com/repos/sneakers-the-rat/lvds-receiver-official/actions/runs/{run_id}/jobs?per_page=100')
    print(f'=== run {run_id}')
    for j in d['jobs']:
        jd=dur(j['started_at'], j['completed_at'])
        print(f"  JOB {j['name']} [{j['conclusion']}] total={jd}s started={j['started_at']}")
        for s in j['steps']:
            sd=dur(s['started_at'], s['completed_at'])
            if sd is not None and sd>=5:
                print(f"    step {s['number']:2d} {s['name'][:64]:64s} {sd:5d}s [{s['conclusion']}]")
