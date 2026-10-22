"""Actual native local CAS and actual HF commit payload; no HF/network credentials."""
import hashlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'.deps'))
import hf_xet
from huggingface_hub import HfApi
from huggingface_hub._commit_api import _prepare_commit_payload
from xet_stream import upload_operation,session_config
from test_assembly import Tests as AssemblyFixtures

class Tests(unittest.TestCase):
 def native(self,source,size,digest,validate=lambda:None):
  with tempfile.TemporaryDirectory() as root:
   return upload_operation(HfApi(token=False),'unused/test','table.gguf',source,size,digest,
    validate_source=validate,session=hf_xet.XetSession(config=session_config()),
    connection={'endpoint':'local://'+root+'/cas'})
 def test_actual_native_stream_and_hf_commit_protocol(self):
  raw,expected=AssemblyFixtures().stream()
  def checked():self.assertEqual(raw.verified_passes,[1,1])
  operation=self.native(raw,len(expected),hashlib.sha256(expected).hexdigest(),checked)
  payload=list(_prepare_commit_payload([operation],{},'Native streaming test'))
  self.assertEqual(payload[1],{'key':'lfsFile','value':{'path':'table.gguf','algo':'sha256',
   'oid':hashlib.sha256(expected).hexdigest(),'size':len(expected)}})
  # HF skips the uploaded operation; the rejected legacy batch endpoint is never called.
  with patch('huggingface_hub._commit_api._upload_files') as legacy:
   HfApi(token=False).preupload_lfs_files('unused/test',[operation])
   legacy.assert_not_called()
 def test_wrong_combined_hash_never_returns_publishable_operation(self):
  with self.assertRaisesRegex(RuntimeError,'Combined SHA256'):
   self.native(io.BytesIO(b'hello'),5,'0'*64)
 def test_corrupt_source_validation_aborts_native_commit(self):
  def bad():raise RuntimeError('Source SHA rejected')
  with self.assertRaisesRegex(RuntimeError,'Source SHA rejected'):
   self.native(io.BytesIO(b'hello'),5,hashlib.sha256(b'hello').hexdigest(),bad)
 def test_short_and_excess_source_rejected(self):
  for data,size in [(b'ab',3),(b'abcd',3)]:
   with self.assertRaisesRegex(RuntimeError,'source'):
    self.native(io.BytesIO(data),size,hashlib.sha256(b'abc').hexdigest())
 def test_native_cas_failure_cannot_return_uploaded_operation(self):
  class BrokenSession:
   def new_upload_commit(self,**kw):raise RuntimeError('CAS unavailable')
  with self.assertRaisesRegex(RuntimeError,'CAS unavailable'):
   upload_operation(HfApi(token=False),'unused/test','x',io.BytesIO(b'x'),1,
    hashlib.sha256(b'x').hexdigest(),session=BrokenSession(),connection={})

if __name__=='__main__':unittest.main()
