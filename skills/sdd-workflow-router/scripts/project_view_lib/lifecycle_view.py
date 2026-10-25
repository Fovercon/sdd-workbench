"""An optional stage-first presentation; the legacy board remains unchanged."""
import base64
import hashlib
from urllib.parse import quote
from . import evidence, lifecycle, repository_map, workstream
from .renderer import HERE, esc, panel, selectable, state_badge, diagram_link, design_render, build_pairs, pair_links, board_script, design_index, anchor, decision_section, decision_link
from .layout import graph


GUIDANCE = {
    'Constitution': '项目约束、工作规则与可用命令。',
    'Align': '我们要解决什么问题，还有哪些选择需要明确。',
    'Spec': '本次范围、术语含义，以及做到什么才算满足要求。',
    'Plan': '准备怎样实现：业务流程、模块分工、数据保存与测试安排。',
    'Tasks': '按可验证的功能拆分任务，明确先后顺序。',
    'Implement': '实现内容、任务与文件的对应关系，以及测试结果和待处理问题。',
    'Converge': '逐条对照需求，核对实现、测试和仍未解决的问题。',
    'Finish': '交付内容、启动办法、接续工作和回退方法。',
}


def records_section(title, records):
    if not records:
        return ''
    entries = []
    for item in records:
        marker = '<span class="planned-label">设计安排 · 尚待实现核对</span>' if item['kind'] == 'design' else ''
        entries.append(selectable(item,
            f'<span class="stage-record-copy"><strong>{esc(item["label"])}</strong>'
            f'<span>{esc(item.get("note", ""))}</span>{marker}</span>'
            f'<span class="stage-record-meta">{state_badge(item)}<span aria-hidden="true">→</span></span>',
            'stage-record', **{'data-state': item['effective_state']}))
    return f'<section class="stage-record-group"><h3>{esc(title)}</h3>{"".join(entries)}</section>'


def stage_content(stage, records, all_items, snapshot):
    from . import workstream_view, stage_reading
    enriched = any('work' in i or 'stage_detail' in i for i in all_items)
    mainline = ''
    if enriched and stage in ('Spec', 'Tasks', 'Converge'):
        model = workstream.model(snapshot, all_items)
        mainline = {'Spec': workstream_view.requirements, 'Tasks': workstream_view.slices,
                    'Converge': workstream_view.coverage}[stage](model)
    elif enriched:
        mainline = stage_reading.render(stage, snapshot, all_items)
    if not records:
        return mainline or '<p class="stage-empty">这一阶段尚未开始。进入后会在这里展示对应记录。</p>'
    required = [i for i in records if i.get('decision', {}).get('kind') != 'feedback']
    optional = [i for i in records if i.get('decision', {}).get('kind') == 'feedback']
    feedback_id = 'feedback-' + (stage or 'common')
    result = decision_section(snapshot, required, all_items) + mainline
    records = [i for i in records if 'work' not in i and 'stage_detail' not in i] if enriched else records
    diagrams = [i for i in records if i['view'] == 'diagram']
    if diagrams:
        pairs = build_pairs(all_items)
        cards = []
        for item in diagrams:
            marker = '设计图 · 尚待实现核对' if item['kind'] == 'design' else '按当前来源绘制'
            cards.append(f'<article class="stage-diagram" data-state="{esc(item["effective_state"])}">'
                f'<span class="diagram-caption">{marker}</span><h3>{esc(item["label"])}</h3>'
                f'<p>{esc(item.get("note", ""))}</p><div class="diagram-actions">{diagram_link(item)}'
                + selectable(item, '查看依据', 'diagram-evidence') + '</div>'
                + pair_links(item, all_items, pairs) + '</article>')
        auxiliary = '<section class="stage-record-group"><h3>业务流程与项目结构</h3><div class="stage-diagrams">' + ''.join(cards) + '</div></section>'
        result += ('<details class="stage-evidence"><summary>补充图示与历史说明</summary>' + auxiliary + '</details>') if any(i['view'] == 'design' for i in records) else auxiliary
    designs = [i for i in records if i['view'] == 'design']
    if designs:
        pairs = build_pairs(all_items)
        cards = []
        for item in designs:
            cards.append(f'<article id="design-{esc(anchor(item["id"]))}" data-design-card="{esc(item["id"])}" class="stage-design" data-state="{esc(item["effective_state"])}">'
                f'<div class="design-head"><h3>{esc(item["label"])}</h3>{state_badge(item)}</div>'
                f'<p class="design-note">{esc(item.get("note", ""))}</p>{design_render(item)}'
                f'<div class="diagram-actions">'
                + selectable(item, '查看依据', 'diagram-evidence') + '</div>'
                + pair_links(item, all_items, pairs) + decision_link(item, all_items) + '</article>')
        result += ('<section class="stage-record-group design-reading"><div class="reading-heading"><div><h3>软件设计</h3>'
                   '<p class="group-help">选一张图，逐层了解方案。</p></div>'
                   + (f'<a class="feedback-jump" href="#{esc(feedback_id)}">提意见 ↗</a>' if optional else '') + '</div>'
                   '<div class="design-gallery">' + design_index(designs) + '<div class="stage-designs">' + ''.join(cards) + '</div></div></section>')
    if optional:
        result += (f'<details class="feedback-area" id="{esc(feedback_id)}"><summary><span>还有想调整的地方？</span>'
                   '<span>写下反馈 →</span></summary>' + decision_section(snapshot, optional, all_items) + '</details>')
    progress = records_section('阶段记录', [i for i in records if i['view'] == 'progress'])
    result += ('<details class="stage-evidence"><summary>阶段记录与依据</summary>' + progress + '</details>') if designs or mainline else progress
    result += records_section('功能与验证记录', [i for i in records if i['view'] == 'capability'])
    structure = [i for i in records if i['view'] == 'structure']
    if structure:
        # A relationship may cite a file first recorded in an earlier stage.
        # Include its actual endpoint without dragging unrelated future records in.
        needed = {edge[key] for edge in structure if 'from' in edge for key in ('from', 'to')}
        present = {item['id'] for item in structure}
        mapped_records = structure + [item for item in all_items if item['id'] in needed - present]
        mapped = repository_map.render(mapped_records)
        result += ('<details class="technical-map stage-structure"><summary>代码与文件对应'
                   '<span>依据本阶段记录，不代表整个仓库清单</span></summary><div class="map-panel">'
                   + (mapped if mapped is not None else graph(mapped_records, namespace=stage or 'common')) + '</div></details>')
        result += records_section('结构依据', structure)
    result += records_section('变更与影响', [i for i in records if i['view'] == 'impact'])
    return result


