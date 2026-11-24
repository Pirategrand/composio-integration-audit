import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
import finalize as m
class FinalizeTests(unittest.TestCase):
 def row(self):return {'id':'a','name':'A','category':'Test','description':'A test fixture','auth_methods':['OAuth2','API key'],'access':{'credential_path':'free_self_serve'},'api':{'styles':['REST'],'breadth':'test'},'mcp':{'status':'not_confirmed'},'verdict':'ready','blocker':'None established','evidence':[{'url':'https://example.com/docs'}],'confidence':'medium'}
 def test_duplicate_id(self):self.assertTrue(any('Duplicate id'in x for x in m.validate([self.row(),self.row()])))
 def test_schema_missing(self):self.assertTrue(m.validate([{}]))
 def test_http_rejected(self):
  r=self.row();r['evidence'][0]['url']='http://example.com';self.assertTrue(m.validate([r]))
 def test_auth_counts_overlap(self):
  s=m.summarize([self.row()]);self.assertEqual(s['auth_support_counts']['OAuth'],1);self.assertEqual(s['auth_support_counts']['API key'],1);self.assertEqual(s['apps'],1)
 def test_no_accuracy_claim(self):self.assertIsNone(m.summarize([self.row()])['independent_accuracy'])
 def test_seeded_sample(self):
  r=self.row();self.assertEqual(m.qa_sample([r],1),m.qa_sample([r],1))
if __name__=='__main__':unittest.main()
