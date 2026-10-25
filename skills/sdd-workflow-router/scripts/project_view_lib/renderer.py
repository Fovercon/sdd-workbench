"""Offline, source-backed project board with optional technical detail."""
import base64
import gzip
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import quote
from . import evidence, decisions
from .layout import graph
from . import repository_map

STATES, KINDS = evidence.STATES, evidence.KINDS
HERE = Path(__file__).resolve().parent
esc = lambda value: html.escape(str(value), quote=True)
anchor = lambda value: 'item-' + quote(value, safe='')
FRESH = {'CURRENT': '文件未变化', 'STALE': '文件已变化', 'UNKNOWN': '文件还需核对'}


def selectable(item, content, cls='', **attrs):
    extra = ''.join(f' {esc(k)}="{esc(v)}"' for k, v in attrs.items())
    return (f'<a class="select {cls}" data-select="{esc(item["id"])}" '
            f'href="#{esc(anchor(item["id"]))}"{extra}>{content}</a>')


def state_badge(item):
    state = item['effective_state']
    # Evidence-backed observations are not automatically accepted/completed work.
    text = decisions.label(item) or ('设计草稿' if item['kind'] == 'design' and state in ('GAP', 'SATISFIED') else STATES[state])
    return f'<span class="badge" data-state="{esc(state)}">{esc(text)}</span>'


def diagram_link(item):
    if item['effective_state'] != 'SATISFIED':
        return f'<span class="diagram-warning">{esc(STATES[item["effective_state"]])} · 请先查看依据</span>'
    return (f'<a class="diagram-open" href="{esc(item["artifact_href"])}" target="_blank" rel="noopener">'
            '打开图示 <span aria-hidden="true">↗</span></a>')


def diagram_section(items):
    diagrams = [i for i in items if i['view'] == 'diagram']
    if not diagrams:
        return ''
    pairs = build_pairs(items)
    cards = []
    for num, item in enumerate(diagrams, 1):
        cards.append(f'<article class="diagram-card" data-state="{esc(item["effective_state"])}">'
            f'<span class="diagram-number">{num:02d}</span><h3>{esc(item["label"])}</h3>'
            f'<p>{esc(item.get("note", ""))}</p><div class="diagram-actions">{diagram_link(item)}'
            + selectable(item, '查看依据', 'diagram-evidence') + '</div>'
            + pair_links(item, items, pairs) + decision_link(item, items) + '</article>')
    return ('<section class="project-diagrams" aria-labelledby="diagrams-title">'
            '<div class="section-heading"><h2 id="diagrams-title">项目怎样工作</h2>'
            '<p>按问题分开看；图示单独打开，依据可以随时核对。</p></div>'
            f'<div class="diagram-cards">{"".join(cards)}</div></section>')


def design_render(item, technical=False):
    """Progressively enhance the exact contract source with the bundled engine."""
    source = item.get('mermaid', '')
    header = next((s.strip() for s in source.splitlines() if s.strip() and not s.strip().startswith('%%')), '')
    kind = next((label for prefix, label in (
        ('sequenceDiagram', '时序图'), ('stateDiagram', '状态图'), ('classDiagram', '类图'),
        ('erDiagram', '实体关系图'), ('C4', '系统架构图'), ('architecture', '部署架构图'),
        ('flowchart', '流程与结构图'), ('graph ', '流程与结构图')) if header.startswith(prefix)), '设计图')
    result = (f'<div class="design-viewer" data-design-id="{esc(item["id"])}" data-title="{esc(item["label"])}" data-technical="{str(technical).lower()}">'
            f'<div class="design-toolbar"><span class="design-type">{kind}</span>'
            '<div class="design-controls"><button type="button" data-diagram-action="zoom-out" aria-label="缩小设计图" disabled>−</button>'
            '<button type="button" data-diagram-action="fit" disabled>适应画布</button>'
            '<button type="button" data-diagram-action="zoom-in" aria-label="放大设计图" disabled>＋</button>'
            '<button type="button" data-diagram-action="expand" disabled>放大查看 ↗</button>'
            '<button type="button" data-diagram-action="download" disabled>导出图形</button></div></div>'
            '<div class="design-figure" tabindex="0" role="region" aria-label="设计图画布，可缩放或放大查看">'
            '<p class="design-render-status" role="status">图形将在浏览器中离线绘制；下方保留原始图源。</p></div>'
            '<details class="design-source-toggle" open><summary>查看图源</summary>'
            f'<pre class="design-source" data-design-source>{esc(source)}</pre></details>'
            '<p class="design-canvas-hint">画布可滚动；复杂图可放大查看，或导出后阅读。</p></div>')
    if item.get('technical_mermaid') and not technical:
        detail = dict(item, id=item['id'] + '--technical', label=item['label'] + ' · 技术细节',
                      mermaid=item['technical_mermaid'])
        result += ('<details class="design-technical"><summary>技术细节与原始命名</summary>'
                   '<p>这里保留代码中的类型、方法和状态标识，便于核对实现。</p>'
                   + design_render(detail, technical=True) + '</details>')
    return result



