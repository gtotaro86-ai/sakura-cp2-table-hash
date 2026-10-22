// Isolated pinned llama.cpp host-gather path. No model inference or GPU execution.
#include "ggml.h"
#include "ggml-backend.h"
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
#include <vector>
#include <sys/mman.h>
#include "upstream/host_rows.cpp"
template<class T> std::vector<T> read_file(const std::string &path) {
 std::ifstream f(path,std::ios::binary|std::ios::ate);if(!f)throw std::runtime_error("sample missing");auto n=f.tellg();f.seekg(0);std::vector<T> b((size_t)n/sizeof(T));f.read((char*)b.data(),n);return b;
}
int main(int argc,char **argv) {
 assert(argc==2);const std::string root=argv[1];constexpr int64_t total=768022850;const size_t bytes=total*110ULL;
 void *p=mmap(nullptr,bytes,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_NORESERVE,-1,0);assert(p!=MAP_FAILED);
 ggml_context *ctx=ggml_init({1<<20,nullptr,true});assert(ctx);
 ggml_tensor *tab=ggml_new_tensor_2d(ctx,GGML_TYPE_Q3_K,256,total);
 auto *buffer=ggml_backend_cpu_buffer_from_ptr(p,bytes);ggml_backend_tensor_alloc(buffer,tab,p);
 assert(tab->nb[1]==110 && llm_graph_host_rows_supported(tab));
 std::ifstream list(root+"/sample-map.tsv");std::vector<int32_t> ids;std::vector<float> expected;
 int64_t start;int count;std::string qp,fp;
 while(list>>start>>count>>qp>>fp) {
  const auto q=read_file<uint8_t>(root+"/"+qp);const auto x=read_file<float>(root+"/"+fp);
  assert(q.size()==(size_t)count*110 && x.size()==(size_t)count*256);
  memcpy((char*)p+start*110,q.data(),q.size());
  for(int i=0;i<count;i++)ids.push_back((int32_t)(start+i));
  expected.insert(expected.end(),x.begin(),x.end());
 }
 assert(ids.size()==192);std::vector<float> out(expected.size());
 llm_graph_host_get_rows(tab,ids.data(),ids.size(),out.data());
 assert(memcmp(out.data(),expected.data(),out.size()*sizeof(float))==0);
 std::reverse(ids.begin(),ids.end());llm_graph_host_get_rows(tab,ids.data(),ids.size(),out.data());
 for(size_t i=0;i<ids.size();i++)assert(memcmp(out.data()+256*i,expected.data()+256*(ids.size()-1-i),256*sizeof(float))==0);
 ggml_backend_buffer_free(buffer);ggml_free(ctx);munmap(p,bytes);
 std::cout<<"PASS: pinned host-gather, 192 real Q3 rows, both layer boundaries, last rows, 64-bit offsets, reverse gathers; no full inference\n";
}
