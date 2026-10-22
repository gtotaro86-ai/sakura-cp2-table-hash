"""Pinned native Xet incremental upload; publish only after size/hash/source checks.

Uses the same CAS authentication and final Hub commit representation as HF 2.2.0.
The native 1.7.0 stream provides backpressure; no local full-file materialization.
Private HF operation fields below are version-pinned and covered by protocol tests.
"""
import hashlib,json,time
from importlib.metadata import version

CHUNK_BYTES=8*1024*1024

def session_config():
 from hf_xet import XetConfig
 return XetConfig().with_config({'data.max_concurrent_file_ingestion':1,
  'client.ac_max_upload_concurrency':4,'client.ac_initial_upload_concurrency':2,
  'shard.cache_size_limit':'256mb','shard.chunk_index_table_max_size':1048576,
  'telemetry.enabled':False})

def upload_operation(api,repo,path,source,size,expected_sha256,validate_source=lambda:None,
                     session=None,connection=None):
 import hf_xet,huggingface_hub
 from huggingface_hub import CommitOperationAdd
 from huggingface_hub.lfs import UploadInfo
 from huggingface_hub.utils._xet import XetTokenType,xet_connection_info_refresh_url,xet_headers_without_auth
 if huggingface_hub.__version__!='2.2.0' or version('hf-xet')!='1.7.0':raise RuntimeError('Pinned HF/Xet versions required')
 if size<=0 or len(expected_sha256)!=64:raise ValueError('Exact positive size and SHA256 required')
 bytes.fromhex(expected_sha256)
 if connection is None:
  headers=api._build_hf_headers()
  connection={'token_refresh_url':xet_connection_info_refresh_url(token_type=XetTokenType.WRITE,
    repo_id=repo,repo_type='model',revision='main',endpoint=api.endpoint),
    'token_refresh_headers':headers,'custom_headers':xet_headers_without_auth(headers)}
 if session is None:session=hf_xet.XetSession(config=session_config())
 count=0;digest=hashlib.sha256();sample=b'';tick=last=time.perf_counter()
 with session.new_upload_commit(**connection) as commit:
  stream=commit.start_upload_stream(name=path,sha256=hf_xet.COMPUTE_SHA256)
  try:
   while count<size:
    chunk=source.read(min(CHUNK_BYTES,size-count))
    if not chunk or len(chunk)>min(CHUNK_BYTES,size-count):raise RuntimeError('Native stream source length mismatch')
    if len(sample)<512:sample=(sample+chunk[:512])[:512]
    digest.update(chunk);stream.write(chunk);count+=len(chunk)
    now=time.perf_counter()
    if now-last>=30:
     print(json.dumps({'xet_stream_bytes':count,'total_bytes':size,'elapsed_seconds':now-tick}),flush=True);last=now
   if source.read(1):raise RuntimeError('Native stream source exceeded declared size')
   if digest.hexdigest()!=expected_sha256:raise RuntimeError('Combined SHA256 differs from independently recorded full hash')
   validate_source()
   result=stream.finish()
   if result.xet_info.file_size!=size or result.xet_info.sha256!=expected_sha256:raise RuntimeError('Native Xet size/SHA256 mismatch')
  except BaseException:
   stream.abort();raise
 # CAS metadata registration has now succeeded; no Hub pointer was committed before checks.
 operation=CommitOperationAdd(path_in_repo=path,path_or_fileobj=b'')
 operation.upload_info=UploadInfo(size=size,sample=sample,sha256=bytes.fromhex(expected_sha256))
 operation._upload_mode='lfs';operation._should_ignore=False;operation._is_uploaded=True
 print(json.dumps({'xet_stream_verified':True,'bytes':count,'sha256':expected_sha256,
  'elapsed_seconds':time.perf_counter()-tick}),flush=True)
 return operation
