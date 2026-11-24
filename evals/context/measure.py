#!/usr/bin/env python3
"""Read native events without printing transcripts or estimating tokens from bytes."""
import argparse
from collections import Counter
import hashlib,json,re
from pathlib import Path


def category(tool,args):
    subject=args.get('path',args.get('command',''))
    if 'project_view.py describe' in subject:return 'authoring_contract'
    if 'project_view.py check' in subject:return 'source_check'
    if re.search(r'project_view.py (render|update)',subject):return 'renderer_result'
    if re.search(r'view[-/\w]*\/(index.html|view.md|snapshot.json|receipt.json)',subject):return 'generated_inspection'
    if '/scripts/'in subject or 'scripts/project_view_lib'in subject or ('runtime' in subject and re.search(r'\b(cat|sed|head|grep|rg)\b|read_text',subject) and '.py' in subject):
        if tool=='read'or re.search(r'\b(cat|sed|head|grep|rg)\b|read_text',subject):return 'method_code'
    if '/references/'in subject or 'references/'in subject or subject.endswith('/SKILL.md'):return 'method_reference'
    return 'source_or_other'


UNITTEST_OK_ROW = re.compile(r'test\w* \([^()\r\n]+\) \.\.\. ok\r?\n')
UNITTEST_SUMMARY = re.compile(r'Ran ([0-9]+) tests in [0-9]+(?:\.[0-9]+)?s\r?\n')


def passing_unittest_lists(text):
    """Yield the delivered UTF-8 rows preceding a complete verbose success footer."""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        summary = UNITTEST_SUMMARY.fullmatch(line)
        if not summary or i < 4 or i + 2 >= len(lines):
            continue
        end = i - 2
        if (lines[end] not in ('\n', '\r\n') or lines[i - 1].rstrip('\r\n') != '-' * 70
                or lines[i + 1] not in ('\n', '\r\n') or lines[i + 2].rstrip('\r\n') != 'OK'):
            continue
        start = end
        while start and UNITTEST_OK_ROW.fullmatch(lines[start - 1]):
            start -= 1
        count = end - start
        if count >= 2 and str(count) == summary.group(1):
            yield ''.join(lines[start:end]).encode('utf-8'), count


def record_unittest_lists(content, end_line, first_ends, stats):
    for item in content:
        if item.get('type') != 'text':
            continue
        for rows, count in passing_unittest_lists(item.get('text', '')):
            size = len(rows)
            stats['complete_lists'] += 1
            stats['list_utf8_bytes'] += size
            first = first_ends.setdefault(hashlib.sha256(rows).digest(), end_line)
            if first == end_line:
                continue
            stats['repeated_lists'] += 1
            stats['repeated_list_utf8_bytes'] += size
            if len(stats['witnesses']) < 8:
                stats['witnesses'].append({'first_end_line': first, 'repeat_end_line': end_line,
                                           'tests': count, 'utf8_bytes': size})


