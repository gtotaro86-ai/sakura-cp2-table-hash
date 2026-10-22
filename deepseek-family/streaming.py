"""Single exact source pass, bounded buffers, native Xet header-only repacks."""
import contextlib,hashlib,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'deepseek-unsloth'))
from ranges import fetch_range
from xet_stream import session_config
CHUNK=8*1024*1024

def operations(api,source,targets,journal,session_factory=None,local_connection=None):
 """Targets share the same payload; only their 192-byte GGUF headers differ.

 Return publishable operations only after the complete pinned input hash,
 independent Python output hashes, native output hashes, and CAS commits pass.
 """
 import hf_xet,huggingface_hub
 from importlib.metadata import version
 from huggingface_hub import CommitOperationAdd
 from huggingface_hub.lfs import UploadInfo
 from huggingface_hub.utils._xet import XetTokenType,xet_connection_info_refresh_url,xet_headers_without_auth
 if huggingface_hub.__version__!='2.2.0' or version('hf-xet')!='1.7.0':raise RuntimeError('Pinned upload versions required')
 if not 1<=len(targets)<=4:raise ValueError('One to four bounded target streams')
 header=bytes.fromhex(source['header_hex']);size=source['size']
 if len(header)!=192 or size<512:raise ValueError('Audited GGUF source required')
 factory=session_factory or (lambda:hf_xet.XetSession(config=session_config()))
 results=[];source_digest=hashlib.sha256();tick=last=time.perf_counter()
 with contextlib.ExitStack() as stack:
  active=[]
  for target in targets:
   out_header=bytes.fromhex(target['header_hex'])
   if len(out_header)!=192 or target['size']!=size:raise ValueError('Header-only fixed-size replacement required')
   session=factory()
   if local_connection is not None:connection=local_connection
   else:
    headers=api._build_hf_headers()
    connection={'token_refresh_url':xet_connection_info_refresh_url(token_type=XetTokenType.WRITE,repo_id=target['repo'],repo_type='model',revision='main',endpoint=api.endpoint),'token_refresh_headers':headers,'custom_headers':xet_headers_without_auth(headers)}
   commit=stack.enter_context(session.new_upload_commit(**connection))
   stream=commit.start_upload_stream(name=target['path'],sha256=hf_xet.COMPUTE_SHA256)
   active.append({'target':target,'session':session,'commit':commit,'stream':stream,'digest':hashlib.sha256(),'sample':None})
  try:
   block_size=64*1024*1024
   for block_start in range(0,size,block_size):
    n=min(block_size,size-block_start)
    if 'read' in source:block=source['read'](block_start,n)
    else:block=fetch_range(f"https://huggingface.co/{source['repo']}/resolve/{source['revision']}/{source['path']}",block_start,n,size,journal,size+block_size)
    if len(block)!=n:raise RuntimeError('Pinned source short/excess read')
    if block_start==0 and block[:192]!=header:raise RuntimeError('Pinned source header mismatch')
    source_digest.update(block)
    for rel in range(0,n,CHUNK):
     start=block_start+rel;raw=block[rel:rel+CHUNK]
     for state in active:
      data=bytes.fromhex(state['target']['header_hex'])+raw[192:] if start==0 else raw
      if start==0:state['sample']=data[:512]
      state['digest'].update(data);state['stream'].write(data)
    now=time.perf_counter()
    if now-last>=30:
     print(json.dumps({'source_stream_bytes':block_start+n,'source_size':size,'target_streams':len(active),'seconds':now-tick}),flush=True);last=now
   if source_digest.hexdigest()!=source['sha256']:raise RuntimeError('Complete pinned source SHA256 mismatch')
   for state in active:
    meta=state['stream'].finish().xet_info;digest=state['digest'].hexdigest()
    if meta.file_size!=size or meta.sha256!=digest:raise RuntimeError('Native size/output SHA256 mismatch')
    results.append((state,digest))
  except BaseException:
   for state in active:state['stream'].abort()
   raise
 # All native commit contexts have completed successfully before creating Hub pointers.
 outputs=[]
 for state,digest in results:
  target=state['target'];op=CommitOperationAdd(path_in_repo=target['path'],path_or_fileobj=b'')
  op.upload_info=UploadInfo(size=size,sample=state['sample'],sha256=bytes.fromhex(digest))
  op._upload_mode='lfs';op._should_ignore=False;op._is_uploaded=True
  proof={'size':size,'sha256':digest,'source_sha256':source['sha256'],'complete_source_sha256_verified':True,'source_read_passes':1,'only_header_changed':True,'native_xet_sha256_verified':True,'elapsed_seconds':time.perf_counter()-tick,'full_inference_test_performed':False}
  outputs.append((target,op,proof))
 print(json.dumps({'header_repack_complete':True,'bytes':size,'targets':len(outputs),'source_sha256':source['sha256'],'seconds':time.perf_counter()-tick}),flush=True)
 return outputs
