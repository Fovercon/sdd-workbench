"""Acceptance-gate evaluation and diffing against the previously accepted run."""
import json
from pathlib import Path

from runner.paths import CONFIG

_OPS = {
    '>=': lambda a, b: a is not None and a >= b,
    '<=': lambda a, b: a is not None and a <= b,
}


def load_gates():
    return json.loads((CONFIG / 'gates.json').read_text(encoding='utf-8'))['gates']


def evaluate_gates(metrics, gates=None):
    """metrics maps layer -> flat metric dict; a missing layer fails its gates
    with missing=True instead of silently passing."""
    gates = gates or load_gates()
    rows = []
    for gate in gates:
        layer_metrics = (metrics or {}).get(gate['layer']) or {}
        observed = layer_metrics.get(gate['metric'])
        passed = _OPS[gate['op']](observed, gate['value'])
        rows.append({'id': gate['id'], 'layer': gate['layer'], 'metric': gate['metric'],
                     'op': gate['op'], 'threshold': gate['value'], 'observed': observed,
                     'missing': observed is None, 'passed': passed})
    return rows


def diff_reports(current, previous):
    """Surface the deltas an optimizer cares about; raw numbers only."""
    if not previous:
        return None
    diff = {'previous_run_id': previous.get('run_id'),
            'gates_regressed': [], 'gates_recovered': [],
            'l1': None, 'l2_conditions': {}}
    prev_gates = {g['id']: g['passed'] for g in previous.get('gates', [])}
    cur_gates = {g['id']: g['passed'] for g in current.get('gates', [])}
    for gate_id, passed in cur_gates.items():
        if gate_id in prev_gates:
            if prev_gates[gate_id] and not passed:
                diff['gates_regressed'].append(gate_id)
            if not prev_gates[gate_id] and passed:
                diff['gates_recovered'].append(gate_id)
    prev_l1 = (previous.get('l1') or {}).get('aggregate') or {}
    cur_l1 = (current.get('l1') or {}).get('aggregate') or {}
    if prev_l1 or cur_l1:
        diff['l1'] = {'n_correct': [prev_l1.get('n_correct'), cur_l1.get('n_correct')],
                      'n_cases': [prev_l1.get('n_cases'), cur_l1.get('n_cases')]}
    prev_conds = ((previous.get('l2') or {}).get('aggregate') or {}).get('conditions') or {}
    cur_conds = ((current.get('l2') or {}).get('aggregate') or {}).get('conditions') or {}
    for cond, metrics in cur_conds.items():
        prev_mean = (prev_conds.get(cond) or {}).get('mean_partial')
        if prev_mean is not None:
            diff['l2_conditions'][cond] = {'mean_partial': [prev_mean, metrics['mean_partial']],
                                           'delta': round(metrics['mean_partial'] - prev_mean, 4)}
    return diff
