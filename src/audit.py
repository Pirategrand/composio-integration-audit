#!/usr/bin/env python3
"""Public-document evidence collector. No keys, no accounts, no claims from memory."""
from __future__ import annotations
import argparse, collections, concurrent.futures, datetime as dt, hashlib, html, ipaddress, json, os, re, socket, sys, threading, time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser

VERSION = '0.1.0'
UA = 'AppEvidenceAudit/0.1 (public documentation research; no authentication)'
MAX_BYTES = 2_000_000
FIELDS = ('category','auth','access','api','mcp','buildability')

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.depth=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','noscript'): self.depth += 1
        if tag in ('p','div','li','h1','h2','h3','br','tr'): self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style','noscript') and self.depth: self.depth -= 1
    def handle_data(self, data):
        if not self.depth: self.parts.append(data)
    def text(self):
        return '\n'.join(re.sub(r'\s+',' ',line).strip() for line in ''.join(self.parts).splitlines() if line.strip())

def utcnow(): return dt.datetime.now(dt.timezone.utc).isoformat()
def digest(data): return hashlib.sha256(data).hexdigest()
def safe_url(url):
    p=urlparse(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password: raise ValueError('Only credential-free HTTPS documentation URLs are allowed')
    if p.port not in (None,443): raise ValueError('Nonstandard ports are not allowed')
    addresses=socket.getaddrinfo(p.hostname,443,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses): raise ValueError('Private, local or reserved network destination rejected')
    return url

class SafeRedirect(HTTPRedirectHandler):
    # Python versions before complete 308 handling require the 301 handler alias.
    http_error_308 = HTTPRedirectHandler.http_error_301
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

class Collector:
    def __init__(self, root, offline=False, refresh=False, delay=1.1):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
        self.offline=offline; self.refresh=refresh; self.delay=delay
        self.opener=build_opener(SafeRedirect()); self.robots={}; self.locks={}; self.last={}; self.guard=threading.Lock()
    def request(self,url):
        safe_url(url)
        req=Request(url,headers={'User-Agent':UA,'Accept':'text/html,text/plain,application/json;q=0.8'})
        with self.opener.open(req,timeout=18) as r:
            raw=r.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES: raise ValueError('Document exceeds size limit')
            typ=r.headers.get('Content-Type','')
            if not any(t in typ for t in ('text/','json','xml')): raise ValueError('Not a supported documentation content type')
            return raw,r.geturl(),typ
    def allowed(self,url):
        p=urlparse(url); origin=f'{p.scheme}://{p.netloc}'
        if origin not in self.robots:
            robot=RobotFileParser(); robot.set_url(origin+'/robots.txt')
            try:
                raw,_,_=self.request(robot.url); robot.parse(raw.decode('utf-8',errors='replace').splitlines())
            except HTTPError as exc:
                if exc.code == 404:
                    robot.parse([])
                else:
                    self.robots[origin]=(None,str(exc)); return False,'robots_unavailable'
            except Exception as exc:
                # A robots request failure is not permission to crawl.
                self.robots[origin]=(None,str(exc)); return False,'robots_unavailable'
            self.robots[origin]=(robot,None)
        robot,error=self.robots[origin]
        if robot is None: return False,'robots_unavailable'
        return robot.can_fetch(UA,url),'robots_disallowed'
    def fetch(self,url):
        key=digest(url.encode()); meta=self.root/f'{key}.json'
        if meta.exists() and not self.refresh:
            cached=json.loads(meta.read_text())
            if cached.get('status')=='ok':
                snapshot=self.root/cached['snapshot']
                if not snapshot.exists() or digest(snapshot.read_bytes())!=cached['text_sha256']: return {'url':url,'status':'cache_integrity_error'}
                return cached
        if self.offline: return {'url':url,'status':'offline_cache_miss'}
        host=urlparse(url).netloc
        with self.guard: lock=self.locks.setdefault(host,threading.Lock())
        with lock:
            try:
                safe_url(url)
                allowed,reason=self.allowed(url)
                if not allowed: return {'url':url,'status':reason}
                time.sleep(max(0,self.delay-(time.monotonic()-self.last.get(host,0))))
                raw,final,typ=self.request(url); self.last[host]=time.monotonic()
                text=raw.decode('utf-8',errors='replace')
                if 'html' in typ:
                    parser=TextExtractor(); parser.feed(text); text=parser.text()
                blob=text.encode(); snap=digest(blob)+'.txt'; (self.root/snap).write_bytes(blob)
                result={'url':url,'final_url':final,'status':'ok','fetched_at':utcnow(),'content_type':typ,'raw_sha256':digest(raw),'text_sha256':digest(blob),'snapshot':snap,'characters':len(text)}
            except Exception as exc: result={'url':url,'status':'fetch_error','error_type':type(exc).__name__,'error':str(exc)[:300],'fetched_at':utcnow()}
            meta.write_text(json.dumps(result,indent=2)); return result

RULES={
 'auth': [('OAuth2',r'oauth\s*2(?:\.0)?|oauth 2\.0'),('API key',r'api[- ]key'),('Basic',r'basic authentication|http basic'),('Bearer/token',r'bearer token|personal access token')],
 'access': [('free/trial signal',r'free (?:plan|tier|trial)|no credit card'),('paid gate signal',r'(?:paid|enterprise|premium) (?:plan|tier|subscription)|requires? a paid'),('approval gate signal',r'app review|admin(?:istrator)? approval|partner(?:ship)? (?:approval|required)|contact sales')],
 'api': [('REST signal',r'\bREST(?:ful)?\b'),('GraphQL signal',r'\bGraphQL\b')],
 'mcp': [('MCP mention',r'model context protocol|\bMCP server\b')]
}

def candidates(text,field):
    out=[]
    for label,pattern in RULES.get(field,[]):
        for match in list(re.finditer(pattern,text,re.I))[:2]:
            start=max(0,text.rfind('\n',0,match.start())+1); end=text.find('\n',match.end())
            if end<0: end=len(text)
            quote=text[max(start,match.start()-180):min(end,match.end()+220)]
            out.append({'value':label,'quote':quote,'offset':match.start(),'status':'candidate_not_verified'})
    return out

def analyze(app,docs,root):
    row={'id':app['id'],'name':app['name'],'category':app.get('category','unknown'),'description':app.get('description','Not supplied'),'sources':docs,'claims':{},'review_flags':[]}
    for field in RULES:
        claims=[]
        for doc in docs:
            if doc['status']!='ok': continue
            text=(Path(root)/doc['snapshot']).read_text()
            for claim in candidates(text,field): claim.update({'source_url':doc['url'],'snapshot':doc['snapshot']}); claims.append(claim)
        row['claims'][field]=claims
        if not claims: row['review_flags'].append('missing_'+field+'_evidence')
    access={c['value'] for c in row['claims']['access']}
    if len(access)>1: row['review_flags'].append('access_signals_need_scope_review')
    if not any(d.get('purpose') == 'access' for d in docs): row['review_flags'].append('no_dedicated_access_source')
    if not any(d.get('purpose') == 'mcp' for d in docs): row['review_flags'].append('no_dedicated_mcp_source')
    row['buildability']='needs_review'
    row['blocker']='Source-support candidates require contextual review; production access not tested'
    row['verification']={'agent_source_support':'candidate_extraction_only','human_checked':False}
    return row

def validate_input(data,expected=None):
    apps=data.get('apps')
    if not isinstance(apps,list) or not apps: raise ValueError('App list missing. Supply the employer list; no substitute is generated.')
    if expected is not None and len(apps)!=expected: raise ValueError(f'Expected {expected} apps, received {len(apps)}')
    seen=set()
    for app in apps:
        if not app.get('id') or app['id'] in seen: raise ValueError('Unique nonempty app ids required')
        seen.add(app['id'])
        if not app.get('name') or not app.get('sources'): raise ValueError('Each app needs a name and primary-source URLs')
        for source in app['sources']:
            p=urlparse(source['url'])
            if p.scheme!='https' or not p.hostname or p.username or p.password: raise ValueError('Source URL must be credential-free HTTPS')
    return apps

def render_report(payload,path):
    # JSON is data, never interpolated into executable code without escaping HTML delimiters.
    raw=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template=Path(__file__).with_name('report_template.html').read_text()
    path.write_text(template.replace('__DATA__',raw))

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input',required=True); p.add_argument('--output',default='output'); p.add_argument('--expected-count',type=int); p.add_argument('--offline',action='store_true'); p.add_argument('--refresh',action='store_true'); p.add_argument('--workers',type=int,default=4)
    a=p.parse_args(argv); data=json.loads(Path(a.input).read_text()); apps=validate_input(data,a.expected_count)
    output=Path(a.output); output.mkdir(parents=True,exist_ok=True); collector=Collector(output/'evidence',a.offline,a.refresh)
    urls=list(dict.fromkeys(s['url'] for app in apps for s in app['sources']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(a.workers,8))) as pool: docs=dict(zip(urls,pool.map(collector.fetch,urls)))
    rows=[analyze(app,[dict(docs[s['url']],purpose=s.get('purpose','unspecified')) for s in app['sources']],collector.root) for app in apps]
    payload={'version':VERSION,'generated_at':utcnow(),'input_sha256':digest(Path(a.input).read_bytes()),'provenance':data.get('provenance',{}),'apps':rows,'metrics':{'apps':len(rows),'sources':len(docs),'fetched':sum(d['status']=='ok' for d in docs.values()),'human_reviewed':0,'independent_accuracy':None}}
    (output/'results.json').write_text(json.dumps(payload,indent=2)); render_report(payload,output/'report.html')
    print(json.dumps(payload['metrics'])); return 0

if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,KeyError,json.JSONDecodeError) as exc: print(f'Input error: {exc}',file=sys.stderr); sys.exit(2)
