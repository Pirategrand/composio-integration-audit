import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
import synthesize as m
class SynthesisTests(unittest.TestCase):
 def test_basic_scoped_not_global(self):
  x=m.contextualize('auth',{'quote':'GitHub Apps and OAuth apps use basic authentication with client ID and client secret.','value':'Basic'});self.assertEqual(x['status'],'scoped_protocol_auth')
 def test_deprecated_not_positive(self):self.assertEqual(m.contextualize('auth',{'quote':'Basic authentication is no longer supported.','value':'Basic'})['status'],'needs_negation_review')
 def test_mcp_no_ownership_inference(self):self.assertEqual(m.contextualize('mcp',{'quote':'Connect an MCP server.','value':'MCP mention'})['status'],'needs_mcp_ownership_review')
 def test_no_patterns_from_candidates(self):self.assertEqual(m.cluster_reviewed({'apps':[{'claims':{'auth':[{'value':'OAuth2'}]}}]})['patterns'],[])
 def test_multi_auth_denominator(self):
  x=m.cluster_reviewed({'apps':[{'reviewed':{'auth':{'value':['OAuth2','API key']}}}]});self.assertEqual(x['field_reviewed_denominators']['auth'],1);self.assertEqual(len(x['patterns']),2)
