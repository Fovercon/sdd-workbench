#!/usr/bin/env python3
"""Read-only review intake. Hashes/identities are evidence claims, never release approval."""
import sys
sys.dont_write_bytecode = True
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import stat

from package import ROOT, check as package_check, digest

REPORT_KIND = 'sdd-review-report'
ID = re.compile(r'[A-Za-z][A-Za-z0-9_-]{0,63}')
SHA = re.compile(r'[0-9a-f]{64}')
ACTIONS = {'REPRODUCED','FIX_REPORTED','RECHECK_PASS','RECHECK_FAIL','REJECT_PROPOSED','DUPLICATE_PROPOSED'}


def require(value, message):
    if not value: raise ValueError(message)


def fields(value, allowed, required=()):
    require(isinstance(value,dict), 'Expected an object')
    require(set(value) <= set(allowed), 'Unknown fields: '+', '.join(sorted(set(value)-set(allowed))))
    require(set(required) <= set(value), 'Missing fields: '+', '.join(sorted(set(required)-set(value))))


def text(value, label):
    require(isinstance(value,str) and bool(value.strip()), 'Nonempty text required: '+label)


def identifier(value):
    require(isinstance(value,str) and ID.fullmatch(value), 'Invalid identifier')


def sha(value):
    require(isinstance(value,str) and SHA.fullmatch(value), 'Invalid SHA256')


def relative(value, evidence=False):
    text(value,'path')
    require('\\' not in value and ':' not in value, 'Use a relative POSIX path')
    path=PurePosixPath(value)
    require(not path.is_absolute() and '..' not in path.parts and path.as_posix()==value and value!='.', 'Unsafe relative path')
    if evidence: require(len(path.parts)>1 and path.parts[0]=='evidence', 'Evidence must be inside evidence/')
    return path


def regular_bytes(path, maximum):
    require(not path.is_symlink(), 'File links are not supported: '+str(path))
    info=path.stat()
    require(stat.S_ISREG(info.st_mode), 'Expected a regular file: '+str(path))
    require(info.st_size <= maximum, 'File exceeds supported size: '+str(path))
    data=path.read_bytes()
    require(len(data)<=maximum, 'File grew beyond supported size')
    return data


def unique_object(pairs):
    result={}
    for key,value in pairs:
        require(key not in result, 'Duplicate JSON key: '+key)
        result[key]=value
    return result


def evidence_bytes(root, name):
    path=relative(name,True)
    actual=root
    for part in path.parts:
        actual=actual/part
        require(not actual.is_symlink(), 'Evidence path contains a link: '+name)
    require(actual.resolve().is_relative_to(root.resolve()/'evidence'),'Evidence resolves outside its directory')
    return regular_bytes(actual,16*1024*1024)


def evidence_entry(root, entry):
    fields(entry,{'path','sha256'},{'path','sha256'});sha(entry['sha256'])
    require(digest(evidence_bytes(root,entry['path']))==entry['sha256'], 'Evidence hash mismatch: '+entry['path'])


def snapshot(source):
    plugin,_suite,files=package_check(source)
    hashes={name:digest(data) for name,data in files.items()}
    return {'schema':1,'kind':'sdd-review-candidate','scope':'RELEASE_INPUTS',
            'name':plugin['name'],'declared_version':plugin['version'],
            'fingerprint':digest(json.dumps(hashes,sort_keys=True).encode()),'files':hashes}


def new_report(current, report_id, reviewer_id, kind):
    identifier(report_id);identifier(reviewer_id)
    return {'schema':1,'kind':REPORT_KIND,'id':report_id,'candidate':current['fingerprint'],
            'status':'DRAFT','reviewer':{'id':reviewer_id,'kind':kind,'relation':'unknown',
                                       'context':'unknown','informed':None},
            'task':'','notes':'','environment':{'client':None,'model':None,'os':None,'tools':None},
            'inputs':[],'findings':[],'followups':[]}


