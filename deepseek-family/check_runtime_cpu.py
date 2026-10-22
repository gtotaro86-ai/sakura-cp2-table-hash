"""Offline parity of the port's actual scalar decoder against pinned GGML."""
import argparse,ctypes,hashlib,json,subprocess
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--maya',required=True,type=Path);ap.add_argument('--library',required=True,type=Path);args=ap.parse_args()
 root=args.maya.resolve();out=HERE/'cpu-check';out.mkdir(exist_ok=True)
 wrapper=out/'wrapper.cpp';wrapper.write_text('#include "'+str(root/'src/ds4/ds4_q3k.cuh')+'"\n#include <cstddef>\nextern "C" void decode(const uint8_t* s,float* d,size_t n){for(size_t r=0;r<n;++r)for(int i=0;i<256;++i)d[r*256+i]=strata::ds4::q3k_value(s+r*110,i);}\n')
 libpath=out/'decoder.so';subprocess.run(['g++','-std=c++17','-O2','-ffp-contract=off','-shared','-fPIC',str(wrapper),'-o',str(libpath)],check=True)
 lib=ctypes.CDLL(str(libpath));ref=ctypes.CDLL(str(args.library.resolve()))
 lib.decode.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t];ref.dequantize_row_q3_K.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int64]
 def check(raw):
  n=len(raw)//110;src=ctypes.create_string_buffer(raw);a=np.empty((n,256),np.float32);b=np.empty_like(a)
  lib.decode(src,a.ctypes.data,n);ref.dequantize_row_q3_K(src,b.ctypes.data,b.size)
  if a.tobytes()!=b.tobytes():raise RuntimeError('Scalar port differs from reference')
  return n
 fixtures=json.loads((HERE.parent/'deepseek-unsloth/fixtures.json').read_text())
 import zlib,base64
 # prepare_fixtures.py has already restored the reviewed tiny fixtures.
 real=0
 for f in sorted((HERE.parent/'deepseek-unsloth/evidence').glob('layer*-row*.q3')):real+=check(f.read_bytes())
 if real!=192:raise RuntimeError('192 real fixture rows required')
 rng=np.random.default_rng(20261022);raw=rng.integers(0,256,(4096,110),dtype=np.uint8)
 bits=(rng.integers(0,65536,4096,dtype=np.uint16)&np.uint16(0x83ff))|np.uint16(0x3c00);raw[:,108:]=bits.astype('<u2').view('u1').reshape(-1,2)
 random_rows=check(raw.tobytes());scales=np.arange(65536,dtype=np.uint16);scales=scales[(scales&0x7c00)!=0x7c00];rows=np.tile(raw[0],(len(scales),1));rows[:,108:]=scales.astype('<u2').view('u1').reshape(-1,2);scale_rows=check(rows.tobytes())
 result={'maya_revision':'ffe2e5e53fd5254e7f3492a20e8ad2b51b26a197','patch_sha256':hashlib.sha256((HERE/'maya-v1.1.22-q3.patch').read_bytes()).hexdigest(),'reference_revision':'c7fc5094179bf8a9c73c18593db714f8da41a402','real_rows':real,'random_rows':random_rows,'finite_fp16_scale_rows':scale_rows,'bit_exact':True,'gpu_executed':False,'full_inference_test_performed':False}
 (HERE/'evidence/runtime-cpu.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
