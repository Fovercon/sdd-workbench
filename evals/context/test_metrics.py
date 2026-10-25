from pathlib import Path
import json,tempfile,unittest
from measure import measure

class MetricsTests(unittest.TestCase):
    def run_events(self,host,events):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'events.jsonl';p.write_text('\n'.join(json.dumps(e)for e in events),encoding='utf-8');return measure(host,p)
    def test_pi_counts_completed_usage_and_separates_sum_peak_cache(self):
        def end(n,c):return {'type':'message_end','message':{'role':'assistant','provider':'deepseek','model':'deepseek-flash','usage':{'input':n,'cacheRead':c,'cacheWrite':0,'output':5,'reasoning':2}}}
        r=self.run_events('pi',[{'type':'message_update','usage':{'input':999}},end(10,30),end(20,40),{'type':'agent_end'}])
        self.assertEqual((r['reported_input_sum'],r['reported_request_input_peak']),(100,60));self.assertEqual(r['reported_cache_read_sum'],70)
        self.assertEqual(r['reported_output_sum'],10);self.assertEqual(r['native_token_totals']['reasoning'],4)
    def test_codex_input_does_not_double_count_cached_subset(self):
        r=self.run_events('codex',[{'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':80,'output_tokens':7}}])
        self.assertIsNone(r['reported_request_input_peak']);self.assertEqual(r['reported_input_event_peak'],100);self.assertEqual(r['reported_input_sum'],100);self.assertEqual(r['input_usage_granularity'],'turn-aggregate')
    def test_tool_result_counted_once_not_again_in_message_end(self):
        start={'type':'tool_execution_start','toolCallId':'a','toolName':'read','args':{'path':'/runtime/references/x.md'}}
        end={'type':'tool_execution_end','toolCallId':'a','result':{'content':[{'type':'text','text':'中文'}]}}
        r=self.run_events('pi',[start,end,{**start,'toolCallId':'b'},{'type':'message_end','message':{'role':'toolResult','content':[{'type':'text','text':'中文'}]}}])
        self.assertEqual(r['delivered_tool_text_utf8_bytes'],6);self.assertEqual(r['repeated_identical_read_requests'],1)
    def test_missing_usage_fields_are_unknown(self):
        r=self.run_events('pi',[{'type':'message_end','message':{'role':'assistant','usage':{'input':4}}}])
        self.assertFalse(r['complete_input_usage']);self.assertIsNone(r['reported_request_input_peak']);self.assertFalse(r['native_completion_event_observed'])
    def test_native_completion_does_not_invent_missing_usage(self):
        r=self.run_events('pi',[{'type':'message_end','message':{'role':'assistant'}},{'type':'agent_end'}])
        self.assertTrue(r['native_completion_event_observed']);self.assertFalse(r['complete_input_usage']);self.assertIsNone(r['reported_input_sum'])
    def test_no_transcript_text_is_exposed(self):
        secret='PRIVATE_CONTENT_NOT_A_METRIC'
        r=self.run_events('pi',[{'type':'tool_execution_start','toolCallId':'a','toolName':'bash','args':{'command':secret}}, {'type':'tool_execution_end','toolCallId':'a','result':{'content':[{'type':'text','text':secret}]}}])
        self.assertNotIn(secret,json.dumps(r));self.assertEqual(r['delivered_tool_text_utf8_bytes'],len(secret))
    def test_invalid_lines_are_recorded(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'events';p.write_bytes(b'not-json\n\xff\n');r=measure('pi',p)
            self.assertEqual(r['malformed_lines'],2);self.assertFalse(r['raw_stream_valid_utf8'])
