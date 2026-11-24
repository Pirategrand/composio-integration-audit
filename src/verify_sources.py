#!/usr/bin/env python3
"""Re-fetch dataset citations and save reproducible public-document snapshots.

This measures retrieval and lexical support, NOT semantic correctness or human accuracy.
"""
from __future__ import annotations
import argparse,concurrent.futures,datetime as dt,hashlib,json,re,sys
from pathlib import Path
from audit import Collector

def support_signals(text):
 rules={'oauth':r'oauth\s*2?(?:\.\d)?','api_key':r'api[- ]key','token':r'\btoken\b','basic':r'basic auth','digest':r'digest auth','rest':r'\bREST\b','graphql':r'\bGraphQL\b','mcp':r'model context protocol|\bMCP\b','free_or_trial':r'free|trial|no.cost','gate':r'approval|review|partner|paid|enterprise|admin','lifecycle':r'end of (?:sale|support)|deprecated|shutdown|shut (?:off|down)|retire'}
 result={}
 for key,pattern in rules.items():
  matches=list(re.finditer(pattern,text,re.I))[:2]
  if matches:result[key]=[re.sub(r'\s+',' ',text[max(0,m.start()-100):m.end()+200])for m in matches]
 return result

def run(data,output,offline=False,limit=None):
 out=Path(output);out.mkdir(parents=True,exist_ok=True);collector=Collector(out/'snapshots',offline=offline)
 urls=list(dict.fromkeys(e['url']for a in data['apps']for e in a['evidence']))
 if limit:urls=urls[:limit]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6)as pool:docs=list(pool.map(collector.fetch,urls))
 index={}
 for d in docs:
  entry=dict(d)
  if d['status']=='ok':entry['support_signals']=support_signals((collector.root/d['snapshot']).read_text())
  index[d['url']]=entry
 statuses={}
 for d in docs:statuses[d['status']]=statuses.get(d['status'],0)+1
 report={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'public-citation retrieval check; lexical signals are not claim verification','attempted':len(docs),'total_dataset_urls':len(set(e['url']for a in data['apps']for e in a['evidence'])),'statuses':statuses,'human_checks':0,'independent_accuracy':None,'sources':index}
 (out/'source-checks.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k]for k in ('attempted','total_dataset_urls','statuses','human_checks','independent_accuracy')}));return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset',required=True);p.add_argument('--output',required=True);p.add_argument('--offline',action='store_true');p.add_argument('--limit',type=int);a=p.parse_args();run(json.loads(Path(a.dataset).read_text()),a.output,a.offline,a.limit)
if __name__=='__main__':main()
