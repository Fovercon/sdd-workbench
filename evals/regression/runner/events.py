"""Tolerant events.jsonl parsing for Pi event streams.

Validated against Pi 1.3.0 (message_end.message.usage / .content blocks) while
keeping the legacy 0.86.x shapes (top-level usage on message_end, tool_call
events, message.text) as a fallback. Streaming message_update deltas are never
counted. Unknown event shapes are counted, never silently dropped.
"""
import json
import re
import shlex
from pathlib import Path

_INPUT_KEYS = ('input', 'input_tokens', 'prompt_tokens')
_CACHE_READ_KEYS = ('cacheRead', 'cache_read_tokens', 'cached_input_tokens', 'cache_read')
_CACHE_WRITE_KEYS = ('cacheWrite', 'cache_write_tokens', 'cache_write')
_OUTPUT_KEYS = ('output', 'output_tokens', 'completion_tokens')
_KNOWN_TYPES = ('session', 'agent_start', 'agent_end', 'agent_settled', 'aborted',
                'turn_start', 'turn_end',
                'message_start', 'message_update', 'message_end',
                'tool_call', 'toolCall', 'tool_call_end', 'toolResult',
                'tool_execution_start', 'tool_execution_update', 'tool_execution_end',
                'message', 'assistant', 'user', 'system', 'error', 'result')
_READ_TOOLS = re.compile(r'read|open|cat|view|edit|write', re.I)
_BASH_SKILL_RE = re.compile(r'(?:\.\./|/|\b)runtime(?:-full)?/([A-Za-z0-9][A-Za-z0-9_-]*)/')


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def _num(usage, *keys):
    return sum(v for k in keys for v in [usage.get(k)]
               if isinstance(v, (int, float)) and not isinstance(v, bool))


def _message_blocks(message):
    content = (message or {}).get('content')
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                yield block


def _event_usage(event):
    message = event.get('message')
    if isinstance(message, dict):
        if message.get('role') not in (None, 'assistant'):
            return None
        if isinstance(message.get('usage'), dict):
            return message['usage']
    return event.get('usage')


def _add_usage(one, usage):
    keys = _INPUT_KEYS + _CACHE_READ_KEYS + _CACHE_WRITE_KEYS + _OUTPUT_KEYS
    if not isinstance(one, dict) or not any(
            isinstance(one.get(key), (int, float)) and not isinstance(one.get(key), bool)
            for key in keys):
        return False
    usage['usage_events'] += 1
    one_input = _num(one, *_INPUT_KEYS)
    usage['input'] += one_input
    usage['input_peak'] = max(usage['input_peak'], one_input)
    usage['cache_read'] += _num(one, *_CACHE_READ_KEYS)
    usage['cache_write'] += _num(one, *_CACHE_WRITE_KEYS)
    usage['output'] += _num(one, *_OUTPUT_KEYS)
    return True


def _handle_message_end(event, usage, assistant_texts, calls):
    message = event.get('message')
    if not isinstance(message, dict):
        return
    if message.get('role') == 'assistant':
        counted = _add_usage(_event_usage(event), usage)
        text = message.get('text')
        if isinstance(text, str) and text.strip():
            assistant_texts.append(text)
        block_text = ''.join(b.get('text') or '' for b in _message_blocks(message)
                             if b.get('type') == 'text')
        if block_text.strip():
            assistant_texts.append(block_text)
        for block in _message_blocks(message):
            if block.get('type') != 'toolCall':
                continue
            name = block.get('name')
            args = block.get('arguments') or {}
            if not isinstance(name, str) or not isinstance(args, dict):
                continue
            if _READ_TOOLS.fullmatch(name):
                for value in args.values():
                    if isinstance(value, str) and ('/' in value or value.endswith(
                            ('.md', '.py', '.txt', '.json', '.yml', '.yaml'))):
                        calls.append((name.lower(), value))
            elif name.lower() == 'bash':
                command = args.get('command')
                if isinstance(command, str):
                    for match in _BASH_SKILL_RE.finditer(command):
                        calls.append((name.lower(), f'runtime/{match.group(1)}/'))
        return counted


