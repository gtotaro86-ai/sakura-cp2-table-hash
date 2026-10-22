"""Update the Maya-S model-card heading only; no model downloads or rebuild."""
import io,json,os,urllib.request
from huggingface_hub import HfApi,CommitOperationAdd,ModelCard
import yaml

REPO="webmp3/Sakura-DeepSeek-V4.1-Flash-1017-Engram-Q3_K-GGUF"
OLD="# Sakura DeepSeek-V4.1-Flash-1017 · Maya-S-IQ2_XXS · Engram Q3_K"
NEW="# Sakura DeepSeek-V4.1-Flash-1017 · Maya-S IQ2_XXS · Engram Q3_K"

def read_card(revision):
    url=f"https://huggingface.co/{REPO}/resolve/{revision}/README.md"
    with urllib.request.urlopen(url,timeout=60) as r:
        raw=r.read(1024*1024+1)
    if len(raw)>1024*1024:
        raise RuntimeError("Unexpectedly large model card")
    return raw.decode("utf-8")

def identities(info):
    result={}
    for f in info.siblings:
        if f.rfilename=="README.md": continue
        lfs=f.lfs
        sha=lfs.get("sha256") if isinstance(lfs,dict) else getattr(lfs,"sha256",None)
        result[f.rfilename]=(f.size,f.blob_id,sha)
    return result

def main():
    assert os.environ.get("GITHUB_ACTIONS")=="true"
    assert os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted"
    assert os.environ.get("RUNNER_OS")=="Linux"
    assert os.environ.get("REPO_VISIBILITY")=="public"
    assert os.environ.get("SAKURA_FREE_STANDARD_RUNNER")=="ubuntu-24.04"
    api=HfApi(token=os.environ["HF_TOKEN"])
    before=api.model_info(REPO,files_metadata=True)
    card=read_card(before.sha)
    headings=[line for line in card.splitlines() if line.startswith("# ")]
    if headings==[NEW]:
        print(json.dumps({"already_correct":True,"repo":REPO,"revision":before.sha,"heading":NEW},ensure_ascii=False))
        return
    if headings!=[OLD] or card.count(OLD)!=1:
        raise RuntimeError("Model-card heading changed concurrently; refusing broad replacement")
    updated=card.replace(OLD,NEW,1)
    assert updated.replace(NEW,OLD,1)==card
    assert card.startswith("---\n") and updated.startswith("---\n")
    assert yaml.safe_load(card.split("---",2)[1])==yaml.safe_load(updated.split("---",2)[1])
    ModelCard(updated).validate()
    result=api.create_commit(
        repo_id=REPO,repo_type="model",parent_commit=before.sha,
        operations=[CommitOperationAdd(path_in_repo="README.md",path_or_fileobj=io.BytesIO(updated.encode("utf-8")))],
        commit_message="Clarify Maya-S IQ2_XXS backbone and Q3_K Engram heading")
    after=api.model_info(REPO,revision=result.oid,files_metadata=True)
    assert identities(before)==identities(after),"A non-README file changed"
    assert read_card(result.oid)==updated,"Published card differs"
    print(json.dumps({"heading_corrected":True,"repo":REPO,"revision":result.oid,"heading":NEW,"all_other_file_identities_preserved":True,"weights_downloaded":False,"full_inference_test_performed":False},ensure_ascii=False),flush=True)

if __name__=="__main__":main()
