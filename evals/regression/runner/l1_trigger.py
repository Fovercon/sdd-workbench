"""Layer 1 - trigger precision/recall, confusion pairs and outcome-enum discipline.

Cases are grouped JSON arrays under corpus/l1/cases/*.json; prompts never name
a skill, so firing depends only on the suite's descriptions plus the fixture
project state. A skill counts as fired when the actor read any file under the
skill's runtime directory (see runner.events.detect_skills).
"""
import json
import re
import shutil
from pathlib import Path

from runner import events, pi_runner
from runner.paths import CORPUS

OUTCOME_ENUMS = {
    'sdd-workflow-router': ('NEXT_STEP_READY', 'HUMAN_DECISION_REQUIRED', 'RECONCILIATION_REQUIRED',
                            'INSUFFICIENT_CONTEXT', 'NO_ROUTING_NEEDED', 'MISSION_COMPLETE',
                            'MISSION_WAITING', 'MISSION_BLOCKED'),
    'sdd-project-bootstrap': ('DISCOVERY_COMPLETE', 'BASELINE_READY_FOR_APPROVAL', 'BASELINE_APPROVED',
                              'BASELINE_CURRENT', 'HUMAN_DECISION_REQUIRED', 'RECONCILIATION_REQUIRED',
                              'INSUFFICIENT_EVIDENCE'),
    'sdd-requirements-contract': ('NEEDS_INPUT', 'READY_FOR_APPROVAL', 'APPROVED',
                                  'AUTHORIZED_DERIVATION', 'SUPERSEDED'),
    'sdd-plan-slices': ('NEEDS_SPEC', 'NEEDS_DECISION', 'READY_FOR_DESIGN_REVIEW',
                        'READY_FOR_IMPLEMENTATION'),
    'sdd-implement-slice': ('SLICE_COMPLETE', 'NEEDS_SPEC', 'NEEDS_PLAN', 'HUMAN_DECISION_REQUIRED',
                            'WORKSPACE_RECONCILIATION_REQUIRED', 'ENVIRONMENT_BLOCKED',
                            'SLICE_INCOMPLETE'),
    'sdd-converge-review': ('CONVERGED', 'NOT_CONVERGED', 'INSUFFICIENT_EVIDENCE',
                            'HUMAN_DECISION_REQUIRED'),
    'sdd-finish-readiness': ('READY_FOR_HUMAN_ACTION', 'NOT_READY', 'NEEDS_CONVERGENCE',
                             'HUMAN_DECISION_REQUIRED', 'INSUFFICIENT_EVIDENCE'),
    'sdd-verification-design': ('VERIFICATION_DESIGN_READY', 'NEEDS_SPEC', 'NEEDS_PLAN',
                                'HUMAN_DECISION_REQUIRED', 'INSUFFICIENT_BASELINE'),
    'sdd-change-impact': ('IMPACT_READY', 'HUMAN_DECISION_REQUIRED', 'INSUFFICIENT_BASELINE',
                          'NO_MATERIAL_IMPACT', 'REJECTED_OR_SUPERSEDED'),
    'sdd-code-review': ('REVIEW_COMPLETE', 'SPEC_BASELINE_FOUND', 'NO_MATERIAL_CODE_CHANGE',
                        'INSUFFICIENT_SCOPE'),
    'sdd-context-handoff': ('HANDOFF_READY', 'RESUME_READY', 'RECONCILIATION_REQUIRED',
                            'INSUFFICIENT_CONTEXT', 'NO_HANDOFF_NEEDED'),
    'sdd-retrospective': ('LEARNING_PACKAGE_READY', 'HUMAN_DECISION_REQUIRED',
                          'RECONCILIATION_REQUIRED', 'INSUFFICIENT_EVIDENCE',
                          'NO_RETROSPECTIVE_NEEDED'),
}


