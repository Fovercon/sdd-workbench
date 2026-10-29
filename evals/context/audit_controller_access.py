#!/usr/bin/env python3
"""Read-only, bounded audit of controller-file requests in native Pi tool events."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex


CONTROLLER_FILES = (
    'input-receipt.json', 'variant.json', 'repository.json', 'prompt.txt',
    'invocation.json', 'events.jsonl', 'stderr.log', 'process-result.json',
    'metrics.json', 'guard-evaluation.json', 'controller-tests.stdout',
    'controller-tests.stderr',
)


def literal_path(cwd, value):
    return Path(os.path.abspath(cwd / value))


def cat_paths(command, project):
    # This is a literal request index, not a shell interpreter or an access monitor.
    if any(char in command for char in '$`*?[]{}~\\#'):
        return [], True
    lexer = shlex.shlex(command, posix=False, punctuation_chars=';&|<>()\n')
    lexer.whitespace = ' \t\r'
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return [], True
    if any(set(token) & set('<>()') for token in tokens):
        return [], True
    offset = 0; previous_word = False
    for token in tokens:
        position = command.find(token, offset)
        operator = bool(re.fullmatch(r'[;&|\n]+', token))
        if (position < 0 or (position == offset and previous_word and not operator)
                or (token[:1] not in ('"', "'") and any(char in token for char in '\'"'))):
            return [], True
        offset = position + len(token); previous_word = not operator
    segments = []; current = []
    for token in tokens:
        if re.fullmatch(r'[;&|\n]+', token):
            for separator in re.findall(r'&&|\|\||[;&|\n]', token):
                if current:
                    segments.append((current, separator)); current = []
        else:
            current.append(token)
    if current:
        segments.append((current, None))
    cwd = project; paths = []; unknown = False
    previous_separator = None; conditional_cwd = False
    for args, separator in segments:
        args = [shlex.split(value)[0] if value[:1] in ('"', "'") else value for value in args]
        if args[0] == 'cd':
            operands = args[1:]
            if operands[:1] == ['--']:
                operands = operands[1:]
            if (len(operands) == 1 and operands[0] != '-' and cwd is not None
                    and previous_separator not in ('|', '&', '||', '&&')
                    and separator not in ('|', '&', '||')):
                cwd = literal_path(cwd, operands[0])
                conditional_cwd = separator == '&&'
            else:
                cwd = None; unknown = True
        elif args[0] == 'cat':
            for value in args[1:]:
                if not value.startswith('-'):
                    if cwd is not None or Path(value).is_absolute():
                        paths.append(literal_path(cwd or project, value))
                    else:
                        unknown = True
        else:
            unknown = True
            if args[0] in ('pushd', 'popd', 'source', '.', 'eval'):
                cwd = None
        if conditional_cwd and separator in (';', '\n', '&', '||'):
            cwd = None; conditional_cwd = False; unknown = True
        previous_separator = separator
    return paths, unknown


def audit(run):
    run = Path(run).resolve()
    result = {'status': 'NOT_RECORDED', 'events_sha256': None,
              'auditor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'findings': [], 'issues': [], 'unclassified_calls': [],
              'manual_review_required': True,
              'limits': [
                  'Findings are submitted literal read requests, not proof that file contents were delivered.',
                  'Tool error state describes the whole call; it does not establish individual command success.',
                  'Only structured read paths and literal cat operands with simple cd are indexed.',
                  'No matches do not prove compliance: dynamic shell, other readers, aliases, symlinks and transient effects need manual review.',
                  'The event digest binds observed bytes, not actor identity, authenticity or OS isolation.',
              ]}
    source = run / 'events.jsonl'
    if not source.exists():
        return result
    try:
        raw = source.read_bytes()
    except OSError:
        result['status'] = 'INVALID_OR_INCOMPLETE'
        result['issues'].append({'line': None, 'reason': 'Native event stream unreadable'})
        return result
    result['events_sha256'] = hashlib.sha256(raw).hexdigest()
    calls = {}; completed = set(); terminal = False
    protected = {run / name: name for name in CONTROLLER_FILES}
    for line_no, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError('Expected event object')
            kind = event.get('type')
            if not isinstance(kind, str):
                raise ValueError('Missing event type')
            if kind in ('agent_start', 'turn_start', 'turn_end', 'message_start',
                        'message_update', 'message_end', 'tool_execution_start',
                        'tool_execution_update', 'tool_execution_end'):
                terminal = False
            if kind == 'agent_end':
                terminal = True
            if kind == 'tool_execution_start':
                ident = event.get('toolCallId'); name = event.get('toolName'); args = event.get('args')
                if not isinstance(ident, str) or not ident or ident in calls:
                    raise ValueError('Missing or duplicate native call ID')
                if not isinstance(name, str) or not isinstance(args, dict):
                    raise ValueError('Invalid native tool arguments')
                call = {'tool_call_id': ident, 'tool': name, 'start_line': line_no,
                        'end_line': None, 'tool_is_error': None}
                calls[ident] = call
                if name == 'read' and isinstance(args.get('path'), str):
                    paths = [literal_path(run / 'project', args['path'])]; unknown = False
                elif name == 'bash' and isinstance(args.get('command'), str):
                    paths, unknown = cat_paths(args['command'], run / 'project')
                else:
                    paths = []; unknown = True
                if unknown:
                    result['unclassified_calls'].append({'tool_call_id': ident, 'start_line': line_no})
                for path in paths:
                    if path in protected:
                        result['findings'].append(dict(call, controller_file=protected[path], requested_path=str(path)))
            if kind == 'tool_execution_end':
                ident = event.get('toolCallId')
                if not isinstance(ident, str) or ident not in calls or ident in completed:
                    raise ValueError('Orphan or duplicate native completion')
                if type(event.get('isError')) is not bool:
                    raise ValueError('Missing native tool error state')
                if event.get('toolName') != calls[ident]['tool']:
                    raise ValueError('Native completion tool does not match its start')
                completed.add(ident)
                calls[ident].update(end_line=line_no, tool_is_error=event['isError'])
        except (ValueError, UnicodeDecodeError) as error:
            result['issues'].append({'line': line_no, 'reason': str(error)})
    for finding in result['findings']:
        call = calls[finding['tool_call_id']]
        finding.update(end_line=call['end_line'], tool_is_error=call['tool_is_error'])
    if not terminal or set(calls) != completed:
        result['issues'].append({'line': None, 'reason': 'Missing terminal event or unfinished native calls'})
    result['status'] = ('INVALID_OR_INCOMPLETE' if result['issues'] else
                        'REQUESTS_FOUND' if result['findings'] else 'NO_REQUESTS_OBSERVED')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    result = audit(parser.parse_args().run)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return {'REQUESTS_FOUND': 1, 'NO_REQUESTS_OBSERVED': 0}.get(result['status'], 2)


if __name__ == '__main__':
    raise SystemExit(main())