def render(snapshot, items, previous_href=None):
    from . import workstream_view
    enriched = any('work' in i or 'stage_detail' in i for i in items)
    stages = lifecycle.stage_status(snapshot, items)
    current = snapshot['lifecycle']['current_stage']
    current_stage = next(stage for stage in stages if stage['name'] == current)
    source_uncertain = current_stage['status'] in ('STALE', 'UNKNOWN')
    current_label = lifecycle.STAGES[current]
    stale = [i for i in items if i['freshness'] != 'CURRENT']
    selected = next((i for i in items if i['id'] == snapshot.get('next_id')), None)
    action = next(iter(stale), None) or selected or current_stage['item']
    next_text = ('先核对变化或缺失的来源，再继续使用相关判断。' if stale
                 else action.get('next') or '阅读本阶段记录，再确定下一项工作。')
    next_title = '重新核对来源' if stale else action.get('next_label') or action['label']
    controls = '<a href="view.md">文字版</a>'
    if previous_href:
        controls += f'<a href="{esc(previous_href)}">上一版 ↗</a>'
    nav, content = [], []
    if enriched:
        content.append('<section id="stage-Overview" class="stage-content work-overview" data-stage-panel="Overview" aria-label="项目总览">'
                       + workstream_view.overview(workstream.model(snapshot, items)) + '</section>')
    for index, stage in enumerate(stages, 1):
        name = stage['name']
        active = name == current
        nav.append(f'<a href="#stage-{name}" class="stage-nav{" is-active" if active else ""}" '
                   f'data-stage-nav="{name}" data-stage-status="{stage["status"]}"'
                   + (' aria-current="step"' if active else '')
                   + f' title="{name} · {stage["subtitle"]}">'
                   + f'<span class="stage-index">{index:02d}</span><strong>{stage["subtitle"]}</strong>'
                   f'<span class="stage-status">{stage["text"]}</span></a>')
        records = [i for i in items if i.get('stage') == name]
        warning = ('<p class="stage-warning">当前阶段早于本阶段。本页保留的后续记录仍需核对，不能直接当作当前结论。</p>'
                   if stage['status'] == 'REVISIT' else '')
        content.append(f'<section id="stage-{name}" class="stage-content" data-stage-panel="{name}"'
                       f' aria-labelledby="heading-{name}"><div class="stage-heading">'
                       f'<p class="stage-kicker">{"当前阶段" if active else "阶段记录"} / {index:02d}</p>'
                       f'<h2 id="heading-{name}">{stage["subtitle"]}</h2>'
                       f'<p>{GUIDANCE[name]}</p></div>{warning}{stage_content(name, records, items, snapshot)}</section>')
    common = [i for i in items if 'stage' not in i]
    if common:
        content.append('<details class="stage-common"><summary>项目补充记录</summary>'
                       + stage_content(None, common, items, snapshot) + '</details>')
    css = (HERE / 'styles.css').read_text(encoding='utf-8') + '\n' + (HERE / 'lifecycle.css').read_text(encoding='utf-8') + '\n' + (HERE / 'workspace.css').read_text(encoding='utf-8')
    if enriched:
        css += '\n' + (HERE / 'workstream.css').read_text(encoding='utf-8')
    script = board_script(items)
    script_hash = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    stage_title = '当前阶段需核对' if source_uncertain else '当前阶段'
    optional_feedback = action.get('decision', {}).get('kind') == 'feedback'
    first_design = next((i for i in items if i['view'] == 'design' and i.get('stage') == current), None)
    next_link = (f'<a class="primary-action" href="#{esc(quote("design-" + anchor(first_design["id"]), safe=""))}">查看设计图 →</a>'
                 if optional_feedback and first_design else selectable(action, '查看相关记录 →', 'primary-action'))
    history = (f'<a href="{esc(previous_href)}">打开上一版看板 <span aria-hidden="true">↗</span></a>'
               if previous_href else '<span>这是第一份看板，后续版本将保留并链接它。</span>')
    brand = '项目工作台'
    overview_link = ('<a class="overview-tab" href="#stage-Overview" data-stage-nav="Overview">'
                     + '<span>项目总览</span></a>') if enriched else ''
    close_inspector = ('<button type="button" class="inspector-close" data-close-inspector aria-label="收起详情">'
                       + '<span aria-hidden="true">×</span></button>') if enriched else ''
    summary = str(snapshot.get('summary', snapshot['scope']))
    summary_control = ('<button type="button" class="summary-toggle" data-summary-toggle aria-expanded="false" aria-controls="project-description">展开项目说明</button>'
                       if enriched and len(summary) > 120 else '')
    document = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-{script_hash}'; base-uri 'none'; form-action 'none'">
