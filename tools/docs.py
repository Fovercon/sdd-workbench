#!/usr/bin/env python3
"""Offline checks for shipped Markdown links and long reference navigation."""
import argparse
import html
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def prose(text):
    result, fence = [], None
    for line in text.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            token = match[1]
            if fence is None: fence = token
            elif token[0] == fence[0] and len(token) >= len(fence): fence = None
            continue
        if fence is None: result.append(line)
    return '\n'.join(result)


def slug(text):
    text = re.sub(r'<[^>]*>', '', html.unescape(text)).lower().strip()
    text = re.sub(r'[^\w\-\s]', '', text)
    return re.sub(r'\s', '-', text)


def headings(text):
    counts, result = {}, []
    for level, title in re.findall(r'^(#{1,6})\s+(.+?)\s*#*$', prose(text), re.M):
        key = slug(title); n = counts.get(key, 0); counts[key] = n + 1
        result.append((len(level), title, key + (f'-{n}' if n else '')))
    return result


def links(text):
    return re.findall(r'!?\[[^\]\n]*\]\((?:<([^>\n]+)>|([^\s)]+))(?:\s+"[^"\n]*")?\)', prose(text))


def check(files):
    errors, count = [], 0
    for name, data in files.items():
        if not name.endswith('.md'): continue
        text = data.decode('utf-8')
        for angled, bare in links(text):
            target = angled or bare; url = urlsplit(target)
            if url.scheme or url.netloc: continue
            count += 1
            path = unquote(url.path)
            parts = list(PurePosixPath(name).parent.parts) if path else list(PurePosixPath(name).parts)
            if path:
                if path.startswith('/'):
                    errors.append(f'{name}: absolute local link {target}'); continue
                for part in path.split('/'):
                    if part == '..':
                        if parts: parts.pop()
                        else: parts = ['__outside__']; break
                    elif part not in ('', '.'): parts.append(part)
            key = '/'.join(parts)
            if key not in files:
                if not url.fragment and any(p.startswith(key.rstrip('/')+'/') for p in files): continue
                errors.append(f'{name}: missing shipped target {target}'); continue
            if url.fragment and key.endswith('.md'):
                anchors = {h[2] for h in headings(files[key].decode('utf-8'))}
                if unquote(url.fragment) not in anchors:
                    errors.append(f'{name}: missing anchor {target}')
        if ('/references/' in name and 'template' not in PurePosixPath(name).name
                and len(text.splitlines()) > 100):
            toc = re.findall(r'\]\(#([^\s)]+)\)', '\n'.join(text.splitlines()[:30]))
            if len(toc) < 3: errors.append(f'{name}: long reference needs a contents list in its first 30 lines')
    return {'markdown_files': sum(p.endswith('.md') for p in files), 'local_links': count, 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('command', choices=['check']); args = parser.parse_args()
    import package
    result = check(package.bundle_files(ROOT))
    print(json.dumps(result, ensure_ascii=False, indent=2)); return bool(result['errors'])


if __name__ == '__main__': sys.exit(main())
