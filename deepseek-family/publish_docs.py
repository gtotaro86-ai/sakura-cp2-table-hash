"""Publish only reviewed cards/catalog metadata, preserving all model/runtime files."""
import argparse,hashlib,json,os,sys
from pathlib import Path
from release import HERE,plan,api_checked,small,raw_small,verify_output
from cards import model_card,overview
sys.path.insert(0,str(HERE.parent/'deepseek-unsloth'))
from publish import safe_public,verify

def normalize(v,m):
 if 'files' not in m:
  m=dict(m,files=m['backbone']+[{k:f[k] for k in ['path','size','sha256']} for f in m['tables']],main_bytes=v['main_bytes'],full_inference_test_performed=False)
 return m

def flash_cards(api):
 from huggingface_hub import CommitOperationAdd,ModelCard
 targets=json.loads((HERE/'flash-doc-plan.json').read_text())
 for t in targets:
  info=api.model_info(t['repo'])
  if info.private:raise RuntimeError('Only existing public Flash releases')
  paths=[f['path'] for f in t['locked_files']];actual={f.path:f for f in api.get_paths_info(repo_id=t['repo'],paths=paths,expand=True)}
  for f in t['locked_files']:
   a=actual.get(f['path'])
   if a is None or a.size!=f['size']:raise RuntimeError('Flash model/runtime file changed')
   if f['sha256']:
    if a.lfs is None or a.lfs.sha256!=f['sha256']:raise RuntimeError('Flash LFS identity changed')
   elif a.blob_id!=f['blob_id']:raise RuntimeError('Flash text/runtime identity changed')
  changes=[]
  for name in t['documents']:
   data=(HERE/'flash-docs'/t['variant']/name).read_bytes();safe_public(data)
   if name=='README.md':ModelCard(data.decode()).validate()
   changes.append(CommitOperationAdd(path_in_repo=name,path_or_fileobj=data))
  c=api.create_commit(repo_id=t['repo'],parent_commit=info.sha,operations=changes,commit_message='Add original-versus-Sakura comparison and Chinese README; remove private build references; weights/runtime unchanged')
  after={f.path:f for f in api.get_paths_info(repo_id=t['repo'],paths=paths,expand=True)}
  for f in t['locked_files']:
   a,b=actual[f['path']],after[f['path']]
   if a.size!=b.size or a.blob_id!=b.blob_id or ((a.lfs.sha256 if a.lfs else None)!=(b.lfs.sha256 if b.lfs else None)):raise RuntimeError('Flash locked file changed during documentation update')
  for name in t['documents']:
   data=raw_small(f"https://huggingface.co/{t['repo']}/resolve/{c.oid}/{name}")
   if data!=(HERE/'flash-docs'/t['variant']/name).read_bytes():raise RuntimeError('Published Flash document differs')
  print(json.dumps({'flash_readme_updated':t['repo'],'revision':c.oid,'model_runtime_starter_unchanged':True,'full_inference_test_performed':False}),flush=True)

