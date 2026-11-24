import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
import discover
class DiscoveryTests(unittest.TestCase):
 def test_lookalike_not_official(self):
  r=discover.score_candidate({'name':'GitHub','official_domains':['github.com']},'auth',{'url':'https://github.com.attacker.test/auth','title':'GitHub authentication','snippet':''});self.assertFalse(r['official_domain_confirmed'])
 def test_primary_domain(self):
  r=discover.score_candidate({'name':'GitHub','official_domains':['github.com']},'auth',{'url':'https://docs.github.com/authentication','title':'GitHub authentication','snippet':''});self.assertTrue(r['official_domain_confirmed'])
 def test_no_domain_no_upgrade(self):
  r=discover.score_candidate({'name':'Example'},'api',{'url':'https://example.com/api','title':'Example API docs','snippet':''});self.assertFalse(r['official_domain_confirmed'])
 def test_no_results_honest(self):
  class Empty:
   def search(self,*args):return {'status':'no_results','results':[]}
  app,logs=discover.discover_app(Empty(),{'id':'a','name':'Example','official_domains':['example.com']});self.assertEqual(app['sources'],[]);self.assertEqual(len(logs),4)
