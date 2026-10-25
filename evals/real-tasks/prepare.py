#!/usr/bin/env python3
"""Freeze public repository tasks outside the checkout, without installing skills."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SUITE = '7c79aad193269b1daae4dfe08f102cb815955d78'
CASES = {
    'encoding': ('2093cc9ca463862a57577a235152196ea5d9cb03',
        '请修复这份真实仓库中已复现的跨平台问题：Windows 非 UTF-8 默认环境运行现有 Python 回归时，doctor 的 JSON 模式输出中文导致 UnicodeEncodeError；文档链接回归读取 UTF-8 文档时出现 UnicodeDecodeError。请实际定位和修复同类 CLI I/O 问题，补相应回归，保留原 JSON 字段与 Unicode 数据含义、原有有效回执格式和用户文件。不要仅给运行命令增加全局 UTF-8 环境变量来规避默认环境。常规技术选择和本地修复/验证已授权，不提交、不推送、不发布。实际过程、失败与验证写在 trace.md，给出可核对的本地交付。'),
    'adapter': (SUITE,
        '请对真实仓库的 adapters/deepseek.mjs 及 tests/test_deepseek_adapter.mjs 做只读工程审查。重点核对同一 skills 树的正文/资源、候选身份与目录边界、取消和错误传播。可以运行本机 Node 检查并在临时子目录写独立探针；指出实际可复现问题和测试盲区，没有证据不要强行找 bug。不要修改原源码/测试或补产品需求，不提交、不推送、不发布。实际过程、命令、结果和限制写在 trace.md。'),
}
RULES = '''
# Isolated real-task trial scope
This is a derived snapshot of a real public repository, not a company project.
Use only this project, its supplied sibling runtime-skills, and temporary children.
Use the supplied SDD Workbench runtime as appropriate and actually perform REQUEST.md.
No network from project tools, package installation, live skill changes, external
messages, Git commit/push/tag/release. Client model calls are outside project tool scope.
Preserve original source except exact authorized repair surfaces, and preserve
user-note.txt. Record actual steps/results/limits in trace.md; no invented human
approval, independent review, or passing command. Use Python -B for local checks.
Do not inspect sibling trial roots, evaluator receipts or held-out probes.
For the readonly adapter task, only trace.md and temporary-probes/ may be added;
all original files remain unchanged. Questions about missing business decisions
belong in questions.md; do not contact the real user.
'''


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()
            and '.git' not in p.parts and '__pycache__' not in p.parts}


def extract(ref, output, paths=()):
    with tempfile.TemporaryFile() as stream:
        subprocess.run(['git', 'archive', ref, *paths], cwd=ROOT, stdout=stream, check=True)
        stream.seek(0)
        with tarfile.open(fileobj=stream) as archive:
            for member in archive.getmembers():
                name = PurePosixPath(member.name)
                if name.is_absolute() or '..' in name.parts or not (member.isdir() or member.isfile()):
                    raise ValueError('Only regular, relative source files are permitted')
            # Validated regular entries only; compatible with Python 3.10+.
            archive.extractall(output)


def prepare(case, output, host, suite=SUITE):
    output = Path(output).resolve()
    if output.is_relative_to(ROOT):
        raise ValueError('Trial output must be outside the source checkout')
    output.mkdir(parents=True, exist_ok=False)
    project = output / 'project'
    project.mkdir()
    source, prompt = CASES[case]
    extract(source, project)
    original = hashes(project)
    with (project / 'AGENTS.md').open('a', encoding='utf-8') as stream:
        stream.write(RULES)
    (project / 'REQUEST.md').write_text(prompt + '\n', encoding='utf-8')
    (project / 'user-note.txt').write_text(
        'Synthetic user note used to check preservation.\n', encoding='utf-8')
    runtime = output / 'runtime-skills'
    runtime.mkdir()
    with tempfile.TemporaryDirectory() as temp:
        tree = Path(temp)
        extract(suite, tree, ('skills',))
        for source in (tree / 'skills').iterdir():
            if not (source / 'SKILL.md').is_file():
                continue
            for path in source.rglob('*'):
                relative = path.relative_to(source)
                if path.is_file() and '__pycache__' not in relative.parts and (
                        relative.as_posix() == 'SKILL.md'
                        or relative.parts[0] in ('references', 'scripts', 'assets', 'agents')):
                    target = runtime / source.name / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(path.read_bytes())
    subprocess.run(['git', 'init', '--quiet'], cwd=project, check=True)
    subprocess.run(['git', 'add', '--all'], cwd=project, check=True)
    subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'user.name=Pilot fixture',
                    '-c', 'user.email=pilot@example.invalid', 'commit', '--quiet',
                    '-m', 'Freeze derived public real-task input'], cwd=project, check=True)
    receipt = {
        'case': case, 'host': host, 'source_kind': 'REAL_PUBLIC_REPOSITORY',
        'repository': 'Fovercon/sdd-workbench', 'upstream_commit': CASES[case][0],
        'suite_commit': suite, 'original_tracked_inputs': original,
        'inputs': hashes(project), 'runtime_skills': hashes(runtime),
        'fixture_git_head': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=project, text=True).strip(),
        'source_adaptations': ['appended isolated execution rules', 'added task request',
                               'added synthetic preservation note'],
        'company_representativeness': 'NOT_ESTABLISHED',
    }
    (output / 'receipt.json').write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES, required=True)
    parser.add_argument('--host', required=True, help='Evidence label, not an executable')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--suite-ref', default=SUITE, help='Frozen runtime Git revision')
    args = parser.parse_args()
    print(prepare(args.case, args.output, args.host, args.suite_ref))
