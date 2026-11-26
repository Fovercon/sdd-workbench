"""Canonical Pi trial launcher.

The argv mirrors evals/context/run_pi.py verbatim except that the `--skill`
segment is parameterised: the baseline condition omits it, ablations point at
a subset runtime. Provider/model follow AGENTS.md (explicit DeepSeek Flash).
"""
import datetime
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

PROVIDER = 'deepseek'
MODEL = 'deepseek-flash'


def private_file(path):
    return os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb')


def build_argv(trial_dir, executable, skills_dir=None, prompt=None):
    base = Path(trial_dir).resolve()
    if prompt is None:
        prompt = (base / 'prompt.txt').read_text(encoding='utf-8')
    argv = [str(executable),
            '--offline', '--no-session', '--mode', 'json', '--no-extensions', '--no-skills']
    if skills_dir is not None:
        argv += ['--skill', str(Path(skills_dir).resolve())]
    argv += ['--no-prompt-templates', '--no-themes', '--no-context-files',
             '--tools', 'read,bash,edit,write',
             '--provider', PROVIDER, '--model', MODEL,
             '--print', prompt]
    return argv


def run(trial_dir, skills_dir=None, executable='pi', timeout=1800, prompt=None):
    """Execute one fresh trial; refuses any reuse of existing logs."""
    base = Path(trial_dir).resolve()
    if not (base / 'project').is_dir() or not (base / 'prompt.txt').is_file():
        raise ValueError('Prepare the trial first (project/ and prompt.txt)')
    for name in ('events.jsonl', 'stderr.log', 'invocation.json', 'process-result.json'):
        if (base / name).exists():
            raise ValueError('Trial logs exist; prepare a new directory')
    exe = shutil.which(executable)
    if not exe:
        raise ValueError('Native Pi executable unavailable')
    argv = build_argv(base, exe, skills_dir, prompt)
    record = {'argv': argv, 'cwd': str(base / 'project'),
              'skills_dir': str(skills_dir) if skills_dir else None,
              'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'permissions': 'instruction scoped, no OS sandbox',
              'backend_revision': 'NOT_REPORTED'}
    with private_file(base / 'invocation.json') as f:
        f.write(json.dumps(record, ensure_ascii=False, indent=2).encode())
    start = time.monotonic()
    with private_file(base / 'events.jsonl') as out, private_file(base / 'stderr.log') as err:
        try:
            code = subprocess.run(argv, cwd=base / 'project', stdout=out, stderr=err,
                                  timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            code = 'TIMEOUT'
    result = {'exit_code': code, 'seconds': round(time.monotonic() - start, 3)}
    with private_file(base / 'process-result.json') as f:
        f.write(json.dumps(result).encode())
    return result


def environment(executable='pi'):
    """Record pi version and the resolved provider model listing (raw strings)."""
    exe = shutil.which(executable)
    info = {'executable': exe}
    if not exe:
        return info
    for key, args in (('pi_version', [exe, '--version']),
                      ('model_listing', [exe, '--list-models', PROVIDER])):
        try:
            proc = subprocess.run(args, capture_output=True, text=True, timeout=120)
            info[key] = (proc.stdout + proc.stderr).strip()[:4000]
        except Exception as exc:  # noqa: BLE001 - probe must degrade, not fail
            info[key] = f'UNAVAILABLE: {exc!r}'
    return info