def load_cases():
    cases = []
    for path in sorted((CORPUS / 'l1' / 'cases').glob('*.json')):
        for case in json.loads(path.read_text(encoding='utf-8')):
            _validate(case, path)
            cases.append(case)
    ids = [c['id'] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate L1 case ids')
    return cases


def _validate(case, path):
    for key in ('id', 'category', 'prompt', 'expect'):
        if key not in case:
            raise ValueError(f'{path.name}: case missing {key}')
    trigger = case['expect'].get('trigger')
    if not isinstance(trigger, list):
        raise ValueError(f'{path.name}/{case["id"]}: expect.trigger must be a list')
    for name in trigger:
        if name not in OUTCOME_ENUMS:
            raise ValueError(f'{path.name}/{case["id"]}: unknown skill {name}')
    fixture = case.get('fixture')
    if fixture is not None and not (CORPUS / 'l1' / 'fixtures' / fixture).is_dir():
        raise ValueError(f'{path.name}/{case["id"]}: unknown fixture {fixture}')


def slot_dir(run_dir, case):
    return Path(run_dir) / 'l1' / case['id']


def prepare(case, run_dir, timeout):
    dest = slot_dir(run_dir, case)
    if dest.exists():
        return None  # resume: logs already present or partial
    dest.mkdir(parents=True)
    project = dest / 'project'
    fixture = case.get('fixture')
    if fixture is None:
        project.mkdir()
        (project / 'README.md').write_text('# 空仓库\n本项目尚未初始化任何内容。\n', encoding='utf-8')
    else:
        shutil.copytree(CORPUS / 'l1' / 'fixtures' / fixture, project)
    (dest / 'prompt.txt').write_text(case['prompt'], encoding='utf-8')
    (dest / 'slot-meta.json').write_text(json.dumps(
        {'id': case['id'], 'category': case['category'], 'timeout': timeout},
        ensure_ascii=False, indent=2), encoding='utf-8')
    return dest


def adjudicate(case, dest, runtime_dir):
    parsed = events.parse(dest / 'events.jsonl')
    process = json.loads((dest / 'process-result.json').read_text(encoding='utf-8'))
    fired = events.detect_skills(parsed, runtime_dir, dest / 'project')
    verdict = score(case, fired, parsed['final_text'])
    result = {'case': case['id'], 'category': case['category'], **verdict,
              'valid_trial': trial_valid(process.get('exit_code'), parsed),
              'usage': parsed['usage'], 'exit_code': process.get('exit_code'),
              'seconds': process.get('seconds'),
              'parse_errors': parsed['parse_errors'],
              'unclassified_shell_calls': len(parsed.get('unclassified_reads', [])),
              'unknown_types': parsed['unknown_types']}
    (dest / 'final-reply.txt').write_text(parsed['final_text'], encoding='utf-8')
    (dest / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                      encoding='utf-8')
    return result


def trial_valid(exit_code, parsed):
    return exit_code == 0 and bool(parsed['final_text'].strip()) and parsed['parse_errors'] == 0


def score(case, fired, final_text):
    expected = list(case['expect']['trigger'])
    may_also = set(case.get('may_also') or [])
    misses = [name for name in expected if name not in fired]
    false_fires = [name for name in fired if name not in expected and name not in may_also]
    primary = expected[0] if expected else None
    enum_ok = None
    if primary is not None and primary in fired and case.get('enum_required', True):
        enum_ok = any(re.search(r'\b' + re.escape(token) + r'\b', final_text)
                      for token in OUTCOME_ENUMS[primary])
    family = case['expect'].get('outcome_family') or []
    family_ok = any(re.search(pattern, final_text) for pattern in family) if family else None
    return {'expected': expected, 'fired': fired,
              'correct': not misses and not false_fires,
              'strict_correct': set(fired) == set(expected),
              'allowed_fires': sorted(set(fired) & may_also - set(expected)),
              'misses': misses, 'false_fires': false_fires,
              'negative_false_positive': bool(false_fires) if not expected else None,
              'enum_ok': enum_ok, 'family_ok': family_ok}


def execute_slot(slot, run_dir, runtime_full, executable='pi'):
    case = slot['case']
    dest = prepare(case, run_dir, slot['timeout'])
    if dest is None:
        dest = slot_dir(run_dir, case)
    if not (dest / 'result.json').exists():
        if not (dest / 'process-result.json').exists():
            pi_runner.run(dest, skills_dir=runtime_full, executable=executable,
                          timeout=slot['timeout'])
        adjudicate(case, dest, runtime_full)


def aggregate(results):
    """Raw counts first; rates are derived so no percentage is invented."""
    per_skill = {}
    confusion = {}
    negatives = {'n': 0, 'false_positives': 0, 'cases': []}
    enum = {'evaluated': 0, 'ok': 0}
    correct_n = 0
    strict_n = 0
    for res in results:
        if not res.get('valid_trial', True):
            continue
        expected, fired = res['expected'], res['fired']
        if res['correct']:
            correct_n += 1
        strict_n += res.get('strict_correct', res['correct'])
        for name in expected:
            per_skill.setdefault(name, {'expected': 0, 'fired': 0, 'correct': 0})['expected'] += 1
        for name in fired:
            if name in res.get('allowed_fires', []):
                continue
            slot = per_skill.setdefault(name, {'expected': 0, 'fired': 0, 'correct': 0})
            slot['fired'] += 1
            if name in expected:
                slot['correct'] += 1
        for miss in res['misses']:
            for extra in res['fired']:
                key = f'{miss} <- {extra}'
                confusion[key] = confusion.get(key, 0) + 1
        if res['negative_false_positive'] is not None:
            negatives['n'] += 1
            if res['negative_false_positive']:
                negatives['false_positives'] += 1
                negatives['cases'].append({'case': res['case'], 'fired': res['fired']})
        if res['enum_ok'] is not None:
            enum['evaluated'] += 1
            if res['enum_ok']:
                enum['ok'] += 1
    for name, slot in per_skill.items():
        slot['recall'] = round(slot['correct'] / slot['expected'], 4) if slot['expected'] else None
        slot['precision'] = round(slot['correct'] / slot['fired'], 4) if slot['fired'] else None
    negative_precision = (round((negatives['n'] - negatives['false_positives']) / negatives['n'], 4)
                          if negatives['n'] else None)
    enum_discipline = round(enum['ok'] / enum['evaluated'], 4) if enum['evaluated'] else None
    return {'n_cases': len(results), 'n_correct': correct_n, 'n_strict_correct': strict_n,
            'n_invalid': sum(not r.get('valid_trial', True) for r in results),
            'per_skill': per_skill, 'confusion_pairs': confusion,
            'negatives': negatives, 'enum': enum,
            'negative_precision': negative_precision,
            'enum_discipline': enum_discipline,
            'router_recall': (per_skill.get('sdd-workflow-router', {}).get('recall')
                              if per_skill.get('sdd-workflow-router') else None)}
