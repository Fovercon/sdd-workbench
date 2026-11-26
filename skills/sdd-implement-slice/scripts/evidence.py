#!/usr/bin/env python3
"""Record one authorized command or verify local Markdown evidence references."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from queue import Queue, Empty
import re
import signal
import stat
import subprocess
import sys
import threading
import time
from urllib.parse import quote, unquote, urlsplit


PREFIX = 'sdd-check-'
IDENTIFIER = re.compile(r'[a-z0-9][a-z0-9-]{0,79}\Z')
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$')
HEADING = re.compile(r'^ {0,3}#{1,6}[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$')
QUOTE = re.compile(r'^ {0,3}> ?')
LIST_ITEM = re.compile(r'^ {0,3}(?:[-+*]|[0-9]{1,9}[.)])(?:( +)|$)')
THEMATIC = re.compile(r'^ {0,3}(?:(?:- *){3,}|(?:\* *){3,}|(?:_ *){3,})$')
DESTINATION = r'(?:<([^>\n]+)>|((?:[^\s()]|\([^\s()]*\))+))'
TITLE = r'(?:"[^"\n]*"|\x27[^\x27\n]*\x27|\([^()\n]*\))'
LINK = re.compile(r'(?<![!\\])\[([^\]\n]*)\](?:\(' + DESTINATION +
                  r'(?:[ \t]+' + TITLE + r')?[ \t]*\)|\[([^\]\n]*)\])?')
LINK_START = re.compile(r'(?<![!\\])\[[^\]\n]*\]\(')
DEFINITION = re.compile(r'^ {0,3}\[([^\]\n]+)\]:[ \t]*' + DESTINATION +
                        r'(?:[ \t]+(?:"[^"]*"|\x27[^\x27]*\x27|\([^)]*\)))?[ \t]*$')
SHA = re.compile(r'[a-f0-9]{64}\Z')


def now():
    return datetime.now(timezone.utc).isoformat()


def json_line(value):
    return (json.dumps(value, ensure_ascii=True, separators=(',', ':')) + '\n').encode('ascii')


def safe_name(name):
    path = PurePosixPath(name)
    if (not name or not name.isprintable() or '\\' in name or ':' in name or PureWindowsPath(name).drive
            or path.is_absolute() or '..' in path.parts or not path.parts):
        raise ValueError(f'Expected a project-relative file: {name!r}')
    return path.as_posix()


def checked_stat(root, name):
    path = root
    for part in PurePosixPath(safe_name(name)).parts:
        path = path / part
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f'Symlink or reparse point in {name!r}')
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f'Not a regular project file: {name!r}')
    return info


@contextmanager
def opened(root, name, *, append=False):
    expected = checked_stat(root, name)
    if append and expected.st_nlink != 1:
        raise ValueError('Refusing a multiply linked log')
    flags = (os.O_RDWR | os.O_APPEND if append else os.O_RDONLY)
    flags |= getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    if os.open in os.supports_dir_fd and hasattr(os, 'O_NOFOLLOW'):
        # Keep directory handles while descending. A raced directory replacement
        # cannot redirect this open to a different ancestor.
        parents = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        directory = os.open(root, parents)
        try:
            parts = PurePosixPath(name).parts
            for part in parts[:-1]:
                child = os.open(part, parents, dir_fd=directory)
                os.close(directory)
                directory = child
            fd = os.open(parts[-1], flags, dir_fd=directory)
        finally:
            os.close(directory)
    else:
        fd = os.open(root / name, flags)
    with os.fdopen(fd, 'r+b' if append else 'rb') as stream:
        if not os.path.samestat(expected, os.fstat(fd)) or not os.path.samestat(expected, checked_stat(root, name)):
            raise ValueError(f'File replaced while opening: {name!r}')
        yield stream


def fingerprint(root, name):
    with opened(root, name) as stream:
        h = hashlib.sha256()
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
        return h.hexdigest()


def read_markdown(root, name):
    if PurePosixPath(name).suffix.lower() != '.md':
        raise ValueError('Expected a Markdown file')
    with opened(root, name) as stream:
        return stream.read().decode('utf-8')


@contextmanager
def locked(stream):
    stream.seek(0)
    if os.name == 'nt':
        import msvcrt
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as e:
            raise ValueError('Another recorder has locked this log') from e
    else:
        import fcntl
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            raise ValueError('Another recorder has locked this log') from e
    try:
        yield
    finally:
        if os.name == 'nt':
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def slug(title):
    return re.sub(r'\s', '-', re.sub(r'[^\w\s-]', '', re.sub(r'<[^>]*>', '', title.strip().lower())))


def continue_containers(line, containers):
    """Remove matching quote markers and list-item content indentation."""
    for depth, width in enumerate(containers):
        if width is None:
            quote = QUOTE.match(line)
            if not quote:
                return line, depth
            line = line[quote.end():]
        elif line.startswith(' ' * width) or not line.strip():
            line = line[width:]
        else:
            return line, depth
    return line, len(containers)


def inline_prose(line):
    """Hide code brackets without changing source offsets or label identity."""
    parts, cursor = [], 0
    for opening in re.finditer(r'`+', line):
        start = opening.start()
        if start < cursor:
            continue
        prefix = line[:start]
        if (len(prefix) - len(prefix.rstrip('\\'))) % 2:
            continue
        closing = re.search(r'(?<!`)' + re.escape(opening[0]) + r'(?!`)', line[opening.end():])
        if closing:
            end = opening.end() + closing.end()
            parts.extend((line[cursor:start], line[start:end].replace('[', '\x00').replace(']', '\x00')))
            cursor = end
    parts.append(line[cursor:])
    return ''.join(parts)


def markdown(text):
    """Visible ATX headings, inline links and fenced block bounds (zero-based lines)."""
    heads, references, blocks, definitions, unsupported = [], [], {}, {}, []
    opened_fence = None
    comment = False
    previous = None
    containers = []
    paragraph = False
    for i, line in enumerate(text.split('\n')):
        line, depth = continue_containers(line.rstrip('\r').expandtabs(4), containers)
        if depth < len(containers):
            # A fenced block in a list or quote ends when its container ends.
            del containers[depth:]
            opened_fence = None
        elif opened_fence:
            start, delimiter = opened_fence
            match = FENCE.match(line)
            if match and match[1][0] == delimiter[0] and len(match[1]) >= len(delimiter) and not match[2].strip():
                blocks[start] = i
                opened_fence = None
            continue
        while not comment:
            quote = QUOTE.match(line)
            item = LIST_ITEM.match(line)
            if quote:
                containers.append(None)
                line = line[quote.end():]
            elif item and not THEMATIC.fullmatch(line) and not (paragraph and line.strip() == '-'):
                padding = len(item[1] or '')
                width = item.end() - padding + (padding if 1 <= padding <= 4 else 1)
                containers.append(width)
                line = line[width:]
            else:
                break
            paragraph = False
        # Unlike ordinary paragraph continuations, indented code starts a
        # new block. Both its four columns and fences are container-relative.
        if line.startswith('    ') and not paragraph and not comment:
            continue
        if comment:
            if '-->' not in line:
                continue
            line = line.split('-->', 1)[1]
            comment = False
        line = re.sub(r'<!--.*?-->', '', line)
        if '<!--' in line:
            line = line.split('<!--', 1)[0]
            comment = True
        match = FENCE.match(line)
        if match and not (match[1][0] == '`' and '`' in match[2]):
            opened_fence = (i, match[1])
            paragraph = False
            continue
        heading = HEADING.match(line)
        paragraph = bool(line.strip()) and not heading and not THEMATIC.fullmatch(line)
        if heading:
            heads.append((i, slug(heading[1])))
        elif (previous and previous[0] == i - 1 and re.fullmatch(r' {0,3}(?:=+|-+)[ \t]*', line)):
            heads.append((previous[0], slug(previous[1])))
            paragraph = False
        previous = (i, line) if line.strip() and not heading and not line.lstrip().startswith(('#', '>', '-', '*')) else None
        definition = DEFINITION.fullmatch(line)
        if definition:
            paragraph = False
            label, angled, bare = definition.groups()
            definitions.setdefault(' '.join(label.casefold().split()), angled or bare)
            continue
        # Preserve offsets and code-formatted labels, while hiding bracket
        # syntax inside code examples. Removing code made [`id`](...) vanish.
        prose = inline_prose(line)
        matches = list(LINK.finditer(prose))
        for opening in LINK_START.finditer(prose):
            if not any(m.start() == opening.start() and m.end() >= opening.end()
                       and (m[2] or m[3]) for m in matches):
                unsupported.append({'target':line[opening.start():], 'history':'UNSUPPORTED',
                                    'error':f'Unsupported link syntax at line {i+1}; use a single-line Markdown link'})
        for match in matches:
            label, angled, bare, ref = match.groups()
            if angled or bare:
                references.append((True, angled or bare))
            else:
                start, end = match.span(4 if ref else 1)
                references.append((False, ' '.join(line[start:end].casefold().split())))
    links = [ref if direct else definitions[ref] for direct, ref in references if direct or ref in definitions]
    return heads, links, blocks, opened_fence, comment, unsupported


def heading_ids(heads):
    ids = {}
    for index, base in heads:
        anchor = base
        n = 0
        while anchor in ids:
            n += 1
            anchor = f'{base}-{n}'
        ids[anchor] = index
    return ids


def record_rows(text, index, blocks):
    lines = text.split('\n')
    fence = index + 1
    while fence < len(lines) and not lines[fence].strip():
        fence += 1
    if fence >= len(lines) or lines[fence].rstrip('\r') != '```jsonl':
        raise ValueError('Missing evidence JSONL fence')
    close = blocks.get(fence)
    # Markdown may be checked out with CRLF. The digest covers LF-framed
    # JSON; the original child bytes, including CR/LF, are escaped inside it.
    rows = [line.removesuffix('\r') for line in lines[fence+1:close]]
    if close is None and rows and not rows[-1]:
        rows.pop()
    return fence, close, rows


def parse_record(text, index, anchor, blocks):
    if text.split('\n')[index].rstrip('\r') != f'## {anchor}':
        raise ValueError('Not a generated evidence heading')
    _, close, lines = record_rows(text, index, blocks)
    if close is None:
        return {'history':'INCOMPLETE'}
    if not lines:
        raise ValueError('Empty evidence record')
    end = json.loads(lines[-1])
    if isinstance(end, dict) and end.get('type') == 'incomplete':
        return {'history':'INCOMPLETE'}
    records = [json.loads(line) for line in lines]
    start = records[0]
    if not isinstance(start, dict) or not isinstance(end, dict):
        raise ValueError('Malformed evidence start/end')
    ident, argv = start.get('id'), start.get('argv')
    if (start.get('type') != 'start' or type(start.get('schema')) is not int or start['schema'] != 1
            or not isinstance(ident, str) or not IDENTIFIER.fullmatch(ident) or anchor != PREFIX + ident
            or not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv)
            or not argv[0] or not isinstance(start.get('started_at'), str) or not start['started_at']
            or start.get('cwd') != '.' or end.get('type') != 'end' or type(end.get('command_exit')) is not int
            or not isinstance(end.get('ended_at'), str) or not end['ended_at']):
        raise ValueError('Malformed evidence start/end')
    before, after = start.get('sources'), end.get('sources')
    if (not isinstance(before, dict) or not before or not isinstance(after, dict)
            or before.keys() != after.keys()):
        raise ValueError('Invalid source set')
    for name, value in before.items():
        safe_name(name)
        if value is not None and (not isinstance(value, str) or not SHA.fullmatch(value)):
            raise ValueError('Invalid source fingerprint')
        if after[name] is not None and (not isinstance(after[name], str) or not SHA.fullmatch(after[name])):
            raise ValueError('Invalid closing fingerprint')
    for item in records[1:-1]:
        if not isinstance(item, dict) or item.get('type') not in ('stdout','stderr') or not isinstance(item.get('data'),str):
            raise ValueError('Malformed output record')
    h = hashlib.sha256()
    for line in lines[:-1]:
        h.update((line + '\n').encode('utf-8'))
    expected = end.pop('sha256', None)
    h.update(json_line(end))
    if expected != h.hexdigest():
        raise ValueError('Evidence digest mismatch')
    return {'history':'RECORDED', 'command_exit':end['command_exit'], 'before':before,
            'source_changes':[n for n in before if before[n] != after[n]]}


def relative_target(source, path):
    if '\\' in path or path.startswith('/') or PureWindowsPath(path).drive or not path.isprintable():
        raise ValueError('Not a local relative reference')
    parts = list(PurePosixPath(source).parent.parts)
    for part in PurePosixPath(path).parts:
        if part == '..':
            if not parts:
                raise ValueError('Reference escapes project')
            parts.pop()
        else:
            parts.append(part)
    return safe_name('/'.join(parts))


def verify(root, document):
    document = safe_name(document)
    docs = {}
    def doc(name):
        if name not in docs:
            text = read_markdown(root, name)
            docs[name] = text, markdown(text)
        return docs[name]
    results = list(doc(document)[1][5])
    for target in doc(document)[1][1]:
        row = {'target':target}
        try:
            url = urlsplit(target)
            if url.scheme in ('http','https','mailto'):
                continue
            if url.scheme or url.netloc or url.query:
                raise ValueError('Unsupported local reference')
            path = relative_target(document, unquote(url.path)) if url.path else document
            anchor = unquote(url.fragment)
            if not anchor:
                checked_stat(root, path)
                row['history'] = 'LINK_OK'
            else:
                text, (heads, _, blocks, _, _, _) = doc(path)
                possible = [(i, name) for i, name in heads if name == anchor]
                helper = anchor.startswith(PREFIX)
                resolved = heading_ids(heads).get(anchor)
                if resolved is None:
                    row['history'] = 'MISSING_ANCHOR'
                elif helper and (len(possible) > 1 or (possible and possible[0][0] != resolved)):
                    row['history'] = 'AMBIGUOUS'
                elif not helper:
                    row['history'] = 'LINK_OK'
                else:
                    row.update(parse_record(text, resolved, anchor, blocks))
                    if row['history'] == 'RECORDED':
                        row['sources'] = {}
                        for name, old in row.pop('before').items():
                            try:
                                sha = fingerprint(root, name)
                            except FileNotFoundError:
                                row['sources'][name] = 'MISSING'
                            except (ValueError, OSError) as exc:
                                # A currently unsafe or unreadable path does not erase the finished run.
                                row['sources'][name] = 'CHANGED' if isinstance(exc, ValueError) else 'UNAVAILABLE'
                                row.setdefault('source_errors', {})[name] = str(exc)
                            else:
                                row['sources'][name] = 'MATCH' if old == sha else 'CHANGED'
        except FileNotFoundError:
            row['history'] = 'MISSING_FILE'
        except (ValueError, OSError, UnicodeError) as exc:
            row.update(history='INVALID', error=str(exc))
        results.append(row)
    if not results:
        return {'status':'NO_LOCAL_REFERENCES', 'links':[]}, 2
    valid = all(x['history'] in ('LINK_OK','RECORDED') for x in results)
    return {'status':'VERIFIED' if valid else 'UNVERIFIED', 'links':results}, 0 if valid else 2


def verification_summary(data):
    links = []
    history_counts = {}
    for row in data['links']:
        history_counts[row['history']] = history_counts.get(row['history'], 0) + 1
        if row['history'] == 'LINK_OK':
            continue
        if (row['history'] == 'RECORDED' and not row['source_changes']
                and all(value == 'MATCH' for value in row['sources'].values())):
            row = {key:row[key] for key in ('target', 'history', 'command_exit')}
        links.append(row)
    return {'status':data['status'], 'links_checked':len(data['links']),
            'history_counts':history_counts,
            'omission_policy':{
                'LINK_OK':'whole rows',
                'RECORDED':{'fields':['source_changes','sources'],
                            'when':'source_changes=[] and all sources=MATCH'}},
            'links':links}


def snapshot(root, names):
    result = {}
    for name in names:
        try:
            result[name] = fingerprint(root, name)
        except FileNotFoundError:
            result[name] = None
    return result


@contextmanager
def orderly_termination():
    if os.name != 'posix':
        yield
        return
    def terminate(signum, frame):
        raise KeyboardInterrupt('Command cancellation (SIGTERM)')
    previous = signal.signal(signal.SIGTERM, terminate)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def capture(argv, root, timeout, output):
    events = Queue(maxsize=32)
    def read_pipe(kind, pipe):
        try:
            with pipe:
                while chunk := os.read(pipe.fileno(), 16384):
                    events.put((kind, chunk))
        except OSError as exc:
            events.put(('error', str(exc)))
        finally:
            events.put((kind, None))

    child = subprocess.Popen(argv, cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=False)
    deadline = time.monotonic() + timeout if timeout is not None else None
    try:
        for kind, pipe in [('stdout', child.stdout), ('stderr', child.stderr)]:
            threading.Thread(target=read_pipe, args=(kind, pipe), daemon=True).start()
        closed = 0
        expired = False
        while closed < 2 or child.poll() is None:
            if deadline is not None and time.monotonic() >= deadline:
                if expired:
                    break  # Descendants may still hold a pipe. Their output is incomplete.
                expired = True
                if child.poll() is None:
                    child.kill()
                deadline = time.monotonic() + 0.5
            try:
                kind, chunk = events.get(timeout=0.05)
            except Empty:
                continue
            if kind == 'error':
                raise OSError(chunk)
            if chunk is None:
                closed += 1
            else:
                output(kind, chunk)
        if expired:
            raise TimeoutError('Command or output capture exceeded timeout')
        return child.wait()
    finally:
        if child.poll() is None:
            child.kill()
        child.wait()


def record(root, args):
    log, origin = safe_name(args.log), safe_name(getattr(args, 'from'))
    if any(PurePosixPath(n).suffix.lower() != '.md' for n in (log, origin)):
        raise ValueError('Log and link origin must be Markdown files')
    # Link origins may be planned documents. Existing ancestors must still be local.
    try:
        checked_stat(root, origin)
    except FileNotFoundError:
        pass
    names = [safe_name(x) for x in args.source]
    if len(set(names)) != len(names) or log in names:
        raise ValueError('Sources must be distinct and separate from the log')
    if not IDENTIFIER.fullmatch(args.id):
        raise ValueError('Use a lowercase ASCII record ID (letters, digits, hyphens)')
    if not args.argv or args.argv[0] != '--' or len(args.argv) < 2:
        raise ValueError('Expected -- followed by the authorized command argv')
    if args.timeout is not None and (not math.isfinite(args.timeout) or args.timeout <= 0):
        raise ValueError('Timeout must be a positive finite number')
    argv = args.argv[1:]
    anchor = PREFIX + args.id
    path = os.path.relpath(root / log, (root / origin).parent).replace(os.sep,'/')
    link = f'[{anchor}]({quote(path, safe="/")}#{anchor})'
    with opened(root, log, append=True) as stream, locked(stream):
        stream.seek(0)
        observed = os.fstat(stream.fileno())
        def check_log():
            info = checked_stat(root, log)
            if info.st_nlink != 1 or not os.path.samestat(info, observed):
                raise ValueError('Log path replaced or linked during recording')
            return info

        def append(data):
            nonlocal observed
            try:
                info = check_log()
            except (OSError, ValueError) as exc:
                raise ValueError('Log path replaced or unavailable') from exc
            if (info.st_size, info.st_mtime_ns) != (observed.st_size, observed.st_mtime_ns):
                raise ValueError('Log modified by another writer during recording')
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            observed = os.fstat(stream.fileno())
            check_log()

        text = stream.read().decode('utf-8')
        heads, _, blocks, unfinished, comment, _ = markdown(text)
        if comment:
            raise ValueError('Unclosed Markdown comment')
        if anchor in heading_ids(heads) or any(key == anchor for _, key in heads):
            raise ValueError('Record ID already exists; use a new ID for a new observation')
        before = snapshot(root, names)
        if unfinished:
            if not heads or not heads[-1][1].startswith(PREFIX):
                raise ValueError('Unclosed Markdown fence')
            last_line, last_anchor = heads[-1]
            fence, _, rows = record_rows(text, last_line, blocks)
            start = json.loads(rows[0]) if rows else {}
            if (fence != unfinished[0] or not isinstance(start, dict) or start.get('schema') != 1
                    or start.get('type') != 'start' or last_anchor != PREFIX+str(start.get('id'))):
                raise ValueError('Unclosed Markdown fence outside a recognized recorder entry')
            append(b'\n' + json_line({'type':'incomplete','reason':'Unsealed prior invocation; exit unknown',
                                      'observed_at':now()}) + b'```\n')
        start = json_line({'type':'start','schema':1,'id':args.id,'started_at':now(),'cwd':'.',
                           'argv':argv,'sources':before})
        append(f'\n\n## {anchor}\n\n```jsonl\n'.encode('ascii') + start)
        h = hashlib.sha256(start)
        tails = {'stdout': b'', 'stderr': b''}
        def output(kind, chunk):
            data = json_line({'type': kind, 'data': chunk.decode('utf-8', 'surrogateescape')})
            append(data)
            h.update(data)
            tails[kind] = (tails[kind] + chunk[-4096:])[-4096:]

        def output_tails():
            return {kind + '_tail': chunk.decode('utf-8', 'surrogateescape') for kind, chunk in tails.items()}
        try:
            with orderly_termination():
                code = capture(argv, root, args.timeout, output)
            after = snapshot(root, names)
        except (OSError, ValueError, KeyboardInterrupt) as exc:
            reason = str(exc) or type(exc).__name__
            append(json_line({'type':'incomplete','observed_at':now(),'reason':reason}) + b'```\n')
            return {'status':'INCOMPLETE','link':link,'error':reason, **output_tails()}, 2
        end = {'type':'end','ended_at':now(),'command_exit':code,'sources':after}
        h.update(json_line(end))
        end['sha256'] = h.hexdigest()
        append(json_line(end) + b'```\n')
        changes = [name for name in names if before[name] != after[name]]
        return {'status':'RECORDED','command_exit':code,'source_changes':changes,'link':link, **output_tails()}, 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    writer = commands.add_parser('record')
    reader = commands.add_parser('verify')
    for tool in (reader, writer):
        tool.add_argument('--root', required=True)
    for field in ('log','id','from'):
        writer.add_argument('--'+field, required=True)
    writer.add_argument('--source', action='append', required=True)
    writer.add_argument('--timeout', type=float)
    writer.add_argument('argv', nargs=argparse.REMAINDER)
    reader.add_argument('--document', required=True)
    reader.add_argument('--summary', action='store_true',
                        help='Compact normal links and matching sources; retain record exits and diagnostics')
    args = parser.parse_args()
    try:
        root = Path(args.root).resolve(strict=True)
        if args.action == 'record':
            data, status = record(root, args)
        else:
            data, status = verify(root, args.document)
            if args.summary:
                data = verification_summary(data)
    except (OSError, ValueError, UnicodeError) as exc:
        data, status = {'status':'ERROR','error':str(exc)}, 2
    print(json.dumps(data, ensure_ascii=True))
    return status


if __name__ == '__main__':
    sys.exit(main())