def validate_report(path, current):
    raw=regular_bytes(path,1024*1024)
    report=json.loads(raw,object_pairs_hook=unique_object)
    keys={'schema','kind','id','candidate','status','reviewer','task','notes','environment','inputs','findings','followups'}
    fields(report,keys,keys)
    require(type(report['schema']) is int and report['schema']==1 and report['kind']==REPORT_KIND,'Unknown review format')
    identifier(report['id']);sha(report['candidate'])
    require(report['status'] in ('DRAFT','SUBMITTED'),'Unknown report status')
    for key in ('task','notes'): require(isinstance(report[key],str),'Expected text: '+key)
    if report['status']=='SUBMITTED': text(report['task'],'task');text(report['notes'],'notes')
    reviewer=report['reviewer'];rkeys={'id','kind','relation','context','informed'};fields(reviewer,rkeys,rkeys)
    identifier(reviewer['id'])
    require(reviewer['kind'] in ('human','agent','unknown'),'Unknown reviewer kind')
    require(reviewer['relation'] in ('author','other','unknown'),'Unknown declared author relationship')
    require(reviewer['context'] in ('fresh','shared','unknown'),'Unknown declared context')
    require(reviewer['informed'] is None or type(reviewer['informed']) is bool,'informed must be true/false/null')
    fields(report['environment'],{'client','model','os','tools'})
    require(all(v is None or isinstance(v,str) for v in report['environment'].values()),'Environment values must be text or null')
    require(isinstance(report['inputs'],list),'Inputs must be an array')
    for item in report['inputs']:evidence_entry(path.parent,item)
    require(isinstance(report['findings'],list) and isinstance(report['followups'],list),'Findings/followups must be arrays')
    local=set()
    for finding in report['findings']:
        fkeys={'id','title','severity','scope','expectation','expectation_source','observation','consequence','steps','evidence'}
        fields(finding,fkeys,fkeys);identifier(finding['id'])
        require(finding['id'] not in local,'Duplicate local identifier');local.add(finding['id'])
        for key in ('title','expectation','expectation_source','observation','consequence'):text(finding[key],key)
        require(finding['severity'] in ('P0','P1','P2','P3'),'Unknown severity')
        require(isinstance(finding['scope'],list) and bool(finding['scope']),'Nonempty scope required')
        for name in finding['scope']:
            relative(name)
            if report['candidate']==current['fingerprint']:require(name in current['files'],'Scope absent from current candidate: '+name)
        require(isinstance(finding['steps'],list) and bool(finding['steps']),'Reproduction/inspection steps required')
        for step in finding['steps']:text(step,'step')
        require(isinstance(finding['evidence'],list) and bool(finding['evidence']),'Finding evidence required')
        for item in finding['evidence']:evidence_entry(path.parent,item)
    for follow in report['followups']:
        ekeys={'id','target','action','reason','evidence','duplicate_of'}
        fields(follow,ekeys,ekeys-{'duplicate_of'});identifier(follow['id'])
        require(follow['id'] not in local,'Duplicate local identifier');local.add(follow['id'])
        require(isinstance(follow['action'],str) and follow['action'] in ACTIONS,'Unknown follow-up action')
        text(follow['reason'],'reason')
        for ref in ('target','duplicate_of'):
            if ref in follow:
                require(isinstance(follow[ref],str) and follow[ref].count('/')==1,'Expected report/finding reference')
                for piece in follow[ref].split('/'):identifier(piece)
        require((follow['action']=='DUPLICATE_PROPOSED')==('duplicate_of' in follow),'duplicate_of is only required for a duplicate proposal')
        require(isinstance(follow['evidence'],list),'Follow-up evidence must be an array')
        if follow['action'] not in ('REJECT_PROPOSED','DUPLICATE_PROPOSED'): require(bool(follow['evidence']),'Follow-up evidence required')
        for item in follow['evidence']:evidence_entry(path.parent,item)
    return report,digest(raw)


