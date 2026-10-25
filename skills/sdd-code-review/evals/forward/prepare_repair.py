#!/usr/bin/env python3
"""Prepare synthetic inputs for a completed review followed by a real user request."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUESTS = {
    'repair': 'The review is complete with the two findings in review.md. Just fix them now. Keep this a bounded local repair, run the appropriate regression checks, and report the actual result. Do not commit, push, publish, or modify notes.txt.\n',
    'review-only': 'The review is complete with the two findings in review.md. Summarize the findings and stop. Do not repair or change source or tests. Do not commit, push or publish.\n',
}


def prepare(output, mode='repair'):
    if output.exists(): raise ValueError('Project destination must be new')
    if mode not in REQUESTS: raise ValueError('Unknown mode')
    output.mkdir(parents=True)
    files = {'AGENTS.md': '''# Synthetic local label utility
No approved Spec governs this small module; README documents its existing intent.
Use the supplied code-review skill for the review, then follow the user's actual
request. Repairs may edit labels.py and tests only when explicitly requested.
Keep notes.txt and the completed review unchanged. Write execution evidence locally.
No external network, package installation, commit, push, release or live directories.
Use python -B -m unittest discover for the original suite; add focused regressions
when repairing. No browser, persistence or server is involved in this utility.
''', 'README.md': '''# Label utility
normalize_label strips surrounding whitespace and rejects an empty/blank label
with ValueError. unique_labels normalizes inputs and returns the first spelling
of each case-insensitively unique label in input order. Invalid labels still fail.
''', 'review.md': '''# Completed review
Outcome: REVIEW_COMPLETE; mode AREA. This review is read-only, no repairs performed.
CR-001: normalize_label accepts blank input, contradicting README's ValueError rule.
CR-002: unique_labels retains case-insensitive duplicates instead of preserving
only their first normalized spelling. Existing tests cover ordinary trim/distinct
labels but do not protect either edge. No unresolved product decision is recorded.
''', 'REQUEST.md': REQUESTS[mode], 'notes.txt':'User-owned synthetic note; preserve exactly.\n'}
    for name in ('labels.py','test_labels.py'):
        files[name]=(HERE/'inputs'/name).read_text(encoding='utf-8')
    for name,content in files.items(): (output/name).write_text(content,encoding='utf-8')
    return {name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in sorted(files)}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mode',choices=REQUESTS,default='repair')
    parser.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args()
    if args.receipt.resolve().is_relative_to(args.output.resolve()) or args.receipt.exists():
        parser.error('Keep a new evaluator receipt outside the actor workspace')
    record={'schema':1,'kind':'review-repair','mode':args.mode,'inputs':prepare(args.output,args.mode)}
    args.receipt.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(record['inputs']),'receipt':str(args.receipt)}))
