#!/usr/bin/env python3
"""Summarize native completed usage events, never streaming deltas or price estimates."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def summarize(host, path):
    data = Path(path).read_bytes()
    records, malformed = [], []
    try:
        decoded = data.decode('utf-8')
        valid_utf8 = True
    except UnicodeDecodeError:
        decoded = data.decode('utf-8', errors='replace')
        valid_utf8 = False
    for number, line in enumerate(decoded.splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError('Native event must be an object')
            records.append(record)
        except ValueError:
            malformed.append(number)
    counts = Counter(value.get('type') for value in records)
    usages, missing, models, interactions = [], 0, set(), []
    tool_calls = tool_errors = 0
    for value in records:
        if host == 'codex':
            if value.get('type') == 'turn.completed':
                if isinstance(value.get('usage'), dict):
                    usages.append(value['usage'])
                else:
                    missing += 1
            if value.get('type') == 'item.completed':
                item = value.get('item', {})
                interactions.append(item)
                if item.get('type') == 'command_execution':
                    tool_calls += 1
                    tool_errors += item.get('exit_code') not in (0, None)
        else:
            if value.get('type') == 'message_end':
                message = value.get('message', {})
                if message.get('role') == 'assistant':
                    models.add((message.get('provider'), message.get('model')))
                    if isinstance(message.get('usage'), dict):
                        usages.append({k: v for k, v in message['usage'].items() if k != 'cost'})
                    else:
                        missing += 1
                # Native reasoning remains in the raw log; this view contains
                # visible text, calls and results only. It is not another judge.
                if message.get('role') != 'system':
                    interactions.append({**message, 'content': [
                        c for c in message.get('content', []) if c.get('type') != 'thinking']})
            if value.get('type') == 'tool_execution_end':
                tool_calls += 1
                tool_errors += bool(value.get('isError'))
    totals, present = Counter(), Counter()
    for usage in usages:
        for key, value in usage.items():
            if type(value) is int and value >= 0:
                totals[key] += value
                present[key] += 1
    complete = (counts['turn.completed'] > 0 if host == 'codex' else counts['agent_end'] > 0)
    report = {
        'host': host, 'events_sha256': hashlib.sha256(data).hexdigest(),
        'raw_stream_valid_utf8': valid_utf8,
        'native_completion_event_observed': complete, 'malformed_json_lines': malformed,
        'completed_usage_events': len(usages), 'completed_messages_without_usage': missing,
        'reported_token_totals': dict(totals), 'field_observation_counts': dict(present),
        'models_observed': [{'provider': provider, 'model': model}
                            for provider, model in sorted(models, key=str)],
        'completed_command_or_tool_calls': tool_calls, 'nonzero_commands_or_tool_errors': tool_errors,
        'event_counts': dict(counts),
        'counting_basis': 'Codex turn.completed.usage' if host == 'codex' else 'Pi assistant message_end.message.usage',
        'limits': ['Only emitted completed usage is counted; interrupted/unreported requests may be missing.',
                   'Streaming updates are excluded. Reasoning is not added to output again.',
                   'Native fields retain host-specific meaning; no billing or framework ranking is inferred.',
                   'CLI exit, current files and independent tests must be checked separately.'],
    }
    if host == 'codex':
        report['field_semantics'] = 'input_tokens includes cached_input_tokens; report the cached subset separately.'
    else:
        report['field_semantics'] = ('Pi input/cacheRead/cacheWrite are separate fields; totalTokens is native total; '
                                    'reasoning, when present, is a subset of output (Pi 0.86.1 Usage type).')
    return report, interactions


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=('codex', 'pi'), required=True)
    parser.add_argument('--events', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--interaction', type=Path)
    args = parser.parse_args()
    report, interactions = summarize(args.host, args.events)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    if args.interaction:
        text = '# Native completed interaction events\n\nRaw stream SHA-256: ' + report['events_sha256'] + '\n'
        for number, item in enumerate(interactions, 1):
            text += '\n## Event ' + str(number) + '\n\n```json\n' + json.dumps(item, ensure_ascii=False, indent=2) + '\n```\n'
        args.interaction.write_text(text, encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True))
