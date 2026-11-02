"""Portable copied-consumer check/compile recipe; never launches VCMI."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def function(text,signature):
    start=text.index(signature);opening=text.index('{',start);depth=1;end=opening+1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return text[start:end]
def check():
    manifest=json.loads((HERE/'selected-manifest.json').read_bytes())
    assert manifest['schema']==2
    for item in manifest['files']:assert sha(HERE/item['path'])==item['sha256'],item['path']
    before=(HERE/'before/client/CServerHandler.cpp').read_text()
    after=(HERE/'patched/client/CServerHandler.cpp').read_text()
    server=(HERE/'support/server/CVCMIServer.cpp').read_text()
    start=(HERE/'support/lib/StartInfo.cpp').read_text()
    entity=(HERE/'support/lib/constants/EntityIdentifiers.cpp').read_text()
    pieces={'debug_before':function(before,'void CServerHandler::debugStartTest('),'debug_after':function(after,'void CServerHandler::debugStartTest('),
        'client_first':function(start,'PlayerColor LobbyInfo::clientFirstColor('),'is_client':function(start,'bool LobbyInfo::isClientColor('),
        'client_my':function(before,'PlayerColor CServerHandler::myFirstColor('),'client_set':function(before,'void CServerHandler::setPlayer('),
        'connected':function(server,'void CVCMIServer::setPlayerConnectedId('),'server_set_full':function(server,'void CVCMIServer::setPlayer('),
        'valid_color':function(entity,'bool PlayerColor::isValidPlayer(')}
    pieces['server_set_prefix']=pieces['server_set_full'].split('\n\t//if that player was somewhere else,')[0]+'\n}'
    validation=server[server.index('\t// prevent loading or starting game where human player is not present on map'):server.index('\n\tgh = std::move(newGH);')]
    pieces['validation']='bool CVCMIServer::validatePlayers()\n{\n'+validation+'\n\treturn true;\n}'
    candidate=pieces['debug_after'];guard='if(playerColor.isValidPlayer())';assert candidate.count(guard)==1
    pieces['debug_never']=candidate.replace(guard,'if(false)')
    pieces['debug_inverted']=candidate.replace(guard,'if(!playerColor.isValidPlayer())')
    for name,text in pieces.items():assert (HERE/'extracted'/f'{name}.inc').read_bytes()==text.encode(),name
    includes=re.findall(r'#include "([^"]+)"',(HERE/'consumer_fixture.cpp').read_text())
    assert all((HERE/name).is_file() for name in includes)
    return {'source_only':True,'selected_files':len(manifest['files']),'actual_method_extracts_verified':len(pieces),'fixture_include_inputs':includes}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check-only',action='store_true');p.add_argument('--vcvars',type=Path);p.add_argument('--revision')
    args=p.parse_args();verification=check()
    if args.check_only:print(json.dumps(verification));return 0
    assert args.vcvars and args.vcvars.is_file() and args.revision and re.fullmatch(r'v[1-9][0-9]*',args.revision)
    target=HERE/'raw-consumer-controls'/args.revision;assert not target.exists();target.mkdir(parents=True)
    env={k.upper():v for k,v in os.environ.items()}
    initialized=subprocess.run(f'cmd /d /s /c ""{args.vcvars.resolve()}" >nul && set"',capture_output=True,text=True,check=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    for line in initialized.stdout.splitlines():
        if '=' in line and not line.startswith('='):key,value=line.split('=',1);env[key.upper()]=value
    compiler=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path'));assert compiler
    temp=target/'temp';temp.mkdir();env.update(TEMP=str(temp),TMP=str(temp))
    volume=target.resolve().anchor
    assert shutil.disk_usage(volume).free>=9*1024**3+128*1024**2
    assert shutil.disk_usage(Path(os.environ.get('SystemRoot','C:/Windows')).anchor).free>=9*1024**3+128*1024**2
    exe=target/'consumer.exe';obj=target/'consumer.obj'
    command=[compiler,'/nologo','/std:c++20','/EHsc','/MD','/W4','/D_ITERATOR_DEBUG_LEVEL=0',str(HERE/'consumer_fixture.cpp'),'/Fo'+str(obj),'/Fe'+str(exe)]
    with (target/'compile.log').open('xb') as log:built=subprocess.run(command,cwd=HERE,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    result={'source_verification':verification,'compile_exit_code':built.returncode,'compiler_sha256':sha(Path(compiler)),'native_vcmi_execution':False,'full_engine_build':False}
    if built.returncode==0:
        with (target/'run.log').open('xb') as log:ran=subprocess.run([str(exe)],cwd=HERE,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=10,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        text=(target/'run.log').read_text();result.update(control_exit_code=ran.returncode,output=text)
        result['ok']=ran.returncode==0 and 'PASS 15 copied-consumer controls' in text and '3 mutants killed' in text
    else:result['ok']=False
    check();assert sum(p.stat().st_size for p in target.rglob('*') if p.is_file())<=128*1024**2
    assert shutil.disk_usage(volume).free>=9*1024**3
    with (target/'result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2));return 0 if result['ok'] else 2
if __name__=='__main__':raise SystemExit(main())
