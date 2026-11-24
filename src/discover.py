#!/usr/bin/env python3
"""Discover public-document candidates from app names. Search results are leads only."""
import argparse,concurrent.futures,datetime as dt,json,re,time,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode,urlparse,urldefrag
from urllib.request import Request,urlopen
from audit import safe_url,SafeRedirect,UA,MAX_BYTES
from urllib.request import build_opener

PURPOSES={'auth':'API authentication OAuth API key documentation','access':'developer API access pricing free trial approval','api':'API reference REST GraphQL documentation','mcp':'official MCP server Model Context Protocol'}
WORDS={'auth':{'authentication','authorization','oauth','token','api-key'},'access':{'pricing','access','plans','partner','developer'},'api':{'api','reference','rest','graphql'},'mcp':{'mcp','model-context-protocol'}}
class Discovery:
 def __init__(self,cache,delay=2,fixture=None):self.fixture=fixture;self.cache=Path(cache);self.cache.mkdir(parents=True,exist_ok=True);self.delay=delay;self.last=0;self.opener=build_opener(SafeRedirect())
 def search(self,query,offline=False):
  if self.fixture:
   fixture=json.loads(Path(self.fixture).read_text())
   return {'query':query,'status':'recorded_fixture_replay','provider':'recorded_public_search_fixture','results':fixture['results']}
  import hashlib
  file=self.cache/(hashlib.sha256(query.encode()).hexdigest()+'.json')
  if file.exists():return json.loads(file.read_text())
  if offline:return {'query':query,'status':'offline_cache_miss','results':[]}
  url='https://www.bing.com/search?'+urlencode({'format':'rss','q':query,'setlang':'en-US'})
  try:
   safe_url(url);time.sleep(max(0,self.delay-(time.monotonic()-self.last)))
   with self.opener.open(Request(url,headers={'User-Agent':UA}),timeout=18) as r:
    raw=r.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:raise ValueError('Search response too large')
   self.last=time.monotonic();root=ET.fromstring(raw)
   results=[{'title':n.findtext('title') or '', 'url':n.findtext('link') or '', 'snippet':n.findtext('description') or ''}for n in root.findall('./channel/item')]
   result={'query':query,'status':'ok' if results else 'no_results','provider':'bing_public_rss','retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat(),'results':results}
  except Exception as exc:result={'query':query,'status':'search_error','error_type':type(exc).__name__,'error':str(exc)[:200],'results':[]}
  file.write_text(json.dumps(result,indent=2));return result

def score_candidate(app,purpose,item):
 p=urlparse(item['url']);text=(item['title']+' '+p.path).lower();tokens=set(re.findall(r'[a-z0-9]+',app['name'].lower()));domains=app.get('official_domains',[])
 official=bool(domains) and any(p.hostname==d or (p.hostname or '').endswith('.'+d) for d in domains)
 name_match=bool(tokens) and any(t in ((p.hostname or '')+' '+text) for t in tokens if len(t)>2)
 score=5*official+2*name_match+sum(w in text for w in WORDS[purpose])
 if any(w in text for w in ('wikipedia','jobs','career','reddit','stackoverflow')):score-=5
 return dict(item,purpose=purpose,relevance_score=score,official_domain_confirmed=official,status='discovery_lead_only')

def discover_app(engine,app,offline=False):
 logs=[];selected={}
 for purpose,suffix in PURPOSES.items():
  domain=(' site:'+app['official_domains'][0]) if app.get('official_domains') else ''
  response=engine.search(app['name']+' '+suffix+domain,offline);logs.append(response)
  ranked=sorted((score_candidate(app,purpose,r) for r in response['results']),key=lambda r:r['relevance_score'],reverse=True)
  # A primary-domain allowlist must be supplied or separately confirmed. No name-similarity upgrade.
  for item in ranked:
   if not item['official_domain_confirmed'] or item['relevance_score']<6:continue
   semantic=(item['title']+' '+urlparse(item['url']).path).lower()
   if purpose in ('auth','api') and not any(t in semantic for t in ('api','oauth','developer','rest','graphql')):continue
   if purpose=='mcp' and not any(t in semantic for t in ('mcp','model-context-protocol')):continue
   if purpose=='access' and not any(t in semantic for t in ('pricing','plans','api','developer','partner')):continue
   url=urldefrag(item['url'])[0]
   if urlparse(url).scheme!='https':continue
   selected.setdefault(url,dict(item,url=url))
   break
 out=dict(app);out['sources']=[{'url':r['url'],'purpose':r['purpose'],'discovered_by':'recorded_fixture' if engine.fixture else 'bing_public_rss','relevance_score':r['relevance_score']}for r in selected.values()];out['discovery_status']='sources_found' if out['sources'] else 'needs_source_discovery_review';out['discovery_leads']=[score_candidate(app,purpose,r)for purpose,log in zip(PURPOSES,logs)for r in log['results']]
 return out,logs

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--cache',default='output/search-cache');p.add_argument('--offline',action='store_true');p.add_argument('--search-fixture',help='Explicit recorded-search replay fixture, never described as a live search');a=p.parse_args();data=json.loads(Path(a.input).read_text());engine=Discovery(a.cache,fixture=a.search_fixture);apps=[];logs=[]
 if not data.get('apps'):raise SystemExit('No apps supplied. Official input remains required.')
 for app in data['apps']:
  out,log=discover_app(engine,app,a.offline);apps.append(out);logs.extend(log)
 data['apps']=apps;Path(a.output).write_text(json.dumps(data,indent=2));Path(a.output+'.search-log.json').write_text(json.dumps(logs,indent=2));print(json.dumps({'apps':len(apps),'with_sources':sum(bool(x['sources'])for x in apps),'search_errors':sum(x['status']=='search_error'for x in logs),'note':'Search snippets are never research evidence.'}))
if __name__=='__main__':main()
