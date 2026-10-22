"""Release-card provenance, comparison arithmetic, language and privacy gates."""
import json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'deepseek-unsloth/.deps'))
sys.path.insert(0,str(HERE.parent/'deepseek-unsloth'))
from huggingface_hub import ModelCard
from cards import model_card,overview
from publish import safe_public
class Tests(unittest.TestCase):
 def test_deepseek_cards_and_catalog(self):
  p=json.loads((HERE/'plan.json').read_text())
  for v in p['variants']:
   files=[dict(f,sha256=f.get('sha256','a'*64)) for f in v['backbone']+v['tables']]
   card=model_card(p,v,{'files':files},True);m=ModelCard(card)
   self.assertEqual(m.data.base_model,v['source_repo']);self.assertEqual(m.data.license,'mit')
   self.assertIn(f"{v['main_bytes']:,}",card);self.assertIn('No full inference test has been performed.',card)
   self.assertIn('<details>',card);self.assertNotIn('<details open',card);self.assertNotIn('experimental',card.lower());safe_public(card)
  catalog=overview(p,{v['repo']:'a'*40 for v in p['variants']});ModelCard(catalog);safe_public(catalog)
  self.assertEqual(catalog.count('| Verified model-card revision |'),1)
 def test_flash_docs_preserve_license_and_unknown_quality(self):
  targets=json.loads((HERE/'flash-doc-plan.json').read_text())
  self.assertEqual(len(targets),2)
  for t in targets:
   root=HERE/'flash-docs'/t['variant'];card=(root/'README.md').read_text();m=ModelCard(card)
   self.assertEqual(m.data.license_name,'qwen-community-1.0');self.assertEqual(m.data.base_model,'unsloth/Qwen3.8-Flash-Next-GGUF')
   self.assertNotIn('experimental',card.lower());self.assertIn('has not been loaded for inference',card);self.assertIn('<details>',card)
   for name in t['documents']:safe_public((root/name).read_bytes())
if __name__=='__main__':unittest.main()
