"""Oracle solution for checklist-import (evaluator-owned)."""
import json
import re

_ITEM_RE = re.compile(r'^\s*-\s\[( |x|X)\]\s?(.*)$')


def parse(md_text):
    items, seen, invalid = [], set(), 0
    for line in md_text.splitlines():
        stripped = line.strip()
        match = _ITEM_RE.match(line)
        if match:
            done = match.group(1) in 'xX'
            text = match.group(2).strip()
            if text in seen:
                continue
            seen.add(text)
            items.append({'text': text, 'done': done})
        elif stripped.startswith('- ['):
            invalid += 1
    return {'items': items, 'invalid_lines': invalid}


def to_json(parsed):
    return json.dumps(parsed, ensure_ascii=False, indent=2)


def from_json(s):
    return json.loads(s)


def stats(parsed):
    done = sum(1 for item in parsed['items'] if item['done'])
    return {'total': len(parsed['items']), 'done': done,
            'open': len(parsed['items']) - done}
