"""Fixed SDD vocabulary, with stage claims bound to ordinary evidence records."""

STAGES = {
    'Constitution': '项目规则',
    'Align': '需求澄清',
    'Spec': '需求规格',
    'Plan': '方案设计',
    'Tasks': '任务拆分',
    'Implement': '开发与测试',
    'Converge': '对照验收',
    'Finish': '交付收尾',
}


def validate(snapshot):
    for item in snapshot['items']:
        if 'stage' in item and item['stage'] not in STAGES:
            raise ValueError('Item stage must use a canonical SDD stage name')
    if 'lifecycle' not in snapshot:
        return
    model = snapshot['lifecycle']
    if not isinstance(model, dict) or set(model) != {'current_stage', 'stage_items'}:
        raise ValueError('lifecycle must contain exactly current_stage and stage_items')
    current, bindings = model['current_stage'], model['stage_items']
    if not isinstance(current, str) or current not in STAGES:
        raise ValueError('current_stage must use a canonical SDD stage name')
    if not isinstance(bindings, dict) or current not in bindings:
        raise ValueError('stage_items must bind the current stage')
    items = {item['id']: item for item in snapshot['items']}
    for stage, key in bindings.items():
        if stage not in STAGES or not isinstance(key, str):
            raise ValueError('stage_items must map canonical stages to item IDs')
        item = items.get(key)
        if (item is None or item['view'] != 'progress' or item.get('stage') != stage
                or not item.get('sources')):
            raise ValueError('Every stage binding needs a source-backed progress item with the same stage')
    if any(item.get('stage') not in bindings for item in snapshot['items'] if 'stage' in item):
        raise ValueError('Items cannot claim a stage without a stage_items binding')


def stage_status(snapshot, items):
    model = snapshot['lifecycle']
    by_id = {item['id']: item for item in items}
    order = list(STAGES)
    current_index = order.index(model['current_stage'])
    result = []
    for index, (name, subtitle) in enumerate(STAGES.items()):
        item = by_id.get(model['stage_items'].get(name))
        if item is None:
            status, text = 'NOT_STARTED', '未开始'
        elif item['effective_state'] in ('STALE', 'UNKNOWN'):
            status, text = item['effective_state'], '来源已变化' if item['effective_state'] == 'STALE' else '依据待核对'
        elif index > current_index:
            status, text = 'REVISIT', '待重新核对'
        elif name == model['current_stage']:
            status, text = 'CURRENT', '当前阶段'
        elif item['effective_state'] == 'SATISFIED':
            status, text = 'SATISFIED', '已有阶段证据'
        else:
            status, text = item['effective_state'], '仍有待办'
        result.append({'name': name, 'subtitle': subtitle, 'item': item,
                       'status': status, 'text': text})
    return result