def board_script(items):
    script = (HERE / 'interaction.js').read_text()
    if any(i['state'] == 'PENDING_HUMAN' or 'decision' in i for i in items):
        script += '\n' + (HERE / 'decision_interaction.js').read_text()
        script += '\n' + (HERE / 'live_feedback.js').read_text()
    if any(i['view'] == 'design' for i in items):
        script += '\n/* Mermaid 12.2.0\n' + (HERE / 'vendor/MERMAID-LICENSE').read_text() + '\n*/\n'
        script += '\n' + gzip.decompress((HERE / 'vendor/mermaid-12.2.0.min.js.gz').read_bytes()).decode()
        script += '\n' + (HERE / 'design_interaction.js').read_text()
    # HTML parsing happens before JavaScript; contract labels cannot close a script.
    return re.sub(r'</script', r'<\\/script', script, flags=re.I)


def decision_link(item, items):
    if item['state'] != 'PENDING_HUMAN' and 'decision' not in item and 'decision_ref' not in item:
        return ''
    target = next((i for i in items if i['id'] == item.get('decision_ref')), item)
    href = '#' + quote('decision-' + anchor(target['id']), safe='')
    text = '提意见' if target.get('decision', {}).get('kind') == 'feedback' else '填写答复'
    return f'<a class="decision-open" href="{esc(href)}">{text} →</a>'


