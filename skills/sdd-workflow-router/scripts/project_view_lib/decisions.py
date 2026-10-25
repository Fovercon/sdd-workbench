"""Human questions and version-bound response drafts; never an approval engine."""
KINDS = {'approval', 'choice', 'input', 'feedback'}
EFFECTS = {'APPROVE', 'REQUEST_CHANGES', 'DEFER', 'ANSWER'}
SCHEMA = 'sdd-decision-response/v1'


def validate(snapshot):
    items = {i['id']: i for i in snapshot['items']}
    ids = set()
    for item in snapshot['items']:
        if 'decision' in item and 'decision_ref' in item:
            raise ValueError('Use decision or decision_ref, not both')
        if 'decision_ref' in item:
            target = items.get(item['decision_ref']) if isinstance(item['decision_ref'], str) else None
            if target is None or target is item or 'decision' not in target:
                raise ValueError('decision_ref must identify another item carrying a decision')
        if 'decision' not in item:
            continue
        question = item['decision']
        if not isinstance(question, dict) or question.get('kind') not in KINDS:
            raise ValueError('decision needs kind approval, choice, input or feedback')
        for key in ('id', 'prompt', 'owner', 'scope'):
            if not isinstance(question.get(key), str) or not question[key].strip():
                raise ValueError(f'decision {key} must be a nonempty string')
        if 'subject' in question and (not isinstance(question['subject'], str) or not question['subject'].strip()):
            raise ValueError('decision subject must be a nonempty string')
        if question['id'] in ids:
            raise ValueError('Decision IDs must be unique')
        ids.add(question['id'])
        if not item.get('sources'):
            raise ValueError('A decision needs the sources of its exact subject')
        options = question.get('options', [])
        if not isinstance(options, list) or (question['kind'] != 'input' and not 2 <= len(options) <= 8):
            raise ValueError('Approval/choice decisions need 2 to 8 explicit options')
        if question['kind'] == 'input' and options:
            raise ValueError('An input decision uses free text, not options')
        option_ids = set()
        for option in options:
            if not isinstance(option, dict):
                raise ValueError('Decision options must be objects')
            for key in ('id', 'label', 'description'):
                if not isinstance(option.get(key), str) or not option[key].strip():
                    raise ValueError(f'Decision option {key} must be a nonempty string')
            if option['id'] in option_ids or option.get('effect') not in EFFECTS:
                raise ValueError('Decision options need unique IDs and an explicit effect')
            option_ids.add(option['id'])
            if 'requires_note' in option and type(option['requires_note']) is not bool:
                raise ValueError('requires_note must be boolean')
            if question['kind'] != 'approval' and option['effect'] == 'APPROVE':
                raise ValueError('Only an explicit approval question can offer APPROVE')


def label(item):
    if item.get('decision', {}).get('kind') == 'feedback' and item['effective_state'] in ('GAP', 'SATISFIED', 'PENDING_HUMAN'):
        return '可提意见'
    if item['effective_state'] != 'PENDING_HUMAN':
        return None
    question = item.get('decision', {})
    if question.get('kind') == 'input':
        return '待补充信息'
    if question.get('kind') == 'choice':
        return '待你选择'
    if item.get('stage') == 'Plan':
        return '待设计评审'
    if item.get('stage') == 'Spec':
        return '待需求确认'
    if item.get('stage') == 'Constitution':
        return '待规则确认'
    return '待确认/审批'


def validate_response(snapshot, items, snapshot_sha256, response):
    if not isinstance(response, dict) or response.get('schema') != SCHEMA:
        raise ValueError('Unsupported decision response schema')
    if response.get('project_id') != snapshot['project_id'] or response.get('snapshot_sha256') != snapshot_sha256:
        raise ValueError('Response belongs to a different project or board version')
    item = next((i for i in items if i['id'] == response.get('item_id')), None)
    if item is None or 'decision' not in item:
        raise ValueError('Response does not identify a concrete decision')
    question = item['decision']
    if response.get('decision_id') != question['id']:
        raise ValueError('Response decision identity differs')
    related = [item, *(i for i in items if i.get('decision_ref') == item['id'])]
    if any(i['freshness'] != 'CURRENT' for i in related):
        raise ValueError('Decision sources changed or are missing; re-read before asking again')
    allowed = ('GAP', 'SATISFIED', 'PENDING_HUMAN') if question['kind'] == 'feedback' else ('PENDING_HUMAN',)
    if item['effective_state'] not in allowed:
        raise ValueError('Decision is no longer pending in this baseline')
    answer, note = response.get('answer'), response.get('note', '')
    if not isinstance(note, str) or len(note) > 12000:
        raise ValueError('Response note must be text up to 12000 characters')
    if question['kind'] == 'input':
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 12000:
            raise ValueError('Input decisions require a nonempty answer')
        effect = 'ANSWER'
    else:
        option = next((o for o in question['options'] if o['id'] == answer), None)
        if option is None:
            raise ValueError('Choose one of the decision options')
        if option.get('requires_note') and not note.strip():
            raise ValueError('This option requires a concrete note')
        effect = option['effect']
    return {'status': 'RESPONSE_VALIDATED', 'decision_id': question['id'], 'item_id': item['id'],
            'kind': question['kind'], 'scope': question['scope'], 'answer': answer, 'note': note,
            'effect': effect, 'requires_human_authority': True, 'writes': False}
