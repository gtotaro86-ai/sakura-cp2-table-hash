"""Publication boundaries and model-card metadata; no external writes."""
import sys,json,hashlib,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'.deps'))
from publish import require_runner,safe_public
from card import make_card
from huggingface_hub import ModelCard
HERE=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_work_and_private_or_self_hosted_refused(self):
  for e in [{},{'GITHUB_ACTIONS':'true','REPO_VISIBILITY':'private','RUNNER_ENVIRONMENT':'github-hosted'},{'GITHUB_ACTIONS':'true','REPO_VISIBILITY':'public','RUNNER_ENVIRONMENT':'self-hosted'}]:
   with self.assertRaises(RuntimeError):require_runner(e)
 def test_model_card_metadata_scope_and_languages(self):
  p=json.loads((HERE/'plan.json').read_text());record={'size':p['combined_table_bytes'],'sha256':'a'*64}
  for v in p['variants']:
   card=make_card(p,v,record);parsed=ModelCard(card)
   self.assertEqual(parsed.data.base_model,p['upstream_repo']);self.assertEqual(parsed.data.base_model_relation,'quantized')
   self.assertIn('No full inference test has been performed.',card);self.assertIn('<details>',card);self.assertIn('中文说明',card);self.assertNotIn('experimental',card.lower());self.assertNotIn('<details open',card)
   self.assertEqual(v['main_bytes'],sum(f['size'] for f in v['backbone'])+record['size']);safe_public(card)
 def test_personal_repo_reference_blocked(self):
  for value in ['https://github.com/gtotaro86-ai/private','sakura-cp2-table-hash']:
   with self.assertRaises(RuntimeError):safe_public(value)
if __name__=='__main__':unittest.main()
