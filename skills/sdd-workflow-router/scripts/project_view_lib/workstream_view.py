"""Engineer-facing reading path over optional typed observations."""
from . import workstream
from .renderer import esc, selectable, state_badge

VERDICTS = {'COVERED': '验证通过', 'GAP': '仍有待解决问题', 'RECHECK': '需重新核对'}


def links(records):
    return ''.join(selectable(i, esc(i['label']), 'work-link') for i in records)


def heading(title, note):
    return f'<div class="work-heading"><h3>{title}</h3><p>{note}</p></div>'


def tag(value, text):
    return f'<span class="work-tag" data-work-state="{esc(value)}">{esc(text)}</span>'


def listing(values, empty):
    return '<ul>' + ''.join(f'<li>{esc(v)}</li>' for v in values) + '</ul>' if values else f'<p class="work-empty">{empty}</p>'


def gap_order(gaps):
    # Keep blockers, failed/unexecuted runs and missing evidence prominent;
    # repetitive source/task notices remain in the complete detail.
    first = []
    for match in (lambda s: '：阻塞：' in s, lambda s: s.endswith('：失败'),
                  lambda s: s.endswith('：未执行'), lambda s: '缺少验证记录' in s,
                  lambda s: s.startswith('验收条件 ')):
        item = next((s for s in gaps if match(s) and s not in first), None)
        if item is not None:
            first.append(item)
    return first + [s for s in gaps if s not in first]


def row_problems(row):
    # A missing/changed related source does not erase a recorded FAIL/NOT_RUN.
    # Explain both facts without changing coverage or the original run result.
    runs = [c['label'] + '：' + workstream.RESULTS[c['work']['result']]
            for c in row['checks'] if c['work']['result'] != 'PASS']
    return gap_order(list(dict.fromkeys([*runs, *row['gaps']])))


def stats(m):
    done = sum(s['work']['status'] == 'DONE' and not m['slice_issues'](s) for s in m['slice'])
    blocked = sum(s['work']['status'] == 'BLOCKED' for s in m['slice'])
    values = [(len(m['requirement']) if m['requirement'] else '未记录', '需求数量', '仅统计列出的需求'),
              (f'{done} / {len(m["slice"])}' if m['slice'] else '未记录', '已完成任务', '仅统计完成记录和实现文件已核对的任务'),
              (f'{m["covered"]} / {len(m["rows"])}' if m['rows'] else '未记录', '验证通过的需求', '仅统计所有条件都有通过记录的需求'),
              (blocked if m['slice'] else '未记录', '受阻任务', '原因见“任务拆分”')]
    return '<div class="work-stats">' + ''.join(f'<div><strong>{esc(n)}</strong><span>{label}</span><small>{note}</small></div>' for n, label, note in values) + '</div>'


def overview(m):
    brief = next(iter(m['brief']), None)
    result = heading('项目总览', '查看项目目标、实施范围、任务进度和待解决问题。')
    if brief:
        result += (f'<article class="work-brief"><div><span class="work-eyebrow">本次目标</span><h3>{esc(brief["label"])}</h3>'
                   f'<p>{esc(brief.get("note", ""))}</p>{selectable(brief, "查看目标来源 →", "work-link")}{state_badge(brief)}</div>'
                   '<div class="work-boundary"><section><h4>本次范围</h4>' + listing(brief['work']['in_scope'], '范围尚未记录')
                   + '</section><section><h4>不在本次范围内</h4>' + listing(brief['work']['out_of_scope'], '排除范围尚未记录') + '</section></div></article>')
    else:
        result += '<p class="work-empty">尚未提供目标和范围记录。上方说明仅代表本次观察范围。</p>'
    result += stats(m)
    result += ('<nav class="work-reading-path" aria-label="需求、任务与验证">'
               '<a href="#stage-Spec" data-stage-nav="Spec"><span>01 · 需求</span><strong>需求与验收条件</strong></a>'
               '<span aria-hidden="true">→</span><a href="#stage-Tasks" data-stage-nav="Tasks"><span>02 · 任务</span><strong>任务进度与依赖</strong></a>'
               '<span aria-hidden="true">→</span><a href="#stage-Converge" data-stage-nav="Converge"><span>03 · 验证</span><strong>验证结果与待解决问题</strong></a></nav>')
    issues = [r for r in m['rows'] if r['verdict'] != 'COVERED']
    result += '<div class="work-attention">' + heading('待解决问题', '按需求查看未完成事项；点击名称可查看说明和来源。')
    if not m['rows']:
        result += '<p class="work-empty">尚未提供逐条需求记录，暂时无法判断验证情况。</p>'
    elif not issues:
        result += '<p>本页列出的验收条件均有通过记录。业务验收和发布批准需另行确认。</p>'
    else:
        for r in issues:
            # First reading must expose actionable missing checks/failures/blockers,
            # rather than letting generic implementation gaps displace them.
            summary = row_problems(r)
            result += ('<article>' + tag(r['verdict'], VERDICTS[r['verdict']]) + links([r['item']])
                       + listing(summary[:3], '请核对相关记录和来源')
                       + (f'<p class="work-more">另有 {len(summary)-3} 项，请在“对照验收”中查看。</p>' if len(summary) > 3 else '') + '</article>')
    return result + '</div><p class="work-caution">本页是生成时的静态记录；验证结果不代表业务验收或发布批准。</p>'


