#!/usr/bin/env python3
"""Context-aware candidate validation. Does not turn source agreement into human accuracy."""
import argparse,collections,copy,datetime as dt,json,re
from pathlib import Path

NEGATION=re.compile(r'no longer|not support|does not support|deprecated|removed|unsupported|not available',re.I)
PRODUCTION=re.compile(r'production|public app|publish|distribution|app review|verification',re.I)
SCOPES=re.compile(r'GitHub Apps and OAuth apps|client ID|client secret|token endpoint|exchange.*code',re.I)

def contextualize(field,claim):
 text=claim['quote'];out=copy.deepcopy(claim);out['status']='agent_context_candidate';out['context_notes']=[]
 if NEGATION.search(text):out['status']='needs_negation_review';out['context_notes'].append('The statement includes removal, deprecation or negation. Do not infer availability from the keyword.')
 if field=='auth' and claim['value']=='Basic' and SCOPES.search(text):out['status']='scoped_protocol_auth';out['context_notes'].append('Basic applies to a specified app/protocol endpoint, not necessarily end-user REST requests.')
 if PRODUCTION.search(text):out['context_notes'].append('Production/public distribution context. Do not generalize to personal development or sandbox access.')
 if re.search(r'sandbox|test mode|development mode',text,re.I):out['context_notes'].append('Sandbox/development statement. Production eligibility is unresolved.')
 if field=='mcp':
  out['status']='needs_mcp_ownership_review';out['context_notes'].append('A mention is not proof of an official runnable MCP server. Verify owner and repository/server endpoint.')
 if field=='access':
  out['status']='needs_access_scope_review';out['context_notes'].append('Confirm the specific plan, capability, account role, geography and sandbox versus production scope.')
 return out

def synthesize(data):
 payload=copy.deepcopy(data);changes=[]
 for app in payload['apps']:
  for field,claims in app['claims'].items():
   fresh=[]
   for claim in claims:
    updated=contextualize(field,claim);fresh.append(updated)
    if updated['status']!=claim.get('status'):changes.append({'app_id':app['id'],'field':field,'value':claim['value'],'before':claim.get('status'),'after':updated['status'],'source_url':claim['source_url'],'reason':'; '.join(updated['context_notes']) or 'Keyword-only extraction upgraded to contextual candidate, not verified fact.'})
   app['claims'][field]=fresh
  app['synthesis']={'auth_methods_for_normal_api_requests':'unknown_until_context_review','access':{'developer_credentials':'unknown','sandbox':'unknown','production':'unknown','public_distribution':'unknown','paid_plan':'unknown','admin_approval':'unknown'},'mcp':{'official':'unknown','community':'unknown'},'buildability':'needs_review','confidence':'insufficient_reviewed_evidence'}
 payload['contextual_pass']={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'reviewer_type':'agent','corrections':changes,'independent_accuracy':None}
 return payload

def cluster_reviewed(payload):
 rows=payload['apps'];counts=collections.Counter();denoms=collections.Counter()
 for row in rows:
  for field,review in row.get('reviewed',{}).items():
   if field in ('auth','access','api','mcp','buildability'):
    denoms[field]+=1;values=review['value'] if isinstance(review['value'],list) else [review['value']]
    for v in values:counts[(field,str(v))]+=1
 return {'apps':len(rows),'field_reviewed_denominators':dict(denoms),'patterns':[{'field':f,'value':v,'count':n,'denominator':denoms[f]}for (f,v),n in sorted(counts.items())],'warning':'Counts use reviewed fields only. Multi-auth percentages can overlap. Empty groups do not establish absence.'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',required=True);p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True);x=synthesize(json.loads(Path(a.results).read_text()));(out/'contextual-results.json').write_text(json.dumps(x,indent=2));(out/'reviewed-clusters.json').write_text(json.dumps(cluster_reviewed(x),indent=2));(out/'context-corrections.json').write_text(json.dumps(x['contextual_pass'],indent=2));print(json.dumps({'contextual_candidates':len(x['contextual_pass']['corrections']),'reviewed_pattern_fields':len(cluster_reviewed(x)['patterns']),'human_checks':0,'independent_accuracy':None}))
if __name__=='__main__':main()