def check_reports(current, paths):
    reports={};metadata=[]
    for path in paths:
        try: report,raw_sha=validate_report(path,current)
        except (OSError,ValueError,KeyError,TypeError,RecursionError) as error:
            raise ValueError(str(path)+': '+str(error)) from error
        require(report['id'] not in reports,'Duplicate report ID: '+report['id'])
        reports[report['id']]=report
        metadata.append({'id':report['id'],'path':str(path.absolute()),'sha256':raw_sha,'status':report['status'],
                         'candidate':report['candidate'],'matches_current_candidate':report['candidate']==current['fingerprint'],
                         'reviewer':report['reviewer'],'inputs':report['inputs']})
    findings={}
    for report in reports.values():
        if report['status']!='SUBMITTED':continue
        for finding in report['findings']:
            ref=report['id']+'/'+finding['id']
            findings[ref]={'ref':ref,'candidate':report['candidate'],'matches_current_candidate':report['candidate']==current['fingerprint'],
                           'reviewer':report['reviewer'],'finding':finding,'status':'OPEN','followups':[], 'duplicate_proposals':[]}
    for report in reports.values():
        if report['status']!='SUBMITTED':continue
        for follow in report['followups']:
            require(follow['target'] in findings,'Unknown submitted finding reference: '+follow['target'])
            origin=findings[follow['target']]
            item=dict(follow,ref=report['id']+'/'+follow['id'],candidate=report['candidate'],reviewer=report['reviewer'],
                      matches_current_candidate=report['candidate']==current['fingerprint'],
                      same_reporter_id=report['reviewer']['id']==origin['reviewer']['id'],
                      self_recheck_declared=(None if report['reviewer']['relation']=='unknown'
                                             else report['reviewer']['relation']=='author'))
            if follow['action']=='DUPLICATE_PROPOSED':
                require(follow['duplicate_of'] in findings and follow['duplicate_of']!=follow['target'],'Unknown or self duplicate target')
                origin['duplicate_proposals'].append(item)
            else:origin['followups'].append(item)
    for finding in findings.values():
        finding['followups'].sort(key=lambda x:x['ref']);finding['duplicate_proposals'].sort(key=lambda x:x['ref'])
        active={e['action'] for e in finding['followups'] if e['matches_current_candidate']}
        historical={e['action'] for e in finding['followups'] if not e['matches_current_candidate']}
        if {'RECHECK_PASS','RECHECK_FAIL'} <= active:finding['status']='DISPUTED'
        elif 'RECHECK_FAIL' in active:finding['status']='RECHECK_FAILED'
        elif 'RECHECK_PASS' in active:finding['status']='RECHECK_REPORTED'
        elif {'RECHECK_PASS','RECHECK_FAIL'} & historical:finding['status']='STALE_RECHECK'
        elif 'FIX_REPORTED' in active:finding['status']='FIX_REPORTED'
        elif 'REPRODUCED' in active:finding['status']='REPRODUCTION_REPORTED'
    return {'schema':1,'validation':'VALID','current_candidate':current['fingerprint'],
            'scope':'RELEASE_INPUTS','reports':sorted(metadata,key=lambda x:x['id']),
            'submitted_reports':sum(r['status']=='SUBMITTED' for r in reports.values()),
            'drafts':sum(r['status']=='DRAFT' for r in reports.values()),
            'findings':[findings[k] for k in sorted(findings)],
            'identity_authenticated':False,'commands_executed':False,'automatic_closure':False,
            'release_readiness':'NOT_ASSESSED'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    for name in ('snapshot','new','check'):
        p=sub.add_parser(name);p.add_argument('--source',type=Path,default=ROOT)
        if name=='new':
            p.add_argument('--id',required=True);p.add_argument('--reviewer',required=True)
            p.add_argument('--kind',choices=('human','agent','unknown'),default='unknown')
        if name=='check':p.add_argument('--report',nargs='+',type=Path,required=True)
    p=sub.add_parser('evidence');p.add_argument('--root',type=Path,required=True);p.add_argument('--path',required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=='evidence':
            result={'path':args.path,'sha256':digest(evidence_bytes(args.root,args.path))}
        else:
            current=snapshot(args.source)
            if args.command=='snapshot':result=current
            elif args.command=='new':result=new_report(current,args.id,args.reviewer,args.kind)
            else:result=check_reports(current,args.report)
        print(json.dumps(result,ensure_ascii=True,indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError,AttributeError,RecursionError) as error:
        print(json.dumps({'schema':1,'validation':'INVALID','error':str(error)},ensure_ascii=True));return 2


if __name__=='__main__':sys.exit(main())
