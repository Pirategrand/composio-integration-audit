#!/usr/bin/env python3
"""Validate, aggregate and audit a research dataset without pretending prose is ground truth."""
from __future__ import annotations
import argparse,collections,datetime as dt,hashlib,json,random,re,sys
from pathlib import Path
from urllib.parse import urlparse

PATHS={'free_self_serve','trial_self_serve','paid_self_serve','admin_gated','review_gated','partner_gated','unknown'}
VERDICTS={'ready','conditional','blocked','unknown'}
REQUIRED={'id','name','category','description','auth_methods','access','api','mcp','verdict','blocker','evidence','confidence'}

def validate(rows,expected=None):
 errors=[];ids=set();names=set()
 if expected is not None and len(rows)!=expected:errors.append(f'Expected {expected} apps; got {len(rows)}')
 for i,r in enumerate(rows):
  missing=REQUIRED-r.keys()
  if missing:errors.append(f'Row {i}: missing {sorted(missing)}');continue
  if r['id']in ids:errors.append(f'Duplicate id {r["id"]}')
  if r['name'].lower()in names:errors.append(f'Duplicate name {r["name"]}')
  ids.add(r['id']);names.add(r['name'].lower())
  if r['access'].get('credential_path')not in PATHS:errors.append(f'{r["id"]}: invalid access path')
  if r['verdict']not in VERDICTS:errors.append(f'{r["id"]}: invalid verdict')
  if not r['evidence']:errors.append(f'{r["id"]}: no evidence')
  for e in r['evidence']:
   u=urlparse(e.get('url',''))
   if u.scheme!='https' or not u.netloc or u.username or u.password:errors.append(f'{r["id"]}: invalid evidence URL')
  if r['mcp'].get('status')not in ('official','community_only','not_confirmed'):errors.append(f'{r["id"]}: invalid MCP status')
 return errors

def auth_family(value):
 s=value.lower()
 if 'oauth'in s:return 'OAuth'
 if 'basic'in s:return 'Basic'
 if 'digest'in s:return 'Digest'
 if 'key'in s:return 'API key'
 if 'token'in s:return 'Token'
 if 'service account'in s:return 'Service account'
 return 'Other'

def summarize(rows):
 counts=lambda f:dict(collections.Counter(f(r)for r in rows))
 category={}
 for r in rows:
  c=category.setdefault(r['category'],{'apps':0,'ready':0,'conditional':0,'blocked':0,'unknown':0,'free_or_trial':0,'official_mcp':0})
  c['apps']+=1;c[r['verdict']]+=1;c['free_or_trial']+=r['access']['credential_path']in ('free_self_serve','trial_self_serve');c['official_mcp']+=r['mcp']['status']=='official'
 auth=collections.Counter()
 for r in rows:auth.update(set(auth_family(v)for v in r['auth_methods']))
 urls={e['url']for r in rows for e in r['evidence']}
 return {'apps':len(rows),'evidence_urls':len(urls),'citations':sum(len(r['evidence'])for r in rows),'verdicts':counts(lambda r:r['verdict']),'credential_paths':counts(lambda r:r['access']['credential_path']),'mcp':counts(lambda r:r['mcp']['status']),'mcp_scopes':counts(lambda r:r['mcp'].get('scope','not_classified')),'auth_support_counts':dict(auth),'categories':category,'confidence':counts(lambda r:r['confidence']),'human_verified':0,'independent_accuracy':None,'auth_denominator_note':'Each app can support multiple authentication families; counts overlap.'}

def qa_sample(rows,n=20,seed=23):
 rng=random.Random(seed);groups=collections.defaultdict(list)
 for row in rows:groups[row['category']].append(row)
 chosen=[]
 for category in sorted(groups):
  candidates=sorted(groups[category],key=lambda r:(r['verdict']=='ready',r['confidence']=='high',r['id']))
  rng.shuffle(candidates);candidates.sort(key=lambda r:(r['verdict']=='ready',r['confidence']=='high'))
  if len(chosen)<n:chosen.append(candidates[0])
 remaining=[r for r in rows if r['id']not in {c['id']for c in chosen}];rng.shuffle(remaining);remaining.sort(key=lambda r:(r['verdict']=='ready',r['confidence']=='high'))
 return chosen+remaining[:max(0,n-len(chosen))]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',nargs='+',required=True);p.add_argument('--output',required=True);p.add_argument('--expected-count',type=int,default=100);a=p.parse_args();rows=[];hashes={}
 for f in a.input:
  blob=Path(f).read_bytes();data=json.loads(blob);rows.extend(data if isinstance(data,list)else data['apps']);hashes[Path(f).name]=hashlib.sha256(blob).hexdigest()
 errors=validate(rows,a.expected_count)
 if errors:print('\n'.join(errors),file=sys.stderr);return 2
 rows.sort(key=lambda r:(r['category'],r['name'].lower()))
 for i,r in enumerate(rows,1):r['number']=i
 out=Path(a.output);out.mkdir(parents=True,exist_ok=True);summary=summarize(rows)
 payload={'title':'Which apps are ready for agents?','generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'selection':'Researcher-selected 100-app benchmark; the assignment page referenced a list that was not present. Selection approved by the candidate.','methodology':'AI-assisted primary-document research plus executable collection, validation and verification utilities. No paid app accounts or credential execution.','input_hashes':hashes,'metrics':summary,'apps':rows}
 (out/'dataset.json').write_text(json.dumps(payload,indent=2));(out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'sample-queue.json').write_text(json.dumps({'method':'Category-stratified and risk-prioritized, seed23; not a random population-accuracy estimate.','sample_ids':[r['id']for r in qa_sample(rows)]},indent=2));print(json.dumps(summary,indent=2));return 0
if __name__=='__main__':sys.exit(main())
