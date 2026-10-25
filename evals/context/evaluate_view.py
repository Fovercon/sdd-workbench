#!/usr/bin/env python3
"""Evaluator-only source/field/history checks; tool audit and browser remain separate."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'skills/sdd-workflow-router/scripts'))
from project_view import previous_version,validate
from project_view_lib import evidence


def evaluate(run):
    run=Path(run).resolve();project=run/'project';original=json.loads((run/'input-receipt.json').read_text(encoding='utf-8'));errors=[]
    unchanged=all((project/p).is_file()and not(project/p).is_symlink()and hashlib.sha256((project/p).read_bytes()).hexdigest()==h for p,h in original['project'].items())
    if not unchanged:errors.append('Original input changed')
    runtime=run/'runtime/sdd-workflow-router'
    runtime_ok=all((runtime/p).is_file()and hashlib.sha256((runtime/p).read_bytes()).hexdigest()==h for p,h in original.get('runtime',{}).items())
    if not runtime_ok:errors.append('Frozen runtime changed')
    versions=[p.parent for p in project.rglob('receipt.json')if p.is_file()and not p.is_symlink()and p.resolve().is_relative_to(project)]
    if not versions:raise ValueError('No completed renderer output')
    parents=set();receipts={}
    for p in versions:
        previous_version(p);r=json.loads((p/'receipt.json').read_text(encoding='utf-8'));receipts[p]=r
        if r['previous']:
            parent=Path(r['previous']['path']).resolve();parents.add(parent);previous_version(parent)
            if hashlib.sha256((parent/'receipt.json').read_bytes()).hexdigest()!=r['previous']['receipt_sha256']:errors.append('Previous receipt changed')
    tips=[p for p in versions if p.resolve()not in parents]
    if len(tips)!=1:errors.append('Multiple disconnected final views; manual selection required')
    latest=tips[0]if len(tips)==1 else max(versions,key=lambda p:receipts[p]['generated_at'])
    data=json.loads((latest/'snapshot.json').read_text(encoding='utf-8'));validate(data);items=evidence.inspect(project,data)
    roles={}
    for i in items:
        if 'stage_detail'in i:roles.setdefault(i['stage_detail']['type'],[]).append(i)
    for role in ['constraint','command','context','assumption','implementation','test_run','deliverable','usage','limitation','handoff','recovery']:
        if not roles.get(role):errors.append('Missing '+role)
    if {i['stage_detail']['result']for i in roles.get('test_run',[])}!={'PASS','FAIL','NOT_RUN'}:errors.append('Recorded run results lost')
    if not all(i['stage_detail'].get('result')=='NOT_RUN'for i in roles.get('command',[])):errors.append('Documented command misreported as executed')
    if not all(i['stage_detail'].get('delivery_status')=='PREPARED'and'delivery_receipt'not in i['stage_detail']for i in roles.get('deliverable',[])):errors.append('Delivery invented')
    if not any(i['stage_detail'].get('owner')=='演示维护者'for i in roles.get('handoff',[])):errors.append('Recorded handoff owner lost')
    brief=next((i for i in items if i.get('work',{}).get('type')=='brief'),None)
    if not brief:errors.append('Structured brief missing')
    else:
        if not all(k in ''.join(brief['work']['in_scope'])for k in ['编号','暂停','成功']):errors.append('In-scope behaviors incomplete')
        if not all(k in ''.join(brief['work']['out_of_scope'])for k in ['真实','生产','部署']):errors.append('Out-of-scope boundaries incomplete')
    if not any(i.get('decision',{}).get('kind')=='input'and i['state']=='PENDING_HUMAN'for i in items):errors.append('Unanswered real question lost')
    if not all(i['freshness']=='CURRENT'for i in items):errors.append('Source reference mismatch')
    expected=next(l.split('：',1)[1]for l in(project/'DELIVERY.md').read_text(encoding='utf-8').splitlines()if l.startswith('示例命令：'))
    if not any(i['stage_detail'].get('command')==expected for i in roles.get('usage',[])):errors.append('Usage command bytes differ from source')
    calls=[]
    with (run/'events.jsonl').open(encoding='utf-8')as events:
        for number,line in enumerate(events,1):
            e=json.loads(line)
            if e.get('type')=='tool_execution_start':calls.append({'line':number,'tool':e.get('toolName'),'args':e.get('args',{})})
    (run/'tool-audit.json').write_text(json.dumps(calls,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'automated_quality':'PASS'if not errors else'FAIL','errors':errors,'latest':str(latest),'versions':[str(v)for v in versions],
            'records':len(items),'role_counts':{k:len(v)for k,v in roles.items()},'original_sources_unchanged':unchanged,'runtime_sources_unchanged':runtime_ok,
            'required_remaining_review':'Full tool/claim audit and independent browser checks; field validation alone is insufficient.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');a=p.parse_args();r=evaluate(a.run)
    (Path(a.run)/'quality.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=True))
