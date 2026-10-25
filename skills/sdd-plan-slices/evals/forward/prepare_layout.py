#!/usr/bin/env python3
"""Prepare a complete local mission with default or established custom artifact locations."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent
INPUTS=HERE.parents[2]/'sdd-workflow-router/evals/forward/inputs/clear'
CUSTOM='''
# Existing project artifact map
This project uses docs/requirements.md for requirements, docs/architecture.md for
the stable technical Plan, and docs/iterations.md for slices, dependencies and the
current execution card. Keep these established pointers and their responsibilities.
Do not introduce design/ as a replacement layout. All original task permissions,
notes protection and evidence rules above remain in force.
'''


def prepare(output,layout='default'):
    if layout not in ('default','custom'):raise ValueError('Unknown layout')
    if output.exists():raise ValueError('Project destination must be new')
    shutil.copytree(INPUTS,output,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    if layout=='custom':
        path=output/'AGENTS.md';path.write_text(path.read_text(encoding='utf-8')+CUSTOM,encoding='utf-8')
    return {p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.rglob('*')) if p.is_file()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--layout',choices=('default','custom'),default='default')
    parser.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args()
    if args.receipt.exists() or args.receipt.resolve().is_relative_to(args.output.resolve()):
        parser.error('Use a new evaluator receipt outside the project')
    record={'schema':1,'layout':args.layout,'inputs':prepare(args.output,args.layout)}
    args.receipt.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(record['inputs'])}))