def main():
 from huggingface_hub import CommitOperationAdd,ModelCard
 from huggingface_hub.utils import RepositoryNotFoundError
 ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group();g.add_argument('--flash-only',action='store_true');g.add_argument('--deepseek-only',action='store_true');args=ap.parse_args()
 api=api_checked()
 if args.flash_only:flash_cards(api);return
 p=plan();revisions={}
 # Every new package must be complete before advertising an eleven-model family.
 for v in p['variants']:
  info=api.model_info(v['repo']);m=normalize(v,small(v['repo'],info.sha,'build-manifest.json'))
  if m.get('complete') is not True or m['main_bytes']!=v['main_bytes']:raise RuntimeError('Do not publish catalog with incomplete release')
  verify(api,v['repo'],m['files'])
 for v in p['variants']:
  info=api.model_info(v['repo']);before=small(v['repo'],info.sha,'build-manifest.json');m=normalize(v,before)
  text=model_card(p,v,m,complete_family=True);safe_public(text);ModelCard(text).validate()
  changes=[CommitOperationAdd(path_in_repo='README.md',path_or_fileobj=text.encode())]
  if m!=before:changes.append(CommitOperationAdd(path_in_repo='build-manifest.json',path_or_fileobj=(json.dumps(m,indent=2)+'\n').encode()))
  if v['kind']=='maya':
   records={'runtime_cpu':json.loads((HERE/'evidence/runtime-cpu.json').read_text()),'runtime_cuda_compile':json.loads((HERE/'evidence/runtime-cuda.json').read_text()),'source_sample_probe':json.loads((HERE/'evidence/maya-xs-probe.json').read_text()),'addressing':json.loads((HERE/'evidence/maya-addressing.json').read_text()),'full_inference_test_performed':False}
   for name,data in [('compatibility-check.json',(json.dumps(records,indent=2)+'\n').encode()),('runtime/maya-v1.1.22-q3.patch',(HERE/'maya-v1.1.22-q3.patch').read_bytes()),('runtime/runtime-pin.json',(HERE/'runtime-pin.json').read_bytes()),('LICENSE.Maya',(HERE/'LICENSE.Maya').read_bytes())]:
    safe_public(data);changes.append(CommitOperationAdd(path_in_repo=name,path_or_fileobj=data))
  commit=api.create_commit(repo_id=v['repo'],parent_commit=info.sha,operations=changes,commit_message='Add detailed source/size/family comparisons and collapsed Chinese; preserve model files')
  if raw_small(f"https://huggingface.co/{v['repo']}/resolve/{commit.oid}/README.md")!=text.encode():raise RuntimeError('Published model card differs')
  verify_output(api,v);revisions[v['repo']]=commit.oid
  print(json.dumps({'readme_updated':v['repo'],'revision':commit.oid,'all_model_hashes_preserved':True}),flush=True)
 catalog=overview(p,revisions);safe_public(catalog);ModelCard(catalog).validate();repo=p['overview_repo']
 marker={'kind':'Sakura DeepSeek Flash 1017 family overview','family_plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()}
 try:
  info=api.model_info(repo);names={f.rfilename for f in info.siblings or []}
  if info.private:raise RuntimeError('Overview must be public')
  if names-{'.gitattributes'}:
   if '.sakura-overview.json' not in names or small(repo,info.sha,'.sakura-overview.json')!=marker:raise RuntimeError('Existing overview is not this task-owned catalog')
 except RepositoryNotFoundError:api.create_repo(repo_id=repo,repo_type='model',private=False,exist_ok=False)
 operations=[CommitOperationAdd(path_in_repo='README.md',path_or_fileobj=catalog.encode()),CommitOperationAdd(path_in_repo='.sakura-overview.json',path_or_fileobj=(json.dumps(marker,indent=2)+'\n').encode()),CommitOperationAdd(path_in_repo='catalog.json',path_or_fileobj=(json.dumps({'revisions':revisions,'main_bytes':{v['repo']:v['main_bytes'] for v in p['variants']},'all_model_hashes_and_real_rows_verified':True,'full_inference_test_performed':False},indent=2)+'\n').encode())]
 commit=api.create_commit(repo_id=repo,operations=operations,commit_message='Publish verified eleven-model Sakura DeepSeek Flash overview with comparisons and Chinese')
 if raw_small(f'https://huggingface.co/{repo}/resolve/{commit.oid}/README.md')!=catalog.encode():raise RuntimeError('Catalog differs after publication')
 print(json.dumps({'overview_published':repo,'revision':commit.oid,'completed_packages':11}),flush=True)
 if not args.deepseek_only:flash_cards(api)
 if os.environ.get('GITHUB_STEP_SUMMARY'):
  Path(os.environ['GITHUB_STEP_SUMMARY']).write_text(f"All 11 DeepSeek packages and comparison cards verified. Overview: https://huggingface.co/{repo}\n\nFlash-Next comparison-card updates run in their separate metadata-only job. No full inference tests.\n")
if __name__=='__main__':main()
