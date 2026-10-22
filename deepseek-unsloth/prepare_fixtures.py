"""Restore only tiny pinned row fixtures, not a model download."""
import base64,hashlib,json,zlib
from pathlib import Path
root=Path(__file__).resolve().parent
for f in json.loads((root/'fixtures.json').read_text())['files']:
 path=root/'evidence'/f['name'];assert path.parent==root/'evidence'
 data=zlib.decompress(base64.b64decode(f['zlib_base64']))
 assert len(data)==f['size'] and hashlib.sha256(data).hexdigest()==f['sha256']
 path.parent.mkdir(exist_ok=True);path.write_bytes(data)
