"""Actual HF hashing/multipart adapter; fake HTTP transport; no model network."""
import sys,io,struct,json,hashlib,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'.deps'))
from assembly import Assembly,BufferedAssembly,descriptor
import huggingface_hub
from huggingface_hub import CommitOperationAdd,lfs
import httpx2
ROOT=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def fixture(self):
  h=bytearray(bytes.fromhex(json.loads((ROOT/'plan.json').read_text())['combined_header_hex']));struct.pack_into('<Q',h,114+struct.unpack_from('<Q',h,106)[0]+12,18)
  parts=[];payloads=[]
  # Existing source headers are pinned Maya headers; only synthetic row counts change here.
  for i,rows in enumerate([7,11]):
   source=bytearray(bytes.fromhex(json.loads((ROOT/'plan.json').read_text())['q3_parts'][i]['header_hex']));pos=106;n=struct.unpack_from('<Q',source,pos)[0];pos+=8+n
   struct.pack_into('<Q',source,pos+12,rows);struct.pack_into('<I',source,pos+20,11)
   data=bytes((j+i*31)%256 for j in range(rows*110));whole=bytes(source)+data
   parts.append({'rows':rows,'size':len(whole),'sha256':hashlib.sha256(whole).hexdigest(),'header_hex':source.hex()});payloads.append(whole)
  expected=bytes(h)+b''.join(p[192:] for p in payloads)
  return bytes(h),parts,payloads,expected
 def stream(self):
  header,parts,payloads,expected=self.fixture()
  raw=Assembly(header,parts,lambda i,o,n:payloads[i][o:o+n],block_bytes=113,cache_blocks=1,max_read=4*1024*1024)
  return raw,expected
 def test_actual_hf_hash_and_multipart(self):
  self.assertEqual(huggingface_hub.__version__,'2.2.0');raw,expected=self.stream()
  with BufferedAssembly(raw) as stream:
   op=CommitOperationAdd(path_in_repo='table.gguf',path_or_fileobj=stream)
   self.assertEqual(op.upload_info.sha256.hex(),hashlib.sha256(expected).hexdigest());self.assertEqual(raw.verified_passes,[1,1]);self.assertEqual(stream.tell(),0)
   emitted=[]
   def upload(method,url,**kw):
    emitted.append(b''.join(kw['data']));return httpx2.Response(200,headers={'etag':str(len(emitted))},request=httpx2.Request(method,url))
   urls=[f'https://example.invalid/{i}' for i in range((len(expected)+516)//517)]
   with patch.object(lfs,'http_backoff',side_effect=upload):lfs._upload_parts_iteratively(op,urls,517)
   self.assertEqual(b''.join(emitted),expected);self.assertEqual(stream.tell(),0)
 def test_random_seek_and_boundaries(self):
  raw,expected=self.stream()
  for start,count in [(192+770-4,16),(0,192),(len(expected)-20,20),(192,110),(192+770,110)]:
   raw.seek(start);self.assertEqual(raw.read(count),expected[start:start+count])
  raw.seek(-4,2);self.assertEqual(raw.read(10),expected[-4:]);self.assertEqual(raw.read(10),b'')
  with self.assertRaises(ValueError):raw.seek(-1)
  with self.assertRaises(ValueError):raw.read(raw.max_read+1)
 def test_full_source_sha_rejects_corruption(self):
  h,parts,payloads,expected=self.fixture();bad=bytearray(payloads[1]);bad[-1]^=1;payloads[1]=bytes(bad)
  raw=Assembly(h,parts,lambda i,o,n:payloads[i][o:o+n],block_bytes=113,max_read=4096)
  with self.assertRaisesRegex(RuntimeError,'full SHA256'):raw.read(len(expected))
 def test_short_source_rejected(self):
  h,p,_,_=self.fixture();raw=Assembly(h,p,lambda i,o,n:b'',block_bytes=113,max_read=4096);raw.seek(192)
  with self.assertRaises(OSError):raw.read(1)
if __name__=='__main__':unittest.main()
