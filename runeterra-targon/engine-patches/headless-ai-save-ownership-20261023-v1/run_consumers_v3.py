"""Compile actual save command/native ownership/protocol consumers in owned report only."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
HERE=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def extract(text,prefix):
    start=text.index(prefix);brace=text.index('{',start);depth=1;end=brace+1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return text[start:end]+'\n'
def assemble(method):
    fixture=(HERE/'fixture-v3.hpp').read_text()
    fixture=fixture.replace('enum class GameConnectionID : int8_t {INVALID=-1,FIRST_CONNECTION=1};','').replace('enum class PlayerConnectionID : int8_t {INVALID=-1,PLAYER_AI=0,FIRST_HUMAN=1};','')
    enums=''
    for name in ('GameConnectionID','PlayerConnectionID'):
        enums+=extract((HERE/('official66fa/lib/serializer/'+name+'.h')).read_text(),'enum class '+name)+';\n'
    fixture=fixture.replace('struct PlayerColor {',enums+'struct PlayerColor {')
    start=(HERE/'official66fa/lib/StartInfo.cpp').read_text();functions=''
    for prefix in ('bool PlayerSettings::isControlledByAI(', 'bool PlayerSettings::isControlledByHuman(',
       'bool LobbyInfo::isClientHost(','std::set<PlayerColor> LobbyInfo::getAllClientPlayers(',
       'std::vector<PlayerConnectionID> LobbyInfo::getConnectedPlayerIdsForClient(',
       'bool LobbyInfo::isClientColor('):functions+=extract(start,prefix)
    functions+=extract((HERE/'official66fa/client/CServerHandler.cpp').read_text(),'bool CServerHandler::isMyColor(')
    functions+=extract((HERE/'official66fa/server/CVCMIServer.cpp').read_text(),'bool CVCMIServer::hasPlayerAt(')
    functions+=extract((HERE/'official66fa/lib/serializer/GameConnection.cpp').read_text(),'std::shared_ptr<INetworkConnection> GameConnection::getConnection(')
    packet=extract((HERE/'official66fa/lib/networkPacks/PacksForServer.h').read_text(),'struct DLL_LINKAGE SaveGame :')+';\n'
    callback=extract((HERE/'official66fa/lib/callback/CCallback.cpp').read_text(),'void CCallback::save(')
    return fixture+functions+packet+callback+method+(HERE/'cases-v3.cpp').read_text()
def main(vcvars,revision):
    target=HERE/'raw-consumer-controls'/revision;assert not target.exists();target.mkdir(parents=True)
    initialized=subprocess.run(f'cmd /d /s /c ""{vcvars}" >nul && set"',capture_output=True,text=True,check=True)
    env=dict(os.environ)
    for line in initialized.stdout.splitlines():
        if '=' in line and not line.startswith('='):key,value=line.split('=',1);env[key]=value
    compiler=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path'));assert compiler
    baseline=extract((HERE/'before-v3/client/ClientCommandManager.cpp').read_text(),'void ClientCommandManager::handleSaveCommand(')
    candidate=extract((HERE/'candidate-v3/client/ClientCommandManager.cpp').read_text(),'void ClientCommandManager::handleSaveCommand(')
    variants={'before-v3':baseline,'candidate':candidate,
      'mutant-human-only-owner':candidate.replace('!ownedPlayers.count(player)','!server.isMyColor(player)'),
      'mutant-all-interface-colors':candidate.replace('!ownedPlayers.count(player)','false'),
      'mutant-invalid-connection':candidate.replace('connection->connectionID == GameConnectionID::INVALID','false'),
      'mutant-ignore-transport':candidate.replace(' || !transport',''),
      'mutant-ignore-player-status':candidate.replace('state->second.status != EPlayerStatus::INGAME','false'),
      'mutant-no-state-mutex':candidate.replace('std::unique_lock stateLock(CGameState::mutex);',''),
      'mutant-claim-saved':candidate.replace('Save request submitted: ','Game saved as: '),
      'mutant-observer-replay':candidate.replace('client.observerMode || server.isReplayActive()','false')}
    receipt={'native_execution':False,'private_source_modified':False,'compiler_sha256':sha(Path(compiler).read_bytes()),
      'scope':'Compiled verbatim save method, actual LobbyInfo/PlayerSettings/connection ownership methods, native enums/SaveGame and CCallback::save with bounded request/thread dependencies; no VCMI network, serializer, process or native save.', 'variants':{}}
    for name,method in variants.items():
        folder=target/name;folder.mkdir();source=folder/'consumer.cpp';source.write_text(assemble(method),encoding='utf-8',newline='\n')
        exe=folder/'consumer.exe';obj=folder/'consumer.obj'
        command=[compiler,'/nologo','/std:c++17','/EHsc','/W4','/Od',str(source),'/Fe:'+str(exe),'/Fo:'+str(obj)]
        built=subprocess.run(command,cwd=folder,env=env,capture_output=True,timeout=60)
        (folder/'compile.stdout.log').write_bytes(built.stdout);(folder/'compile.stderr.log').write_bytes(built.stderr)
        item={'compile_exit_code':built.returncode,'source_sha256':sha(source.read_bytes())}
        if built.returncode==0:
            ran=subprocess.run([str(exe)],cwd=folder,env=env,capture_output=True,timeout=15)
            (folder/'run.stdout.log').write_bytes(ran.stdout);(folder/'run.stderr.log').write_bytes(ran.stderr)
            summary=re.search(rb'TOTAL\|(\d+)\|(\d+)',ran.stdout)
            item.update(run_exit_code=ran.returncode,cases=int(summary[1]) if summary else None,failures=int(summary[2]) if summary else None,binary_sha256=sha(exe.read_bytes()))
        receipt['variants'][name]=item;print(name,json.dumps(item))
    receipt['passed']=all(x['compile_exit_code']==0 for x in receipt['variants'].values()) and receipt['variants']['candidate'].get('run_exit_code')==0 and all(x.get('run_exit_code')==1 for name,x in receipt['variants'].items() if name!='candidate')
    (target/'result.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n');return receipt['passed']
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--vcvars',type=Path,required=True);p.add_argument('--revision',required=True);args=p.parse_args();assert re.fullmatch(r'v[1-9][0-9]*',args.revision)
    raise SystemExit(0 if main(args.vcvars.resolve(),args.revision) else 2)
