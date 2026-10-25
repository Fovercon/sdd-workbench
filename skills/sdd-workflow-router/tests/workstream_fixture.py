"""Synthetic, portable workstream inputs; never real progress or approval."""
import hashlib
import json
from pathlib import Path


def fixture(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    items = []

    def add(key, label, stage, view='capability', work=None, **extra):
        path = f'source-{len(items)}.md'
        text = '# 合成回归输入，不代表真实进展或批准\n' + label + '\n' + json.dumps(work or {}, ensure_ascii=False)
        (root / path).write_text(text, encoding='utf-8')
        item = dict(id=key, label=label, stage=stage, view=view, kind='assessment', state='SATISFIED',
                    sources=[dict(path=path, line=1, sha256=hashlib.sha256(text.encode()).hexdigest())])
        if work:
            item['work'] = work
        item.update(extra)
        items.append(item)
        return item

    for stage in ['Align', 'Spec', 'Tasks', 'Implement', 'Converge']:
        add(stage, stage + ' 阶段记录', stage, 'progress')
    add('brief', '让资料人员安全地选择、执行并恢复治理任务', 'Align', 'progress',
        dict(type='brief', in_scope=['严格范围选择', '暂停后继续', '重跑时保护成功结果'],
             out_of_scope=['调用真实治理模型', '解析生产资料', '向远程仓库提交']),
        note='合成演示：用于验证看板阅读和交互，所有状态均为回归输入。')
    for key, label, acceptance in [
        ('R1', '只处理用户选中的资料', ['编号优先；找不到编号时明确提示，不能改用标题匹配。']),
        ('R2', '暂停后接着处理剩余资料', ['暂停时保留进度；继续后跳过已有成功项。']),
        ('R3', '重跑失败项时保留成功结果', ['重跑仅处理失败项，原成功结果内容与时间不变。'])]:
        add(key, label, 'Spec', work=dict(type='requirement', acceptance=acceptance))
    for n, label in [(1, '范围匹配实现'), (2, '暂停与继续实现')]:
        filename = f'component-{n}.py'
        (root / filename).write_text('# Synthetic implementation source\n', encoding='utf-8')
        item = add('code' + str(n), label, 'Implement', 'structure', kind='code_observation', file=filename)
        item['sources'] = [dict(path=filename, line=1, sha256=hashlib.sha256((root / filename).read_bytes()).hexdigest())]
    add('S1 范围%', '范围选择与预览', 'Tasks', work=dict(type='slice', status='DONE', requirement_ids=['R1']), implementation_ids=['code1'])
    items[-1]['sources'] += next(i for i in items if i['id'] == 'code1')['sources']
    add('S2', '执行、暂停与继续', 'Tasks', work=dict(type='slice', status='DOING', requirement_ids=['R2'], depends_on=['S1 范围%']),
        note='服务端状态已实现，暂停路径还需浏览器验证。', implementation_ids=['code2'])
    items[-1]['sources'] += next(i for i in items if i['id'] == 'code2')['sources']
    add('S3', '仅重跑失败项', 'Tasks', work=dict(type='slice', status='BLOCKED', requirement_ids=['R3'], depends_on=['S2'],
        blocker='等待暂停与继续路径稳定，再核对失败项重跑。'))
    add('S4', '对比重跑前后的成功结果', 'Tasks', work=dict(type='slice', status='TODO', requirement_ids=['R3'], depends_on=['S1 范围%']))
    for key, label, req, sid, result in [
        ('V1', '严格编号匹配回归', 'R1', 'S1 范围%', 'PASS'),
        ('V2', '暂停继续浏览器流程', 'R2', 'S2', 'NOT_RUN'),
        ('V3', '成功结果保护回归', 'R3', 'S3', 'FAIL')]:
        add(key, label, 'Converge', work=dict(type='check', requirement_ids=[req], slice_ids=[sid], result=result, acceptance_refs={req: [1]}), kind='runtime_evidence')
    items[-1].update(next='先补齐暂停继续流程，再验证重跑前后的成功结果一致。', next_label='补齐暂停与结果保护验证')
    return dict(project_id='workstream-synthetic', title='配置治理 · 看板交互演示（合成数据）', scope='合成输入，仅供界面回归，不代表真实交付或审批。',
                summary='明确选择范围、按进度执行任务，在重跑时保留成功结果。演示数据仅用于检查可视化。', captured_at='2026-10-26', next_id='V3',
                lifecycle=dict(current_stage='Converge', stage_items={s: s for s in ['Align', 'Spec', 'Tasks', 'Implement', 'Converge']}), items=items)


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1])
    data = fixture(root)
    (root / 'input.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