<title>{esc(snapshot['title'])} · 项目看板</title><style>{css}</style></head><body class="lifecycle-board{' workstream-enabled' if enriched else ''}" data-current-stage="{current}" data-initial-stage="{'Overview' if enriched else current}">
<a class="skip" href="#workspace">跳到项目内容</a><div class="shell">
<header class="topbar"><a class="brand" href="{'#stage-Overview' if enriched else '#top'}"><span class="brand-mark" aria-hidden="true"></span>{brand}</a><nav aria-label="辅助阅读">{'<span class="snapshot-label">离线快照</span>' if enriched else ''}{controls}</nav></header>
<main id="top"><section class="project-overview{' has-optional-feedback' if optional_feedback else ''}"><div class="project-intro"><p class="eyebrow">项目进展与验证记录</p>
<h1>{esc(snapshot['title'])}</h1><p class="intro{' is-collapsible' if summary_control else ''}" id="project-description">{esc(summary)}</p>{summary_control}
<div class="current-stage" data-state="{current_stage['status']}"><span>{stage_title}</span><strong>{current_label}</strong></div>
</div><section class="next-action" aria-labelledby="next-title"><div class="next-label"><span class="next-index">{'阅读提示' if optional_feedback else '下一步'}</span>
<span class="next-status">{'来源需重新核对' if stale else '依据本次保存的记录'}</span></div><h2 id="next-title">{esc(next_title)}</h2>
<p>{esc(next_text)}</p>{next_link}</section></section>
<section class="lifecycle-section" aria-labelledby="lifecycle-title"><div class="lifecycle-heading"><h2 id="lifecycle-title">项目进程</h2>
<p>按阶段查看需求、方案、任务和验证结果。</p></div>{overview_link}<nav class="stage-navigation" aria-label="开发阶段">{''.join(nav)}</nav></section>
<div id="workspace" class="workspace lifecycle-workspace"><div class="stage-board">{''.join(content)}</div>
<aside id="detail-pane" class="detail-pane" aria-label="说明与来源" data-default="{esc(first_design['id'] if optional_feedback and first_design else current_stage['item']['id'])}">
<div class="inspector-bar"><span>说明与来源</span><a href="#workspace" class="back-map">返回记录 ↑</a>{close_inspector}</div>
<div class="detail-placeholder"><p>选择一项记录查看说明</p><span>来源文件与核验信息会显示在这里。</span></div>{''.join(panel(i, items) for i in items)}</aside></div>
<section class="view-history"><div><h2>看板变化记录</h2><p>每个版本单独保存。旧版保留当时的内容，来源变化后应生成新版本。</p></div>
<div>{history}<a href="snapshot.json">本版记录数据 ↗</a></div></section>
<details class="scope"><summary>本版范围与记录时间</summary><p>{esc(snapshot['scope'])}</p><p>记录时间：{esc(snapshot['captured_at'])}。文件核对：{esc(snapshot.get('checked_at', '本次生成时'))}。</p>
<p>本页是生成时的静态记录。来源文件一致不代表业务验收或发布批准。</p></details>
<noscript><p class="noscript-note">未启用 JavaScript：所有阶段和详情均保留，可点击链接定位，也可阅读文字版。</p></noscript>
</main><footer><span>{esc(snapshot['title'])}</span><span>阶段名称固定 · 来源可查 · 旧版保留</span></footer></div><script>{script}</script></body></html>'''
    return document, evidence.markdown(snapshot, items)
