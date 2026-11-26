"""Freeze sandboxed skill runtime snapshots from a git ref or the worktree.

Mirrors the evals/context/prepare.py convention: only SKILL.md plus references/,
scripts/ and agents/ subtrees are copied, so evals/ and tests/ never enter a
runtime snapshot handed to an actor.
"""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from runner.paths import ROOT, suite_skills

RUNTIME_PARTS = ('references', 'scripts', 'agents')


def _entries_ref(revision, name):
    prefix = f'skills/{name}/'
    listing = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision, prefix],
                                      cwd=ROOT, text=True).splitlines()
    for path in listing:
        rel = path[len(prefix):]
        if rel == 'SKILL.md' or rel.startswith(tuple(part + '/' for part in RUNTIME_PARTS)):
            data = subprocess.check_output(['git', 'show', f'{revision}:{path}'], cwd=ROOT)
            yield rel, data


def _entries_worktree(name):
    base = ROOT / 'skills' / name
    if not base.is_dir():
        raise ValueError(f'skill directory missing: {base}')
    for path in sorted(base.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        rel = path.relative_to(base).as_posix()
        if rel == 'SKILL.md' or rel.startswith(tuple(part + '/' for part in RUNTIME_PARTS)):
            yield rel, path.read_bytes()


def freeze(destination, ref=None, names=None):
    """Write the frozen runtime tree; refuses an existing destination."""
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Runtime destination exists; prepare a new directory')
    revision = None
    if ref:
        revision = subprocess.check_output(['git', 'rev-parse', ref + '^{commit}'],
                                           cwd=ROOT, text=True).strip()
    for name in (suite_skills() if names is None else names):
        skill_dir = destination / name
        skill_dir.mkdir(parents=True)
        entries = _entries_ref(revision, name) if revision else _entries_worktree(name)
        for rel, data in entries:
            target = skill_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return {'destination': str(destination), 'revision': revision or 'WORKTREE'}


def subset(source, destination, names):
    """Copy only the named skills into a fresh condition runtime directory."""
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise ValueError('Subset destination exists; prepare a new directory')
    for name in names:
        src = source / name
        if not src.is_dir():
            raise ValueError(f'skill missing from runtime source: {name}')
        shutil.copytree(src, destination / name)


def snapshot_hash(runtime_dir):
    """Content hash per skill plus a total, following the suite snapshot convention."""
    runtime_dir = Path(runtime_dir)
    per_skill = {}
    for skill_dir in sorted(p for p in runtime_dir.iterdir() if p.is_dir()):
        files = {p.relative_to(skill_dir).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(skill_dir.rglob('*')) if p.is_file()
                 and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.pyo')}
        per_skill[skill_dir.name] = hashlib.sha256(
            json.dumps(files, sort_keys=True).encode()).hexdigest()
    return {'skills': per_skill,
            'total': hashlib.sha256(json.dumps(per_skill, sort_keys=True).encode()).hexdigest()}


def resolve_condition(skill_spec, all_names):
    """Resolve a condition spec (list, ['ALL'] or ['ALL_MINUS', name]) to skill names."""
    if skill_spec == ['ALL']:
        return list(all_names)
    if skill_spec and skill_spec[0] == 'ALL_MINUS':
        removed = set(skill_spec[1:])
        return [n for n in all_names if n not in removed]
    return list(skill_spec)
