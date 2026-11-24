#!/usr/bin/env python3
"""Apply contextual reviews without rewriting first-pass outputs or reviewer identity."""
import argparse,datetime as dt,hashlib,json,random,sys
from pathlib import Path
FIELDS={'category','description','auth','access','api','mcp','buildability','blocker'}

def sample(rows,n=12,seed=23):
    """Deterministic category/risk sample, not a statistically unbiased estimate."""
    rng=random.Random(seed); groups={}
    for row in rows:groups.setdefault(row.get('category','unknown'),[]).append(row)
    selected=[]
    for category in sorted(groups):
        group=groups[category][:];rng.shuffle(group);group.sort(key=lambda r:len(r.get('review_flags',[])),reverse=True)
        if group and len(selected)<n:selected.append(group[0])
    remaining=[r for r in rows if r['id'] not in {x['id'] for x in selected}];rng.shuffle(remaining)
    remaining.sort(key=lambda r:len(r.get('review_flags',[])),reverse=True)
    return selected+remaining[:max(0,n-len(selected))]

def apply_reviews(payload,reviews,evidence_root,ledger_path):
    root=Path(evidence_root); rows={r['id']:r for r in payload['apps']}; events=[]
    for review in reviews:
        row=rows[review['app_id']]; field=review['field'];who=review['reviewer_type']
        if field not in FIELDS:raise ValueError('Unknown field')
        if who not in ('agent','human'):raise ValueError('Reviewer type must be agent or human')
        if not review.get('reason') or not review.get('value'):raise ValueError('A review requires a value and reason')
        source=next((s for s in row['sources'] if s.get('url')==review['source_url'] and s.get('status')=='ok'),None)
        if source is None:raise ValueError('Review source must be a successful source for this app')
        snapshot=root/source['snapshot'];raw=snapshot.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=source['text_sha256']:raise ValueError('Snapshot integrity failure')
        quote=review.get('quote','')
        if not quote or quote not in raw.decode():raise ValueError('Exact supporting quote missing from snapshot')
        before=row.get('reviewed',{}).get(field)
        row.setdefault('reviewed',{})[field]={k:review[k] for k in ['value','source_url','quote','reason','reviewer_type']}
        event={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'app_id':row['id'],'field':field,'before':before,'after':review['value'],'reviewer_type':who,'source_url':review['source_url'],'snapshot_sha256':source['text_sha256'],'reason':review['reason']}
        events.append(event)
    # Validate the complete batch first, then append, avoiding partially written ledgers.
    with Path(ledger_path).open('a') as f:
        for event in events:f.write(json.dumps(event)+'\n')
    for row in rows.values():
        checked={k for k,v in row.get('reviewed',{}).items() if v['reviewer_type']=='human'}
        row['verification']['human_checked']=FIELDS.issubset(checked)
        row['verification']['human_checked_fields']=sorted(checked)
    payload['metrics']['human_reviewed']=sum(r['verification']['human_checked'] for r in rows.values())
    return payload

def score(predictions,truth):
    """Field accuracy against separately supplied labels; unknowns count as misses."""
    compared=correct=0; details=[]
    for item in truth:
        key=(item['app_id'],item['field'])
        if key not in predictions:actual='unknown'
        else:actual=predictions[key]
        matched=actual==item['value'];compared+=1;correct+=matched
        details.append({'app_id':key[0],'field':key[1],'predicted':actual,'reference':item['value'],'matched':matched,'reference_reviewer_type':item['reviewer_type']})
    return {'correct':correct,'compared':compared,'accuracy':correct/compared if compared else None,'details':details,'independent_human_ground_truth':bool(truth) and all(t.get('reviewer_type')=='human' for t in truth)}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',required=True);p.add_argument('--reviews');p.add_argument('--evidence-root');p.add_argument('--output');p.add_argument('--sample',type=int,default=12);a=p.parse_args()
    payload=json.loads(Path(a.results).read_text())
    if not a.reviews:
        out={'sampling':'category-stratified and risk-prioritized; not random population inference','human_checks_completed':0,'sample':[{'id':r['id'],'name':r['name'],'category':r.get('category'),'flags':r['review_flags'],'sources':[s['url'] for s in r['sources']]} for r in sample(payload['apps'],a.sample)]}
        print(json.dumps(out,indent=2));return
    if not a.evidence_root or not a.output:p.error('--evidence-root and --output required to apply reviews')
    reviews=json.loads(Path(a.reviews).read_text());output=Path(a.output);output.mkdir(parents=True,exist_ok=True)
    payload=apply_reviews(payload,reviews,a.evidence_root,output/'corrections.jsonl');(output/'reviewed-results.json').write_text(json.dumps(payload,indent=2))
if __name__=='__main__':main()
