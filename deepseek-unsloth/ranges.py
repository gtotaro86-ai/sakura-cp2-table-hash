"""Public pinned exact HTTP ranges, persistent byte budget reserved before I/O."""
import fcntl,json,os,tempfile,urllib.request
from pathlib import Path

def fetch_range(url,start,count,total,journal,limit_bytes):
 if not (0<=start<start+count<=total) or count<=0 or count>64*1024*1024:raise ValueError('Range bounds/buffer limit')
 path=Path(journal);path.parent.mkdir(parents=True,exist_ok=True)
 with path.with_suffix(path.suffix+'.lock').open('a') as lock:
  fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
  j=json.loads(path.read_text()) if path.exists() else {'reserved_bytes':0,'requests':0}
  if j['reserved_bytes']+count>limit_bytes:raise RuntimeError('Full-build source budget exhausted')
  j['reserved_bytes']+=count;j['requests']+=1
  fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='budget-')
  with os.fdopen(fd,'w') as f:json.dump(j,f);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 end=start+count-1
 request=urllib.request.Request(url+f'?sakura_repack={start}-{end}',headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'})
 with urllib.request.urlopen(request,timeout=90) as response:
  if response.status!=206:raise RuntimeError(f'HTTP {response.status}; whole response rejected before body read')
  if response.headers.get('Content-Range')!=f'bytes {start}-{end}/{total}':raise RuntimeError('Content-Range rejected before body read')
  if response.headers.get('Content-Encoding','identity')!='identity':raise RuntimeError('Encoded response rejected')
  length=response.headers.get('Content-Length')
  if length is not None and int(length)!=count:raise RuntimeError('Wrong Content-Length')
  raw=response.read(count+1)
  if len(raw)!=count:raise RuntimeError('Short/excess range body')
 return raw
