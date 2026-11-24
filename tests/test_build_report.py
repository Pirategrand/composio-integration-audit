import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from build_report import render
import json
class ReportTest(unittest.TestCase):
 def test_full_matrix_and_no_remote_runtime(self):
  root=Path(__file__).resolve().parents[1]
  d=json.loads((root/'output/final/dataset.json').read_text());s=json.loads((root/'data/review/risk-sample.json').read_text());h=render(d,s)
  self.assertEqual(h.count('<article data-verdict='),100)
  self.assertIn('independent human checks remain zero',h)
  self.assertNotIn('<script src=',h)
  self.assertIn('data-verdict="blocked"',h)
 def test_claim_text_escaped(self):
  root=Path(__file__).resolve().parents[1]
  d=json.loads((root/'output/final/dataset.json').read_text());s={'checks':[]};d['apps'][0]['description']='<script>bad</script>'
  self.assertIn('&lt;script&gt;bad&lt;/script&gt;',render(d,s))
if __name__=='__main__':unittest.main()
