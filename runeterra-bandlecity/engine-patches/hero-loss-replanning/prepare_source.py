"""Reconstruct fourth plus fifth (optionally sixth) into a new own src child."""
import argparse, hashlib, json, re, stat, zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
ZIP_SHA = 'ecf04d296dcd02fc26219eae26749165fb2890022e4ae7454beb032945751346'
sha = lambda data: hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zip', type=Path, required=True)
    parser.add_argument('--destination', default='src')
    parser.add_argument('--with-preview', action='store_true')
    args = parser.parse_args()
    assert re.fullmatch(r'src(?:-[A-Za-z0-9]+)*', args.destination)
    destination = ROOT / args.destination
    assert not destination.exists(), 'refusing existing source destination'
    assert sha(args.zip.read_bytes()) == ZIP_SHA, 'corresponding-source ZIP mismatch'
    files = {}
    with zipfile.ZipFile(args.zip) as archive:
        pins = json.loads(archive.read('SOURCE-FILES-SHA256.json'))
        for name, expected in pins.items():
            data = archive.read(name)
            assert sha(data) == expected, name
            if not name.startswith('vcmi/'):
                continue
            relative = name[5:]
            parts = PurePosixPath(relative).parts
            assert parts and not PurePosixPath(relative).is_absolute() and '..' not in parts and '\\' not in relative
            assert not stat.S_ISLNK(archive.getinfo(name).external_attr >> 16), name
            files[relative] = data
    families = [ROOT.parent / 'ai-turn-lifecycle', ROOT]
    if args.with_preview:
        families.append(ROOT.parent / 'creature-previews')
    for family in families:
        document = json.loads((family / 'changes.json').read_text())
        if family.name == 'creature-previews':
            assert document['schema'] == 1 and len(document['files']) == 6
            entries = {entry['path']: entry for entry in document['files']}
            assert len(entries) == 6
        else:
            entries = document
        for name, pins in entries.items():
            assert (sha(files[name]) if name in files else None) == pins['before_sha256'], (str(family), name)
            data = (family / 'overlay' / name).read_bytes()
            assert sha(data) == pins['after_sha256'], (str(family), name)
            files[name] = data
    # No source write occurs until every input and incremental before/after pin passed.
    destination.mkdir()
    for name, data in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    inventory = {name: sha(data) for name, data in sorted(files.items())}
    print(json.dumps({'destination': str(destination), 'files': len(inventory), 'inventory_sha256': sha(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode())}))

if __name__ == '__main__':
    main()