def parse(path):
    path = Path(path)
    lines = path.read_text(encoding='utf-8', errors='replace').splitlines() if path.exists() else []
    usage = {'input': 0, 'cache_read': 0, 'cache_write': 0, 'output': 0,
             'input_peak': 0, 'usage_events': 0}
    assistant_texts, calls, skill_events, tool_calls = [], [], [], []
    tool_results = {}
    parse_errors = 0
    unknown_types = {}
    turn_usage_events, missing_message_usage = 0, 0
    unclassified_usage_events = 0
    result_fallbacks = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            parse_errors += 1
            continue
        etype = event.get('type') if isinstance(event, dict) else None
        etype = etype if isinstance(etype, str) else 'UNKNOWN'
        if etype == 'turn_start':
            unclassified_usage_events += missing_message_usage
            turn_usage_events, missing_message_usage = 0, 0
        if etype == 'message_end':
            counted = _handle_message_end(event, usage, assistant_texts, calls)
            if counted is True:
                turn_usage_events += 1
            elif counted is False:
                missing_message_usage += 1
            for block in _message_blocks(event.get('message')):
                if block.get('type') == 'toolCall':
                    tool_calls.append(block)
        elif etype == 'tool_execution_end':
            result = event.get('result') or {}
            structured = result.get('structuredContent') or {}
            if not isinstance(structured, dict):
                structured = {}
            tool_results[event.get('toolCallId')] = (
                event.get('isError') is False and structured.get('exit_code', 0) == 0)
        elif 'skill' in etype.lower():
            for node in _walk(event):
                for key, value in node.items():
                    if 'skill' in str(key).lower() and isinstance(value, str) and value:
                        skill_events.append({'type': etype, 'key': key, 'value': value})
        else:
            # Pi 1.3 repeats the same assistant message at turn_end. Use its
            # usage only for a legacy turn without a counted message_end.
            if etype == 'turn_end':
                one = _event_usage(event)
                if not turn_usage_events and _add_usage(one, usage):
                    missing_message_usage = max(0, missing_message_usage - 1)
                elif not turn_usage_events and any('usage' in node for node in _walk(event)):
                    unclassified_usage_events += 1
                unclassified_usage_events += missing_message_usage
                turn_usage_events, missing_message_usage = 0, 0
            elif etype == 'result':
                result_fallbacks.append(_event_usage(event))
            elif etype not in _KNOWN_TYPES and any('usage' in node for node in _walk(event)):
                unclassified_usage_events += 1
            # Preserve legacy tool calls and text independently from usage.
            for node in _walk(event):
                tool = node.get('tool') or node.get('name')
                if (etype.startswith('tool') and isinstance(tool, str)
                        and _READ_TOOLS.fullmatch(tool)):
                    args = node.get('args') or node.get('arguments') or {}
                    if isinstance(args, dict):
                        for value in args.values():
                            if isinstance(value, str) and ('/' in value):
                                calls.append((tool.lower(), value))
                role, text = node.get('role'), node.get('text')
                if role == 'assistant' and isinstance(text, str) and text.strip():
                    assistant_texts.append(text)
        if etype not in _KNOWN_TYPES and not etype.startswith('tool'):
            unknown_types[etype] = unknown_types.get(etype, 0) + 1
    unclassified_usage_events += missing_message_usage
    if not usage['usage_events'] and result_fallbacks:
        if len(result_fallbacks) != 1 or not _add_usage(result_fallbacks[0], usage):
            unclassified_usage_events += len(result_fallbacks)
    usage['unclassified_usage_events'] = unclassified_usage_events
    usage['complete'] = bool(usage['usage_events']) and not unclassified_usage_events
    seen, reads = set(), []
    for tool, target in calls:
        key = (tool, target)
        if key in seen:
            continue
        seen.add(key)
        reads.append({'tool': tool, 'path': target})
    return {'usage': usage, 'reads': reads, 'skill_events': skill_events,
            'tool_calls': tool_calls, 'tool_results': tool_results,
            'final_text': assistant_texts[-1] if assistant_texts else '',
            'all_assistant_text': '\n'.join(assistant_texts),
            'parse_errors': parse_errors, 'unknown_types': unknown_types,
            'lines': len(lines)}


