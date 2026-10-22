"""Compile CUDA translation units and LINK the real GPU test, never execute it.

Requires a patched Maya checkout and an existing CUDA SDK. No package install,
cloud allocation, credentials, model reads or GPU execution are performed.
"""
import argparse,hashlib,json,subprocess,time
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sdk',required=True,type=Path)
    ap.add_argument('--maya',required=True,type=Path);ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--arch',default='sm_80');args=ap.parse_args()
    sdk=args.sdk.resolve();maya=args.maya.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    nvcc=sdk/'bin/nvcc'
    if not (maya/'src/ds4/ds4_q3k.cuh').exists():raise SystemExit('Patched Maya checkout required')
    flags=[str(nvcc),'-std=c++17','-arch='+args.arch,'-I'+str(sdk/'include/cccl'),'-I'+str(maya/'include')]
    commands=[flags+['-c',str(maya/'src/ds4/ds4_kernels.cu'),'-o',str(out/'kernels.o')],
        flags+['-c',str(maya/'tests/sakura_engram_q3_test.cu'),'-o',str(out/'gpu-test.o')],
        flags+['-DSTRATA_VERSION="1.1.22-sakura-q3"','-I'+str(maya/'include'),
            '-I'+str(maya/'third_party/ggml'),'-c',str(maya/'src/ds4/ds4_model.cu'),'-o',str(out/'model.o')],
        ['g++','-std=c++17','-O2','-c',str(maya/'src/ds4/ds4_host_ar.cpp'),'-o',str(out/'host-ar.o')],
        flags+['-I'+str(maya/'third_party/ggml'),'-c',str(maya/'src/ds4/ds4_iq.cu'),'-o',str(out/'iq.o')],
        ['g++','-std=c++17','-O2','-I'+str(maya/'third_party/ggml'),'-c',str(maya/'src/ds4/ds4_iq_cpu.cpp'),'-o',str(out/'iq-cpu.o')],
        flags+[str(out/'gpu-test.o'),str(out/'kernels.o'),str(out/'host-ar.o'),'-L'+str(sdk/'lib'),'-o',str(out/'sakura-engram-q3-gpu-test')]]
    results=[]
    for n,command in enumerate(commands):
        tick=time.perf_counter();log=out/f'compile-{n}.log'
        with log.open('w') as f:result=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
        results.append({'command':command,'returncode':result.returncode,'seconds':time.perf_counter()-tick,
            'log':log.name})
        if result.returncode:break
    report={'cuda_compiler':subprocess.check_output([str(nvcc),'--version'],text=True),
        'maya_revision':'ffe2e5e53fd5254e7f3492a20e8ad2b51b26a197 plus Sakura patch',
        'cuda_translation_units_compiled':len(results)==len(commands) and all(x['returncode']==0 for x in results),
        'iq1_translation_units_compiled':len(results)==len(commands) and all(x['returncode']==0 for x in results),
        'execution_context':'ChatGPT Work Linux cloud CPU compiler; no GPU execution; not a GitHub runner measurement',
        'gpu_test_linked':len(results)==len(commands) and results[-1]['returncode']==0,
        'full_maya_executable_linked':False,'gpu_executed':False,'hip_compiled':False,
        'windows_build':False,'model_inference_tested':False,'results':results,
        'patch_sha256':hashlib.sha256((Path(__file__).resolve().parent/'maya-v1.1.22-q3.patch').read_bytes()).hexdigest(),
        'source_sha256':{str(p.relative_to(maya)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [maya/'src/ds4/ds4_model.cu',maya/'src/ds4/ds4_kernels.cu',
                      maya/'src/ds4/ds4_q3k.cuh',maya/'tests/sakura_engram_q3_test.cu']}}
    (out/'cuda-build-status.json').write_text(json.dumps(report,indent=2)+'\n')
    print('CUDA compile/link PASS; NO GPU execution' if report['gpu_test_linked'] else 'CUDA compile FAIL')
    raise SystemExit(0 if report['gpu_test_linked'] else 1)
if __name__=='__main__':main()
