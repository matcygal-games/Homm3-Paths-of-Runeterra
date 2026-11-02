"""Compile copied actual consumers only. No full engine build or game execution."""
import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path
import prepare_patch as p

def extract(text,prefix):
    start=text.index(prefix); brace=text.index('{',start); depth=1; pos=brace+1
    while depth:
        if text[pos]=='{': depth+=1
        elif text[pos]=='}': depth-=1
        pos+=1
    return text[start:pos]+'\n'

def prepare_consumer(method):
    packet=extract((p.HERE/'upstream/lib/networkPacks/PacksForServer.h').read_text(),
                   'struct DLL_LINKAGE SaveGame :')+';\n'
    callback=extract((p.HERE/'upstream/lib/callback/CCallback.cpp').read_text(),'void CCallback::save(')
    return '#include "../../tests/fixture.hpp"\n'+packet+callback+method+'\n'+(p.HERE/'tests/cases.cpp').read_text()

def main(vcvars,revision):
    target=p.HERE/'raw-receipts'/revision
    if target.exists(): raise ValueError('Preserve previous regression execution')
    target.mkdir(parents=True)
    environment=subprocess.run(f'cmd /d /s /c ""{vcvars}" >nul && set"',capture_output=True,text=True,check=True)
    env=dict(os.environ)
    for line in environment.stdout.splitlines():
        if '=' in line and not line.startswith('='):
            key,value=line.split('=',1);env[key]=value
    compiler=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path'))
    if not compiler: raise ValueError('MSVC compiler missing from supplied developer environment')
    original=extract((p.HERE/'upstream/client/ClientCommandManager.cpp').read_text(),'void ClientCommandManager::handleSaveCommand(')
    patched=(p.HERE/'handleSaveCommand.cpp').read_text()
    variants={'upstream':original,'patched':patched,
        'mutation-observer':patched.replace('client.observerMode || server.isReplayActive()', 'false'),
        'mutation-foreign-owner':patched.replace('!server.isMyColor(player)', 'false'),
        'mutation-unsynchronized-ai-producer':patched.replace('std::unique_lock stateLock(CGameState::mutex);',''),
        'mutation-unsynchronized-human-command':patched.replace('std::scoped_lock interfaceLock(ENGINE->interfaceMutex);',''),
        'mutation-false-saved-message':patched.replace('Save request submitted: ', 'Game saved as: '),
        'mutation-no-headless-route':patched.replace('if(!settings["session"]["headless"].Bool())','if(true)')}
    receipt={'scope':'Compiled verbatim console method, native SaveGame definition and CCallback::save against bounded dependency fixtures. No VCMI game, full engine build, real network, UI or serializer execution.',
        'compiler_sha256':p.sha(Path(compiler).read_bytes()),'compiler':compiler,'variants':{}}
    for name,method in variants.items():
        folder=target/name;folder.mkdir()
        source=folder/'consumer.cpp';source.write_text(prepare_consumer(method),encoding='utf-8',newline='\n')
        # Include path is a portable relative dependency; compiler outputs remain outside selection.
        text=source.read_text().replace('#include "../../tests/fixture.hpp"','#include "../../../tests/fixture.hpp"')
        source.write_text(text,encoding='utf-8',newline='\n')
        exe=folder/'consumer.exe';obj=folder/'consumer.obj'
        command=[compiler,'/nologo','/std:c++17','/EHsc','/W4','/Od',str(source),'/Fe:'+str(exe),'/Fo:'+str(obj)]
        compiled=subprocess.run(command,cwd=folder,env=env,capture_output=True,timeout=60)
        (folder/'compile.stdout.log').write_bytes(compiled.stdout);(folder/'compile.stderr.log').write_bytes(compiled.stderr)
        item={'compile_command':command,'compile_exit_code':compiled.returncode,'source_sha256':p.sha(source.read_bytes())}
        if compiled.returncode==0:
            run_command=[str(exe)]+(['upstream'] if name=='upstream' else [])
            executed=subprocess.run(run_command,cwd=folder,env=env,capture_output=True,timeout=15)
            (folder/'run.stdout.log').write_bytes(executed.stdout);(folder/'run.stderr.log').write_bytes(executed.stderr)
            summary=re.search(rb'TOTAL\|(\d+)\|(\d+)',executed.stdout)
            item.update(run_command=run_command,run_exit_code=executed.returncode,binary_sha256=p.sha(exe.read_bytes()),
                cases=int(summary[1]) if summary else None,failures=int(summary[2]) if summary else None)
        receipt['variants'][name]=item
        print(name,item.get('compile_exit_code'),item.get('run_exit_code'),item.get('cases'),item.get('failures'))
    checked=subprocess.run(['git','apply','--check',str(p.HERE/'0003-make-console-save-use-owned-headless-player.patch')],
        cwd=p.HERE/'upstream',capture_output=True)
    (target/'apply-check.stdout.log').write_bytes(checked.stdout);(target/'apply-check.stderr.log').write_bytes(checked.stderr)
    receipt['apply_check_exit_code']=checked.returncode
    receipt['passed']=checked.returncode==0 and all(v.get('compile_exit_code')==0 for v in receipt['variants'].values()) and \
        receipt['variants']['patched'].get('run_exit_code')==0 and receipt['variants']['upstream'].get('run_exit_code')==1 and \
        all(receipt['variants'][k].get('run_exit_code')==1 for k in variants if k.startswith('mutation-'))
    p.write_new(target/'result.json',p.jb(receipt))
    return receipt['passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vcvars',type=Path,required=True)
    parser.add_argument('--revision',required=True)
    args=parser.parse_args()
    if not re.fullmatch('v[1-9][0-9]*',args.revision): parser.error('Use a bounded new revision')
    raise SystemExit(0 if main(args.vcvars.resolve(),args.revision) else 2)
