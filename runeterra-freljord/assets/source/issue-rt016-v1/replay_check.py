"""Prove a minimal frozen editable source closure rerenders all Hunter poses.

Private development source only; never a mod package or a release command.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import zipfile
sys.dont_write_bytecode=True

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
REPORT=PROJECT/'build/reports/issue-resolution-20261023/walks-rt016-finish-v1'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pins=json.loads((REPORT/'dependency-pins.json').read_text())
    for path in HERE.glob('*.py'):pins[path.relative_to(PROJECT).as_posix()]=sha(path)
    archive=REPORT/'editable-closure.zip'
    # Flat timestamp and ordering make the archive reproducible.
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,value in sorted(pins.items()):
            path=PROJECT/name
            assert sha(path)==value
            info=zipfile.ZipInfo('runeterra-freljord/'+name,(2026,10,23,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,path.read_bytes())
    dest=REPORT/'source-replay'
    dest.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:z.extractall(dest)
    for name,value in pins.items():assert sha(dest/'runeterra-freljord'/name)==value
    script=REPORT/'replay-driver.py'
    script.write_text('''from pathlib import Path
import json,sys
sys.dont_write_bytecode=True
from PIL import Image
sys.path.insert(0,sys.argv[1])
import author_walks as a
out=Path(sys.argv[2]);out.mkdir(exist_ok=False)
rows={}
for unit in a.UNITS:
    target=out/unit;target.mkdir()
    mats=a.materials(unit,target/'materials')
    records=[]
    for phase in range(6):
        mesh,joints=a.author(phase/6,unit)
        body=a.previous.render(mesh,mats);shadow=a.shadow(mesh)
        row={}
        for name,image in (('surface',body),('shadow',shadow),('composite',Image.alpha_composite(shadow,body))):
            path=target/(name+'-g00-f'+str(phase).zfill(3)+'.png');image.save(path)
            row[name]=a.sha(path)
        records.append(row)
    rows[unit]=records
(out/'replay-receipt.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\\n')
''',encoding='utf-8')
    env=dict(os.environ,OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
    result=subprocess.run([sys.executable,'-B',str(script),str(dest/'runeterra-freljord/assets/source/issue-rt016-v1'),str(REPORT/'replay-output')],
                          capture_output=True,text=True,env=env,timeout=240,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    (REPORT/'source-replay.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    assert result.returncode==0,result.stderr
    replay=json.loads((REPORT/'replay-output/replay-receipt.json').read_text())
    comparisons=[]
    for unit,rows in replay.items():
        receipt=json.loads((HERE/'candidates'/unit/'receipt.json').read_text())
        for phase,row in enumerate(rows):
            for name,value in row.items():
                expected=receipt['frames'][phase][name+'_sha256']
                comparisons.append({'unit':unit,'phase':phase,'role':name,'sha256':value,'expected':expected,'match':value==expected})
    final={'archive_sha256':sha(archive),'closure_files':len(pins),'source_pins':pins,
           'archive_source_hashes_verified':True,'replay_process_exit':result.returncode,
           'comparisons':comparisons,'all_match':all(row['match'] for row in comparisons),
           'scope':'All twelve Hunter surface/shadow/composite PNG poses rerendered from minimal copied editable inputs; no compiler/stage/native/art acceptance'}
    (REPORT/'source-replay.json').write_text(json.dumps(final,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'closure_files':len(pins),'all_replay_pngs_match':final['all_match']}))
    return 0 if final['all_match'] else 1


if __name__=='__main__':sys.exit(main())
