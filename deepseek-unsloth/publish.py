"""Authorized free public Actions repack + two releases; never full-read in Work."""
import hashlib,json,os,time,urllib.request
from pathlib import Path
from assembly import Assembly,BufferedAssembly
from ranges import fetch_range
HERE=Path(__file__).resolve().parent
MARKER='.sakura-build.json'

def safe_public(data):
 text=data.decode().lower() if isinstance(data,bytes) else str(data).lower()
 if any(x in text for x in ['gtotaro86','sakura-cp2-table-hash']):raise RuntimeError('Personal GitHub reference in public metadata')

def require_runner(env):
 if env.get('GITHUB_ACTIONS')!='true' or env.get('REPO_VISIBILITY')!='public' or env.get('RUNNER_ENVIRONMENT')!='github-hosted':raise RuntimeError('Full build requires a real public GitHub-hosted Actions runner; Work/local is refused')
 if env.get('SAKURA_FREE_STANDARD_RUNNER')!='ubuntu-24.04':raise RuntimeError('Only standard free ubuntu-24.04 allowed')
 if not env.get('HF_TOKEN'):raise RuntimeError('Explicit GitHub HF_TOKEN secret required')

def small(repo,rev,path):
 url=f'https://huggingface.co/{repo}/resolve/{rev}/{path}'
 with urllib.request.urlopen(url,timeout=60) as r:
  if int(r.headers.get('Content-Length','0'))>200000:raise RuntimeError('Small metadata cap')
  data=r.read(200001)
 if len(data)>200000:raise RuntimeError('Small metadata cap')
 return json.loads(data)

def verify(api,repo,files):
 items={x.path:x for x in api.get_paths_info(repo_id=repo,paths=[f['path'] for f in files],expand=True)}
 for f in files:
  x=items.get(f['path'])
  if x is None or x.size!=f['size'] or x.lfs is None or x.lfs.sha256!=f['sha256']:raise RuntimeError('Remote file size/SHA mismatch: '+f['path'])

def initialize(api,repo,identity):
 from huggingface_hub import CommitOperationAdd
 from huggingface_hub.utils import RepositoryNotFoundError
 try:
  info=api.model_info(repo)
  if info.private:raise RuntimeError('Public destination required')
  names={x.rfilename for x in info.siblings or []}
  if MARKER in names:
   if small(repo,info.sha,MARKER)!=identity:raise RuntimeError('Existing destination identity differs')
   return
  if names-{'.gitattributes'}:raise RuntimeError('Existing destination is not empty; refusing overwrite')
 except RepositoryNotFoundError:api.create_repo(repo_id=repo,repo_type='model',private=False,exist_ok=False)
 api.create_commit(repo_id=repo,operations=[CommitOperationAdd(path_in_repo=MARKER,path_or_fileobj=(json.dumps(identity,indent=2)+'\n').encode()),CommitOperationAdd(path_in_repo='README.md',path_or_fileobj=b'---\nlicense: mit\n---\n# Sakura DeepSeek Unsloth Engram Q3_K\n\nBuild in progress. Incomplete; do not download yet.\n')],commit_message='Initialize authorized cloud repack; incomplete until finalization')

def build_table(api,plan,identity):
 from huggingface_hub import CommitOperationAdd
 first=plan['variants'][0];repo=first['repo'];info=api.model_info(repo)
 if 'table-build.json' in {x.rfilename for x in info.siblings or []}:
  record=small(repo,info.sha,'table-build.json')
  if record['identity']!=identity:raise RuntimeError('Saved table identity mismatch')
  verify(api,repo,[{'path':first['table_path'],'size':record['size'],'sha256':record['sha256']}]);return record
 source_files=[{'path':p['path'],'size':p['size'],'sha256':p['sha256']} for p in plan['q3_parts']]
 verify(api,plan['q3_source_repo'],source_files)
 journal=HERE/'source-budget.json';limit=3*sum(p['size'] for p in plan['q3_parts'])
 def source(index,offset,count):
  require_runner(os.environ);p=plan['q3_parts'][index]
  return fetch_range(f"https://huggingface.co/{plan['q3_source_repo']}/resolve/{plan['q3_source_revision']}/{p['path']}",offset,count,p['size'],journal,limit)
 for i,p in enumerate(plan['q3_parts']):
  if source(i,0,192)!=bytes.fromhex(p['header_hex']):raise RuntimeError('Pinned Q3 source header mismatch')
 raw=Assembly(bytes.fromhex(plan['combined_header_hex']),plan['q3_parts'],source)
 tick=time.perf_counter();print('Hashing existing Q3 payloads into the combined Unsloth table; bounded RAM only',flush=True)
 with BufferedAssembly(raw) as stream:
  operation=CommitOperationAdd(path_in_repo=first['table_path'],path_or_fileobj=stream)
  if min(raw.verified_passes)<1:raise RuntimeError('Both full source SHA256 checks must pass before upload')
  digest=operation.upload_info.sha256.hex();size=operation.upload_info.size
  if size!=plan['combined_table_bytes']:raise RuntimeError('Combined size mismatch')
  print(json.dumps({'hash_pass_complete':True,'bytes':size,'sha256':digest,'elapsed_seconds':time.perf_counter()-tick}),flush=True)
  api.create_commit(repo_id=repo,operations=[operation],commit_message='Add shared combined Q3_K Engram table; backbone unchanged')
  verify(api,repo,[{'path':first['table_path'],'size':size,'sha256':digest}])
  passes=raw.verified_passes.copy()
 record={'identity':identity,'size':size,'sha256':digest,'source_full_sha256_verified_passes':passes,'source_budget':json.loads(journal.read_text()),'elapsed_seconds':time.perf_counter()-tick,'full_inference_test_performed':False}
 safe_public(json.dumps(record))
 api.create_commit(repo_id=repo,operations=[CommitOperationAdd(path_in_repo='table-build.json',path_or_fileobj=(json.dumps(record,indent=2)+'\n').encode())],commit_message='Record full source and uploaded table SHA256 verification')
 return record

