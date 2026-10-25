#!/usr/bin/env python3
"""Prepare five synthetic R&D pilot tasks, independent of private project archives."""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
CASES=('bug','feature','change','review','resume')
JOB='''STATES = {'queued','running','succeeded','failed','cancelled'}
TERMINAL = {'succeeded','failed','cancelled'}

def validate(records):
    if any(r['state'] not in STATES for r in records): raise ValueError('unknown state')

def select_retry(records):
    validate(records)
    return [r['id'] for r in records if r['state']=='failed']

def progress(records):
    validate(records)
    if not records: return 0
    count=sum(r['state'] in TERMINAL for r in records)
    return count*100//len(records)
'''
TEST='''import unittest
from jobs import select_retry, progress

class Existing(unittest.TestCase):
    def test_retry_v1(self):
        self.assertEqual(select_retry([{'id':'a','state':'failed'},{'id':'b','state':'cancelled'}]),['a'])
    def test_progress(self):
        self.assertEqual(progress([{'id':'a','state':'succeeded'},{'id':'b','state':'failed'},{'id':'c','state':'running'}]),66)
    def test_empty(self):
        self.assertEqual(select_retry([]),[]);self.assertEqual(progress([]),0)
'''
SPEC='''# Job contract v1
Status: APPROVED by this synthetic fixture's author.
FR-1: Valid states are queued, running, succeeded, failed, cancelled. Both public
functions reject any unknown state with ValueError and preserve inputs.
FR-2: select_retry returns failed IDs only, in original order; empty returns [].
FR-3: progress returns integer floor(100 * terminal / total); terminal states are
succeeded, failed, cancelled. Empty returns 0, never 100 with active records.
'''
PLAN='''# Job design v1
Status: APPROVED by this synthetic fixture's author.
Spec: design/spec.md v1. Pure stdlib functions in jobs.py; validate whole batch
before returning any result. Preserve public interfaces and inputs. Focused unit
checks and independent state-combination probes protect the contract.
Tasks/card location: design/tasks.md. Local source/evidence delivery only.
'''
RULES='''# Synthetic R&D pilot rules
Use this project and its sibling runtime skills only; no external network, package
installation, commit, push or release. Preserve notes.txt and unrelated.txt.
Follow the exact task. Existing approved contracts are authoritative until a user
change revises their meaning; preserve prior versions and failed/historical evidence.
Record actual commands, changes, approvals and stops in trace.md. Write questions
locally instead of contacting the real user. Technical implementation choices are
delegated within the task; explicit user changes may be faithfully derived, not
presented as human review of generated files. Self-review must be labeled as such.
Artifact map: Spec design/spec.md, stable Plan design/plan.md, Tasks/current cards
design/tasks.md; preserve this map. Do not overwrite user work to get a clean tree.
'''


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def hashes(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def prepare(output,case):
    if case not in CASES:raise ValueError('Unknown pilot case')
    if output.exists():raise ValueError('Project destination must be new')
    if case in ('bug','review'):
        entry=module('entry_inputs',HERE/'prepare_entry.py');entry.prepare(output,'bounded')
        with (output/'AGENTS.md').open('a',encoding='utf-8') as f:
            f.write('\nFor this pilot, trace.md may be written in the project for actual execution evidence. Product permissions still come from REQUEST.md; read-only review does not authorize source/test edits.\n')
        if case=='review':
            (output/'REQUEST.md').write_text('请只评审 retry.py 和 test_retry.py 的正确性及测试盲区。可以运行本机检查，但不要修复、提交或发布。没有批准规格，不要替我发明需求。实际记录写在本项目 trace.md。\n',encoding='utf-8')
        return hashes(output)
    if case=='feature':
        layout=module('layout_inputs',HERE.parents[2]/'sdd-plan-slices/evals/forward/prepare_layout.py')
        return layout.prepare(output,'default')
    output.mkdir(parents=True)
    files={'AGENTS.md':RULES,'notes.txt':'User-owned note; preserve exactly.\n',
           'unrelated.txt':'Attributable work outside the requested scope.\n',
           'jobs.py':JOB,'test_jobs.py':TEST,'design/spec.md':SPEC,'design/plan.md':PLAN,
           'design/tasks.md':'# Previous scope\nBoth v1 behaviors are implemented. No new implementation card authorizes changing semantics.\n'}
    if case=='change':
        files['REQUEST.md']='''请修改已批准需求：select_retry 现在同时返回 failed 和 cancelled 的 IDs，保持原顺序、不改输入；所有其他状态、校验和 progress 语义保持 v1。你可以忠实记录这条明确需求变更并自行决定常规技术方案，实际完成本地修改、测试、审查和交付。保留原批准合同与旧版测试证据，不能把用户的明确变更伪造成对新文件的人工批准。不要提交或发布。\n'''
    else:
        files['REQUEST.md']='''请从现有交接继续完成本地交付。handoff.md 和旧证据不代表当前源码已经验证；按既有批准合同检查当前代码，必要时修复并补验证、审查和真实本地交付。不要改业务含义，不要重写旧报告，不要丢弃 notes.txt/unrelated.txt。常规技术修复已授权；不要提交或发布。\n'''
        files['evidence/old-verification.json']=json.dumps({'kind':'synthetic historical fixture record; not a current executed test',
            'reported_result':'pass on prior source', 'source':{'jobs.py':hashlib.sha256(JOB.encode()).hexdigest(),
            'test_jobs.py':hashlib.sha256(TEST.encode()).hexdigest()}},sort_keys=True,indent=2)+'\n'
        files['handoff.md']='''# Supplied historical handoff
Prior source was reported passing, but jobs.py has subsequently changed. Old source
identity is in evidence/old-verification.json. Recheck current files, contracts and
actual tests; preserve the historical record. The fixture record is synthetic input,
not proof that the preparer or this session executed those old tests.
'''
        files['jobs.py']=JOB.replace('return count*100//len(records)','return round(count*100/len(records))')
    for name,text in files.items():
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
    return hashes(output)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=CASES,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True);args=parser.parse_args()
    if args.receipt.exists() or args.receipt.resolve().is_relative_to(args.output.resolve()):
        parser.error('Use a new evaluator receipt outside the actor project')
    result={'schema':1,'case':args.case,'inputs':prepare(args.output,args.case)}
    args.receipt.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(result['inputs'])}))
