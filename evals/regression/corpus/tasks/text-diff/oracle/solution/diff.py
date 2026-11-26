"""Oracle solution for text-diff (evaluator-owned)."""
import difflib
import sys


def tokenize(text):
    return text.split()


def word_diff(old, new, ignore_case=False):
    a, b = tokenize(old), tokenize(new)
    if ignore_case:
        a_cmp = [t.lower() for t in a]
        b_cmp = [t.lower() for t in b]
    else:
        a_cmp, b_cmp = a, b
    ops = []
    matcher = difflib.SequenceMatcher(a=a_cmp, b=b_cmp, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            ops.extend(('=', tok) for tok in a[i1:i2])
            continue
        ops.extend(('-', tok) for tok in a[i1:i2])
        ops.extend(('+', tok) for tok in b[j1:j2])
    return ops


def render(ops):
    return '\n'.join(f"{' ' if op == '=' else op} {tok}" for op, tok in ops)


def main(argv):
    ignore_case = False
    args = list(argv[1:])
    if '--ignore-case' in args:
        ignore_case = True
        args.remove('--ignore-case')
    if len(args) != 2:
        print('usage: diff.py [--ignore-case] OLD NEW', file=sys.stderr)
        return 2
    try:
        with open(args[0], encoding='utf-8') as fh:
            old = fh.read()
        with open(args[1], encoding='utf-8') as fh:
            new = fh.read()
    except OSError:
        print('ERROR unreadable', file=sys.stderr)
        return 2
    ops = word_diff(old, new, ignore_case=ignore_case)
    text = render(ops)
    sys.stdout.write(text + '\n' if text else '')
    return 0 if all(op == '=' for op, _ in ops) else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
