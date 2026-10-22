"""Real native local CAS, corruption aborts, per-target hashes; no model/network."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'deepseek-unsloth/.deps'))
import hf_xet
from huggingface_hub import HfApi
from huggingface_hub._commit_api import _prepare_commit_payload
from streaming import operations,session_config
from metadata import table
HERE=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def fixture(self):
  p=json.loads((HERE/'plan.json').read_text());h=bytes.fromhex(p['combined_source']['header_hex'])
  raw=h+bytes(range(256))*4
  source={'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'header_hex':h.hex(),'read':lambda o,n:raw[o:o+n]}
  targets=[]
  for k,rs in p['new_table_groups'].items():
   v=next(v for v in p['variants'] if v['repo']==rs[0]);f=v['tables'][0]
   targets.append({'repo':'unused/test','path':k+'.gguf','size':len(raw),'header_hex':f['header_hex']})
  return raw,source,targets
 def run_native(self,source,targets):
  with tempfile.TemporaryDirectory() as root:
   return operations(HfApi(token=False),source,targets,None,lambda:hf_xet.XetSession(config=session_config()),{'endpoint':'local://'+root+'/cas'})
 def test_all_four_headers_and_native_outputs(self):
  raw,source,targets=self.fixture();outputs=self.run_native(source,targets)
  self.assertEqual(len(outputs),4);self.assertEqual(len({x[2]['sha256'] for x in outputs}),4)
  for target,op,proof in outputs:
   expected=bytes.fromhex(target['header_hex'])+raw[192:]
   self.assertEqual(proof['sha256'],hashlib.sha256(expected).hexdigest())
   payload=list(_prepare_commit_payload([op],{},'test'))[1]
   self.assertEqual(payload['value']['oid'],proof['sha256']);self.assertEqual(payload['value']['size'],len(raw))
 def test_corrupt_source_cannot_return_publishable_operations(self):
  raw,s,t=self.fixture();s['sha256']='0'*64
  with self.assertRaisesRegex(RuntimeError,'source SHA256'):self.run_native(s,t)
 def test_header_and_short_source_fail(self):
  raw,s,t=self.fixture();s['read']=lambda o,n:b'\0'*n
  with self.assertRaisesRegex(RuntimeError,'header'):self.run_native(s,t)
  raw,s,t=self.fixture();s['read']=lambda o,n:raw[o:o+n-1]
  with self.assertRaisesRegex(RuntimeError,'short'):self.run_native(s,t)
 def test_frozen_headers_and_totals(self):
  p=json.loads((HERE/'plan.json').read_text())
  for v in p['variants']:
   self.assertEqual(v['main_bytes'],sum(f['size'] for f in v['backbone']+v['tables']))
   for f in v['tables']:
    t=table(bytes.fromhex(f['header_hex']));self.assertEqual(t['type'],11)
    self.assertEqual(f['size'],192+t['rows']*110)
  self.assertEqual(len(p['variants']),11)
if __name__=='__main__':unittest.main()
