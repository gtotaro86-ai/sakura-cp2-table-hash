"""Authorized full family assembly on free public hosted CPU runners only."""
import argparse,hashlib,json,os,sys,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'deepseek-unsloth'))
from publish import require_runner,safe_public,verify,small,probe_xet_upload
from ranges import fetch_range
from streaming import operations
from metadata import parse,addressing,table

def plan():
 # Preserve frozen build-identity hashes while resolving the renamed public repository.
 text=(HERE/'plan.json').read_text().replace('webmp3/Sakura-DeepSeek-V4.1-Flash-1017-Engram-Q3_K-GGUF','webmp3/Sakura-DeepSeek-V4.1-Flash-1017-Maya-S-IQ2_XXS-Engram-Q3_K-GGUF')
 return json.loads(text)
def identity(v):return {'family_plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),'variant':v['variant'],'no_full_inference_test':True}
def raw_small(url):
 with urllib.request.urlopen(url,timeout=60) as r:data=r.read(200001)
 if len(data)>200000:raise RuntimeError('Metadata cap')
 return data
def api_checked():
 require_runner(os.environ)
 from huggingface_hub import HfApi
 api=HfApi(token=os.environ['HF_TOKEN']);u=api.whoami()
 if u.get('name')!='webmp3' or u.get('isPro') is not False:raise RuntimeError('Only the personal free destination account is authorized')
 return api
def verify_source(api,repo,files,revision):
 items={x.path:x for x in api.get_paths_info(repo_id=repo,revision=revision,paths=[f['path'] for f in files],expand=True)}
 for f in files:
  x=items.get(f['path'])
  if x is None or x.size!=f['size'] or x.lfs is None or x.lfs.sha256!=f['sha256']:raise RuntimeError('Pinned source file identity differs: '+f['path'])

def initialize(api,v):
 from huggingface_hub import CommitOperationAdd
 from huggingface_hub.utils import RepositoryNotFoundError
 repo=v['repo'];marker='.sakura-build.json'
 try:
  info=api.model_info(repo)
  if info.private:raise RuntimeError('Only dedicated public releases')
  names={s.rfilename for s in info.siblings or []}
  if marker in names:
   if small(repo,info.sha,marker)!=identity(v):raise RuntimeError('Destination belongs to another build')
   return
  if names-{'.gitattributes'}:raise RuntimeError('Destination is not empty')
 except RepositoryNotFoundError:api.create_repo(repo_id=repo,repo_type='model',private=False,exist_ok=False)
 card='---\nlicense: mit\n---\n# Sakura DeepSeek '+v['variant']+'\n\nBuild in progress. Incomplete; do not download yet.\n'
 api.create_commit(repo_id=repo,operations=[CommitOperationAdd(path_in_repo=marker,path_or_fileobj=(json.dumps(identity(v),indent=2)+'\n').encode()),CommitOperationAdd(path_in_repo='README.md',path_or_fileobj=card.encode())],commit_message='Initialize authorized free cloud build; incomplete until finalization')
def is_complete(api,v):
 info=api.model_info(v['repo'])
 if 'build-manifest.json' not in {s.rfilename for s in info.siblings or []}:return False
 m=small(v['repo'],info.sha,'build-manifest.json')
 if m.get('identity')!=identity(v) or m.get('complete') is not True:raise RuntimeError('Existing release identity differs')
 verify(api,v['repo'],m['files']);return True

def preflight_unsloth(api,p):
 ref=None;records=[]
 for v in [v for v in p['variants'] if v['kind']=='unsloth']:
  verify_source(api,v['source_repo'],v['backbone']+[{k:f[k] for k in ['path','size','sha256']} for f in v['source_tables']],v['source_revision'])
  f=v['backbone'][0]
  if f['size']>7000000:raise RuntimeError('Expected metadata-only source shard')
  url=f"https://huggingface.co/{v['source_repo']}/resolve/{v['source_revision']}/"
  data=fetch_range(url+f['path'],0,f['size'],f['size'],HERE/'metadata-budget.json',65000000)
  if hashlib.sha256(data).hexdigest()!=f['sha256']:raise RuntimeError('Full metadata-only shard hash mismatch')
  nt,m,_=parse(data,metadata_only=True);current=addressing(m)
  if ref is None:ref=current
  if current!=ref:raise RuntimeError('Unsloth Engram addressing differs across variants')
  if m['split.count']!=len(v['backbone'])+1 or m['split.tensors.count']!=1043:raise RuntimeError('Unsloth split contract differs')
  source=v['source_tables'][0];h=fetch_range(url+source['path'],0,192,source['size'],HERE/'metadata-budget.json',65000000);d=table(h)
  out=table(bytes.fromhex(v['tables'][0]['header_hex']))
  if d['name']!='per_layer_token_embd.weight' or d['rows']!=768022850 or d['type']!=source['type'] or d['split']!=out['split']:raise RuntimeError('Source table does not match frozen layout')
  records.append({'variant':v['variant'],'metadata_sha256':f['sha256'],'complete_metadata_and_addressing_verified':True,'source_table_header_verified':True})
 (HERE/'unsloth-preflight.json').write_text(json.dumps(records,indent=2)+'\n')
 print(json.dumps({'all_nine_unsloth_metadata_and_layouts_verified':True}),flush=True)

def uploaded_receipt(api,v):
 info=api.model_info(v['repo'])
 if 'table-build.json' not in {s.rfilename for s in info.siblings or []}:return None
 r=small(v['repo'],info.sha,'table-build.json')
 if r['identity']!=identity(v):raise RuntimeError('Table receipt identity differs')
 verify(api,v['repo'],r['files']);return r
def store_upload(api,v,outputs):
 from huggingface_hub import CommitOperationAdd
 files=[{'path':t['path'],'size':proof['size'],'sha256':proof['sha256']} for t,op,proof in outputs]
 receipt={'identity':identity(v),'files':files,'streams':[proof for _,_,proof in outputs],'source_scope':'Existing Sakura Q3_K payload reused without requantization; only valid GGUF split headers changed','full_inference_test_performed':False}
 safe_public(json.dumps(receipt))
 api.create_commit(repo_id=v['repo'],operations=[op for _,op,_ in outputs]+[CommitOperationAdd(path_in_repo='table-build.json',path_or_fileobj=(json.dumps(receipt,indent=2)+'\n').encode())],commit_message='Add fully hashed Q3 table stream and source proof; no inference test')
 verify(api,v['repo'],files);return receipt

def finalize(api,v,receipt,copy_from=None):
 from huggingface_hub import CommitOperationAdd,CommitOperationCopy,ModelCard
 from cards import model_card
 verify_source(api,v['source_repo'],v['backbone'],v['source_revision'])
 files=v['backbone']+receipt['files'];info=api.model_info(v['repo'])
 if small(v['repo'],info.sha,'.sakura-build.json')!=identity(v):raise RuntimeError('Destination changed')
 checks={'full_inference_test_performed':False,'gpu_runtime_executed':False,'source_revision':v['source_revision'],'table_source_hashes_verified':True}
 if v['kind']=='unsloth':checks['addressing']=json.loads((HERE/'unsloth-preflight.json').read_text());checks['native_host_gather']=json.loads((HERE/'evidence/unsloth-addressing-check.json').read_text())
 else:
  checks['source_sample_probe']=json.loads((HERE/'evidence/maya-xs-probe.json').read_text());checks['addressing']=json.loads((HERE/'evidence/maya-addressing.json').read_text());checks['scalar_cpu']=json.loads((HERE/'evidence/runtime-cpu.json').read_text());checks['cuda_compile']=json.loads((HERE/'evidence/runtime-cuda.json').read_text())
 manifest={'identity':identity(v),'complete':True,'variant':v['variant'],'files':files,'main_bytes':sum(f['size'] for f in files),'table_build':receipt,'checks':checks,'full_inference_test_performed':False,'gpu_runtime_executed':False}
 if manifest['main_bytes']!=v['main_bytes']:raise RuntimeError('Release total mismatch')
 card=model_card(plan(),v,manifest);safe_public(card);ModelCard(card).validate()
 ops=[CommitOperationCopy(src_repo_id=v['source_repo'],src_repo_type='model',src_revision=v['source_revision'],src_path_in_repo=f['path'],path_in_repo=f['path']) for f in v['backbone']]
 if copy_from:
  repo,rev,srcfiles=copy_from
  for src,dest in zip(srcfiles,receipt['files']):ops.append(CommitOperationCopy(src_repo_id=repo,src_repo_type='model',src_revision=rev,src_path_in_repo=src['path'],path_in_repo=dest['path']))
 data=[('README.md',card.encode()),('build-manifest.json',(json.dumps(manifest,indent=2)+'\n').encode()),('compatibility-check.json',(json.dumps(checks,indent=2)+'\n').encode()),('LICENSE.DeepSeek',(HERE/'LICENSE.DeepSeek').read_bytes()),('LICENSE.ggml',(HERE/'LICENSE.ggml').read_bytes())]
 if v['kind']=='maya':
  data.append(('LICENSE.Maya',(HERE/'LICENSE.Maya').read_bytes()))
  data += [('runtime/maya-v1.1.22-q3.patch',(HERE/'maya-v1.1.22-q3.patch').read_bytes()),('runtime/runtime-pin.json',(HERE/'runtime-pin.json').read_bytes())]
 for path,b in data:safe_public(b);ops.append(CommitOperationAdd(path_in_repo=path,path_or_fileobj=b))
 commit=api.create_commit(repo_id=v['repo'],parent_commit=info.sha,operations=ops,commit_message='Release unchanged backbone with verified Q3_K Engram; no full inference test')
 verify(api,v['repo'],files);verify_output(api,v)
 print(json.dumps({'released':v['repo'],'revision':commit.oid,'main_bytes':v['main_bytes'],'all_hashes_verified':True,'full_inference_test_performed':False}),flush=True)

def build_unsloth(api,p):
 preflight_unsloth(api,p)
 primaries={g:next(v for v in p['variants'] if v['repo']==repos[0]) for g,repos in p['new_table_groups'].items()}
 pending=[];receipts={}
 for g,v in primaries.items():
  initialize(api,v);r=uploaded_receipt(api,v)
  if r:receipts[g]=r
  else:pending.append(v)
 if pending:
  probe_xet_upload(api,pending[0]['repo'])
  source=p['combined_source'];verify_source(api,source['repo'],[{k:source[k] for k in ['path','size','sha256']}],source['revision'])
  targets=[dict(v['tables'][0],repo=v['repo']) for v in pending]
  outputs=operations(api,source,targets,HERE/'unsloth-source-budget.json')
  for v in pending:receipts[v['group']]=store_upload(api,v,[o for o in outputs if o[0]['repo']==v['repo']])
 for g,repos in p['new_table_groups'].items():
  primary=primaries[g];r=receipts[g]
  if not is_complete(api,primary):finalize(api,primary,r)
  rev=api.model_info(primary['repo']).sha
  for repo in repos[1:]:
   v=next(v for v in p['variants'] if v['repo']==repo);initialize(api,v)
   if is_complete(api,v):continue
   cloned=dict(r,identity=identity(v),files=[dict(f,path=v['tables'][i]['path']) for i,f in enumerate(r['files'])])
   finalize(api,v,cloned,(primary['repo'],rev,r['files']))

def build_maya(api,p):
 v=next(v for v in p['variants'] if v['group']=='maya-xs')
 cpu=json.loads((HERE/'evidence/runtime-cpu.json').read_text());cuda=json.loads((HERE/'evidence/runtime-cuda.json').read_text());patch=hashlib.sha256((HERE/'maya-v1.1.22-q3.patch').read_bytes()).hexdigest()
 if not cpu['bit_exact'] or not cuda['gpu_test_linked'] or cpu['patch_sha256']!=patch or cuda['patch_sha256']!=patch:raise RuntimeError('New XS runtime checks are incomplete or refer to another patch')
 initialize(api,v)
 if is_complete(api,v):return
 verify_source(api,v['source_repo'],v['backbone'],v['source_revision'])
 source_info=p['split_sources'];verify_source(api,source_info['repo'],[{k:f[k] for k in ['path','size','sha256']} for f in source_info['files']],source_info['revision'])
 existing=uploaded_receipt(api,v)
 if existing:finalize(api,v,existing);return
 probe_xet_upload(api,v['repo']);all_outputs=[]
 for i,(src,dest) in enumerate(zip(source_info['files'],v['tables'])):
  source=dict(src,repo=source_info['repo'],revision=source_info['revision']);all_outputs+=operations(api,source,[dict(dest,repo=v['repo'])],HERE/f'maya-source-{i}-budget.json')
 receipt=store_upload(api,v,all_outputs);finalize(api,v,receipt)

def verify_output(api,v):
 info=api.model_info(v['repo']);m=small(v['repo'],info.sha,'build-manifest.json')
 if m.get('complete') is not True or m.get('main_bytes')!=v['main_bytes']:raise RuntimeError('Release missing or wrong total')
 verify(api,v['repo'],m['files']);samples=json.loads((HERE/'evidence/unsloth-probe-result.json').read_text())['samples']
 for i,f in enumerate(v['tables']):
  actual=next(x for x in m['files'] if x['path']==f['path']);url=f"https://huggingface.co/{v['repo']}/resolve/{info.sha}/{f['path']}";journal=HERE/'verification-budget.json'
  header=fetch_range(url,0,192,actual['size'],journal,2000000)
  if header!=bytes.fromhex(f['header_hex']):raise RuntimeError('Published table header mismatch')
  for s in samples:
   layer=[1,14].index(s['layer_id'])
   if v['kind']=='maya' and layer!=i:continue
   row=s['row_start'] if v['kind']=='maya' else s['combined_row_start'];n=s['rows']*110
   expected=(HERE.parent/f"deepseek-unsloth/evidence/layer{layer}-row{s['row_start']}.q3").read_bytes()
   raw=fetch_range(url,192+row*110,n,actual['size'],journal,2000000)
   if raw!=expected:raise RuntimeError('Published true row data mismatch')
 print(json.dumps({'independently_checked':v['repo'],'revision':info.sha,'all_file_hashes':True,'true_rows':192,'full_inference_test_performed':False}),flush=True)
 return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['unsloth','maya','verify']);args=ap.parse_args();p=plan()
 request=json.loads((HERE/'request.json').read_text())
 if request.get('plan_sha256')!=hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest() or request.get('mode')!='free-public-standard-cpu':raise RuntimeError('Build request differs from frozen family plan')
 api=api_checked()
 if args.mode=='unsloth':build_unsloth(api,p)
 elif args.mode=='maya':build_maya(api,p)
 else:
  for v in p['variants']:verify_output(api,v)
if __name__=='__main__':main()
