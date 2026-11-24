import importlib.util,tempfile,unittest,hashlib,copy
from pathlib import Path
spec=importlib.util.spec_from_file_location('review',Path(__file__).parents[1]/'src/review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ReviewTests(unittest.TestCase):
 def test_sampling_deterministic(self):
  rows=[{'id':str(i),'category':str(i%3),'review_flags':[] }for i in range(30)];self.assertEqual(m.sample(rows,8),m.sample(rows,8));self.assertEqual(len(m.sample(rows,8)),8)
 def test_no_ground_truth_no_accuracy(self):self.assertIsNone(m.score({},[])['accuracy'])
 def test_unknown_counts_as_miss(self):self.assertEqual(m.score({},[{'app_id':'a','field':'auth','value':'OAuth2','reviewer_type':'agent'}])['accuracy'],0)
 def test_agent_not_human_ground_truth(self):self.assertFalse(m.score({('a','auth'):'key'},[{'app_id':'a','field':'auth','value':'key','reviewer_type':'agent'}])['independent_human_ground_truth'])
 def test_review_requires_snapshot_quote(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);raw=b'Use OAuth2.';(root/'s.txt').write_bytes(raw)
   data={'apps':[{'id':'x','sources':[{'url':'https://example.com','status':'ok','snapshot':'s.txt','text_sha256':hashlib.sha256(raw).hexdigest()}],'verification':{'human_checked':False}}],'metrics':{}}
   review={'app_id':'x','field':'auth','reviewer_type':'agent','value':'OAuth2','reason':'Documentation explicitly states this auth method.','source_url':'https://example.com','quote':'Not present'}
   with self.assertRaises(ValueError):m.apply_reviews(copy.deepcopy(data),[review],root,root/'log.jsonl')
   self.assertFalse((root/'log.jsonl').exists());review['quote']='Use OAuth2.'
   out=m.apply_reviews(copy.deepcopy(data),[review],root,root/'log.jsonl');self.assertFalse(out['apps'][0]['verification']['human_checked']);self.assertEqual(out['metrics']['human_reviewed'],0);self.assertTrue((root/'log.jsonl').exists())
if __name__=='__main__':unittest.main()
