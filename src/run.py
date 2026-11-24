#!/usr/bin/env python3
"""One-command discovery, collection, contextual checks, sample queue and report."""
import argparse,datetime as dt,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--output',default='output/run');p.add_argument('--expected-count',type=int);p.add_argument('--offline',action='store_true');a=p.parse_args();source=Path(a.input).resolve();out=Path(a.output).resolve();data=json.loads(source.read_text());apps=data.get('apps',[])
 if not apps:raise SystemExit('The official app list is missing; no substitute is generated.')
 if a.expected_count is not None and len(apps)!=a.expected_count:raise SystemExit(f'Expected {a.expected_count} apps; received {len(apps)}.')
 out.mkdir(parents=True,exist_ok=True)
 def run(script,args):
  completed=subprocess.run([sys.executable,str(HERE/script),*args],capture_output=True,text=True)
  print(completed.stdout,end='')
  if completed.returncode:raise RuntimeError(script+': '+completed.stderr)
  return completed.stdout
 if any(not app.get('sources') for app in apps):
  discovered=out/'discovered.json';args=['--input',str(source),'--output',str(discovered),'--cache',str(out/'search-cache')]
  if a.offline:args+=['--offline']
  run('discover.py',args);data=json.loads(discovered.read_text())
 missing=[app['id'] for app in data['apps'] if not app.get('sources')]
 usable=[app for app in data['apps'] if app.get('sources')]
 status={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'requested_apps':len(apps),'processable_apps':len(usable),'discovery_unresolved':missing,'stage':'discovery_partial' if missing else 'research','human_checks':0,'independent_accuracy':None}
 (out/'run-status.json').write_text(json.dumps(status,indent=2))
 if not usable:
  print(json.dumps(status));return 3
 # A partial run is explicitly labeled and never reported as full coverage.
 data['apps']=usable
 if missing:data['provenance']=dict(data.get('provenance',{}),run_scope='partial',excluded_ids=missing)
 prepared=out/'processable-input.json';prepared.write_text(json.dumps(data,indent=2));args=['--input',str(prepared),'--output',str(out)]
 if a.offline:args+=['--offline']
 run('audit.py',args);run('synthesize.py',['--results',str(out/'results.json'),'--output',str(out/'contextual')]);
 from audit import render_report
 render_report(json.loads((out/'contextual/contextual-results.json').read_text()),out/'report.html')
 queue=run('review.py',['--results',str(out/'results.json'),'--sample','12']);(out/'human-review-queue.json').write_text(queue)
 print('Report:',out/'report.html');return 3 if missing else 0
if __name__=='__main__':
 try:sys.exit(main())
 except (ValueError,RuntimeError) as exc:print(str(exc),file=sys.stderr);sys.exit(2)