def decision_section(snapshot, records, all_items):
    pending = [i for i in records if (i['state'] == 'PENDING_HUMAN' or 'decision' in i) and 'decision_ref' not in i]
    if not pending:
        return ''
    cards = []
    for item in pending:
        q = item.get('decision')
        feedback = q is not None and q['kind'] == 'feedback'
        linked = [i for i in all_items if i.get('decision_ref') == item['id']]
        allowed = ('GAP', 'SATISFIED', 'PENDING_HUMAN') if feedback else ('PENDING_HUMAN',)
        disabled = item['effective_state'] not in allowed or any(i['freshness'] != 'CURRENT' for i in linked)
        card_id = 'decision-' + anchor(item['id'])
        common = (f'<article id="{esc(card_id)}" class="decision-card" data-decision-item="{esc(item["id"])}"'
                  + (' data-optional-feedback="true"' if feedback else '') + '>'
                  + f'<div class="decision-heading"><span>{"方案反馈 · 可选" if feedback else "需要你的答复"}</span>{state_badge(item)}</div>')
        if q is None:
            clarify = f'关于「{item["label"]}」，请先说明具体需要我决定什么，以及可选方案和影响。'
            cards.append(common + f'<h3>{esc(item["label"])}</h3>'
                         '<p>问题尚未说明清楚，可以先在对话里问一句：</p>'
                         f'<textarea class="decision-clarify" readonly aria-label="对话中可直接发送的话">{esc(clarify)}</textarea>'
                         '<button type="button" data-copy-clarification>复制这句话</button>'
                         '<p class="decision-status" role="status"></p></article>')
            continue
        request = {'schema': decisions.SCHEMA, 'project_id': snapshot['project_id'],
                   'snapshot_sha256': snapshot.get('input_sha256', ''), 'item_id': item['id'],
                   'decision_id': q['id'], 'kind': q['kind'], 'prompt': q['prompt'],
                   'subject': q.get('subject', item['label']), 'scope': q['scope'], 'options': q.get('options', [])}
        controls = ''
        if q['kind'] == 'input':
            controls = '<label class="decision-input-label">填写资料位置或说明<textarea data-decision-answer maxlength="12000" required></textarea></label>'
        else:
            name = 'decision-' + hashlib.sha256(item['id'].encode()).hexdigest()[:12]
            controls = '<fieldset class="decision-options"><legend class="sr-only">选择你的答复</legend>'
            for option in q['options']:
                controls += (f'<label class="decision-option"><input type="radio" name="{name}" value="{esc(option["id"])}" required>'
                             f'<span><strong>{esc(option["label"])}</strong><small>{esc(option["description"])}</small></span></label>')
            controls += '</fieldset>'
        warning = ('<p class="decision-blocked">这份记录需要先重新核对，请在对话里说明你的意见。</p>' if disabled else '')
        review = (f'<p class="decision-review-note">已收到你的意见：{esc(item["review_note"])}</p>' if item.get('review_note') else '')
        cards.append(common + f'<h3>{esc(q["prompt"])}</h3>' + review
            + f'<p class="decision-scope">{esc(q["scope"])}</p>' + warning
            + f'<form class="decision-form" data-live-feedback-ready data-decision-request="{esc(json.dumps(request, ensure_ascii=False))}">'
            + f'<fieldset class="decision-fields"{" disabled" if disabled else ""}>' + controls
            + '<details class="decision-note-wrap"><summary>补充一句（可选）</summary>'
              '<label class="decision-input-label"><span data-note-label>补充说明</span><textarea data-decision-note maxlength="12000" placeholder="例如：时序图的字再大一些，失败分支单独展开。"></textarea></label></details>'
            + '<div class="decision-actions"><button type="button" data-decision-action="copy">'
            + ('复制反馈' if feedback else '复制答复') + '</button>'
              '<span>复制后，回到对话粘贴并发送。</span></div>'
              '<details class="decision-tools"><summary>更多操作</summary><div>'
              '<button type="button" data-decision-action="generate">预览答复</button>'
              '<button type="button" data-decision-action="download">导出答复文件</button></div></details></fieldset>'
              '<p class="decision-help">也可以直接在对话里说你的意见，不用填写这张卡。</p>'
              '<noscript><p class="decision-help">未启用脚本，请直接在项目对话中回复。</p></noscript>'
              '<p class="decision-status" role="status" aria-live="polite"></p>'
              '<details class="decision-output" hidden><summary>将发送到对话的内容</summary>'
              '<textarea readonly aria-label="答复内容"></textarea></details></form>'
            + '<details class="decision-context"><summary>查看答复范围和依据</summary>'
            + f'<p>{esc(q["scope"])}</p><small>答复人：{esc(q["owner"])} · 编号：{esc(q["id"])}</small>'
            + selectable(item, '查看相关记录', 'decision-basis') + '</details></article>')
    return '<section class="human-decisions"><div class="decision-cards">' + ''.join(cards) + '</div></section>'


def design_index(items):
    links = ''.join(f'<a data-design-select="{esc(item["id"])}" href="#{esc(quote("design-" + anchor(item["id"]), safe=""))}"><span>{n:02d}</span>{esc(item["label"])}</a>'
                    for n, item in enumerate(items, 1))
    return (f'<details class="design-index" open><summary>设计图 <span>{len(items):02d}</span></summary>'
            f'<nav aria-label="设计视图索引">{links}</nav></details>')


def build_pairs(items):
    """Declare a pairing once; both sides navigate to each other."""
    pairs = {}
    for item in items:
        for rid in item.get('related_ids', []):
            pairs.setdefault(item['id'], set()).add(rid)
            pairs.setdefault(rid, set()).add(item['id'])
    return pairs


def pair_links(item, items, pairs):
    by_id = {i['id']: i for i in items}
    links = []
    for rid in sorted(pairs.get(item['id'], ())):
        other = by_id[rid]
        if 'artifact' in other:
            links.append(f'<a class="pair-link" href="{esc(other["artifact_href"])}" target="_blank" rel="noopener">'
                         f'对照图示 · {esc(other["label"])} <span aria-hidden="true">↗</span></a>')
        else:
            links.append(selectable(other, f'对照设计 · {esc(other["label"])} <span aria-hidden="true">→</span>', 'pair-link'))
    return f'<div class="design-pair">{"".join(links)}</div>' if links else ''


