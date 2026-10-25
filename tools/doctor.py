#!/usr/bin/env python3
"""Read-only suite diagnostics. Never runs a client, installer, browser or repair."""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

from package import ROOT, check, load, tree_hashes
from install import Installation, target_directories


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def diagnose(selected=None, home=None, destination=None, state=None, source=ROOT, which=None):
    which = which or shutil.which
    plugin, suite, _files = check(Path(source))
    names = suite['skills']
    expected = {name: tree_hashes(Path(source)/'skills'/name) for name in names}
    registry = load(ROOT/'agent-targets.json')['targets']
    targets = target_directories(selected, home)
    if destination is not None and len(targets) != 1:
        raise ValueError('--dest requires exactly one target')
    if state is not None and destination is None:
        raise ValueError('--state requires an explicit --dest')
    shared = target_directories(['shared'], home)['shared']
    issues, roots, cache = [], {}, {}

    def issue(code, severity, path, message, action):
        value = {'code':code, 'severity':severity, 'path':str(path), 'message':message, 'next_action':action}
        if not any((v['code'],v['path']) == (code,str(path)) for v in issues): issues.append(value)

    def scan_skill(path, name):
        item = {'path':str(path), 'present':False, 'real_path':None, 'fingerprint':None,
                'matches_source':None, 'receipt_version':None}
        try:
            if path.is_symlink() and not path.exists():
                issue('BROKEN_SKILL_LINK','ERROR',path,'技能链接失效。','保留现有内容后，核对链接目标和安装方式；不自动删除。')
                return item, None
            if not path.exists(): return item, None
            real = path.resolve()
            item['present'] = True; item['real_path'] = str(real)
            if not real.is_dir(): raise ValueError('Skill is not a directory')
            key = os.path.normcase(str(real))
            md = real/'SKILL.md'
            if md.is_symlink(): raise ValueError('SKILL.md symlink is outside the supported directory-link layout')
            text = md.read_text(encoding='utf-8')
            front = text.split('---',2)
            if len(front) != 3 or front[0].strip(): raise ValueError('Missing frontmatter')
            match = re.search(r'^name:\s*[\'\"]?([a-z0-9-]+)[\'\"]?\s*$',front[1],re.M)
            if not match or match[1] != name or not re.search(r'^description:\s*\S',front[1],re.M):
                raise ValueError('Invalid skill name/description')
            if key not in cache:
                cache[key] = tree_hashes(real)
            hashes = cache[key]
            item['fingerprint'] = fingerprint(hashes)
            item['matches_source'] = hashes == expected[name] if name in expected else None
            return item, hashes
        except (OSError, ValueError, RuntimeError, UnicodeError) as error:
            issue('UNREADABLE_OR_INVALID_SKILL','ERROR',path,str(error),'保留用户修改，核对目录、权限和文件来源；不要直接覆盖。')
            return item, None

    def scan_root(path, custom_state=None):
        key = str(path)
        if key in roots: return roots[key]
        root = {'path':key, 'present':False, 'receipt_version':None, 'pending_recovery':False, 'skills':{}}
        roots[key] = root
        receipt = None
        try:
            root['present'] = path.is_dir()
            if path.exists() and not root['present']:
                issue('INVALID_SKILL_ROOT','ERROR',path,'搜索根不是目录。','核对安装目录，不自动替换现有文件。')
            installation = Installation(path, custom_state)
            root['state_path'] = str(installation.state)
            pending = installation.journal_path
            root['pending_recovery'] = pending.exists() or pending.is_symlink()
            if root['pending_recovery']:
                issue('PENDING_RECOVERY','ERROR',pending,'存在未恢复安装事务；不能继续覆盖安装。','先保留新编辑，再对这个 destination/state 手动运行安装器 recover。')
            if installation.receipt_path.is_symlink(): raise ValueError('Receipt cannot be a symlink')
            receipt = installation.receipt()
            if receipt:
                version = receipt.get('version')
                if not isinstance(version,str): raise ValueError('Invalid receipt version')
                root['receipt_version'] = version
                if version != plugin['version']:
                    issue('VERSION_DIFFERS_FROM_SOURCE','WARNING',path,'回执版本与本次检查源不同；不表示互联网最新版本。','核对目标版本、备份与当前源码身份，再选择是否更新。')
        except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError) as error:
            receipt = None
            issue('INVALID_OR_UNREADABLE_RECEIPT','ERROR',path,str(error),'保留回执和备份，核对正确 state/destination；不要强制接管。')
        recorded = receipt['skills'] if receipt else {}
        for name in sorted(set(names)|set(recorded)):
            item, hashes = scan_skill(path/name, name)
            root['skills'][name] = item
            if name in recorded:
                item['receipt_version'] = root['receipt_version']
                if hashes != recorded[name]:
                    issue('MANAGED_CONTENT_CHANGED','ERROR',path/name,'实际内容与安装器记录不符，可能是用户编辑、缺失或损坏。','先保存编辑并核对差异；诊断器不会强制覆盖或回退。')
                if name not in names:
                    issue('EXTRA_RECORDED_SKILL','WARNING',path/name,'回执还管理本次源目录未包含的技能。','核对版本迁移和备份；不要手动删除不明内容。')
            if item['present'] and hashes is not None and item['matches_source'] is False:
                issue('CONTENT_DIFFERS_FROM_SOURCE','WARNING',path/name,'与本次检查源的字节不同；不能据此单独判定损坏或版本。','核对回执、个人修改和准确版本；同版本不同内容不要直接覆盖。')
        return root

    agents = {}
    for agent, native in targets.items():
        entry = registry[agent]
        if destination is not None:
            search = [Path(destination).expanduser().absolute()]
        else:
            search = [native]
            if entry.get('reads_shared') and shared not in search: search.append(shared)
        scans = [scan_root(path, state if destination is not None else None) for path in search]
        missing, duplicates, differing, found = [], [], [], 0
        for name in names:
            copies = {}
            for scanned in scans:
                item = scanned['skills'].get(name,{})
                if item.get('present') and item.get('fingerprint'):
                    copies[os.path.normcase(item['real_path'])] = item
            if not copies: missing.append(name); continue
            found += 1
            if len(copies)>1:
                duplicates.append(name)
                if len({v['fingerprint'] for v in copies.values()})>1: differing.append(name)
        if missing:
            issue('NO_VISIBLE_DEFAULT_SKILLS','WARNING',search[0],
                  '未在所检查入口发现完整套件：'+', '.join(missing),
                  '核对宿主的真实搜索目录；插件缓存/自定义目录请用 --dest 显式检查。未发现不等于未安装。')
        if duplicates:
            issue('CONFLICTING_COPIES' if differing else 'DUPLICATE_PHYSICAL_COPIES',
                  'ERROR' if differing else 'WARNING',search[0],
                  '存在多个物理副本：'+', '.join(duplicates),
                  '核对宿主优先级并选择一种管理方式；先保留个人修改，不自动删除副本。')
        command = entry.get('command')
        executable = which(command) if command else None
        agents[agent] = {'checked_roots':[str(path) for path in search], 'found_skills':found,
                         'expected_skills':len(names), 'missing':missing, 'duplicates':duplicates,
                         'conflicting':differing, 'reads_shared_by_default':bool(entry.get('reads_shared')),
                         'client':{'command':command, 'path':executable,
                                   'status':'PATH_FOUND_NOT_EXECUTED' if executable else 'NOT_OBSERVED_ON_PATH',
                                   'discovery':'NOT_TESTED', 'execution':'NOT_TESTED'}}
    return {'schema':1, 'source':{'name':plugin['name'], 'declared_version':plugin['version'],
                                'skills_sha256':fingerprint(expected)},
            'scope':{'read_only':True, 'explicit_destination':destination is not None,
                     'source_version_is_not_tag_proof':True},
            'environment':{'python':sys.version.split()[0],
                           'node_path':which('node'), 'git_path':which('git'),
                           'browser_commands':{name:which(name) for name in ('chromium','google-chrome','chrome')},
                           'executables_ran':False},
            'agents':agents, 'roots':list(roots.values()), 'issues':issues,
            'summary':'NEEDS_ATTENTION' if issues else 'NO_FILE_ISSUES_OBSERVED',
            'unverified':['宿主实际搜索与插件缓存、自定义目录', '客户端/浏览器能否启动及工具权限',
                          '模型连通、任务行为、真人易用性与公司推广就绪']}


