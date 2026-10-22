"""Failure injection for independent publication checks. No network."""
import copy,json,unittest
from pathlib import Path
from card import make_card
from verify_release import HERE,verify_variant,fixtures
class Tests(unittest.TestCase):
 def setUp(self):
  self.plan=json.loads((HERE/'plan.json').read_text());self.v=self.plan['variants'][0]
  import hashlib
  record={'size':self.plan['combined_table_bytes'],'sha256':'a'*64,'source_full_sha256_verified_passes':[2,2]}
  self.files=self.v['backbone']+[{'path':self.v['table_path'],'size':record['size'],'sha256':record['sha256']}]
  self.info={'sha':'b'*40,'siblings':[{'rfilename':f['path'],'size':f['size'],'lfs':{'sha256':f['sha256']}} for f in self.files]}
  self.card=make_card(self.plan,self.v,record)
  self.manifest={'complete':True,'identity':{'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()},'full_inference_test_performed':False,'gpu_runtime_executed':False,'table_build':record,'files':self.files,'main_bytes':self.v['main_bytes']}
  q=fixtures();samples=json.loads((HERE/'evidence/probe-result.json').read_text())['samples']
  self.ranges={0:bytes.fromhex(self.plan['combined_header_hex'])}
  for s in samples:self.ranges[192+s['combined_row_start']*110]=q[f"layer{[1,14].index(s['layer_id'])}-row{s['row_start']}.q3"]
 def read(self,url):return self.card.encode() if url.endswith('/README.md') else json.dumps(self.manifest).encode()
 def rr(self,url,start,count,total,journal,limit):
  self.assertEqual(total,self.plan['combined_table_bytes']);self.assertEqual(limit,1_000_000);return self.ranges[start]
 def run_check(self):return verify_variant(self.plan,self.v,self.info,self.read,self.rr)
 def test_valid_release(self):
  r=self.run_check();self.assertEqual(r['real_rows_verified'],192);self.assertEqual(r['model_range_bytes'],21312)
 def test_body_hash_mismatch_rejected(self):
  self.info['siblings'][1]['lfs']['sha256']='c'*64
  with self.assertRaisesRegex(RuntimeError,'SHA256'):self.run_check()
 def test_wrong_boundary_payload_rejected(self):
  offset=192+384006168*110;d=bytearray(self.ranges[offset]);d[0]^=1;self.ranges[offset]=bytes(d)
  with self.assertRaisesRegex(RuntimeError,'real-row bytes'):self.run_check()
 def test_private_link_rejected(self):
  self.card+='\nhttps://github.com/gtotaro86-ai/private\n'
  with self.assertRaisesRegex(RuntimeError,'Forbidden'):self.run_check()
 def test_unfinished_release_rejected(self):
  self.manifest['complete']=False
  with self.assertRaisesRegex(RuntimeError,'Incomplete'):self.run_check()
if __name__=='__main__':unittest.main()
