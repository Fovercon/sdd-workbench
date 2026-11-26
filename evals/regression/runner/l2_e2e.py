"""Layer 2 - paired end-to-end evaluation on spec-to-PR task packs.

Every (task, condition, trial) slot gets a fresh copy of the starter project,
a condition-specific runtime (baseline: none), and the identical entry prompt.
Two task kinds share one pipeline:
- kind=code: adjudication runs evaluator-owned hidden unittests (partial credit).
- kind=process: criteria-driven adjudication (reply/artifact regex components,
  question count, optional hidden tests) per the weights in task.json.
"""
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from runner import events, pi_runner, runtime as runtime_mod
from runner.paths import CORPUS, CONFIG, HARNESS, suite_skills

WRAPPER = HARNESS / 'runner' / '_run_tests.py'


def load_tasks():
    tasks = []
    for task_json in sorted((CORPUS / 'tasks').glob('*/task.json')):
        task = json.loads(task_json.read_text(encoding='utf-8'))
        for key in ('id', 'title', 'timeout', 'entry_prompt', 'directed_prompt'):
            if key not in task:
                raise ValueError(f'{task_json}: missing {key}')
        task['kind'] = task.get('kind', 'code')
        task['root'] = task_json.parent
        if not (task['root'] / 'project').is_dir():
            raise ValueError(f'{task_json}: starter project/ missing')
        if not (task['root'] / 'oracle' / 'solution').is_dir():
            raise ValueError(f'{task_json}: oracle/solution missing')
        if task['kind'] == 'code':
            if not (task['root'] / 'hidden' / 'tests').is_dir():
                raise ValueError(f'{task_json}: code task needs hidden/tests')
        elif task['kind'] == 'process':
            proc = task.get('process')
            if not isinstance(proc, dict) or not proc.get('reply_must_match'):
                raise ValueError(f'{task_json}: process task needs process.reply_must_match')
            if not (task['root'] / 'oracle' / 'reply.txt').is_file():
                raise ValueError(f'{task_json}: process task needs oracle/reply.txt')
        else:
            raise ValueError(f'{task_json}: unknown kind {task["kind"]}')
        tasks.append(task)
    return tasks


def load_conditions(extra_ablate=None):
    config = json.loads((CONFIG / 'conditions.json').read_text(encoding='utf-8'))
    all_names = suite_skills()
    conditions = []
    for cond in config['conditions']:
        conditions.append({'id': cond['id'],
                           'prompt': cond.get('prompt', 'organic'),
                           'skills': runtime_mod.resolve_condition(cond['skills'], all_names)})
    for skill in extra_ablate or []:
        conditions.append({'id': 'minus-' + skill.removeprefix('sdd-'),
                           'prompt': 'organic',
                           'skills': [n for n in all_names if n != skill]})
    return conditions


def prepare_slot(task, condition, trial, run_dir, runtime_full):
    root = Path(task['root'])  # may be a str when replayed from slots.json
    dest = Path(run_dir) / 'l2' / task['id'] / condition['id'] / f't{trial}'
    if dest.exists():
        return dest
    dest.mkdir(parents=True)
    project = dest / 'project'
    shutil.copytree(root / 'project', project)
    if condition['skills']:
        runtime_mod.subset(runtime_full, dest / 'runtime', condition['skills'])
    prompt = task['directed_prompt'] if condition.get('prompt') == 'directed' else task['entry_prompt']
    (dest / 'prompt.txt').write_text(prompt, encoding='utf-8')
    starter = {p.relative_to(project).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(project.rglob('*')) if p.is_file()}
    (dest / 'starter-manifest.json').write_text(json.dumps(starter, indent=2), encoding='utf-8')
    return dest


def _run_test_dir(tests_dir, project_dir, test_files=None):
    env = dict(os.environ)
    env['PYTHONPATH'] = str(project_dir) + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    env['PYTHONUTF8'] = '1'
    argv = [sys.executable, '-B', str(WRAPPER), str(tests_dir)]
    if test_files is not None:
        argv.extend(str(path) for path in test_files)
    proc = subprocess.run(argv,
                          cwd=project_dir, env=env, capture_output=True, text=True, timeout=600)
    line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ''
    try:
        payload = json.loads(line)
    except ValueError:
        payload = {'total': 0, 'passed': 0, 'failures': 0, 'errors': 0, 'skipped': 0,
                   'detail': [f'RUNNER_ERROR exit={proc.returncode}', proc.stderr[-500:]]}
    payload['runner_exit'] = proc.returncode
    return payload


