"""Oracle solution for csv-report (evaluator-owned; never shown to actors)."""
import sys


def parse_line(line):
    if line is None:
        return None
    parts = line.split(',')
    if len(parts) != 4:
        return None
    date, region, product, amount = (p.strip() for p in parts)
    try:
        return date, region, product, float(amount)
    except ValueError:
        return None


def summarize(rows):
    totals = {}
    for row in rows:
        totals[row[1]] = totals.get(row[1], 0.0) + row[3]
    return sorted(totals.items())


def main(argv):
    if len(argv) != 2:
        print('usage: report.py INPUT.csv', file=sys.stderr)
        return 2
    try:
        with open(argv[1], encoding='utf-8-sig') as fh:
            lines = fh.read().splitlines()
    except OSError:
        print('ERROR missing file', file=sys.stderr)
        return 2
    rows, skipped = [], 0
    for line in lines:
        if not line.strip():
            skipped += 1
            continue
        parsed = parse_line(line)
        if parsed is None:
            skipped += 1
        else:
            rows.append(parsed)
    if skipped:
        print(f'SKIPPED\t{skipped}', file=sys.stderr)
    for region, total in summarize(rows):
        print(f'{region}\t{total:.2f}')
    print(f'REGIONS\t{len(summarize(rows))}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
