#!/usr/bin/env python3
"""Prepare frozen synthetic actor inputs without upstream downloads or answers."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
VARIANTS = ('preserving', 'lossy', 'stale-error', 'combined')
SPEC = '''# Synthetic record browser contract v1
Status: APPROVED for this synthetic fixture by its author.
FR-1: Public reads and appends retain the identity/date of every existing record.
FR-2: Untrustworthy stored state is rejected on read and attempted append without
changing any original bytes. In this fixture a repeated JSON object key is
untrustworthy, including two conflicting root records values. This is this
fixture's policy, not a universal JSON policy. Duplicate record IDs are rejected.
FR-3: Reversed date ranges produce an operation-specific readable filter error.
After correction the same browser session shows the matching record identities
and removes that filter operation's stale error. No unrelated error is cleared.
FR-4: Local browser and HTTP behavior run without internet or user data.
Non-goals: production hardening, concurrent writes, authentication or deployment.
'''
PLAN = '''# Synthetic technical plan v1
Status: APPROVED for this synthetic fixture by its author.
A Python stdlib Ledger owns the JSON records file. HTTP GET /api/records exposes
reads, optionally filtered by ISO start/end; POST appends an id/date object.
Unreadable/untrustworthy persisted state returns 409; invalid request/range 400;
successful reads 200 and appends 201. Validation precedes storage writes.
The page uses a separate filter-error element and list items with record IDs.
The app binds only 127.0.0.1; state is always supplied with --state.
Commands: python -B -m unittest discover; python -B app.py --state state.json.
'''
RULES = '''# Synthetic evaluation workspace
Use only this workspace, its supplied skills snapshot and temporary children.
No external network, package installation, Git commit/push, release or live user directories.
Preserve supplied source, original tests, state, contracts and notes during review
or verification design. You may create isolated copies/probes for authorized checks
and write evidence here. Do not repair this application. Record actual commands,
outputs and limits. Do not ask the real user; put unresolved questions in questions.md.
'''
REQUESTS = {
    'execute': 'Use sdd-converge-review for a local handoff review of this application against spec.md and plan.md. Select and actually execute the necessary checks of everyday behavior, data preservation and error recovery, including the rendered UI where relevant. You may run isolated tests and local browser checks. Report evidence and return stages; do not repair the application or claim checks you did not execute.\n',
    'design': 'Use sdd-verification-design to design the smallest faithful safety net for this application against spec.md and plan.md, including everyday behavior, data preservation and error recovery. Inspect the raw project, but do not implement or execute tests, alter application files, or claim checks ran. Write verification.md and identify missing evidence.\n',
}


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def snapshot(source, output):
    if output.exists(): raise ValueError('Skill snapshot destination must be new')
    output.mkdir(parents=True)
    for skill in sorted(source.glob('sdd-*')):
        if not skill.is_dir(): continue
        dest = output/skill.name; dest.mkdir()
        shutil.copyfile(skill/'SKILL.md', dest/'SKILL.md')
        for part in ('references', 'scripts', 'assets', 'agents'):
            if (skill/part).is_dir():
                shutil.copytree(skill/part, dest/part, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    return hashes(output)


def prepare(output, variant='preserving', mode='execute'):
    if variant not in VARIANTS or mode not in REQUESTS: raise ValueError('Unknown variant/mode')
    if output.exists(): raise ValueError('Project destination must be new')
    output.mkdir(parents=True)
    app = (HERE/'inputs/recovery_app.py').read_text(encoding='utf-8')
    page = (HERE/'inputs/recovery.html').read_text(encoding='utf-8')
    if variant in ('lossy', 'combined'):
        app = app.replace('return json.loads(text, object_pairs_hook=unique)', 'return json.loads(text)')
    if variant in ('stale-error', 'combined'):
        page = page.replace("  error.textContent = '';\n", '')
    files = {'app.py': app, 'index.html': page, 'spec.md': SPEC, 'plan.md': PLAN,
             'AGENTS.md': RULES, 'REQUEST.md': REQUESTS[mode], 'notes.txt': 'Synthetic keep-me note.\n',
             'test_baseline.py': (HERE/'inputs/test_recovery_baseline.py').read_text(encoding='utf-8'),
             'state.json': '{"records":[{"id":"kept-1","date":"2026-01-10"},{"id":"kept-2","date":"2026-02-20"}]}\n'}
    for name, content in files.items(): (output/name).write_text(content, encoding='utf-8')
    return hashes(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--variant', choices=VARIANTS, default='preserving')
    parser.add_argument('--mode', choices=REQUESTS, default='execute')
    parser.add_argument('--skills', type=Path); parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    if args.receipt.resolve().is_relative_to(args.output.resolve()):
        parser.error('Keep the evaluator receipt outside the actor workspace')
    if bool(args.skills) != bool(args.snapshot): parser.error('Use --skills and --snapshot together')
    if args.snapshot:
        project, skills = args.output.resolve(), args.snapshot.resolve()
        if project.is_relative_to(skills) or skills.is_relative_to(project):
            parser.error('Project and runtime snapshot must be separate directories')
        if args.receipt.resolve().is_relative_to(skills):
            parser.error('Keep the evaluator receipt outside the runtime snapshot')
    if args.receipt.exists(): parser.error('Receipt must be new')
    record = {'schema': 1, 'kind':'synthetic-recovery', 'variant': args.variant, 'mode': args.mode,
              'inputs': prepare(args.output, args.variant, args.mode)}
    if args.skills: record['skills'] = snapshot(args.skills, args.snapshot)
    args.receipt.write_text(json.dumps(record, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'files':len(record['inputs']), 'receipt':str(args.receipt)}))