def _visible_test_files(project_dir, starter_manifest):
    starter = json.loads(starter_manifest.read_text(encoding='utf-8'))
    found = []
    for path in sorted(project_dir.rglob('test_*.py')):
        rel = path.relative_to(project_dir).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if starter.get(rel) != digest:
            found.append(path)
    return found


def _run_visible_tests(dest, project, visible_files):
    # Keep __file__-relative CLI paths, test fixtures and duplicate basenames.
    # Run only selected actor tests; no evaluator-owned tests enter this copy.
    # Rebase internal symlinks; external/cyclic targets are evaluator errors.
    # This is a disposable copy, not an OS sandbox for arbitrary Python code.
    if project.is_symlink():
        raise ValueError('EVALUATOR_ERROR symlink project root')
    symlinks = {}
    for base, directories, names in os.walk(project, followlinks=False):
        for name in directories + names:
            path = Path(base) / name
            if not path.is_symlink():
                continue
            try:
                target = path.resolve().relative_to(project.resolve())
            except (OSError, RuntimeError) as exc:
                raise ValueError(f'EVALUATOR_ERROR unresolved symlink: {path}') from exc
            except ValueError as exc:
                raise ValueError(f'EVALUATOR_ERROR external symlink: {path}') from exc
            symlinks[path.relative_to(project)] = target
    with tempfile.TemporaryDirectory(prefix='visible-grader-', dir=dest) as tmp:
        isolated = Path(tmp) / 'project'
        shutil.copytree(project, isolated, symlinks=True)
        for relative, target in symlinks.items():
            copied_link = isolated / relative
            copied_link.unlink()
            copied_link.symlink_to(os.path.relpath(isolated / target, copied_link.parent))
        selected = [isolated / path.relative_to(project) for path in visible_files]
        return _run_test_dir(isolated, isolated, selected)


def process_score(task, project_dir, final_text, hidden_partial=None):
    """Criteria-driven adjudication for kind=process tasks.

    Components (weights from task.json 'process', renormalised over the
    applicable ones): reply = must-match regex hits (any must-not hit zeroes
    it); artifact = file existence + its own must/must-not patterns;
    questions = '?'/'?' count >= min_question_marks; hidden = hidden-unittest
    partial credit when the pack ships hidden tests.
    """
    proc = task['process']
    weights = proc.get('weights') or {'reply': 0.4, 'artifact': 0.3,
                                      'questions': 0.1, 'hidden': 0.2}
    components = {}
    must = proc.get('reply_must_match') or []
    if must:
        hits = sum(1 for pat in must if re.search(pat, final_text))
        score = hits / len(must)
        if any(re.search(pat, final_text) for pat in proc.get('reply_must_not_match') or []):
            score = 0.0
        components['reply'] = score
    artifact_rel = proc.get('artifact')
    artifact_globs = proc.get('artifact_glob') or []
    if artifact_rel or artifact_globs:
        texts = []
        if artifact_rel:
            path = Path(project_dir) / artifact_rel
            if path.is_file():
                texts.append(path.read_text(encoding='utf-8', errors='replace'))
        for pattern in artifact_globs:
            root = Path(project_dir)
            for match in root.glob(pattern):
                if match.is_file():
                    texts.append(match.read_text(encoding='utf-8', errors='replace'))
        text = '\n'.join(texts)
        amust = proc.get('artifact_must_match') or []
        if not text:
            score = 0.0
        elif amust:
            score = sum(1 for pat in amust if re.search(pat, text)) / len(amust)
        else:
            score = 1.0
        if text and any(re.search(pat, text)
                        for pat in proc.get('artifact_must_not_match') or []):
            score = 0.0
        components['artifact'] = score
    min_questions = proc.get('min_question_marks') or 0
    if min_questions:
        count = final_text.count('?') + final_text.count('？')
        components['questions'] = 1.0 if count >= min_questions else 0.0
    if hidden_partial is not None:
        components['hidden'] = hidden_partial
    total_weight = sum(weights.get(name, 0) for name in components)
    if not total_weight:
        return 0.0, components
    score = sum(components[name] * weights.get(name, 0) for name in components) / total_weight
    return round(score, 4), components