def _shell_reads(command, cwd):
    """Identify the final literal read in a successful simple shell call.

    shortcut: earlier compound reads, pipelines and dynamic shell forms remain
    unclassified; overall shell success cannot prove every subcommand succeeded.
    """
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|()<>\n')
        lexer.whitespace = ' \t\r'
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return None
    if any(t in ('||', '&', '(', ')', '<<', '>>', '>', '<') or
           any(c in t for c in '$`') for t in tokens):
        return None
    segments = []
    segment = []
    for token in tokens + [';']:
        if token and all(c in ';&|()<>\n' for c in token):
            if segment:
                segments.append(segment)
            segment = []
        else:
            segment.append(token)
    if not segments:
        return []
    if segments[0][0] == 'cd':
        if len(segments[0]) != 2:
            return None
        cwd = (cwd / segments.pop(0)[1]).resolve()
        if not cwd.is_dir():
            return None
    if not segments or any(s[0] not in ('ls', 'echo', 'pwd', 'wc', 'cat', 'head', 'tail', 'sed')
                           for s in segments[:-1]):
        return None
    name, *args = segments[-1]
    if name not in ('cat', 'head', 'tail', 'sed'):
        return None
    if any(a in ('--help', '--version') or any(c in a for c in '*?') for a in args):
        return None
    if name == 'sed':
        if args and args[0] == '-n':
            args = args[1:]
        if not args or not re.fullmatch(r'\d+(?:,\d+)?[pqd]', args[0]):
            return None
        args = args[1:]
    paths = [cwd / a for a in args if not a.startswith('-')]
    return [p for p in paths if p.is_file()] if paths else None


def detect_skills(parsed, runtime_dir, project_cwd=None):
    """Successful native reads, conservative literal shell reads, or known
    lifecycle starts are exposure evidence. Legacy calls without result events
    remain unverified; raw reads/commands are retained for manual review."""
    runtime = Path(runtime_dir).resolve()
    names = {child.name for child in runtime.iterdir()} if runtime.is_dir() else set()
    fired = set()
    reads = parsed['reads']
    if 'tool_calls' in parsed:
        reads = []
        parsed['unclassified_reads'] = []
        for call in parsed['tool_calls']:
            if not parsed['tool_results'].get(call.get('id')):
                continue
            args = call.get('arguments') or {}
            tool = call.get('name')
            if tool in ('read', 'open', 'cat', 'view') and isinstance(args.get('path'), str):
                reads.append({'tool': tool, 'path': args['path']})
            elif tool == 'bash' and isinstance(args.get('command'), str):
                targets = _shell_reads(args['command'], Path(project_cwd or Path.cwd()))
                if targets is None:
                    parsed.setdefault('unclassified_reads', []).append(call.get('id'))
                for path in targets or []:
                    reads.append({'tool': 'shell_read', 'path': str(path)})
    for item in reads:
        # Compatibility for legacy/pre-parsed records without result events.
        marker = _BASH_SKILL_RE.search(item['path'])
        if 'tool_calls' not in parsed and marker and marker.group(1) in names:
            fired.add(marker.group(1))
            continue
        p = Path(item['path'])
        if p.is_absolute():
            candidates = [p]
        else:
            candidates = [Path(project_cwd) / p] if project_cwd else []
            candidates.append(Path.cwd() / p)
        for cand in candidates:
            try:
                rel = cand.resolve().relative_to(runtime)
            except (ValueError, OSError):
                continue
            if len(rel.parts) >= 2 and rel.parts[0] in names:
                fired.add(rel.parts[0])
    for ref in parsed['skill_events']:
        value = str(ref.get('value', ''))
        if (ref.get('type') in ('skill_start', 'skill_load', 'skill_loaded',
                               'skill_activated', 'skill_invoked') and value in names):
            fired.add(value)
    return sorted(fired)
