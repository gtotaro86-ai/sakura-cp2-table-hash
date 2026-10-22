"""Bounded, seekable repack of existing Q3 payloads. No quantization or implicit network."""
import hashlib,io,struct
from collections import OrderedDict

def descriptor(header):
 if len(header)!=192 or header[:8]!=b'GGUF\x03\0\0\0' or struct.unpack_from('<Q',header,8)[0]!=1:raise ValueError('One-tensor GGUF v3 with 192-byte header required')
 pos=106;n=struct.unpack_from('<Q',header,pos)[0];pos+=8
 if not 1<=n<=40:raise ValueError('Tensor name length')
 name=header[pos:pos+n].decode();pos+=n
 dims,width,rows,typ,offset=struct.unpack_from('<IQQIQ',header,pos)
 if dims!=2 or width!=256 or rows<=0 or typ!=11 or offset!=0:raise ValueError('Only correctly typed width-256 Q3_K tables supported')
 return name,rows

def sha(data):return hashlib.sha256(data).hexdigest()

class Assembly(io.RawIOBase):
 def __init__(self,header,parts,source,block_bytes=64*1024*1024,cache_blocks=2,max_read=64*1024*1024):
  super().__init__();name,rows=descriptor(header)
  if name!='per_layer_token_embd.weight' or rows!=sum(x['rows'] for x in parts):raise ValueError('Combined rows/name mismatch')
  if len(parts)!=2 or not 1<=block_bytes<=64*1024*1024 or not 1<=cache_blocks<=2:raise ValueError('Bounded two-part assembly required')
  for part,expected_name in zip(parts,['blk.1.engram_embd.weight','blk.14.engram_embd.weight']):
   n,r=descriptor(bytes.fromhex(part['header_hex']))
   if n!=expected_name or r!=part['rows'] or part['size']!=192+r*110:raise ValueError('Part layout mismatch')
  self.header=header;self.parts=parts;self.source=source;self.block_bytes=block_bytes;self.cache_blocks=cache_blocks;self.max_read=max_read
  self.pos=0;self.size=192+rows*110;self.cache=OrderedDict();self.track=[None,None];self.verified_passes=[0,0]
 def readable(self):return not self.closed
 def seekable(self):return not self.closed
 def tell(self):self._checkClosed();return self.pos
 def seek(self,offset,whence=io.SEEK_SET):
  self._checkClosed()
  if not isinstance(offset,int) or whence not in (0,1,2):raise ValueError('Invalid seek')
  p=offset+(0 if whence==0 else self.pos if whence==1 else self.size)
  if p<0:raise ValueError('Negative seek')
  self.pos=p;return p
 def _block(self,part_idx,index):
  key=(part_idx,index)
  if key in self.cache:self.cache.move_to_end(key);return self.cache[key]
  part=self.parts[part_idx];payload=part['rows']*110;start=index*self.block_bytes;count=min(self.block_bytes,payload-start)
  if count<=0:raise ValueError('Out-of-bounds source block')
  data=self.source(part_idx,192+start,count)
  if len(data)!=count:raise OSError('Source short read')
  state=self.track[part_idx]
  if index==0 and (state is None or state['next']!=0):
   state={'next':0,'digest':hashlib.sha256(bytes.fromhex(part['header_hex']))};self.track[part_idx]=state
  if state is not None and state['next']==index:
   state['digest'].update(data);state['next']+=1
   if start+count==payload:
    if state['digest'].hexdigest()!=part['sha256']:raise RuntimeError('Pinned Q3 source full SHA256 mismatch')
    self.verified_passes[part_idx]+=1
  self.cache[key]=data
  while len(self.cache)>self.cache_blocks:self.cache.popitem(last=False)
  return data
 def read(self,size=-1):
  self._checkClosed()
  if size is None or size<0:size=max(0,self.size-self.pos)
  if size>self.max_read:raise ValueError('Read exceeds bounded RAM request')
  todo=min(size,max(0,self.size-self.pos));out=[]
  while todo:
   if self.pos<192:part=self.header[self.pos:min(192,self.pos+todo)]
   else:
    payload=self.pos-192;first_size=self.parts[0]['rows']*110;pi=0 if payload<first_size else 1
    local=payload if pi==0 else payload-first_size;block=self._block(pi,local//self.block_bytes);off=local%self.block_bytes
    part=block[off:off+todo]
   if not part:raise OSError('Unexpected empty source block')
   out.append(part);self.pos+=len(part);todo-=len(part)
  return b''.join(out)
 def readinto(self,buffer):
  view=memoryview(buffer).cast('B');data=self.read(len(view));view[:len(data)]=data;return len(data)
 def close(self):self.cache.clear();super().close()

class BufferedAssembly(io.BufferedIOBase):
 def __init__(self,raw):super().__init__();self.raw=raw
 def readable(self):return not self.closed
 def seekable(self):return not self.closed
 def tell(self):self._checkClosed();return self.raw.tell()
 def seek(self,offset,whence=io.SEEK_SET):self._checkClosed();return self.raw.seek(offset,whence)
 def read(self,size=-1):self._checkClosed();return self.raw.read(size)
 def readinto(self,buffer):self._checkClosed();return self.raw.readinto(buffer)
 def __iter__(self):
  while True:
   b=self.read(4*1024*1024)
   if not b:break
   yield b
 def close(self):
  if not self.closed:self.raw.close()
  super().close()
