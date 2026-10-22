from pathlib import Path

raise SystemExit("Archived v0.1 one-shot migration. Do not run against current source.")

path = Path("src/solarops/reports/templates/monthly.html")
s = path.read_text(encoding="utf-8")
s = s.replace(
    "{{ '합성 데이터 데모' if report.synthetic else 'BR-PVGen · 공개 데이터' }}",
    "{{ '합성·공개 혼합 데모' if report.synthetic and report.public else ('합성 데이터 데모' if report.synthetic else 'BR-PVGen · 공개 데이터') }}",
)
s = s.replace("{% if not report.synthetic %}", "{% if report.public %}")
path.write_text(s, encoding="utf-8")
path = Path("src/solarops/api/dashboard.html")
s = path.read_text(encoding="utf-8")
s = s.replace("get('/api/v1/plants')", "get('/api/v1/plants?limit=100')")
s = s.replace("+'/metrics');let b=", "+'/metrics?limit=1');let b=")
s = s.replace(
    "b.onclick=()=>detail(p.plant_id,m.items.at(-1)?.local_date)",
    "b.onclick=async()=>{let last=await get('/api/v1/plants/'+encodeURIComponent(p.plant_id)+'/metrics?limit=1&offset='+Math.max(0,m.total-1));detail(p.plant_id,last.items[0]?.local_date)}",
)
s = s.replace(
    "r.period+' · '+r.scope+' · '+r.status",
    "r.period+' · '+r.scope+' · '+(r.status==='complete'?'월 전체':'부분 기간')",
)
path.write_text(s, encoding="utf-8")