def design_section(items):
    designs = [i for i in items if i['view'] == 'design']
    if not designs:
        return ''
    pairs = build_pairs(items)
    cards = []
    for num, item in enumerate(designs, 1):
        cards.append(f'<article id="design-{esc(anchor(item["id"]))}" data-design-card="{esc(item["id"])}" class="design-card" data-state="{esc(item["effective_state"])}">'
            f'<div class="design-head"><span class="design-number">{num:02d}</span><h3>{esc(item["label"])}</h3>'
            f'{state_badge(item)}</div><p class="design-note">{esc(item.get("note", ""))}</p>'
            f'{design_render(item)}<div class="diagram-actions">'
            + selectable(item, '查看依据', 'diagram-evidence') + '</div>'
            + pair_links(item, items, pairs) + decision_link(item, items) + '</article>')
    return ('<section class="project-designs" aria-labelledby="design-title">'
            '<div class="section-heading"><h2 id="design-title">设计方案视图</h2>'
            '<p>按设计问题阅读；支持离线绘图、放大和导出，审批状态可查。</p></div>'
            f'<div class="design-gallery">{design_index(designs)}<div class="design-cards">{"".join(cards)}</div></div></section>')


def panel(item, items):
    by_id = {i['id']: i for i in items}
    refs=[]
    for ref in item.get('sources', []):
        refs.append(f'<li class="source"><a href="{esc(ref["href"])}" target="_blank" rel="noopener" class="source-link">'
                    f'<span>{esc(Path(ref["path"]).name)}</span><span aria-hidden="true">↗</span></a>'
                    f'<p class="source-meta">第 {ref.get("line",1)} 行 · {FRESH[ref["freshness"]]}</p>'
                    f'<details class="fingerprint"><summary>文件位置与校验值</summary><p>{esc(ref["path"])}</p><code>SHA256 {esc(ref.get("sha256", "未知"))}</code></details></li>')
    connected=([by_id[item['from']],by_id[item['to']]] if 'from' in item else
               [i for i in items if i.get('from')==item['id'] or i.get('to')==item['id']])
    related=''.join(selectable(i, esc(i['label'])+' <span aria-hidden="true">→</span>', 'related-link') for i in connected)
    owners=[by_id[key] for key in item.get('implementation_ids',[])]
    capabilities=[i for i in items if item['id'] in i.get('implementation_ids',[])]
    mapping=''
    for title,records in [('这项功能在哪里实现',owners),('这个文件负责的功能',capabilities)]:
        if records:
            mapping+=f'<div class="implementation"><h3>{title}</h3>'+''.join(selectable(i,
                esc(Path(i['file']).name if 'file' in i else i['label'])+' <span aria-hidden="true">→</span>','implementation-link') for i in records)+'</div>'
    stage_attr = f' data-record-stage="{esc(item["stage"])}"' if 'stage' in item else ''
    return (f'<article id="{esc(anchor(item["id"]))}" class="detail-content" data-id="{esc(item["id"])}" data-state="{esc(item["effective_state"])}"{stage_attr}>'
            f'<h2 tabindex="-1">{esc(item["label"])}</h2>{state_badge(item)}'
            +(f'<code class="detail-file">{esc(item["file"])}</code>' if 'file' in item else '')
            +f'<p class="description">{esc(item.get("note", ""))}</p>'
            +(f'<div class="detail-diagram">{diagram_link(item)}</div>' if 'artifact' in item else '')
            +(f'<details class="related design-source-details"><summary>设计视图源码（Mermaid）</summary>'
              f'<pre class="design-source">{esc(item["mermaid"])}</pre></details>' if 'mermaid' in item else '')
            +pair_links(item, items, build_pairs(items))
            +decision_link(item, items)
            +mapping
            +(f'<div class="detail-next"><h3>接下来</h3><p>{esc(item["next"])}</p></div>' if item.get('next') else '')
            +(f'<details class="related"><summary>查看相关连接 · {len(connected)}</summary>{related}</details>' if related else '')
            +f'<details class="evidence"><summary>查看相关文件 · {len(refs)}</summary><ul>{"".join(refs) or "<li>尚无可核验来源</li>"}</ul>'
            f'<p class="evidence-note">依据类型：{KINDS[item["kind"]]}。本次核对：{FRESH[item["freshness"]]}。原记录：{STATES[item["state"]]}。文件未变化不代表业务已经验收。</p>'
            +(f'<p class="source-meta">代码位置：{esc(item["sublabel"])}</p>' if item.get('sublabel') else '')
            +'</details></article>')


