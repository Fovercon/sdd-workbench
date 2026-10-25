#!/usr/bin/env python3
"""Read-only evidence snapshot. Hash agreement never grants semantic approval."""
import argparse
import copy
import hashlib
import html
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote
from . import lifecycle, decisions, workstream

STATES = {'SATISFIED': '已有对应证据', 'GAP': '尚有缺口', 'STALE': '来源已变化',
          'UNKNOWN': '尚不能确认', 'PENDING_HUMAN': '待确认/审批', 'CONFLICT': '来源冲突',
          'BLOCKED_EXTERNAL': '外部条件未就绪', 'NOT_APPLICABLE': '本次不适用'}
VIEWS = {'progress': '工作进展', 'diagram': '项目怎样工作', 'design': '设计视图', 'capability': '功能与分工', 'structure': '当前结构', 'impact': '变更与证据'}
KINDS = {'approved_contract': '已批准合同', 'design': '设计安排', 'code_observation': '代码观察',
         'runtime_evidence': '运行证据', 'assessment': '分析判断'}


def source_path(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError('Source paths must be relative to the project root')
    result = (root / value).resolve()
    if not result.is_relative_to(root):
        raise ValueError('Source path escapes the project root')
    return result


def inspect(root, snapshot):
    root = Path(root).resolve()
    result, ids = [], set()
    for original in snapshot['items']:
        item = copy.deepcopy(original)
        if not isinstance(item['id'], str) or not item['id'] or item['id'] in ids:
            raise ValueError('Item IDs must be unique nonempty strings')
        ids.add(item['id'])
        if item['state'] not in STATES or item['view'] not in VIEWS or item['kind'] not in KINDS:
            raise ValueError('Unknown state, view or evidence kind')
        if item['view'] == 'diagram' or 'artifact' in item:
            artifact = source_path(root, item.get('artifact'))
            refs = {source_path(root, ref['path']) for ref in item.get('sources', [])}
            if (item['view'] != 'diagram' or artifact.suffix.lower() != '.html'
                    or artifact not in refs or not refs - {artifact}):
                raise ValueError('A diagram needs an HTML artifact and sources citing both it and its basis')
        if item['view'] == 'design':
            if not isinstance(item.get('mermaid'), str) or not item['mermaid'].strip():
                raise ValueError('A design view needs the nonempty mermaid source copied from its contract')
            if any(key in item for key in ('artifact', 'from', 'to', 'file', 'implementation_ids')):
                raise ValueError('A design view is standalone; artifacts and structure links belong elsewhere')
            if not item.get('sources'):
                raise ValueError('A design view must cite the contract section carrying its mermaid source')
            if 'technical_mermaid' in item and (not isinstance(item['technical_mermaid'], str) or not item['technical_mermaid'].strip()):
                raise ValueError('Technical diagram source must be nonempty text')
        elif 'technical_mermaid' in item:
            raise ValueError('technical_mermaid belongs to a design view')
        item['freshness'] = 'CURRENT' if item.get('sources') else 'UNKNOWN'
        for ref in item.get('sources', []):
            path = source_path(root, ref['path'])
            line = ref.get('line', 1)
            if type(line) is not int or line < 1:
                raise ValueError('Source line must be a positive integer')
            ref['href'] = path.as_uri()
            digest = ref.get('sha256', '')
            try:
                current = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                current = None
            if current is None or not re.fullmatch('[0-9a-f]{64}', digest):
                ref['freshness'] = 'UNKNOWN'
                item['freshness'] = 'UNKNOWN'
            elif current != digest:
                ref['freshness'] = 'STALE'
                if item['freshness'] != 'UNKNOWN':
                    item['freshness'] = 'STALE'
            else:
                ref['freshness'] = 'CURRENT'
        item['effective_state'] = item['state'] if item['freshness'] == 'CURRENT' else item['freshness']
        result.append(item)
    nodes = {item['id']: item for item in result}
    for item in result:
        related = item.get('related_ids')
        if related is None:
            continue
        # Pairing connects a contract-bound design view with a delivered diagram
        # of the same subject; it is navigation, never shared evidence.
        if (item['view'] not in ('design', 'diagram') or not isinstance(related, list)
                or any(not isinstance(value, str) or not value for value in related)):
            raise ValueError('related_ids is valid only on design/diagram items as a list of IDs')
        if item['id'] in related:
            raise ValueError('An item cannot be paired with itself')
        for key in related:
            if key not in nodes:
                raise ValueError('related_ids must identify existing items')
    file_paths = set()
    for item in result:
        if 'file' not in item:
            continue
        path = source_path(root, item['file'])
        if item['view'] != 'structure' or 'from' in item or 'to' in item:
            raise ValueError('A file must identify a structure node')
        if item['file'] not in [ref['path'] for ref in item.get('sources', [])]:
            raise ValueError('A file node must cite that file as a source')
        if path in file_paths:
            raise ValueError('One file cannot be represented as multiple structure nodes')
        if path.is_dir():
            raise ValueError('File nodes must cite files, not directories')
        file_paths.add(path)
    for item in result:
        if 'implementation_ids' not in item:
            continue
        if item['view'] != 'capability':
            raise ValueError('Only capabilities have implementation_ids')
        refs = {ref['path'] for ref in item.get('sources', [])}
        for key in item['implementation_ids']:
            owner = nodes.get(key)
            if owner is None or 'file' not in owner:
                raise ValueError('Implementation IDs must identify file nodes')
            if owner['file'] not in refs:
                raise ValueError('A capability must cite its implementation file')
    for item in result:
        if 'from' not in item and 'to' not in item:
            continue
        if item['view'] != 'structure' or 'from' not in item or 'to' not in item:
            raise ValueError('A structure relationship needs both endpoints')
        endpoints = [nodes.get(item[key]) for key in ('from', 'to')]
        if any(node is None or node['view'] != 'structure' or 'from' in node or 'to' in node
               for node in endpoints):
            raise ValueError('Relationship endpoints must be existing structure nodes')
        freshness = [item['freshness']] + [node['freshness'] for node in endpoints]
        item['freshness'] = ('UNKNOWN' if 'UNKNOWN' in freshness else
                             'STALE' if 'STALE' in freshness else 'CURRENT')
        item['effective_state'] = item['state'] if item['freshness'] == 'CURRENT' else item['freshness']
    from . import stage_details
    stage_details.inspect(root, result)
    workstream.propagate(result)
    return result


def markdown_data(value):
    # Keep source content inside its assigned field, including in permissive
    # Markdown renderers. Newlines must not create headings or status rows.
    value = html.escape(str(value), quote=True).replace('\r\n', '\n').replace('\r', '\n')
    value = value.replace('\n', ' ↵ ')
    return re.sub(r'([\\`*_{}\[\]()#+.!|>-])', r'\\\1', value)


def markdown(snapshot, items):
    by_id = {i['id']: i for i in items}
    lines = [f'# {markdown_data(snapshot["title"])}', '',
             f'观察范围：{markdown_data(snapshot["scope"])}',
             f'原观察时间：{markdown_data(snapshot["captured_at"])}',
             f'本次来源核验：{markdown_data(snapshot["checked_at"])}',
             '离线快照；来源一致不代表批准或验收。', '']
    if 'lifecycle' in snapshot:
        lines.extend([f'当前阶段：{snapshot["lifecycle"]["current_stage"]}', '',
                      '## SDD 阶段', ''])
        for stage in lifecycle.stage_status(snapshot, items):
            lines.append(f'- {stage["name"]} · {stage["subtitle"]}：{stage["text"]}')
        lines.append('')
    for view, heading in VIEWS.items():
        lines.extend([f'## {heading}', ''])
        for item in (i for i in items if i['view'] == view):
            lines.extend([f'### {markdown_data(item["label"])}',
                f'- 状态：{STATES[item["effective_state"]]}；原判断：{STATES[item["state"]]}；来源：{item["freshness"]}',
                f'- 类别：{KINDS[item["kind"]]}',
                *([f'- 所属阶段：{item["stage"]} · {lifecycle.STAGES[item["stage"]]}'] if 'stage' in item else []),
                f'- 说明：{markdown_data(item.get("note", ""))}',
                f'- 下一步：{markdown_data(item.get("next", ""))}'])
            if 'from' in item:
                lines.append(f'- 关系：{markdown_data(by_id[item["from"]]["label"])} → {markdown_data(by_id[item["to"]]["label"])}')
            if 'file' in item:
                lines.append(f'- 实际文件：{markdown_data(item["file"])}')
            if 'artifact' in item:
                lines.append(f'- 独立交互图：{markdown_data(item["artifact"])}')
            if 'mermaid' in item:
                # Verbatim indented code block: readable, and immune to Markdown
                # injection because every nonblank line stays a code line.
                lines.append('- Mermaid 源码（摘自所引合同）：')
                lines.extend(('    ' + ln if ln.strip() else '') for ln in item['mermaid'].splitlines())
            if 'technical_mermaid' in item:
                lines.append('- 技术细节图源（保留原始标识）：')
                lines.extend(('    ' + ln if ln.strip() else '') for ln in item['technical_mermaid'].splitlines())
            if 'decision' in item:
                q = item['decision']
                lines.extend([f'- 待确认问题：{markdown_data(q["prompt"])}',
                              f'- 决策 ID：{markdown_data(q["id"])}；答复人：{markdown_data(q["owner"])}',
                              f'- 适用范围：{markdown_data(q["scope"])}'])
                for option in q.get('options', []):
                    lines.append(f'  - {markdown_data(option["id"])}：{markdown_data(option["label"])} — {markdown_data(option["description"])}')
                lines.append('- 在项目对话中明确答复；核对当前版本并记录后，生成下一版看板。')
            if 'decision_ref' in item:
                lines.append(f'- 共用决策入口：{markdown_data(item["decision_ref"])}')
            for rid in item.get('related_ids', []):
                if rid in by_id:
                    lines.append(f'- 配对视图：{markdown_data(by_id[rid]["label"])}（{by_id[rid]["id"]}）')
            for owner in item.get('implementation_ids', []):
                lines.append(f'- 实现位置：{markdown_data(by_id[owner]["file"])}')
            if 'work' in item:
                work = item['work']
                lines.append(f'- 主线记录类型：{work["type"]}')
                for field in ('status', 'result'):
                    if field in work:
                        lines.append(f'- {field}（原记录，非批准）：{work[field]}')
                for field in ('in_scope', 'out_of_scope', 'acceptance', 'requirement_ids', 'depends_on', 'slice_ids'):
                    for value in work.get(field, []):
                        lines.append(f'- {field}：{markdown_data(value)}')
                if work.get('blocker'):
                    lines.append(f'- 阻塞原因：{markdown_data(work["blocker"])}')
                for key, indexes in work.get('acceptance_refs', {}).items():
                    lines.append(f'- 对应验项：{markdown_data(key)} / {indexes}')
            if 'stage_detail' in item:
                from .stage_details import SECTIONS, RESULTS, DELIVERY
                detail = item['stage_detail']
                lines.append('- 记录分类：' + SECTIONS[item['stage']][detail['type']])
                if 'result' in detail:
                    lines.append('- 原记录运行结果：' + RESULTS[detail['result']])
                if 'delivery_status' in detail:
                    lines.append('- 原记录交付状态：' + DELIVERY[detail['delivery_status']])
                for key in ('cwd', 'path', 'delivery_receipt', 'owner'):
                    if key in detail: lines.append(f'- {key}：{markdown_data(detail[key])}')
                for value in detail.get('steps', []): lines.append('- 步骤：' + markdown_data(value))
                for key in detail.get('record_ids', []): lines.append('- 相关记录：' + markdown_data(by_id[key]['label']))
                if 'command' in detail:
                    lines.append('- 命令原文（仅供阅读，不执行）：')
                    lines.extend('    ' + line for line in detail['command'].splitlines())
            for ref in item.get('sources', []):
                lines.append(f'- 来源：{markdown_data(ref["path"])}，行 {ref.get("line", 1)}；SHA256 {markdown_data(ref.get("sha256", "未知"))}；{ref["freshness"]}')
            lines.append('')
    return '\n'.join(lines)+'\n'