class ReferenceTiming:
    """Locate exact reference text in successful Pi tool returns."""

    def __init__(self, path, extra_tools=()):
        raw = Path(path).read_bytes()
        body = raw[:-2] if raw.endswith(b'\r\n') else raw.removesuffix(b'\n')
        self.text = body.decode('utf-8')
        if not self.text.strip():
            raise ValueError('reference text must contain non-whitespace content')
        self.report = {'source_sha256': hashlib.sha256(raw).hexdigest(), 'matched_text_utf8_bytes': len(body),
                       'matched_calls': 0, 'first_return': None}
        self.tools = {'read', 'bash', *extra_tools}
        if extra_tools:
            self.report['tools_considered'] = sorted(self.tools)
        self.request = 0
        self.issuers = {}
        self.pending = {}
        self.extra_ends = Counter()

    def observe(self, event, line):
        kind = event.get('type')
        if kind == 'message_end' and event.get('message', {}).get('role') == 'assistant':
            self.request += 1
            unissued = self.issuers
            self.issuers = {}
            for block in event['message'].get('content', []):
                if isinstance(block, dict) and block.get('type') == 'toolCall' and isinstance(block.get('id'), str):
                    call_id = block['id']
                    duplicate = call_id in unissued or call_id in self.issuers
                    self.issuers[call_id] = None if duplicate else (block.get('name'), self.request, line)
            return
        call_id = event.get('toolCallId')
        if not isinstance(call_id, str) or not call_id:
            return
        tool = event.get('toolName')
        if kind == 'tool_execution_start':
            declaration = self.issuers.pop(call_id, None)
            issuer = declaration[1:] if declaration and declaration[0] in (None, tool) else (None, None)
            if call_id in self.pending:
                self.pending[call_id] = None
                self.extra_ends[call_id] += 1
            else:
                self.pending[call_id] = (tool, line, issuer)
        elif kind == 'tool_execution_end':
            if self.extra_ends[call_id]:
                self.extra_ends[call_id] -= 1
                return
            start = self.pending.pop(call_id, None)
            result = event.get('result') or {}
            if tool not in self.tools or not start or start[0] != tool:
                return
            if event.get('isError') is not False or result.get('isError'):
                return
            blocks = (block for block in result.get('content', []) if isinstance(block, dict))
            texts = (block.get('text') for block in blocks if block.get('type') == 'text')
            if not any(isinstance(text, str) and self.text in text for text in texts):
                return
            self.report['matched_calls'] += 1
            if self.report['first_return'] is None:
                request, issuer_line = start[2]
                self.report['first_return'] = {'request': request, 'assistant_end_line': issuer_line,
                                               'start_line': start[1], 'end_line': line, 'tool': tool}


