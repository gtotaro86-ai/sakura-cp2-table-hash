"""Update only the authorized model card, never download or mutate weights."""
import hashlib
import json
import os
from pathlib import Path

REPO = 'webmp3/Sakura-DeepSeek-V4.1-Flash-1017-Engram-Q3_K-GGUF'


def weights(info):
    result = {}
    for file in info.siblings or []:
        if file.rfilename.endswith('.gguf'):
            if file.lfs is None:
                raise RuntimeError('Missing GGUF LFS hash')
            result[file.rfilename] = (file.size, file.lfs.sha256)
    if len(result) != 6:
        raise RuntimeError('Expected six existing GGUF files')
    return result


def main():
    if (os.environ.get('GITHUB_ACTIONS') != 'true'
            or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted'
            or os.environ.get('REPO_VISIBILITY') != 'public'):
        raise RuntimeError('Public hosted cloud workflow required')
    token = os.environ.get('HF_TOKEN')
    if not token:
        raise RuntimeError('HF_TOKEN must be a protected Actions secret')
    from huggingface_hub import HfApi, ModelCard, CommitOperationAdd, hf_hub_download
    new = Path(__file__).with_name('MODEL_CARD.md').read_bytes()
    if not new.startswith(b'---\n') or len(new) > 100000:
        raise RuntimeError('Bounded model card with YAML required')
    if any(word in new.lower() for word in (b'gtotaro86', b'sakura-cp2-table-hash', b'experimentell')):
        raise RuntimeError('Forbidden public model-card reference')
    if b'No full inference test has been performed.' not in new:
        raise RuntimeError('Required inference notice missing')
    card = ModelCard(new.decode('utf-8'))
    if card.data.base_model != 'peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF':
        raise RuntimeError('Direct quantization source must be Maya-S')
    card.validate()
    api = HfApi(token=token)
    before = api.model_info(REPO, files_metadata=True)
    if before.private:
        raise RuntimeError('Expected public destination')
    baseline = weights(before)
    meta = list(api.get_paths_info(repo_id=REPO, paths=['README.md'], revision=before.sha))
    if len(meta) != 1 or meta[0].size > 100000:
        raise RuntimeError('Unexpected existing model-card size')
    old_path = hf_hub_download(REPO, 'README.md', revision=before.sha, token=token)
    old = Path(old_path).read_bytes()
    if old == new:
        revision = before.sha
    else:
        commit = api.create_commit(repo_id=REPO, parent_commit=before.sha,
            operations=[CommitOperationAdd(path_in_repo='README.md', path_or_fileobj=new)],
            commit_message='Publish complete English model card with source provenance and comparisons')
        revision = commit.oid
    after = api.model_info(REPO, revision=revision, files_metadata=True)
    if weights(after) != baseline:
        raise RuntimeError('GGUF file inventory changed during documentation update')
    actual = Path(hf_hub_download(REPO, 'README.md', revision=revision, token=token)).read_bytes()
    if actual != new:
        raise RuntimeError('Published model card differs from prepared document')
    ModelCard(actual.decode('utf-8')).validate()
    result = {'repository': REPO, 'revision': revision, 'yaml_validated': True,
              'readme_sha256': hashlib.sha256(actual).hexdigest(),
              'gguf_files_unchanged': 6, 'model_weight_bytes_downloaded': 0,
              'model_weight_bytes_uploaded': 0}
    print(json.dumps(result, indent=2))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        Path(os.environ['GITHUB_STEP_SUMMARY']).write_text(
            'Model card updated; all six weight files unchanged.\n\n```json\n'
            + json.dumps(result, indent=2) + '\n```\n')


if __name__ == '__main__':
    main()
