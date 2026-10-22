"""Bounded GGUF metadata parser; hashes complete large arrays for addressing parity."""
import hashlib,json,struct
class Reader:
 def __init__(self,data):self.data=data;self.pos=0
 def read(self,n):
  if n<0 or self.pos+n>len(self.data):raise ValueError('Metadata bounds')
  b=self.data[self.pos:self.pos+n];self.pos+=n;return b
 def num(self,fmt):return struct.unpack('<'+fmt,self.read(struct.calcsize('<'+fmt)))[0]
 def string(self,keep=True):
  n=self.num('Q');b=self.read(n);return b.decode() if keep else None
 def value(self,t,keep):
  formats={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
  if t in formats:
   n=self.num(formats[t]);return n if keep else None
  if t==8:return self.string(keep)
  if t==9:
   child=self.num('I');n=self.num('Q')
   if n>2000000:raise ValueError('Metadata array cap')
   if n>128 and child in formats:
    data=self.read(n*struct.calcsize('<'+formats[child]))
    return {'count':n,'type':child,'sha256':hashlib.sha256(data).hexdigest()} if keep else None
   values=[self.value(child,keep) for _ in range(n)];return values if keep else None
  raise ValueError('Unsupported metadata value')
def parse(data,metadata_only=False):
 r=Reader(data)
 if r.read(4)!=b'GGUF' or r.num('I')!=3:raise ValueError('GGUFv3 required')
 nt,nk=r.num('Q'),r.num('Q');meta={}
 if nk>10000 or nt>10000:raise ValueError('Metadata count cap')
 for _ in range(nk):
  key=r.string();typ=r.num('I');keep=key.startswith(('split.','deepseek41.ple.','deepseek41.engram.')) or key in ['general.architecture','deepseek41.embedding_length_per_layer_input']
  value=r.value(typ,keep)
  if keep:meta[key]=value
 if metadata_only and (nt!=0 or r.pos!=len(data)):raise ValueError('Expected complete metadata-only shard')
 return nt,meta,r
def addressing(meta):return {k:v for k,v in meta.items() if not k.startswith('split.')}
def table(data):
 nt,meta,r=parse(data)
 if nt!=1:raise ValueError('One isolated table required')
 name=r.string();nd=r.num('I')
 if nd!=2:raise ValueError('Two-dimensional table required')
 width,rows,typ,offset=r.num('Q'),r.num('Q'),r.num('I'),r.num('Q')
 if width!=256 or offset!=0 or r.pos>192:raise ValueError('Audited table geometry required')
 return {'name':name,'rows':rows,'type':typ,'split':meta}