def measure(host,path,reference_text=None,reference_tools=()):
    if reference_tools and reference_text is None:
        raise ValueError('--reference-tool requires --reference-text')
    if reference_text is not None and host != 'pi':
        raise ValueError('reference-text timing requires native Pi tool events')
    reference = ReferenceTiming(reference_text, reference_tools) if reference_text is not None else None
    counts=Counter();tools=Counter();sizes=Counter();calls={};seen_reads=Counter();models=set();largest=[]
    usage_count=missing_input=missing_usage=repeated=malformed=nontext=0;inputs=[];outputs=[];cache=[];native_totals=Counter();digest=hashlib.sha256();valid_utf8=True
    first_list_ends = {}
    observed_bash_ids = set()
    verbose_lists = {'complete_lists': 0, 'list_utf8_bytes': 0, 'repeated_lists': 0,
                     'repeated_list_utf8_bytes': 0, 'witnesses': []}
    with Path(path).open('rb')as stream:
        for line_no,raw in enumerate(stream,1):
            digest.update(raw)
            if not raw.strip():continue
            try:line=raw.decode('utf-8')
            except UnicodeDecodeError:valid_utf8=False;malformed+=1;continue
            try:e=json.loads(line)
            except ValueError:malformed+=1;continue
            if not isinstance(e,dict):malformed+=1;continue
            kind=e.get('type');counts[kind]+=1;u=None
            if reference is not None:
                reference.observe(e, line_no)
            if host=='pi'and kind=='message_end'and e.get('message',{}).get('role')=='assistant':
                message=e['message'];u=message.get('usage');models.add((message.get('provider'),message.get('model')))
            elif host=='codex'and kind=='turn.completed':u=e.get('usage')
            if (host=='pi'and kind=='message_end'and e.get('message',{}).get('role')=='assistant')or(host=='codex'and kind=='turn.completed'):
                if not isinstance(u,dict):missing_usage+=1
                else:
                    usage_count+=1
                    for key,value in u.items():
                        if type(value)is int and value>=0:native_totals[key]+=value
                    keys=['input','cacheRead','cacheWrite']if host=='pi'else['input_tokens']
                    if all(type(u.get(k))is int and u[k]>=0 for k in keys):inputs.append(sum(u[k]for k in keys))
                    else:missing_input+=1
                    output=u.get('output'if host=='pi'else'output_tokens')
                    if type(output)is int and output>=0:outputs.append(output)
                    cached=u.get('cacheRead'if host=='pi'else'cached_input_tokens')
                    if type(cached)is int and cached>=0:cache.append(cached)
            if host=='pi'and kind=='tool_execution_start':
                tool=e.get('toolName');args=e.get('args',{});tools[tool]+=1
                if not isinstance(args,dict):args={}
                calls[e.get('toolCallId')]={'tool':tool,'category':category(tool,args),'line':line_no}
                if tool=='read':
                    signature=json.dumps(args,sort_keys=True);repeated+=seen_reads[signature]>0;seen_reads[signature]+=1
            if host=='pi'and kind=='tool_execution_end':
                call=calls.get(e.get('toolCallId'),{'tool':e.get('toolName'),'category':'unmatched_tool','line':line_no})
                content=e.get('result',{}).get('content',[]);n=0
                call_id = e.get('toolCallId')
                if (isinstance(call_id, str) and call_id and call_id in calls
                        and call['tool'] == e.get('toolName') == 'bash' and call_id not in observed_bash_ids):
                    observed_bash_ids.add(call_id)
                    record_unittest_lists(content, line_no, first_list_ends, verbose_lists)
                for item in content:
                    if item.get('type')=='text':n+=len(item.get('text','').encode('utf-8'))
                    else:nontext+=1
                sizes[call['category']]+=n
                largest.append({'event_line':line_no,'start_line':call['line'],'tool':call['tool'],'category':call['category'],'utf8_bytes':n})
                largest=sorted(largest,key=lambda x:x['utf8_bytes'],reverse=True)[:8]
            if host=='codex'and kind=='item.completed':
                item=e.get('item',{})
                if item.get('type')=='command_execution':tools['command_execution']+=1;sizes['source_or_other']+=len(item.get('aggregated_output','').encode('utf-8'))
    complete=counts['agent_end']>0 if host=='pi'else counts['turn.completed']>0
    return {**({'pi_reference_text': reference.report} if reference is not None else {}),
            'host':host,'analyzer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'events_sha256':digest.hexdigest(),'raw_stream_valid_utf8':valid_utf8,'malformed_lines':malformed,
            'native_completion_event_observed':complete,'completed_usage_events':usage_count,'completed_without_usage':missing_usage,
            'usage_events_with_input':len(inputs),'usage_events_missing_input_fields':missing_input,'complete_input_usage':missing_usage==0 and missing_input==0 and usage_count>0,
            'input_usage_granularity':'assistant-message'if host=='pi'else'turn-aggregate',
            'reported_input_sum':sum(inputs)if inputs else None,'reported_input_event_peak':max(inputs)if inputs else None,
            'reported_request_input_peak':max(inputs)if inputs and host=='pi'else None,
            'reported_output_sum':sum(outputs)if outputs else None,'reported_cache_read_sum':sum(cache)if cache else None,
            'native_token_totals':dict(native_totals),'models_observed':[{'provider':a,'model':b}for a,b in sorted(models,key=str)],
            'pi_unittest_verbose_lists': verbose_lists if host == 'pi' else None,
            'tool_calls':dict(tools),'repeated_identical_read_requests':repeated,'delivered_tool_text_utf8_bytes':sum(sizes.values()),
            'tool_text_bytes_by_heuristic_category':dict(sizes),'largest_tool_outputs':largest,'nontext_blocks_not_tokenized':nontext,
            'limits':['Pi request peak is observed assistant-message input, not a measured resident window or host capacity. Codex turn aggregates do not expose a per-request peak.',
                      'Cumulative input includes replay/cache; Pi sums separate input/cache fields, Codex input_tokens already includes cache.',
                      'Missing usage is unknown; incomplete sums and peaks cover only reported requests.',
                      'Tool bytes are delivered text, not tokens; categories are heuristics, and repeated reads may be necessary after changes.',
                      'No billing, quality, comparative advantage or causal token attribution is inferred.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',choices=['pi','codex'],required=True);p.add_argument('--events',required=True);p.add_argument('--output',required=True)
    p.add_argument('--reference-text', type=Path, help='Pi only: locate an exact frozen UTF-8 reference in read/bash returns')
    p.add_argument('--reference-tool', action='append', default=[],
                   help='also check successful returns from this named Pi tool (repeatable)')
    a=p.parse_args()
    try:
        result=measure(a.host,a.events,a.reference_text,a.reference_tool)
    except (OSError, ValueError) as exc:
        p.error(str(exc))
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k]for k in ['completed_usage_events','reported_input_sum','reported_request_input_peak','delivered_tool_text_utf8_bytes']},ensure_ascii=True))
