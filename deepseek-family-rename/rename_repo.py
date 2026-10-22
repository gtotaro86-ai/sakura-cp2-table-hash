"""Rename the Maya-S repository and update public references, metadata only."""
import io,json,os,urllib.parse,urllib.request
from pathlib import Path
from huggingface_hub import HfApi,CommitOperationAdd,ModelCard
from huggingface_hub.utils import RepositoryNotFoundError

OLD='webmp3/Sakura-DeepSeek-V4.1-Flash-1017-Engram-Q3_K-GGUF'
NEW='webmp3/Sakura-DeepSeek-V4.1-Flash-1017-Maya-S-IQ2_XXS-Engram-Q3_K-GGUF'
TOTAL=0

def read_small(repo,revision,path):
 global TOTAL
 url=f'https://huggingface.co/{repo}/resolve/{revision}/{urllib.parse.quote(path,safe="/")}'
 with urllib.request.urlopen(url,timeout=90) as response:data=response.read(1000001)
 if len(data)>1000000:raise RuntimeError('Small-document budget exceeded: '+path)
 TOTAL+=len(data)
 if TOTAL>20000000:raise RuntimeError('Total metadata budget exceeded')
 return data

def identities(info,exclude=()):
 result={}
 for f in info.siblings:
  if f.rfilename in exclude:continue
  lfs=f.lfs
  sha=lfs.get('sha256') if isinstance(lfs,dict) else getattr(lfs,'sha256',None)
  result[f.rfilename]=(f.size,f.blob_id,sha)
 return result

def main():
 assert os.environ.get('GITHUB_ACTIONS')=='true'
 assert os.environ.get('RUNNER_ENVIRONMENT')=='github-hosted'
 assert os.environ.get('RUNNER_OS')=='Linux'
 assert os.environ.get('REPO_VISIBILITY')=='public'
 assert os.environ.get('SAKURA_FREE_STANDARD_RUNNER')=='ubuntu-24.04'
 api=HfApi(token=os.environ['HF_TOKEN'])
 assert api.whoami()['name']=='webmp3'
 plan=json.loads((Path(__file__).parents[1]/'deepseek-family/plan.json').read_text())
 repos=[OLD]+[v['repo'] for v in plan['variants'] if v['repo']!=OLD]+[plan['overview_repo']]
 snapshots={};staged={}
 # Prepare every reference change before the rename. Never read model weights.
 for repo in repos:
  info=api.model_info(repo,files_metadata=True)
  if info.private:raise RuntimeError('Expected public model repository')
  snapshots[repo]=info
  changes={}
  for f in info.siblings:
   if not f.rfilename.endswith(('.md','.json')):continue
   if f.lfs is not None or (f.size is not None and f.size>1000000):continue
   raw=read_small(repo,info.sha,f.rfilename)
   if OLD.encode() not in raw:continue
   updated=raw.replace(OLD.encode(),NEW.encode())
   if f.rfilename.endswith('.json'):json.loads(updated)
   if f.rfilename=='README.md':ModelCard(updated.decode()).validate()
   changes[f.rfilename]=updated
  staged[repo]=changes
 source=snapshots[OLD]
 weights={k:v for k,v in identities(source).items() if k.endswith('.gguf')}
 assert len(weights)==6 and sum(v[0] for v in weights.values())==262675668988
 # A move preserves the repository and its history; never overwrite a target.
 if source.id==OLD:
  try:target=api.model_info(NEW)
  except RepositoryNotFoundError:target=None
  if target is not None:raise RuntimeError('Destination exists; refusing to replace another repository')
  api.move_repo(from_id=OLD,to_id=NEW,repo_type='model')
 elif source.id!=NEW:raise RuntimeError('Unexpected source repository identity')
 moved=api.model_info(NEW,files_metadata=True)
 assert moved.id==NEW and moved.sha==source.sha
 assert identities(moved)==identities(source),'Rename changed file identities'
 print(json.dumps({'repository_renamed':True,'repo':NEW,'history_preserved':True,'all_file_identities_preserved':True}),flush=True)
 for repo in repos:
  destination=NEW if repo==OLD else repo
  before=snapshots[repo];changes=staged[repo]
  if changes:
   result=api.create_commit(repo_id=destination,parent_commit=before.sha,
    operations=[CommitOperationAdd(path_in_repo=p,path_or_fileobj=io.BytesIO(data)) for p,data in changes.items()],
    commit_message='Use explicit Maya-S IQ2_XXS repository name in model references')
   after=api.model_info(destination,revision=result.oid,files_metadata=True)
   assert identities(before,changes)==identities(after,changes),'A locked file changed'
   for path,expected in changes.items():assert read_small(destination,result.oid,path)==expected
  else:after=api.model_info(destination,files_metadata=True)
  assert {k:v for k,v in identities(before).items() if k.endswith('.gguf')}=={k:v for k,v in identities(after).items() if k.endswith('.gguf')}
  print(json.dumps({'references_updated':destination,'revision':after.sha,'documents':sorted(changes),'all_weight_hashes_preserved':True}),flush=True)
 # Verify actual API identity and legacy-URL redirect after all commits.
 final=api.model_info(NEW,files_metadata=True)
 assert final.id==NEW
 with urllib.request.urlopen('https://huggingface.co/'+OLD,timeout=90) as response:
  assert urllib.parse.urlsplit(response.geturl()).path.rstrip('/')=='/'+NEW
  response.read(1)
 print(json.dumps({'complete':True,'repo':NEW,'page_heading_is_repository_name':True,'legacy_url_redirect_verified':True,'packages':11,'overview_updated':True,'weights_downloaded':False,'weights_rebuilt':False,'metadata_bytes':TOTAL}),flush=True)

if __name__=='__main__':main()