def finalize(api,plan,identity,record):
 from huggingface_hub import CommitOperationAdd,CommitOperationCopy,ModelCard
 from card import make_card
 common=plan['variants'][0];common_rev=api.model_info(common['repo']).sha
 for v in plan['variants']:
  verify(api,plan['upstream_repo'],v['backbone'])
  info=api.model_info(v['repo'])
  if small(v['repo'],info.sha,MARKER)!=identity:raise RuntimeError('Destination identity changed')
  table={'path':v['table_path'],'size':record['size'],'sha256':record['sha256']}
  files=v['backbone']+[table];manifest={'identity':identity,'complete':True,'quant':v['quant'],'files':files,'main_bytes':sum(f['size'] for f in files),'table_build':record,'checks':json.loads((HERE/'evidence/addressing-check.json').read_text()),'full_inference_test_performed':False,'gpu_runtime_executed':False}
  if manifest['main_bytes']!=v['main_bytes']:raise RuntimeError('Release size mismatch')
  card=make_card(plan,v,record);safe_public(card);ModelCard(card).validate()
  ops=[CommitOperationCopy(src_repo_id=plan['upstream_repo'],src_repo_type='model',src_revision=plan['upstream_revision'],src_path_in_repo=f['path'],path_in_repo=f['path']) for f in v['backbone']]
  if v['repo']!=common['repo']:
   ops.append(CommitOperationCopy(src_repo_id=common['repo'],src_repo_type='model',src_revision=common_rev,src_path_in_repo=common['table_path'],path_in_repo=v['table_path']))
  for path,data in [('README.md',card.encode()),('build-manifest.json',(json.dumps(manifest,indent=2)+'\n').encode()),('compatibility-check.json',(HERE/'evidence/addressing-check.json').read_bytes()),('LICENSE.DeepSeek',(HERE/'LICENSE.DeepSeek').read_bytes()),('LICENSE.ggml',(HERE/'LICENSE.ggml').read_bytes())]:
   safe_public(data);ops.append(CommitOperationAdd(path_in_repo=path,path_or_fileobj=data))
  commit=api.create_commit(repo_id=v['repo'],operations=ops,parent_commit=info.sha,commit_message='Release unchanged Unsloth backbone with combined Q3_K Engram; no full inference test')
  verify(api,v['repo'],files)
  published=api.model_info(v['repo']);actual=small(v['repo'],published.sha,'build-manifest.json')
  if actual!=manifest:raise RuntimeError('Published manifest differs')
  ModelCard.load(v['repo'],token=os.environ['HF_TOKEN']).validate()
  print(json.dumps({'released':v['repo'],'revision':published.sha,'main_bytes':v['main_bytes'],'table_sha256':record['sha256'],'all_five_hashes_verified':True,'full_inference_test_performed':False}),flush=True)
  if os.environ.get('GITHUB_STEP_SUMMARY'):
   with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(f"Released https://huggingface.co/{v['repo']} — {v['main_bytes']} bytes. All five sizes/SHA256 verified. No full inference test.\n\n")

def main():
 require_runner(os.environ)
 import huggingface_hub
 if huggingface_hub.__version__!='2.2.0':raise RuntimeError('Pinned HF version required')
 from huggingface_hub import HfApi
 plan=json.loads((HERE/'plan.json').read_text());identity={'kind':'Sakura Unsloth IQ1_S/IQ1_M combined Engram Q3_K','plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),'release_notice':plan['release_notice']}
 request=json.loads((HERE/'release-request.json').read_text())
 if request.get('plan_sha256')!=identity['plan_sha256'] or request.get('mode')!='free-public-standard-cpu':raise RuntimeError('Build request and frozen plan differ')
 api=HfApi(token=os.environ['HF_TOKEN']);user=api.whoami()
 if user.get('name')!='webmp3' or user.get('isPro') is not False:raise RuntimeError('Only authenticated personal free webmp3 account allowed; no paid storage assumed')
 for v in plan['variants']:
  if not v['repo'].startswith('webmp3/Sakura-DeepSeek-V4.1-Flash-1017-Unsloth-UD-IQ1_'):raise RuntimeError('Unexpected destination')
  initialize(api,v['repo'],identity)
 record=build_table(api,plan,identity);finalize(api,plan,identity,record)
if __name__=='__main__':main()
