#!/usr/bin/env python3
"""Freeze/evaluate a synthetic excerpt task; accepts valid manual baseline packets."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SKILL = 'skills/sdd-workflow-router/'
PROMPT = ('请使用 ../runtime/sdd-workflow-router/SKILL.md，为当前切片准备同一工作区新会话需要的原文材料。'
          'selection.json 已明确选择任务、来源范围和共享约束，请保持原文而不做摘要，'
          '只新建 packet/context.md 和必要的来源回执。正文不超过4096个UTF-8字节，回执元数据另计；'
          '记录来源文件、范围和完整文件SHA256，排除无关历史。不能因生成了材料就宣称已批准或可以实施。'
          '不修改任何输入或运行时，不实现、不提交、不推送、不安装；最后说明实际完成项与边界。')
INPUTS = {
    'AGENTS.md': ('Synthetic; no implementation or approval authority.\n'
                  'Source files must remain unchanged.\n'
                  'Only packet/ is an authorized output.\n'),
    'spec.md': ('# Synthetic retry contract\n'
                'FR-007: Retry selected failed units only.\n'
                'AC-007.1: Successful output bytes and modification times stay unchanged.\n'
                + '\n'.join('UNRELATED_HISTORY_Z9 ' + 'old unrelated note ' * 6 for _ in range(250)) + '\n'),
    'shared.md': 'Shared invariant: all task writes require the same task lock.\n',
    'CURRENT-CARD.md': 'Current slice S2: expose the existing retry action; do not change its semantics.\n',
}
RANGES = {'AGENTS.md': (1, 3), 'spec.md': (2, 3), 'shared.md': (1, 1), 'CURRENT-CARD.md': (1, 1)}


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()
            and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.pyo')}


def prepare(output, ref=None):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Output exists; preserve previous trials')
    revision = subprocess.check_output(['git', 'rev-parse', ref + '^{commit}'], cwd=ROOT,
                                       text=True).strip() if ref else 'WORKTREE'
    runtime = output / 'runtime/sdd-workflow-router'
    runtime.mkdir(parents=True)
    if ref:
        names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision, SKILL],
                                        cwd=ROOT, text=True).splitlines()
        for name in names:
            rel = name[len(SKILL):]
            if rel != 'SKILL.md' and not rel.startswith(('references/', 'scripts/', 'agents/')):
                continue
            target = runtime / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(subprocess.check_output(['git', 'show', revision + ':' + name], cwd=ROOT))
    else:
        shutil.copytree(ROOT / SKILL, runtime, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('tests', 'evals', '__pycache__', '*.pyc', '*.pyo'))
    project = output / 'project'
    project.mkdir()
    selected = []
    for name, text in INPUTS.items():
        (project / name).write_text(text, encoding='utf-8')
        selected.append({'id': name, 'path': name, 'start': RANGES[name][0], 'end': RANGES[name][1],
                         'reason': '当前义务' if name != 'shared.md' else '共享约束',
                         'expected_sha256': hashlib.sha256(text.encode()).hexdigest()})
    (project / 'selection.json').write_text(json.dumps(
        {'schema': 1, 'task': '准备 S2 上下文；无实施或批准授权', 'sources': selected},
        ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'prompt.txt').write_text(PROMPT, encoding='utf-8')
    (output / 'input-receipt.json').write_text(json.dumps(
        {'project': hashes(project), 'runtime': hashes(output / 'runtime')}, indent=2), encoding='utf-8')
    (output / 'variant.json').write_text(json.dumps({'source': revision,
        'prompt_sha256': hashlib.sha256(PROMPT.encode()).hexdigest()}, indent=2), encoding='utf-8')
    return str(output)


def evaluate(run):
    run = Path(run).resolve()
    before = json.loads((run / 'input-receipt.json').read_text(encoding='utf-8'))
    project, errors = run / 'project', []
    after = hashes(project)
    unchanged = all(after.get(p) == sha for p, sha in before['project'].items())
    if not unchanged:
        errors.append('Protected input changed')
    runtime_ok = hashes(run / 'runtime') == before['runtime']
    if not runtime_ok:
        errors.append('Runtime changed')
    if any(p not in before['project'] and not p.startswith('packet/') for p in after):
        errors.append('Unexpected output outside packet')
    context_path = project / 'packet/context.md'
    body = context_path.read_bytes() if context_path.is_file() else b''
    text = body.decode('utf-8')
    if not body or len(body) > 4096:
        errors.append('Missing context or byte budget exceeded')
    obligations = [('Source files must remain unchanged.', 'Missing preservation obligation'),
                   ('FR-007: Retry selected failed units only.', 'Missing current behavior'),
                   ('AC-007.1: Successful output bytes and modification times stay unchanged.', 'Missing preservation behavior'),
                   ('Shared invariant: all task writes require the same task lock.', 'Missing shared obligation'),
                   ('Current slice S2: expose the existing retry action; do not change its semantics.', 'Missing current card')]
    errors += [message for clause, message in obligations if clause not in text]
    if 'UNRELATED_HISTORY_Z9' in text:
        errors.append('Unrelated history included')
    metadata = '\n'.join(p.read_text(encoding='utf-8') for p in (project / 'packet').rglob('*')
                         if p.is_file()) if (project / 'packet').is_dir() else ''
    for name in INPUTS:
        if name not in metadata or before['project'][name] not in metadata:
            errors.append('Missing source identity: ' + name)
    result = {'automated_guards': 'FAIL' if errors else 'PASS', 'errors': errors,
              'protected_sources_unchanged': unchanged, 'runtime_unchanged': runtime_ok,
              'context_bytes': len(body), 'manual_review_required':
              'Read ranges, meaning, all tool calls and final authority claims; no OS sandbox or cost conclusion.'}
    (run / 'packet-evaluation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('prepare')
    create.add_argument('--output', required=True)
    create.add_argument('--ref')
    inspect = commands.add_parser('evaluate')
    inspect.add_argument('run')
    args = parser.parse_args()
    if args.command == 'prepare':
        print(prepare(args.output, args.ref))
    else:
        result = evaluate(args.run)
        print(json.dumps(result, ensure_ascii=True))
        raise SystemExit(result['automated_guards'] != 'PASS')
