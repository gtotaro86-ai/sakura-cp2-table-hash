"""Correct a single provenance typo in existing released cards; weights untouched."""
import json,os,urllib.request
from pathlib import Path
from publish import require_runner,verify,safe_public
HERE=Path(__file__).resolve().parent
WRONG='1bae0e1088993b9b82de08f59de5be5f34e42170'
CORRECT='1bae0e1088993b9b82de08f59de5be5a34e42170'

def small_text(url):
 with urllib.request.urlopen(url,timeout=45) as response:data=response.read(100001)
 if len(data)>100000:raise RuntimeError('Metadata cap')
 return data.decode('utf-8')

def main():
 require_runner(os.environ)
 from huggingface_hub import HfApi,CommitOperationAdd,ModelCard
 api=HfApi(token=os.environ['HF_TOKEN'])
 official=api.model_info('deepseek-ai/DeepSeek-V4.1-Flash-1017')
 if official.sha!=CORRECT:raise RuntimeError('Expected original revision was not confirmed')
 for v in json.loads((HERE/'plan.json').read_text())['variants']:
  info=api.model_info(v['repo'])
  if info.private:raise RuntimeError('Only existing public releases')
  base=f"https://huggingface.co/{v['repo']}/resolve/{info.sha}/"
  manifest=json.loads(small_text(base+'build-manifest.json'))
  if manifest.get('complete') is not True:raise RuntimeError('Release incomplete')
  verify(api,v['repo'],manifest['files'])
  card=small_text(base+'README.md')
  if WRONG not in card:
   if card.count(CORRECT)!=2:raise RuntimeError('Unexpected card provenance')
   continue
  if card.count(WRONG)!=2:raise RuntimeError('Unexpected replacement scope')
  corrected=card.replace(WRONG,CORRECT);safe_public(corrected);ModelCard(corrected).validate()
  commit=api.create_commit(repo_id=v['repo'],parent_commit=info.sha,operations=[CommitOperationAdd(path_in_repo='README.md',path_or_fileobj=corrected.encode())],commit_message='Correct original checkpoint revision in English and Chinese provenance')
  after=small_text(f"https://huggingface.co/{v['repo']}/resolve/{commit.oid}/README.md")
  if after!=corrected:raise RuntimeError('Published card mismatch')
  verify(api,v['repo'],manifest['files'])
  print(json.dumps({'repo':v['repo'],'revision':commit.oid,'readme_revision_corrected':True,'all_five_weights_unchanged':True}),flush=True)
if __name__=='__main__':main()
