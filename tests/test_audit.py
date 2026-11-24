import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('audit',Path(__file__).parents[1]/'src/audit.py'); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class AuditTests(unittest.TestCase):
 def test_missing_list_rejected(self):
  with self.assertRaises(ValueError):m.validate_input({'apps':[]},100)
 def test_wrong_count_rejected(self):
  with self.assertRaises(ValueError):m.validate_input({'apps':[{'id':'x','name':'X','sources':[{'url':'https://example.com'}]}]},100)
 def test_duplicate_ids_rejected(self):
  a={'id':'x','name':'X','sources':[{'url':'https://example.com'}]}
  with self.assertRaises(ValueError):m.validate_input({'apps':[a,a]})
 def test_script_ignored(self):
  p=m.TextExtractor();p.feed('<p>API key</p><script>OAuth2</script><style>Basic</style>');self.assertEqual(p.text(),'API key')
 def test_auth_evidence_offsets(self):
  t='Use OAuth 2.0 to authenticate.';x=m.candidates(t,'auth');self.assertEqual(x[0]['value'],'OAuth2');self.assertIn('OAuth 2.0',x[0]['quote']);self.assertEqual(x[0]['status'],'candidate_not_verified')
 def test_mcp_absence_unknown(self):self.assertEqual(m.candidates('Public REST API.','mcp'),[])
 def test_gates_not_automatically_decided(self):
  values={x['value'] for x in m.candidates('Free trial. Enterprise plan. App review required.','access')};self.assertEqual(len(values),3)
 def test_private_address_rejected(self):
  with patch.object(m.socket,'getaddrinfo',return_value=[(None,None,None,None,('127.0.0.1',443))]):
   with self.assertRaises(ValueError):m.safe_url('https://example.com')
 def test_secret_url_rejected(self):
  with self.assertRaises(ValueError):m.safe_url('https://user:secret@example.com')
 def test_http_rejected(self):
  with self.assertRaises(ValueError):m.safe_url('http://example.com')
 def test_offline_cache_miss_honest(self):
  with tempfile.TemporaryDirectory() as td:self.assertEqual(m.Collector(td,offline=True).fetch('https://example.com')['status'],'offline_cache_miss')
 def test_cache_hash_verified(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);url='https://example.com';(p/'x.txt').write_text('tampered');(p/(m.digest(url.encode())+'.json')).write_text(json.dumps({'status':'ok','snapshot':'x.txt','text_sha256':'nope'}));self.assertEqual(m.Collector(td,offline=True).fetch(url)['status'],'cache_integrity_error')
 def test_html_payload_escape(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'report.html';m.render_report({'apps':[],'danger':'</script><script>alert(1)</script>'},p);self.assertNotIn('</script><script>alert',p.read_text());self.assertIn('\\u003c/script',p.read_text())
 def test_analyzer_no_human_claim(self):
  with tempfile.TemporaryDirectory() as td:
   row=m.analyze({'id':'x','name':'X'},[],td);self.assertFalse(row['verification']['human_checked']);self.assertEqual(row['buildability'],'needs_review');self.assertIn('missing_auth_evidence',row['review_flags'])
if __name__=='__main__':unittest.main()
