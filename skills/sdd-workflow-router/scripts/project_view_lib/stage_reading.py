"""Consistent reading sections; missing sources never become invented facts."""
from . import stage_details, workstream
from .renderer import esc, selectable, state_badge
from .workstream_view import links, listing, tag


def section(title, content, key):
    return f'<section class="stage-reading-section" data-stage-section="{key}"><h3>{title}</h3>{content}</section>'


def empty(text):
    return f'<p class="stage-reading-empty">{text}</p>'


def status(item, model):
    if model['usable'](item):
        return '<span class="record-source-state">记录及相关来源已核对</span>'
    if item['freshness'] == 'STALE': text = '来源已变化，需要重新核对本记录。'
    elif item['freshness'] == 'UNKNOWN': text = '来源缺失或无法核对，暂不能确认本记录。'
    else: text = '本记录或关联记录仍需核对；原记录中的状态不代表当前结论。'
    return f'<p class="stage-reading-warning">{text}</p>'


def detail_content(item, items):
    d = item.get('stage_detail')
    if not d: return ''
    nodes = {i['id']: i for i in items}
    result = ''
    if 'result' in d:
        result += '<p class="stage-field"><strong>原记录中的运行结果</strong>' + tag(d['result'], stage_details.RESULTS[d['result']]) + '</p>'
    if d['type'] == 'command' and 'result' not in d:
        result += '<p class="record-source-state">尚未提供执行结果</p>'
    if 'delivery_status' in d:
        result += '<p class="stage-field"><strong>原记录中的交付状态</strong>' + tag('delivery', stage_details.DELIVERY[d['delivery_status']]) + '</p>'
    if 'path' in d:
        result += '<p class="stage-file"><span>文件</span><code>' + esc(d['path']) + '</code></p>'
    if 'delivery_receipt' in d:
        result += '<p class="stage-file"><span>交付回执</span><code>' + esc(d['delivery_receipt']) + '</code></p>'
    if 'owner' in d:
        result += '<p class="stage-field"><strong>接续负责人</strong><span>' + esc(d['owner']) + '</span></p>'
    if d['type'] == 'handoff' and not d.get('owner'):
        result += '<p class="record-source-state">尚未记录接续负责人</p>'
    if 'steps' in d:
        result += '<ol class="stage-steps">' + ''.join('<li>'+esc(s)+'</li>' for s in d['steps']) + '</ol>'
    if 'command' in d:
        result += '<div class="stage-command"><p>命令原文' + (' · 执行位置：' + esc(d['cwd']) if d.get('cwd') else '') + '</p><pre tabindex="0" role="region" aria-label="命令原文"><code>' + esc(d['command']) + '</code></pre></div>'
    if d.get('record_ids'):
        result += '<div class="stage-related-records"><span>相关记录</span>' + links([nodes[k] for k in d['record_ids']]) + '</div>'
    return result


def cards(records, items, model):
    result = ''
    for item in records:
        result += (f'<article class="stage-reading-card" data-stage-record="{esc(item["id"])}"><h4>{esc(item["label"])}</h4>'
                   f'<p class="stage-record-description">{esc(item.get("note", ""))}</p>' + detail_content(item, items)
                   + status(item, model) + '<div class="stage-reading-footer">'
                   + selectable(item, '查看说明与来源 →', 'work-link') + state_badge(item) + '</div></article>')
    return '<div class="stage-reading-cards">' + result + '</div>'


