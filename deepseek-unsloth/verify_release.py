"""Independent read-only public release check, <=1 MB total pinned model ranges."""
import argparse,base64,hashlib,json,os,zlib,urllib.request
from pathlib import Path
import yaml
from ranges import fetch_range
from assembly import descriptor
HERE=Path(__file__).resolve().parent

def require(ok,message):
 if not ok:raise RuntimeError(message)

def metadata(url,cap=1000000):
 with urllib.request.urlopen(url,timeout=45) as r:
  require(int(r.headers.get('Content-Length','0'))<=cap,'Metadata Content-Length cap')
  data=r.read(cap+1)
 require(len(data)<=cap,'Metadata size cap')
 return data

def fixtures():
 out={}
 for f in json.loads((HERE/'fixtures.json').read_text())['files']:
  if not f['name'].endswith('.q3'):continue
  data=zlib.decompress(base64.b64decode(f['zlib_base64']))
  require(len(data)==f['size'] and hashlib.sha256(data).hexdigest()==f['sha256'],'Bad fixed row fixture')
  out[f['name']]=data
 return out

def verify_variant(plan,v,info,read=metadata,range_reader=fetch_range):
 repo=v['repo'];rev=info['sha'];base=f'https://huggingface.co/{repo}/resolve/{rev}/'
 manifest=json.loads(read(base+'build-manifest.json'))
 expected_plan_hash=hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()
 require(manifest.get('complete') is True and manifest['identity']['plan_sha256']==expected_plan_hash,'Incomplete release or different frozen plan')
 require(manifest.get('full_inference_test_performed') is False and manifest.get('gpu_runtime_executed') is False,'Incorrect inference/GPU status')
 table_build=manifest['table_build'];require(min(table_build['source_full_sha256_verified_passes'])>=1,'Missing full source SHA256 proof')
 expected=v['backbone']+[{'path':v['table_path'],'size':plan['combined_table_bytes'],'sha256':table_build['sha256']}]
 require(manifest['files']==expected and manifest['main_bytes']==v['main_bytes'],'Manifest file geometry differs')
 byname={f['rfilename']:f for f in info['siblings']}
 require({n for n in byname if n.endswith('.gguf')}=={f['path'] for f in expected},'Main GGUF file inventory differs')
 for f in expected:
  actual=byname[f['path']]
  require(actual.get('size')==f['size'] and (actual.get('lfs') or {}).get('sha256')==f['sha256'],'Published size/SHA256 differs: '+f['path'])
 card=read(base+'README.md').decode('utf-8');require(card.startswith('---\n'),'Missing YAML front matter')
 data=yaml.safe_load(card.split('---',2)[1])
 require(data.get('license')=='mit' and data.get('base_model')==plan['upstream_repo'] and data.get('base_model_relation')=='quantized','Wrong YAML provenance')
 require('No full inference test has been performed.' in card,'Missing full-inference notice')
 require('<details>' in card and '<details open' not in card and '中文说明' in card,'Missing default-collapsed Chinese README')
 require(not any(x in card.lower() for x in ['gtotaro86','sakura-cp2-table-hash','experimental']),'Forbidden private reference or unwanted release label')
 url=base+v['table_path'];size=plan['combined_table_bytes'];journal=HERE/'post-release-range-budget.json'
 header=range_reader(url,0,192,size,journal,1_000_000)
 require(header==bytes.fromhex(plan['combined_header_hex']),'Published combined Q3 header differs')
 require(descriptor(header)==('per_layer_token_embd.weight',768022850),'Published tensor format differs')
 q=fixtures();samples=json.loads((HERE/'evidence/probe-result.json').read_text())['samples'];count=192
 for s in samples:
  name=f"layer{[1,14].index(s['layer_id'])}-row{s['row_start']}.q3";expected_rows=q[name]
  got=range_reader(url,192+s['combined_row_start']*110,len(expected_rows),size,journal,1_000_000)
  require(got==expected_rows,'Published real-row bytes differ: '+name);count+=len(got)
 return {'repo':repo,'revision':rev,'complete':True,'main_bytes':v['main_bytes'],'all_five_lfs_sizes_and_sha256_verified':True,'published_header_verified':True,'real_rows_verified':sum(s['rows'] for s in samples),'model_range_bytes':count,'yaml_and_english_chinese_readme_verified':True,'full_inference_test_performed':False,'table_sha256':table_build['sha256']}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--read-public-output-samples',action='store_true',required=True);ap.parse_args()
 plan=json.loads((HERE/'plan.json').read_text());results=[]
 for v in plan['variants']:
  info=json.loads(metadata('https://huggingface.co/api/models/'+v['repo']+'?blobs=true'))
  require(info.get('private') is False,'Only public releases allowed')
  result=verify_variant(plan,v,info);results.append(result);print(json.dumps(result),flush=True)
 require(len({r['table_sha256'] for r in results})==1,'IQ1_S and IQ1_M tables are not byte-identical')
 (HERE/'post-release-verification.json').write_text(json.dumps(results,indent=2)+'\n')
 if os.environ.get('GITHUB_STEP_SUMMARY'):
  Path(os.environ['GITHUB_STEP_SUMMARY']).write_text('Both DeepSeek Unsloth releases independently verified. No full inference test.\n\n```json\n'+json.dumps(results,indent=2)+'\n```\n')
if __name__=='__main__':main()