def adjudicate(dest, condition, task):
    project = dest / 'project'
    has_hidden = (Path(task['root']) / 'hidden' / 'tests').is_dir()
    hidden = (_run_test_dir(_hidden_dir(dest), project) if has_hidden
              else {'total': 0, 'passed': 0, 'failures': 0, 'errors': 0, 'skipped': 0,
                    'detail': []})
    visible_files = _visible_test_files(project, dest / 'starter-manifest.json')
    visible = None
    if visible_files:
        visible = _run_visible_tests(dest, project, visible_files)
    parsed = events.parse(dest / 'events.jsonl')
    proc_result = json.loads((dest / 'process-result.json').read_text(encoding='utf-8'))
    runtime_dir = dest / 'runtime'
    fired = (events.detect_skills(parsed, runtime_dir, project)
             if runtime_dir.is_dir() else [])
    hidden_partial = round(hidden['passed'] / hidden['total'], 4) if hidden['total'] else 0.0
    components = None
    if task.get('kind') == 'process':
        hidden_partial, components = process_score(task, project, parsed['final_text'],
                                                   hidden_partial if has_hidden else None)
    visible_partial = (round(visible['passed'] / visible['total'], 4)
                       if visible and visible['total'] else None)
    result = {'task': dest.parent.parent.name, 'condition': condition['id'],
              'trial': dest.name, 'kind': task.get('kind', 'code'),
              'hidden': hidden, 'hidden_partial': hidden_partial,
              'process_components': components,
              'visible': visible, 'visible_partial': visible_partial,
              'gap': (round(visible_partial - hidden_partial, 4)
                      if visible_partial is not None else None),
              'fired_skills': fired,
              'usage': parsed['usage'], 'seconds': proc_result.get('seconds'),
              'exit_code': proc_result.get('exit_code'),
              'parse_errors': parsed['parse_errors'],
              'final_text': parsed['final_text'][:4000]}
    (dest / 'final-reply.txt').write_text(parsed['final_text'], encoding='utf-8')
    (dest / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                      encoding='utf-8')
    return result


def _hidden_dir(dest):
    task_id = dest.parent.parent.name
    return CORPUS / 'tasks' / task_id / 'hidden' / 'tests'


def execute_slot(slot, run_dir, runtime_full, executable='pi'):
    dest = prepare_slot(slot['task'], slot['condition'], slot['trial'], run_dir, runtime_full)
    if not (dest / 'result.json').exists():
        if not (dest / 'process-result.json').exists():
            pi_runner.run(dest, skills_dir=(dest / 'runtime') if slot['condition']['skills'] else None,
                          executable=executable, timeout=slot['timeout'])
        adjudicate(dest, slot['condition'], slot['task'])


# ---------- statistics ----------

def normalized_gain(base, treat):
    if base is None or treat is None:
        return None
    if base >= 1.0:
        return None
    return round((treat - base) / (1.0 - base), 4)


def bootstrap_ci(values, seed=13, n=10000):
    values = [v for v in values if v is not None]
    if not values:
        return None
    rng = random.Random(seed)
    means = []
    for _ in range(n):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    means.sort()
    return {'mean': round(sum(values) / len(values), 4),
            'p5': round(means[int(0.05 * (n - 1))], 4),
            'p95': round(means[int(0.95 * (n - 1))], 4),
            'n': len(values)}