def render(report):
    lines = ['SDD Workbench 只读诊断', '检查源声明版本：'+report['source']['declared_version'],
             '检查源技能指纹：'+report['source']['skills_sha256'],
             '结果：'+('发现需要处理的观察项' if report['issues'] else '所检查文件未发现问题'),
             '注意：命令路径未执行；没有认证宿主发现、客户端可用性或模型任务行为。']
    for name, value in report['agents'].items():
        observed = '发现命令路径，尚未执行' if value['client']['path'] else 'PATH 未观察到命令，桌面客户端需另验'
        lines.append(f"{name}: {value['found_skills']}/{value['expected_skills']} 个可读技能；{observed}")
    for issue in report['issues']:
        lines.extend([f"[{issue['severity']}] {issue['code']} {issue['path']}",
                      '  '+issue['message'], '  下一步：'+issue['next_action']])
    return '\n'.join(lines)+'\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent',nargs='+',help='codex (default), hermes, zcode, deepseek, opencode, pi, shared, all')
    parser.add_argument('--home',type=Path,help='Isolated profile base; ignores target environment overrides')
    parser.add_argument('--dest',type=Path,help='One explicit skill root; disables other root scans')
    parser.add_argument('--state',type=Path,help='Custom Python receipt/backup root; requires --dest')
    parser.add_argument('--source',type=Path,default=ROOT,help='Exact comparison source; not an internet version lookup')
    parser.add_argument('--json',action='store_true',help='Machine-readable report')
    args = parser.parse_args(argv)
    try:
        report = diagnose(args.agent,args.home,args.dest,args.state,args.source)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError) as error:
        if args.json: print(json.dumps({'schema':1,'summary':'DIAGNOSTIC_FAILED','error':str(error)},ensure_ascii=False))
        else: print('无法完成只读诊断：'+str(error),file=sys.stderr)
        return 2
    print(json.dumps(report,ensure_ascii=False,indent=2) if args.json else render(report),end='\n' if args.json else '')
    return 1 if report['issues'] else 0


if __name__=='__main__':sys.exit(main())