def render(snapshot, items, previous_href=None):
    if 'lifecycle' in snapshot:
        from . import lifecycle_view
        return lifecycle_view.render(snapshot, items, previous_href)
    markdown = evidence.markdown(snapshot, items)
    progress=[i for i in items if i['view']=='progress']
    nodes=[i for i in items if i['view']=='structure' and 'from' not in i]
    capabilities=[i for i in items if i['view']=='capability']
    stale=[i for i in items if i['freshness']!='CURRENT']
    gaps=[i for i in progress if i['effective_state'] not in ('SATISFIED','NOT_APPLICABLE')]
    selected=[i for i in items if i['id']==snapshot.get('next_id')]
    action=next(iter(stale or selected or gaps or [i for i in progress if i.get('next')]),None)
    primary=action or next(iter(progress or items),None)
    pending=bool(action and action['effective_state']=='PENDING_HUMAN')
    unfinished=bool(gaps or (action and action['effective_state'] not in ('SATISFIED','NOT_APPLICABLE')))
    status='需重新核对来源' if stale else '有待确认的事项' if pending else '仍有工作待完成' if unfinished else '查看当前记录'
    next_text='先重新核对变化或缺失的来源，再使用下方判断。' if stale else (action.get('next') or action['label']) if action else '查看当前范围与依据；有新的任务后再更新视图。'
    next_title='重新核对来源' if stale else (action.get('next_label') or re.sub(r'^(已完成|待确认|未完成)：','',action['label'])) if action else '暂无已记录的下一步'
    steps=[]
    for num,item in enumerate(progress,1):
        state=item['effective_state'];label=re.sub(r'^(已完成|待确认|未完成)：','',item['label'])
        steps.append(selectable(item, f'<span class="step-number" aria-hidden="true">{str(num).zfill(2)}</span><span class="step-copy"><strong>{esc(label)}</strong><small>{esc(STATES[state])}</small></span><span class="step-arrow" aria-hidden="true">→</span>', 'step', **{'data-state':state}))
    modules=[]
    for item in capabilities or nodes:
        state=item['effective_state']
        # Planned modules must stay distinguishable on the first reading layer.
        marker=('<span class="module-state">设计中 · '+esc(STATES[state])+'</span>' if item['kind']=='design' else
                '<span class="module-state">'+esc(STATES[state])+'</span>' if state!='SATISFIED' else '')
        modules.append(selectable(item, f'<span class="module-copy"><strong>{esc(item["label"])}</strong><span>{esc(item.get("note", ""))}</span>{marker}</span><span class="module-arrow" aria-hidden="true">↗</span>', 'module-link', **{'data-state':state,'data-kind':item['kind']}))
    by_id={i['id']: i for i in items}
    relations=[selectable(edge, esc(by_id[edge['from']]['label']+' → '+by_id[edge['to']]['label']+' · '+edge['label'])+' <span aria-hidden="true">↗</span>', 'relation-link', **{'data-state':edge['effective_state']}) for edge in items if 'from' in edge]
    file_map=repository_map.render(items)
    diagram=file_map if file_map is not None else graph(items)+f'<div class="relations" aria-label="结构关系">{"".join(relations)}</div>'
    map_title=('查看文件与功能对应' if any(i['view']=='diagram' for i in items) else '查看项目结构') if file_map is not None else '查看模块连接图'
    map_hint='实际文件、调用关系与功能对应' if file_map is not None else '当前记录中的模块联系'
    impacts=[i for i in items if i['view']=='impact']
    impact=(''.join(selectable(i, esc(i['label'])+' <span aria-hidden="true">→</span>', 'impact-link') for i in impacts))
    impact_section=f'<section class="impact"><h2>这次变更影响哪里</h2>{impact}</section>' if impacts else ''
    controls='<a href="view.md">文字版</a>' + (f'<a href="{esc(previous_href)}">上一版 ↗</a>' if previous_href else '')
    primary_button=selectable(primary,'查看详情 <span aria-hidden="true">→</span>','primary-action') if primary else ''
    css=(HERE/'styles.css').read_text() + '\n' + (HERE/'workspace.css').read_text();script=board_script(items)
    script_hash=base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    checked=snapshot.get('checked_at','本次生成时')
    document=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-{script_hash}'; base-uri 'none'; form-action 'none'">