def requirements(m):
    result = heading('需求与验收条件', '逐条列出预期行为、验收条件、实施任务和验证记录。')
    if not m['rows']:
        return result + '<p class="work-empty">尚未提供逐条需求记录。下方保留已有阶段说明，无法据此判断需求是否完成。</p>'
    for n, row in enumerate(m['rows'], 1):
        i = row['item']
        result += (f'<article class="requirement-card" data-requirement="{esc(i["id"])}">'
                   f'<div class="work-card-title"><span class="work-number">{n:02d}</span><h3>{esc(i["label"])}</h3>'
                   + tag(row['verdict'], VERDICTS[row['verdict']]) + '</div>'
                   + (f'<p>{esc(i["note"])}</p>' if i.get('note') else '')
                   + '<h4>验收条件</h4><ol class="acceptance-list">'
                   + ''.join('<li>' + tag('PASS' if ac['passed'] else 'GAP', '已有通过记录' if ac['passed'] else '缺少通过记录')
                             + '<span>' + esc(ac['text']) + '</span></li>' for ac in row['acceptance']) + '</ol>'
                   + '<div class="requirement-trace"><section><h4>实施任务</h4>' + (links(row['slices']) or '<p class="work-empty">尚未安排任务</p>')
                   + '</section><section><h4>验证记录</h4>' + (links(row['checks']) or '<p class="work-empty">尚无验证记录</p>')
                   + '</section></div><div class="work-card-footer">' + selectable(i, '查看需求来源 →', 'work-link') + state_badge(i) + '</div></article>')
    return result


def slices(m):
    result = heading('任务进度', '每项任务列出对应需求、前置任务和阻塞原因。')
    if not m['slice']:
        return result + '<p class="work-empty">尚未提供逐项任务记录，暂时无法统计完成数量。</p>'
    result += '<div class="slice-board">'
    for status, label in workstream.EXECUTION.items():
        items = [s for s in m['slice'] if s['work']['status'] == status]
        result += f'<section class="slice-column" data-slice-column="{status}"><h4>{label}<span>{len(items)}</span></h4>'
        if not items:
            result += '<p class="work-empty">暂无任务</p>'
        for i in items:
            w = i['work']
            caution = []
            if not m['usable'](i):
                caution.append('任务记录或相关来源需要核对')
            for dep in w.get('depends_on', []):
                if m['slice_issues'](m['nodes'][dep]):
                    caution.append('前置任务尚未完成或需核对：' + m['nodes'][dep]['label'])
            if status == 'DONE':
                caution += m['slice_issues'](i)
            result += (f'<article class="slice-card" data-slice="{esc(i["id"])}"><h5>{esc(i["label"])}</h5>'
                       + (f'<p>{esc(i["note"])}</p>' if i.get('note') else '')
                       + '<h6>对应需求</h6>' + links([m['nodes'][k] for k in w['requirement_ids']])
                       + '<h6>前置任务</h6>' + (links([m['nodes'][k] for k in w.get('depends_on', [])]) or '<span class="work-empty">未记录前置任务</span>')
                       + (f'<p class="work-blocker"><strong>阻塞原因</strong>{esc(w["blocker"])}</p>' if w.get('blocker') else '')
                       + (f'<div class="work-warning">{listing(list(dict.fromkeys(caution)), "")}</div>' if caution else '')
                       + '<div class="work-card-footer">' + selectable(i, '查看任务来源 →', 'work-link') + '</div></article>')
        result += '</section>'
    return result + '</div><p class="work-caution">任务按原记录中的状态分列；即使标记为已完成，来源变化或前置任务问题仍会单独提示。</p>'


