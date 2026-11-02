import json
from pathlib import Path

from formatting import label


def _rows(path, origin, meanings, strip):
    rows = json.loads(Path(path).read_text(encoding='utf-8'))
    result = []
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'id', 'text', 'state'}
                or not all(isinstance(value, str) for value in row.values())
                or row['state'] not in meanings):
            raise ValueError('Invalid legacy record')
        result.append({'id': row['id'], 'label': label(origin, row['id']),
                       'text': row['text'].strip() if strip else row['text'],
                       'state': row['state'], 'meaning': meanings[row['state']]})
    return result


def web_rows(path):
    return _rows(path, 'web', {'pending': 'pending', 'done': 'converted'}, False)


def batch_rows(path):
    return _rows(path, 'batch', {'pending': 'pending', 'done': 'delivered'}, True)
