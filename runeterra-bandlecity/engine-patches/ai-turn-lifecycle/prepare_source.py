"""Recreate a separate candidate from its pinned corresponding-source ZIP and own overlay."""
from __future__ import annotations
import argparse, hashlib, json, re, stat, zipfile
from pathlib import Path, PurePosixPath
ROOT=Path(__file__).resolve().parent
ZIP_SHA256="ecf04d296dcd02fc26219eae26749165fb2890022e4ae7454beb032945751346"
def sha(data): return hashlib.sha256(data).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument("--zip",type=Path,required=True);p.add_argument("--destination",default="src-reproduced")
    args=p.parse_args()
    assert re.fullmatch(r"src(?:-[A-Za-z0-9]+)*",args.destination),"destination must be a single own src-prefixed child"
    destination=ROOT/args.destination
    assert not destination.exists(),"refusing existing source destination"
    assert sha(args.zip.read_bytes())==ZIP_SHA256,"corresponding-source ZIP hash mismatch"
    changes=json.loads((ROOT/"changes.json").read_text())
    files={}
    with zipfile.ZipFile(args.zip) as z:
        pins=json.loads(z.read("SOURCE-FILES-SHA256.json"))
        for name,expected in pins.items():
            data=z.read(name);assert sha(data)==expected,name
            if not name.startswith("vcmi/"): continue
            rel=name[5:];parts=PurePosixPath(rel).parts
            assert parts and not PurePosixPath(rel).is_absolute() and ".." not in parts and "\\" not in rel
            assert not stat.S_ISLNK(z.getinfo(name).external_attr>>16),name
            files[rel]=data
    for rel,pins in changes.items():
        assert (sha(files[rel]) if rel in files else None)==pins["before_sha256"],rel
        data=(ROOT/"overlay"/rel).read_bytes();assert sha(data)==pins["after_sha256"],rel
        files[rel]=data
    # All validation occurs before the only writes, within a new owned source child.
    destination.mkdir()
    for rel,data in files.items():
        target=destination/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    inventory={rel:sha(data) for rel,data in sorted(files.items())}
    print(json.dumps({"destination":str(destination),"files":len(inventory),"inventory_sha256":sha(json.dumps(inventory,sort_keys=True,separators=(",", ":")).encode())}))
if __name__=="__main__":main()