def coverage(m):
    result = heading('需求验证对照表', '逐条核对实施任务、实现文件和验证结果，查看仍需处理的问题。')
    if not m['rows']:
        return result + '<p class="work-empty">尚未提供逐条需求记录，暂时无法核对验收条件。测试数量不能证明需求已经满足。</p>'
    result += '<p class="table-scroll-hint"><span aria-hidden="true">↔</span> 左右滑动表格，查看验证结果和待解决问题</p><div class="coverage-scroll" tabindex="0" role="region" aria-label="需求验证覆盖表，可横向滚动"><table class="coverage-table"><caption>本页所列需求的验证结果；不代表已获业务验收批准</caption><thead><tr><th scope="col">需求</th><th scope="col">任务与实现文件</th><th scope="col">验证结果</th><th scope="col">结论与待解决问题</th></tr></thead><tbody>'
    for row in m['rows']:
        req = row['item']
        result += f'<tr data-coverage="{esc(req["id"])}" data-verdict="{row["verdict"]}"><th scope="row">' + links([req]) + '</th><td>'
        for s in row['slices']:
            result += '<div class="coverage-slice">' + links([s]) + tag(s['work']['status'], workstream.EXECUTION[s['work']['status']])
            result += '<div class="coverage-files">' + (links([m['nodes'][k] for k in s.get('implementation_ids', [])]) or '<span class="work-empty">未关联实现文件</span>') + '</div></div>'
        if not row['slices']:
            result += '<span class="work-empty">尚未安排任务</span>'
        result += '</td><td>'
        for c in row['checks']:
            result += ('<div class="coverage-check">' + tag(c['work']['result'], workstream.RESULTS[c['work']['result']])
                       + links([c]) + '<small>' + esc('记录及相关来源已核对' if m['usable'](c) else '记录或相关来源需核对')
                       + '</small><small>' + esc('对应验收条件：' + '、'.join(map(str, c['work'].get('acceptance_refs', {}).get(req['id'], [])))
                                                if c['work'].get('acceptance_refs', {}).get(req['id']) else '尚未关联具体验收条件') + '</small></div>')
        if not row['checks']:
            result += '<span class="work-empty">缺少验证记录</span>'
        gaps = row_problems(row)
        result += '</td><td>' + tag(row['verdict'], VERDICTS[row['verdict']]) + listing(gaps[:2], '所列任务均已完成，验收条件均有通过记录')
        if len(gaps) > 2:
            result += f'<details class="coverage-gap-details"><summary>其余 {len(gaps)-2} 项待解决问题</summary>' + listing(gaps[2:], '') + '</details>'
        result += '</td></tr>'
    return result + '</tbody></table></div><p class="work-caution">“通过”表示原记录中的运行结果。相关来源变化、前置任务未完成或项目返回前一阶段时，需要重新核对验证结论。</p>'


def detail(item, items):
    work = item.get('work')
    if not work:
        # Reverse trace from actual files is handled by the existing implementation map.
        return ''
    nodes = {i['id']: i for i in items}
    result = '<section class="work-detail"><h3>相关需求、任务与验证</h3>'
    for key, label in [('requirement_ids', '对应需求'), ('depends_on', '前置任务'), ('slice_ids', '对应任务')]:
        if work.get(key):
            result += f'<h4>{label}</h4>' + links([nodes[k] for k in work[key]])
    if work['type'] == 'requirement':
        result += '<h4>验收条件</h4><ol>' + ''.join('<li>' + esc(t) + '</li>' for t in work['acceptance']) + '</ol>'
        for role, label in [('slice', '实施任务'), ('check', '验证记录')]:
            linked = [i for i in items if i.get('work', {}).get('type') == role and item['id'] in i['work'].get('requirement_ids', [])]
            result += f'<h4>{label}</h4>' + (links(linked) or '<p class="work-empty">尚未关联</p>')
    if work['type'] == 'slice':
        result += '<h4>原记录中的任务状态</h4>' + tag(work['status'], workstream.EXECUTION[work['status']])
        if work.get('blocker'):
            result += '<p class="work-blocker">' + esc(work['blocker']) + '</p>'
        result += '<h4>验证记录</h4>' + (links([i for i in items if item['id'] in i.get('work', {}).get('slice_ids', [])]) or '<p class="work-empty">尚未关联</p>')
    if work['type'] == 'check':
        result += '<h4>原记录中的运行结果</h4>' + tag(work['result'], workstream.RESULTS[work['result']])
        result += '<h4>对应验收条件</h4>' + listing([nodes[k]['label'] + ' / 验收条件 ' + '、'.join(map(str, n))
                  for k, n in work.get('acceptance_refs', {}).items()], '尚未关联具体验收条件，暂时不能判断该需求验证通过。')
    return result + '</section>'