<title>{esc(snapshot['title'])} · 项目视图</title><style>{css}</style></head><body>
<a class="skip" href="#workspace">跳到项目内容</a>
<div class="shell"><header class="topbar"><a class="brand" href="#top"><span class="brand-mark" aria-hidden="true"></span>项目看板</a><nav aria-label="辅助阅读">{controls}</nav></header>
<main id="top"><div class="overview"><div><p class="eyebrow">{esc(snapshot.get("context", snapshot['title']))}</p><h1>{esc(snapshot.get("headline", snapshot["title"]))}</h1><p class="intro">{esc(snapshot.get("summary", "查看当前进展，选择功能了解详情。"))}</p><p class="snapshot-meta"><span class="status-dot" data-stale="{str(bool(stale) or not items).lower()}"></span>{'有文件变化，需要重新核对' if stale else '查看这次保存的项目状态' if items else '还没有项目记录'}<span>·</span>不会自动更新</p></div>
<section class="next-action" aria-labelledby="next-title"><div class="next-label"><span class="next-index">下一步</span><span class="next-status">{esc(status)}</span></div><h2 id="next-title">{esc(next_title)}</h2><p>{esc(next_text)}</p>{primary_button}</section></div>
{diagram_section(items)}
{decision_section(snapshot, items, items)}
{design_section(items)}
<div id="workspace" class="workspace"><div class="board"><section class="progress" aria-labelledby="progress-title"><div class="section-heading"><h2 id="progress-title">做到哪了</h2><p>点一项查看记录</p></div>{''.join(steps) or '<p class="empty">还没有进展记录。</p>'}</section>
<section class="modules" aria-labelledby="module-title"><div class="section-heading"><h2 id="module-title">功能与分工</h2><p>点一个模块，查看说明与依据</p></div><div class="module-list">{''.join(modules) or '<p class="empty">还没有模块记录。</p>'}</div></section>
<details id="project-structure" class="technical-map"><summary>{map_title} <span>{map_hint}</span></summary><section class="map-panel" aria-label="项目结构">{diagram}<p class="map-note">{esc(snapshot.get("map_note", "箭头含义以每条连接的说明为准；连接图不代表操作顺序。"))}</p></section></details></div>
<aside id="detail-pane" class="detail-pane" aria-label="详情与依据" data-default="{esc(primary['id']) if primary else ''}"><div class="inspector-bar"><span>正在查看</span><a href="#workspace" class="back-map">返回列表 ↑</a></div><div class="detail-placeholder"><p>选择一项，了解更多</p><span>这里会显示说明、下一步和相关文件。</span></div>{''.join(panel(i,items) for i in items)}</aside></div>
{impact_section}
<details class="scope"><summary>关于这份看板</summary><p>{esc(snapshot['scope'])}</p><p>记录时间：{esc(snapshot['captured_at'])}。文件核对时间：{esc(checked)}。</p><p>看板不会自动跟随仓库变化。文件变化后，需要重新阅读来源并生成新版本。有来源的记录不等于业务验收通过；看板也不会修改项目文件或批准任务。</p></details>
<noscript><p class="noscript-note">浏览器未启用 JavaScript：所有详情均保留，点击条目可定位到对应记录，也可阅读文字版。</p></noscript>
</main><footer><span>{esc(snapshot['title'])}</span><span>记录可查 · 旧版保留</span></footer></div><script>{script}</script></body></html>'''
    return document, markdown
