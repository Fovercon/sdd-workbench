#!/usr/bin/env python3
"""Independent deterministic checks. Keep outside the actor's working directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink()
            and '.git' not in p.parts and '__pycache__' not in p.parts}


def preservation(trial):
    receipt = json.loads((trial / 'receipt.json').read_text(encoding='utf-8'))
    project = trial / 'project'
    current = hashes(project)
    before = receipt['inputs']
    changed = sorted(name for name, sha in before.items() if current.get(name) != sha)
    added = sorted(set(current) - set(before))
    errors = []
    for name in ('AGENTS.md', 'REQUEST.md', 'user-note.txt', 'plugin.json', 'suite.json'):
        if name in changed:
            errors.append('protected input changed: ' + name)
    if receipt['case'] == 'adapter':
        errors.extend('readonly input changed: ' + name for name in changed)
        errors.extend('unauthorized addition: ' + name for name in added
                      if name != 'trace.md' and not name.startswith('temporary-probes/'))
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=project, text=True).strip()
    if head != receipt['fixture_git_head']:
        errors.append('actor changed fixture commit')
    if subprocess.check_output(['git', 'remote'], cwd=project, text=True).strip():
        errors.append('actor added git remote')
    if hashes(trial / 'runtime-skills') != receipt['runtime_skills']:
        errors.append('runtime skill snapshot changed')
    links = []
    for path in project.rglob('*'):
        if path.is_symlink():
            relative = path.relative_to(project).as_posix()
            expected = (receipt['host'] == 'codex' and relative == '.agents/skills'
                        and path.resolve() == (trial / 'runtime-skills').resolve())
            if not expected:
                links.append(relative)
    errors.extend('unexpected symlink: ' + name for name in links)
    return {'pass': not errors, 'errors': errors, 'changed': changed, 'added': added}


def encoding(project):
    results = []
    env = dict(os.environ, PYTHONIOENCODING='cp1252', PYTHONUTF8='0', PYTHONDONTWRITEBYTECODE='1')
    with tempfile.TemporaryDirectory(prefix='sdd-legacy-probe-') as temp:
        base = Path(temp)
        profile = base / '中文-profile'
        evidence = base / 'evidence'
        evidence.mkdir()
        data = '实际观察\n'.encode('utf-8')
        (evidence / '中文.txt').write_bytes(data)
        cases = [
            ('install-preview', 'install.py', ['install', '--dry-run', '--home', str(profile)], 0,
             lambda s: '中文-profile' in json.loads(s.decode('cp1252'))['agents']['codex']['destination']),
            ('doctor-json', 'doctor.py', ['--json', '--home', str(profile)], 1,
             lambda s: json.loads(s.decode('cp1252'))['summary'] == 'NEEDS_ATTENTION'
             and '未在' in json.loads(s.decode('cp1252'))['issues'][0]['message']),
            ('review-evidence', 'review.py', ['evidence', '--root', str(base), '--path', 'evidence/中文.txt'], 0,
             lambda s: json.loads(s.decode('cp1252')) == {
                 'path': 'evidence/中文.txt', 'sha256': hashlib.sha256(data).hexdigest()}),
            ('doctor-human', 'doctor.py', ['--home', str(profile)], 1,
             lambda s: '只读诊断' in s.decode('utf-8')),
        ]
        for name, tool, args, code, predicate in cases:
            command = [sys.executable, '-B', str(project / 'tools' / tool), *args]
            result = subprocess.run(command, cwd=project, env=env, capture_output=True, timeout=120)
            try:
                passed = result.returncode == code and bool(predicate(result.stdout))
            except (ValueError, KeyError, IndexError, UnicodeError):
                passed = False
            results.append({'name': name, 'pass': passed and not profile.exists(),
                            'required': name != 'doctor-human',
                            'exit': result.returncode, 'stderr': result.stderr.decode('utf-8', errors='replace'),
                            'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(),
                            'profile_created': profile.exists()})
    # Emulate the default encoding of Path.read_text on legacy Windows. Explicit
    # UTF-8 arguments still work. No test/function names are hard-coded.
    script = '''import io, runpy, unittest
from unittest.mock import patch
original=io.open
def legacy(file,mode='r',buffering=-1,encoding=None,*args,**kwargs):
    if 'b' not in mode and encoding in (None,'locale'): encoding='cp1252'
    return original(file,mode,buffering,encoding,*args,**kwargs)
namespace=runpy.run_path('tests/test_entry_fixtures.py')
suite=unittest.TestSuite()
for value in namespace.values():
    if isinstance(value,type) and issubclass(value,unittest.TestCase):
        for name in unittest.defaultTestLoader.getTestCaseNames(value):
            if 'link' in name: suite.addTest(value(name))
assert suite.countTestCases()>0, 'No document link regression discovered'
with patch('io.open',legacy):
    result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
'''
    result = subprocess.run([sys.executable, '-B', '-c', script], cwd=project,
                            env=env, capture_output=True, timeout=120)
    results.append({'name': 'legacy-document-links', 'pass': result.returncode == 0, 'required': True,
                    'exit': result.returncode, 'stderr': result.stderr.decode('utf-8', errors='replace')})
    return results


def check(trial):
    trial = Path(trial).resolve()
    receipt = json.loads((trial / 'receipt.json').read_text(encoding='utf-8'))
    report = {'case': receipt['case'], 'host': receipt['host'],
              'upstream_commit': receipt['upstream_commit'], 'suite_commit': receipt['suite_commit'],
              'preservation': preservation(trial),
              'semantic_review': 'REQUIRED: inspect native events, trace, regression and findings; exit 0 is insufficient'}
    if receipt['case'] == 'encoding':
        report['contract_probes'] = encoding(trial / 'project')
    else:
        result = subprocess.run(['node', '--test', 'tests/test_deepseek_adapter.mjs'],
                                cwd=trial / 'project', capture_output=True, text=True, timeout=120)
        report['contract_probes'] = [{'name': 'original-node-regression', 'pass': result.returncode == 0,
                                     'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}]
    report['deterministic_pass'] = report['preservation']['pass'] and all(
        value['pass'] for value in report['contract_probes'] if value.get('required', True))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trial', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to((args.trial / 'project').resolve()):
        parser.error('Evidence output must remain outside the actor project')
    value = check(args.trial)
    args.output.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    print(json.dumps({'deterministic_pass': value['deterministic_pass'], 'semantic_review': 'REQUIRED'}))
    raise SystemExit(0 if value['deterministic_pass'] else 1)
