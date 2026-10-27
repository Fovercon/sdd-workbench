#!/usr/bin/env python3
"""Build/check explicit UTF-8 source excerpts; freshness is not approval or completeness."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def source_path(project, value):
    if (not nonempty(value) or '\\' in value or PureWindowsPath(value).drive
            or PurePosixPath(value).is_absolute() or '..' in PurePosixPath(value).parts):
        raise ValueError('Source path must be project-relative without traversal')
    path = project
    for part in PurePosixPath(value).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Source path contains a symlink')
    if not path.is_file():
        raise ValueError('Source path is missing or not a regular file')
    return path


def sources(value):
    if not isinstance(value, list) or not value:
        raise ValueError('Sources must be a nonempty list')
    identifiers = set()
    for item in value:
        if not isinstance(item, dict) or not all(nonempty(item.get(k)) for k in ('id', 'path', 'reason')):
            raise ValueError('Each source needs id, path and reason')
        if item['id'] in identifiers:
            raise ValueError('Source ids must be unique')
        identifiers.add(item['id'])
        if any(type(item.get(k)) is not int or item[k] < 1 for k in ('start', 'end')):
            raise ValueError('Source range requires positive integer start/end')
        if item['end'] < item['start']:
            raise ValueError('Source range is reversed')
    return value


def fingerprint(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
        raise ValueError('Invalid SHA256 fingerprint')
    return value


def binding(receipt):
    metadata = {key: receipt[key] for key in ('schema', 'project', 'task', 'sources')}
    sha = digest(json.dumps(metadata, sort_keys=True, ensure_ascii=True).encode('utf-8'))
    return '# Selected source context\n\nSelection SHA256: ' + sha + '\n\n'


def build(project, selection, output, max_bytes=32768):
    project, output = Path(project).resolve(), Path(output)
    if not project.is_dir():
        raise ValueError('Project directory missing')
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists; preserve the earlier packet')
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError('Byte budget must be positive')
    if (not isinstance(selection, dict) or type(selection.get('schema')) is not int
            or selection['schema'] != 1 or not nonempty(selection.get('task'))):
        raise ValueError('Invalid selection schema/task')
    records, sections = [], []
    for item in sources(selection.get('sources')):
        data = source_path(project, item['path']).read_bytes()
        sha = digest(data)
        if 'expected_sha256' in item and fingerprint(item['expected_sha256']) != sha:
            raise ValueError('Source fingerprint differs from the selected version')
        data.decode('utf-8')  # Validate the whole source, not just selected lines.
        lines = data.splitlines(keepends=True)
        if item['end'] > len(lines):
            raise ValueError('Source range exceeds the current file')
        excerpt = b''.join(lines[item['start'] - 1:item['end']]).decode('utf-8')
        record = {k: item[k] for k in ('id', 'path', 'start', 'end', 'reason')}
        record['sha256'] = sha
        records.append(record)
        fence = '`' * max(3, 1 + max((len(s) for s in re.findall(r'`+', excerpt)), default=0))
        sections.append(json.dumps(record, ensure_ascii=False) + '\n\n' + fence + 'text\n'
                        + excerpt + ('' if excerpt.endswith('\n') else '\n') + fence + '\n')
    receipt = {'schema': 1, 'project': str(project), 'task': selection['task'], 'sources': records}
    context = (binding(receipt) + 'Task: ' + json.dumps(selection['task'], ensure_ascii=False)
               + '\n\nSelection is explicit, not a completeness, reading or approval decision. '
               'Reconcile current obligations and authority before acting.\n\n'
               + '\n'.join(sections)).encode('utf-8')
    if len(context) > max_bytes:
        raise ValueError(f'Context byte budget exceeded: {len(context)} > {max_bytes}; no truncation')
    receipt.update(context_bytes=len(context), limit_bytes=max_bytes, context_sha256=digest(context))
    # Validate everything before reserving a fresh directory; never replace old evidence.
    output.mkdir(parents=True, exist_ok=False)
    (output / 'context.md').write_bytes(context)
    (output / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n',
                                       encoding='utf-8')
    return receipt


def check(project, packet):
    project, packet = Path(project).resolve(), Path(packet)
    for name in ('receipt.json', 'context.md'):
        path = packet / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Packet file missing or symlinked')
    receipt = json.loads((packet / 'receipt.json').read_text(encoding='utf-8'))
    if (not isinstance(receipt, dict) or type(receipt.get('schema')) is not int
            or receipt['schema'] != 1 or not nonempty(receipt.get('project'))
            or not nonempty(receipt.get('task'))):
        raise ValueError('Invalid packet receipt')
    records = sources(receipt.get('sources'))
    for item in records:
        fingerprint(item.get('sha256'))
    if receipt['project'] != str(project):
        return {'status': 'FOREIGN_WORKSPACE'}
    context = (packet / 'context.md').read_bytes()
    if (not context.startswith(binding(receipt).encode('utf-8'))
            or digest(context) != fingerprint(receipt.get('context_sha256'))
            or type(receipt.get('context_bytes')) is not int or len(context) != receipt['context_bytes']
            or type(receipt.get('limit_bytes')) is not int or not 0 < len(context) <= receipt['limit_bytes']):
        raise ValueError('Context body/byte budget differs from the receipt')
    stale = []
    for item in records:
        try:
            current = digest(source_path(project, item['path']).read_bytes())
        except (OSError, ValueError):
            current = None
        if current != item['sha256']:
            stale.append(item['id'])
    return {'status': 'STALE' if stale else 'CURRENT', 'stale_ids': stale,
            'sources': len(records), 'context_bytes': len(context)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('build')
    create.add_argument('--project', required=True)
    create.add_argument('--selection', required=True)
    create.add_argument('--output', required=True)
    create.add_argument('--max-bytes', type=int, default=32768)
    inspect = commands.add_parser('check')
    inspect.add_argument('packet')
    inspect.add_argument('--project', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'build':
            selection = json.loads(Path(args.selection).read_text(encoding='utf-8'))
            receipt = build(args.project, selection, args.output, args.max_bytes)
            result = {'status': 'BUILT', 'sources': len(receipt['sources']),
                      'context_bytes': receipt['context_bytes']}
        else:
            result = check(args.project, args.packet)
        print(json.dumps(result, ensure_ascii=True))
        return {'STALE': 1, 'FOREIGN_WORKSPACE': 2}.get(result['status'], 0)
    except (OSError, ValueError, UnicodeError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
