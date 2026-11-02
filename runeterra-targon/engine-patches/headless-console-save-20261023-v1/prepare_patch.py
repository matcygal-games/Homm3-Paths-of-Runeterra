"""Prepare isolated official66fa console-save patch; never edits external sources."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import urllib.request

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
COMMIT='66fa496c6328a276c4eb14c0011b3a9d751dfac3'
PATHS=(
 'client/ClientCommandManager.cpp','client/ClientCommandManager.h','client/Client.h','client/Client.cpp',
 'client/CServerHandler.cpp','client/CServerHandler.h','client/GameInstance.cpp','client/GameInstance.h',
 'client/GameEngine.cpp','client/adventureMap/CInGameConsole.cpp','clientapp/EntryPoint.cpp',
 'lib/callback/CCallback.cpp','lib/callback/CBattleCallback.cpp','lib/CPlayerState.h',
 'lib/network/NetworkInterface.h','lib/network/NetworkHandler.cpp','lib/network/NetworkConnection.cpp',
 'lib/networkPacks/PacksForServer.h','server/NetPacksServer.cpp','server/CGameHandler.cpp',
 'server/activities/Activity.cpp','server/activities/MapActivities.cpp','server/activities/VisitActivities.cpp',
 'lib/constants/Enumerations.h','license.txt','AUTHORS.h',
 'lib/gameState/CGameState.h','AI/Nullkiller2/AIGateway.cpp','lib/serializer/GameConnection.cpp',
 'lib/serializer/GameConnection.h',
 'lib/UnlockGuard.h','clientsdl3/events/InputHandler.cpp','clientsdl3/events/InputHandler.h',
 'clientsdl2/events/InputHandler.cpp','clientsdl2/events/InputHandler.h',
 'lib/CConsoleHandler.cpp','lib/callback/IBattleCallback.h','client/CPlayerInterface.cpp',
)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def jb(value): return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def write_new(path,raw):
    if not path.resolve().is_relative_to(HERE): raise ValueError('Outside owned directory')
    if path.exists() and path.read_bytes()!=raw: raise ValueError('Preserve existing output: '+str(path.relative_to(HERE)))
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw)

def prepare(source,tree_path):
    tree_raw=tree_path.read_bytes()
    assert sha(tree_raw)=='775085011d61128840a881fd065938deebba81650e2af6cad0c6876da95b5182'
    tree=json.loads(tree_path.read_bytes()); assert tree['sha']==COMMIT and not tree['truncated']
    write_new(HERE/'official-source-tree.json',tree_raw)
    entries={item['path']:item['sha'] for item in tree['tree'] if item['type']=='blob'}
    pins={}
    for name in PATHS:
        raw=(source/name).read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob!=entries[name] and name=='client/Client.cpp':
            raw=(HERE/'upstream'/name).read_bytes()
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob!=entries[name] and name=='AI/Nullkiller2/AIGateway.cpp':
            url=f'https://raw.githubusercontent.com/vcmi/vcmi/{COMMIT}/{name}'
            raw=(HERE/'upstream'/name).read_bytes() if (HERE/'upstream'/name).exists() else urllib.request.urlopen(url,timeout=30).read()
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert blob==entries[name], 'Official source mismatch: '+name
        write_new(HERE/'upstream'/name,raw)
        pins[name]={'sha256':sha(raw),'official_git_blob_sha1':blob,
                    'url':f'https://raw.githubusercontent.com/vcmi/vcmi/{COMMIT}/{name}'}
    name='client/ClientCommandManager.cpp'
    before=(HERE/'upstream'/name).read_text(encoding='utf-8')
    method=(HERE/'handleSaveCommand.cpp').read_text(encoding='utf-8')
    start=before.index('void ClientCommandManager::handleSaveCommand(')
    end=before.index('\nvoid ClientCommandManager::handleLoadCommand(',start)
    after=before[:start]+method.rstrip()+'\n'+before[end:]
    after=after.replace('#include "../lib/logging/VisualLogger.h"',
        '#include "../lib/logging/VisualLogger.h"\n#include "../lib/network/NetworkInterface.h"\n#include "../lib/networkPacks/PacksForServer.h"')
    write_new(HERE/'patched-v3'/name,after.encode())
    patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    write_new(HERE/'0003-make-console-save-use-owned-headless-player.patch',patch.encode())
    write_new(HERE/'source-provenance-v4.json',jb({'status':'authored configuration','native_execution':False,
        'source_commit':COMMIT,'official_tree_sha256':sha(tree_path.read_bytes()),'files':pins,
        'patch_inputs':{name:{'before_sha256':sha((HERE/'upstream'/name).read_bytes()),'after_sha256':sha(after.encode())}},
        'patch_sha256':sha(patch.encode()),'license':'GPL-2.0-or-later; upstream notices and full license retained',
        'scope':'Source identity only. No publisher source-to-binary attestation or native gameplay.'}))
    print(json.dumps({'source_files':len(pins),'patch_sha256':sha(patch.encode())}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--official-source',type=Path,required=True)
    parser.add_argument('--official-tree',type=Path,default=HERE/'official-source-tree.json')
    args=parser.parse_args(); prepare(args.official_source.resolve(),args.official_tree.resolve())
