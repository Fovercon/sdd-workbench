"""Oracle solution for date-recurrence (evaluator-owned)."""
import re
from datetime import date, timedelta

_DAY_CODES = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6}


def parse_spec(text):
    spec = text.strip()
    if spec == 'daily':
        return {'kind': 'daily'}
    if spec.startswith('weekly:'):
        codes = spec[len('weekly:'):].strip()
        if not codes:
            raise ValueError('empty weekly spec')
        days = []
        for code in codes.split(','):
            day = _DAY_CODES.get(code.strip().upper())
            if day is None:
                raise ValueError(f'unknown weekday: {code}')
            if day not in days:
                days.append(day)
        return {'kind': 'weekly', 'days': days}
    match = re.fullmatch(r'every:(\d+)d', spec)
    if match:
        step = int(match.group(1))
        if step <= 0:
            raise ValueError('step must be positive')
        return {'kind': 'interval', 'step': step}
    raise ValueError(f'unrecognized spec: {text}')


def expand(spec_text, start, end, include_start=True, include_end=False):
    spec = parse_spec(spec_text)
    if start > end:
        return []
    out = []
    if spec['kind'] == 'weekly':
        wanted = set(spec['days'])
        current = start
        while current <= end:
            if current.weekday() in wanted:
                out.append(current)
            current += timedelta(days=1)
    else:
        step = 1 if spec['kind'] == 'daily' else spec['step']
        current = start
        while current <= end:
            out.append(current)
            current += timedelta(days=step)
    if not include_start and out and out[0] == start:
        out = out[1:]
    if not include_end and out and out[-1] == end:
        out = out[:-1]
    return out
