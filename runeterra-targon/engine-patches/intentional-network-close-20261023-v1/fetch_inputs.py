"""Copy/fetch only immutable official commit inputs into this isolated patch folder."""
from pathlib import Path
import hashlib
import json
import urllib.request
import datetime

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'turn-lifecycle-20261023-v1'
COMMIT = '66fa496c6328a276c4eb14c0011b3a9d751dfac3'
TREE_SHA = '775085011d61128840a881fd065938deebba81650e2af6cad0c6876da95b5182'
PATHS = ('server/CVCMIServer.cpp', 'server/CVCMIServer.h', 'server/NetPacksLobbyServer.cpp',
         'server/LobbyNetPackVisitors.h', 'lib/network/NetworkConnection.cpp', 'lib/network/NetworkConnection.h',
         'lib/network/NetworkInterface.h', 'lib/serializer/GameConnection.cpp', 'lib/serializer/GameConnection.h',
         'lib/networkPacks/PacksForLobby.h', 'client/CServerHandler.cpp', 'server/CMakeLists.txt',
         'lib/network/NetworkHandler.cpp', 'server/CVCMIServer.h', 'license.txt')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    tree_raw = (PRIOR / 'official-source-tree.json').read_bytes()
    assert sha(tree_raw) == TREE_SHA
    entries = {v['path']: v for v in json.loads(tree_raw)['tree'] if v['type'] == 'blob'}
    output = HERE / 'provenance.json'
    if output.exists():
        raise ValueError('Preserve existing provenance')
    rows = []
    for name in dict.fromkeys(PATHS):
        expected = entries[name]['sha']
        source = PRIOR / 'upstream' / name
        url = f'https://raw.githubusercontent.com/vcmi/vcmi/{COMMIT}/{name}'
        raw = source.read_bytes() if source.exists() else urllib.request.urlopen(url, timeout=30).read()
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        assert blob == expected, (name, blob, expected)
        target = HERE / 'upstream' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == raw
        else:
            target.write_bytes(raw)
        rows.append({'path': name, 'official_url': url, 'sha256': sha(raw), 'git_blob_sha1': blob,
                     'official_tree_blob_sha1': expected, 'source': str(source) if source.exists() else url})
    value = {'commit': COMMIT, 'access_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'official_tree_receipt': str(PRIOR / 'official-source-tree.json'), 'official_tree_sha256': TREE_SHA,
        'official_commit_metadata_sha256': sha((PRIOR / 'official-commit.json').read_bytes()),
        'source_scope': 'Immutable official commit consumers only; existing private checkout/build untouched', 'sources': rows}
    output.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'files': len(rows), 'provenance_sha256': sha(output.read_bytes())}))


if __name__ == '__main__':
    main()