def render(stage, snapshot, items):
    if stage not in stage_details.SECTIONS: return ''
    model = workstream.model(snapshot, items)
    own = [i for i in items if i.get('stage') == stage]
    groups = {key: [i for i in own if i.get('stage_detail', {}).get('type') == key] for key in stage_details.SECTIONS[stage]}
    def group(key, missing, title=None):
        return section(title or stage_details.SECTIONS[stage][key], cards(groups[key], items, model) if groups[key] else empty(missing), key)
    result = ''
    if stage == 'Constitution':
        result += group('constraint', '尚未提供具体约束。请从项目规则中整理适用范围、禁止事项和必须保留的内容。')
        result += group('command', '尚未提供开发或检查命令。命令需要注明执行位置；未执行的命令不能标为通过。')
        result += '<p class="work-caution">命令仅供阅读，不会在看板中执行。项目规则以所引用的原始文件为准。</p>'
    elif stage == 'Align':
        result += group('context', '尚未记录需要解决的问题、使用者或当前困难。')
        brief = next(iter(model['brief']), None)
        content = (f'<article class="stage-reading-card"><h4>{esc(brief["label"])}</h4><p class="stage-record-description">{esc(brief.get("note", ""))}</p>'
                   '<div class="stage-scope-grid"><div><h5>本次范围</h5>' + listing(brief['work']['in_scope'], '尚未记录本次范围')
                   + '</div><div><h5>不在本次范围内</h5>' + listing(brief['work']['out_of_scope'], '尚未记录排除范围')
                   + '</div></div>' + status(brief, model) + selectable(brief, '查看目标与范围来源 →', 'work-link') + '</article>') if brief else empty('尚未提供目标与范围记录。不能根据现有代码推断需求已经确定。')
        result += section('目标与范围', content, 'scope')
        result += group('assumption', '尚未提供假设记录；这不表示所有问题都已核实。', '假设与核实情况')
        decisions = [i for i in own if 'decision' in i and i['decision']['kind'] != 'feedback']
        result += section('确认事项与答复', (links(decisions) + '<p class="stage-help">请查看各条记录的状态；尚待答复的问题保留原答复入口。记录来源一致不表示问题已经获得确认。</p>') if decisions else empty('尚未提供确认事项记录；这不表示需求已经获得确认。'), 'questions')
    elif stage == 'Implement':
        result += group('implementation', '尚未提供实现说明。下方任务和文件仅展示已记录的对应关系。')
        rows = []
        for task in model['slice']:
            files = [model['nodes'][k] for k in task.get('implementation_ids', [])]
            checks = [c for c in model['check'] if task['id'] in c['work']['slice_ids']]
            file_links = ''.join(selectable(f, esc(f['file']), 'work-link') for f in files)
            rows.append('<tr><th scope="row">' + links([task]) + '</th><td>' + tag(task['work']['status'], workstream.EXECUTION[task['work']['status']])
                        + '</td><td>' + (file_links or '尚未关联实现文件') + '</td><td>' + (links(checks) or '尚无验收记录') + '</td></tr>')
        content = ('<div class="stage-table-scroll" tabindex="0" role="region" aria-label="任务与实现文件对应表，可横向滚动"><table class="stage-reading-table"><thead><tr><th scope="col">任务</th><th scope="col">原记录状态</th><th scope="col">实现文件</th><th scope="col">验收记录</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>') if rows else empty('尚未提供任务与实现文件的对应关系。文件存在不能证明任务已经完成。')
        result += section('任务与实现文件', content, 'task-files')
        result += group('test_run', '尚未提供本阶段的测试或运行记录。请记录实际命令、结果和验证范围；未执行的检查要明确标出。')
        issues = [i for i in own if i['view'] == 'impact' or not model['usable'](i)
                  or i.get('stage_detail', {}).get('result') in ('FAIL', 'NOT_RUN', 'UNKNOWN')]
        unfinished = [t for t in model['slice'] if model['slice_issues'](t)]
        content = (links(issues) if issues else '')
        if unfinished:
            content += '<p class="stage-help">未完成或仍需核对的任务</p>' + links(unfinished)
        result += section('待处理问题', content or empty('本阶段没有单独列出问题记录。请同时核对测试结果和“对照验收”，不能据此认定没有问题。'), 'issues')
        result += '<p class="work-caution">测试通过只说明该次运行的结果。需求是否满足，请到“对照验收”逐条核对。</p>'
    elif stage == 'Finish':
        result += group('deliverable', '尚未提供交付物记录。准备好文件、完成测试和实际交付是不同状态。')
        result += group('usage', '尚未提供使用方法。需要说明准备条件、操作步骤和预期结果。')
        result += group('limitation', '尚未提供限制或待办记录。不能据此认定没有遗留问题。')
        result += group('handoff', '尚未记录接续负责人和后续工作。')
        result += group('recovery', '尚未提供恢复或回退方法。处理已有数据前，请先核对项目说明。')
        result += '<p class="work-caution">“有交付记录”仅反映所引用的交付事实，不代表已获发布批准或可以投入生产使用。</p>'
    return '<div class="stage-reading" data-stage-reading="' + stage + '">' + result + '</div>'
