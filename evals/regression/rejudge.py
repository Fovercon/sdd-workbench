#!/usr/bin/env python3
"""Offline L1 rejudgment into a fresh directory; never reruns actors or accepts a baseline."""
import argparse
import datetime
import hashlib
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runner import compare, events, l1_trigger, reporting, runtime
from runner.paths import runs_root


def rejudge(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output == source or source in output.parents:
        raise ValueError('Derived output must be outside the source run')
    manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    slots = json.loads((source / 'slots.json').read_text(encoding='utf-8'))['slots']
    for slot in slots:
        if slot['kind'] == 'l1' and not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slot['case']['id']):
            raise ValueError('Invalid L1 case id')
    snapshot = runtime.snapshot_hash(source / 'runtime-full')
    if manifest.get('snapshot_hash') and manifest['snapshot_hash'] != snapshot['total']:
        raise ValueError('Source runtime differs from its recorded snapshot')
    output.mkdir(parents=True, exist_ok=False)
    hashes, results = {}, []

    def record(path):
        hashes[path.relative_to(source).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()

    record(source / 'slots.json')
    record(source / 'manifest.json')
    for slot in slots:
        if slot['kind'] != 'l1':
            continue
        case = slot['case']  # historical expectation, never today's edited corpus
        trial = source / 'l1' / case['id']
        if not (trial / 'result.json').is_file():
            continue
        for name in ('result.json', 'events.jsonl'):
            record(trial / name)
        parsed = events.parse(trial / 'events.jsonl')
        old_result = json.loads((trial / 'result.json').read_text(encoding='utf-8'))
        fired = events.detect_skills(parsed, source / 'runtime-full', trial / 'project')
        result = {'case': case['id'], 'category': case['category'],
                  **l1_trigger.score(case, fired, parsed['final_text']),
                  'valid_trial': l1_trigger.trial_valid(old_result.get('exit_code'), parsed),
                  'parse_errors': parsed['parse_errors'], 'unknown_types': parsed['unknown_types'],
                  'unclassified_shell_calls': len(parsed.get('unclassified_reads', []))}
        results.append(result)
        dest = output / 'l1' / case['id']
        dest.mkdir(parents=True)
        (dest / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                        encoding='utf-8')
    provenance = {'source': str(source), 'source_run_id': manifest['run_id'],
                  'scope': 'L1 detector/scoring only; original cases; no actor rerun',
                  'source_files': hashes,
                  'runtime_hash': snapshot,
                  'scorer_files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                      (Path(__file__), Path(events.__file__), Path(l1_trigger.__file__),
                       Path(runtime.__file__))}}
    (output / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2),
                                          encoding='utf-8')
    aggregate = l1_trigger.aggregate(results)
    report = {'run_id': output.name, 'profile': 'offline-rejudge', 'manifest': manifest,
              'l1': {'aggregate': aggregate}, 'l2': None, 'l3': None,
              'gates': compare.evaluate_gates({'l1': aggregate}),
              'optimization_hints': [provenance['scope']], 'comparison': None}
    reporting.write_report(output, report)  # no index mutation or baseline acceptance
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = runs_root() / (stamp + '-rejudge-' + args.source.name)
    result = rejudge(args.source, destination)
    print(json.dumps({'output': str(destination), 'l1': result['l1']['aggregate']},
                     ensure_ascii=False))