def aggregate(results, conditions):
    """Condition-level and per-task metrics; every rate carries its raw counts."""
    by_cond, by_task = {}, {}
    for res in results:
        cond = res['condition']
        by_cond.setdefault(cond, []).append(res)
        by_task.setdefault((res['task'], cond), []).append(res)
    metrics = {'conditions': {}, 'tasks': {}}
    for cond, items in by_cond.items():
        partials = [r['hidden_partial'] for r in items]
        tokens = [r['usage']['input'] + r['usage']['cache_read'] + r['usage']['cache_write'] + r['usage']['output']
                  for r in items]
        inputs = [r['usage']['input'] for r in items]
        complete_usage = all(r['usage'].get('complete', True) for r in items)
        metrics['conditions'][cond] = {
            'n_runs': len(items),
            'mean_partial': round(sum(partials) / len(partials), 4),
            'pass_at_k': any(p == 1.0 for p in partials),
            'pass_cap_k': all(p == 1.0 for p in partials) and bool(partials),
            'full_pass_runs': sum(1 for p in partials if p == 1.0),
            'tokens_total': sum(tokens) if complete_usage else None,
            'tokens_mean': round(sum(tokens) / len(tokens), 1) if complete_usage else None,
            'input_mean': round(sum(inputs) / len(inputs), 1) if complete_usage else None,
            'usage_complete_runs': sum(bool(r['usage'].get('complete', True)) for r in items),
            'seconds_mean': (round(sum(r['seconds'] for r in items if r['seconds']) /
                                   max(1, sum(1 for r in items if r['seconds'])), 1)),
            'invocation_rate': round(sum(1 for r in items if r['fired_skills']) / len(items), 4),
        }
    for (task, cond), items in sorted(by_task.items()):
        metrics['tasks'][f'{task}|{cond}'] = {
            'mean_partial': round(sum(r['hidden_partial'] for r in items) / len(items), 4),
            'trials': [r['hidden_partial'] for r in items],
            'visible_gap_mean': (round(sum(r['gap'] for r in items if r['gap'] is not None) /
                                       max(1, sum(1 for r in items if r['gap'] is not None)), 4)
                                 if any(r['gap'] is not None for r in items) else None),
        }
    if 'baseline' in metrics['conditions'] and 'full' in metrics['conditions']:
        base_cond, full_cond = metrics['conditions']['baseline'], metrics['conditions']['full']
        gains, deltas = {}, {}
        for key, value in metrics['tasks'].items():
            task, cond = key.split('|')
            if cond != 'full':
                continue
            base = metrics['tasks'].get(f'{task}|baseline', {}).get('mean_partial')
            if base is not None:
                gains[task] = normalized_gain(base, value['mean_partial'])
                deltas[task] = round(value['mean_partial'] - base, 4)
        gain_values = [g for g in gains.values() if g is not None]
        metrics['full_vs_baseline'] = {
            'macro_delta': round(full_cond['mean_partial'] - base_cond['mean_partial'], 4),
            'normalized_gain_per_task': gains,
            'delta_per_task': deltas,
            'gain_nonneg_task_fraction': (round(sum(1 for g in gain_values if g >= 0) /
                                                len(gain_values), 4) if gain_values else None),
            'worst_task_delta': min(deltas.values()) if deltas else None,
            'token_ratio': (round(full_cond['tokens_mean'] / base_cond['tokens_mean'], 4)
                            if base_cond['tokens_mean'] and full_cond['tokens_mean'] is not None else None),
            'input_overhead': (round(full_cond['input_mean'] - base_cond['input_mean'], 1)
                               if base_cond.get('input_mean') is not None and full_cond.get('input_mean') is not None else None),
            'input_ratio': (round(full_cond['input_mean'] / base_cond['input_mean'], 4)
                            if base_cond.get('input_mean') and full_cond.get('input_mean') is not None else None),
        }
    if 'baseline' in metrics['conditions'] and 'directed' in metrics['conditions']:
        base = metrics['conditions']['baseline']
        directed = metrics['conditions']['directed']
        metrics['directed_vs_baseline'] = {
            'macro_delta': round(directed['mean_partial'] - base['mean_partial'], 4),
            'token_ratio': (round(directed['tokens_mean'] / base['tokens_mean'], 4)
                            if base['tokens_mean'] and directed['tokens_mean'] is not None else None),
            'invocation_rate': directed['invocation_rate'],
        }
    return metrics
