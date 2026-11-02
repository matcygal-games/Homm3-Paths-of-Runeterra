"""Isolated Bandle engine candidate. Never launches client/server; test invokes vcmitest only."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parents[2]
SOURCE=ROOT/"src"
BUILD=ROOT/"b"
DEPS=WORKSPACE/"runeterra-freljord/.tools/engine-shutdown-fix"
REPORTS=WORKSPACE/"runeterra-bandlecity/build/reports/engine-ai-lifecycle"
VS=Path(r"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools")
CMAKE=VS/"Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
NINJA=VS/"Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe"
def digest(p):
    with p.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()
def source_hashes():
    return {p.relative_to(SOURCE).as_posix():digest(p) for p in sorted(SOURCE.rglob("*")) if p.is_file()}
def environment():
    r=subprocess.run(["cmd.exe","/d","/c",str(ROOT/"capture_msvc_environment.cmd")],capture_output=True,text=True,check=True)
    env=dict(os.environ)
    for line in r.stdout.splitlines():
        if "=" in line and not line.startswith("="):
            k,v=line.split("=",1);env[k]=v
    runtime=DEPS/"conan-generated/_runtime_libs.txt"
    dirs=sorted({str(Path(x).parent) for x in runtime.read_text().splitlines() if x})
    env["PATH"]=os.pathsep.join(dirs+[str(NINJA.parent),env["PATH"]])
    return env
def main():
    parser=argparse.ArgumentParser();parser.add_argument("phase",choices=["configure","build","test"])
    parser.add_argument("--filter",default="Nullkiller2_TurnLifecycle.*:TerminalMoveCancellation.*:ExecuteHeroChainMovementTest.*")
    parser.add_argument("--jobs",type=int,choices=(1,2,3,4),default=2)
    parser.add_argument("--tests-only",action="store_true")
    args=parser.parse_args(); report=REPORTS/f"{args.phase}-{time.time_ns()}";report.mkdir(parents=True)
    env=environment();before=source_hashes(); archives={}
    if args.phase=="configure":
        command=[str(CMAKE),"-S",str(SOURCE),"-B",str(BUILD),"-G","Ninja","--toolchain",str(DEPS/"conan-generated/conan_toolchain.cmake"),"-DCMAKE_BUILD_TYPE=Release","-DENABLE_LAUNCHER=OFF","-DENABLE_EDITOR=OFF","-DENABLE_DISCORD=OFF","-DENABLE_MMAI=OFF","-DENABLE_TEST=ON","-DENABLE_CCACHE=OFF","-DENABLE_LTO=OFF","-DENABLE_SDL3=ON","-DENABLE_GITVERSION=OFF","-DCOPY_CONFIG_ON_BUILD=OFF"]
    elif args.phase=="build": command=[str(CMAKE),"--build",str(BUILD),"--parallel",str(args.jobs),"--target"]+(["vcmitest"] if args.tests_only else ["vcmiclient","vcmiserver","vcmitest"])
    else:
        app=BUILD/"bin";user=report/"user"
        for name in ("config", "Mods", "scripts"):
            target=app/name
            if target.is_symlink() or getattr(target,"is_junction",lambda:False)():
                # CMake intentionally links these three resources to this own source.
                # Remove only that verified link; never descend or delete its target.
                assert target.parent.resolve()==app.resolve() and app.resolve().is_relative_to(ROOT)
                assert target.resolve()==(SOURCE/name).resolve(), "unexpected private resource link target"
                if getattr(target,"is_junction",lambda:False)(): target.rmdir()
                else: target.unlink()
            assert not target.is_symlink() and not getattr(target,"is_junction",lambda:False)(), "private test resource path redirected"
            shutil.copytree(SOURCE/name,target,dirs_exist_ok=True)
        for dll in sorted((VS/"VC/Redist/MSVC/14.51.36231/x64/Microsoft.VC145.CRT").glob("*.dll")): shutil.copy2(dll,app/dll.name)
        (app/"config").mkdir(exist_ok=True)
        (app/"config/dirs.json").write_text(json.dumps({"userDataPath":str(user),"userConfigPath":str(user/"config"),"userLogsPath":str(user/"logs"),"userCachePath":str(user/"cache")},indent=2))
        original=Path(r"D:\e2e\Heroes of Might & Magic III\Data")
        for p in sorted(original.iterdir()):
            if p.suffix.lower() not in (".lod",".snd",".vid"): continue
            expected=digest(p);out=app/"Data"/p.name;out.parent.mkdir(exist_ok=True)
            if not out.exists() or digest(out)!=expected: shutil.copy2(p,out)
            assert digest(p)==digest(out)==expected;archives[str(p)]=expected
        command=[str(app/"vcmitest.exe"),"--gtest_filter="+args.filter,"--gtest_output=json:"+str(report/"gtest.json")]
    start=time.time()
    with (report/"output.log").open("wb") as f:
        result=subprocess.run(command,cwd=BUILD/"bin" if args.phase=="test" else SOURCE,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0),timeout=300 if args.phase=="test" else None)
    after=source_hashes();assert before==after,"Source changed during command"
    for path,sha in archives.items(): assert digest(Path(path))==sha
    binaries={p.relative_to(BUILD/"bin").as_posix():digest(p) for p in sorted((BUILD/"bin").rglob("*")) if p.is_file() and p.suffix.lower() in (".dll",".exe")}
    record={"phase":args.phase,"command":command,"exit_code":result.returncode,"elapsed_seconds":time.time()-start,"source_hashes":before,"binaries_sha256":binaries,"original_archives_before_after":archives,"output_sha256":digest(report/"output.log"),"scope":"isolated candidate; no client/server launch, selection or gameplay acceptance"}
    (report/"result.json").write_text(json.dumps(record,indent=2)+"\n");print(report);print("exit",result.returncode);return result.returncode
if __name__=="__main__": raise SystemExit(main())
