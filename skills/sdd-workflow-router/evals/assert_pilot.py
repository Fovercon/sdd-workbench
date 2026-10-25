#!/usr/bin/env python3
"""Evaluator-only pilot probes; never supply this file to the task actor.

Checks product behavior and protected input bytes, not semantic contract approval,
review quality, evidence identity or human usability. Those require the rubric.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

STATES = ('queued', 'running', 'succeeded', 'failed', 'cancelled')


def evaluate(project, receipt, case):
    checks = 0

    def require(condition, message):
        nonlocal checks
        checks += 1
        if not condition: raise AssertionError(message)

    inputs = receipt['inputs']
    for name, digest in inputs.items():
        protected = case == 'review' or name in ('REQUEST.md', 'notes.txt', 'unrelated.txt',
                                                'handoff.md', 'evidence/old-verification.json')
        if protected:
            path = project/name
            require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest,
                    'Protected input changed: '+name)
    if case == 'review':
        return {'case':case, 'checks':checks, 'result':'PASS', 'semantic_review':'REQUIRED'}
    module_path = project/('retry.py' if case == 'bug' else 'jobs.py')
    spec = importlib.util.spec_from_file_location('pilot_product', module_path)
    product = importlib.util.module_from_spec(spec); spec.loader.exec_module(product)
    if case == 'bug':
        for value, expected in [('0',0),('12',12)]:
            require(product.parse_retries(value) == expected, 'Accepted retry input changed')
        for value in ('-1','-900','',' ','wrong'):
            try: product.parse_retries(value)
            except ValueError: pass
            else: raise AssertionError('Invalid retry input accepted: '+repr(value))
            checks += 1
    else:
        retry_states = ('failed','cancelled') if case == 'change' else ('failed',)
        for length in range(5):
            for states in itertools.product(STATES, repeat=length):
                records = [{'id':str(i % 3), 'state':s} for i,s in enumerate(states)]
                original = copy.deepcopy(records)
                require(product.select_retry(records) == [r['id'] for r in records if r['state'] in retry_states],
                        'Retry selection/order differs: '+str(states))
                expected = sum(s in STATES[2:] for s in states)*100//length if length else 0
                actual = product.progress(records)
                require(type(actual) is int and actual == expected, 'Progress differs: '+str(states))
                require(records == original, 'Valid input mutated')
        for position, invalid in itertools.product(range(3), ('unknown', None, [], {})):
            for method in (product.select_retry, product.progress):
                records = [{'id':str(i), 'state':'failed'} for i in range(3)]
                records[position]['state'] = invalid
                original = copy.deepcopy(records)
                try: method(records)
                except ValueError: pass
                except Exception as error:
                    raise AssertionError('Wrong rejection exception: '+type(error).__name__) from error
                else: raise AssertionError('Unknown state accepted')
                checks += 1
                require(records == original, 'Invalid input mutated')
    return {'case':case, 'checks':checks, 'result':'PASS', 'semantic_review':'REQUIRED'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project',type=Path)
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--case',choices=('bug','feature','change','review','resume'),required=True)
    args = parser.parse_args()
    try:
        result = evaluate(args.project,json.loads(args.receipt.read_text()),args.case)
    except (AssertionError, OSError, ValueError) as error:
        print(json.dumps({'case':args.case,'result':'FAIL','error':str(error)}));sys.exit(1)
    print(json.dumps(result,sort_keys=True))
