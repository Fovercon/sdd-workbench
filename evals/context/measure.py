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


def measure(host,path):
    counts=Counter();tools=Counter();sizes=Counter();calls={};seen_reads=Counter();models=set();largest=[]
    usage_count=missing_input=missing_usage=repeated=malformed=nontext=0;inputs=[];outputs=[];cache=[];native_totals=Counter();digest=hashlib.sha256();valid_utf8=True
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
    return {'host':host,'analyzer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'events_sha256':digest.hexdigest(),'raw_stream_valid_utf8':valid_utf8,'malformed_lines':malformed,
            'native_completion_event_observed':complete,'completed_usage_events':usage_count,'completed_without_usage':missing_usage,
            'usage_events_with_input':len(inputs),'usage_events_missing_input_fields':missing_input,'complete_input_usage':missing_usage==0 and missing_input==0 and usage_count>0,
            'input_usage_granularity':'assistant-message'if host=='pi'else'turn-aggregate',
            'reported_input_sum':sum(inputs)if inputs else None,'reported_input_event_peak':max(inputs)if inputs else None,
            'reported_request_input_peak':max(inputs)if inputs and host=='pi'else None,
            'reported_output_sum':sum(outputs)if outputs else None,'reported_cache_read_sum':sum(cache)if cache else None,
            'native_token_totals':dict(native_totals),'models_observed':[{'provider':a,'model':b}for a,b in sorted(models,key=str)],
            'tool_calls':dict(tools),'repeated_identical_read_requests':repeated,'delivered_tool_text_utf8_bytes':sum(sizes.values()),
            'tool_text_bytes_by_heuristic_category':dict(sizes),'largest_tool_outputs':largest,'nontext_blocks_not_tokenized':nontext,
            'limits':['Pi request peak is observed assistant-message input, not a measured resident window or host capacity. Codex turn aggregates do not expose a per-request peak.',
                      'Cumulative input includes replay/cache; Pi sums separate input/cache fields, Codex input_tokens already includes cache.',
                      'Missing usage is unknown; incomplete sums and peaks cover only reported requests.',
                      'Tool bytes are delivered text, not tokens; categories are heuristics, and repeated reads may be necessary after changes.',
                      'No billing, quality, comparative advantage or causal token attribution is inferred.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',choices=['pi','codex'],required=True);p.add_argument('--events',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=measure(a.host,a.events);Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k]for k in ['completed_usage_events','reported_input_sum','reported_request_input_peak','delivered_tool_text_utf8_bytes']},ensure_ascii=True))
