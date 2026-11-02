"""Re-execute actual assembly, portable source replay and review packaging."""
from __future__ import annotations
import hashlib,html,json,shutil,subprocess,sys
from pathlib import Path
from PIL import Image,ImageDraw
from assemble_humanoids import HERE,PROJECT,ROOT,REPORT,dump,sha

def inventory():
    groups=[HERE/'humanoids',HERE/'animals',HERE/'proposed-recipes',REPORT/'compiled']
    out={}
    for group in groups:
        for p in group.rglob('*'):
            if p.is_file() and p.suffix in ['.png','.json']:
                out[p.relative_to(ROOT).as_posix()]=sha(p)
    return out

def assembly_replay():
    before=inventory();runs=[]
    for name in ['assemble_humanoids.py','assemble_animals.py']:
        log=REPORT/(name.replace('.py','')+'-determinism-replay.log')
        with log.open('w',encoding='utf-8') as f:
            result=subprocess.run([sys.executable,'-B',str(HERE/name)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
        runs.append({'producer':str((HERE/name).relative_to(PROJECT)).replace('\\','/'),'exit_code':result.returncode,'log':log.name})
        if result.returncode:raise RuntimeError('Actual assembler replay failed: '+name)
    after=inventory();changed=[p for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)]
    dump(REPORT/'actual-assembly-determinism.json',{'status':'authored configuration','ok':not changed,'runs':runs,
            'checked_files':len(after),'changed_files':changed,'scope':'Real full source-frame assembly and regional compiler execution repeated, not a metadata prediction'})
    if changed:raise RuntimeError('Assembly replay changed '+str(len(changed))+' files')

def portable_replay():
    destination=REPORT/'portable-replay-v2';portable=destination/'runeterra-targon'
    if destination.exists():raise RuntimeError('Refuse to overwrite an existing portable evidence directory')
    relative_here=HERE.relative_to(PROJECT)
    shutil.copytree(HERE,portable/relative_here,ignore=shutil.ignore_patterns('__pycache__'))
    original=PROJECT/'assets/source/creatures/painted-rebuild-20261027-v1'
    shutil.copytree(original,portable/original.relative_to(PROJECT))
    for name in ['faction_art_compile.py','faction_sdk_profile.py']:
        target=destination/'scripts'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'scripts'/name,target)
    for name in ['scripts/creature_art_policy.py','content/creatures.json','design/unit-identity.json','design/creature-art-policy.json']:
        target=portable/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PROJECT/name,target)
    for name in ['RUNETERRA_DEMACIA_PROJECT_PROMPT.txt','RUNETERRA_TARGON_PROJECT_PROMPT.txt','RUNETERRA_CREATURE_ART_POLICY.txt','RUNETERRA_REGIONAL_HERALDRY_POLICY.txt']:
        if (ROOT/name).is_file():shutil.copy2(ROOT/name,destination/name)
    # Execute the exact shipped compiler against only the copied closure. No
    # original controls, external generated-image directories or old geometry
    # are in this directory or needed by these recipes.
    command=r'''
import hashlib,json,sys
from pathlib import Path
root=Path.cwd();project=root/'runeterra-targon'
sys.path.insert(0,str(root/'scripts'));sys.path.insert(0,str(project/'scripts'))
from faction_art_compile import create_compiler
from creature_art_policy import recipe_errors
compiler=create_compiler('targon');results=[]
recipes=sorted((project/'assets/source/creatures/playable-completion-20261028-v1/proposed-recipes').glob('*/*.json'))
for path in recipes:
 recipe=json.loads(path.read_text());errors=recipe_errors(project,recipe,set())
 assert not errors,(path,errors)
 a,receipt=compiler.plan(project,path);b,_=compiler.plan(project,path);assert a==b
 results.append({'recipe':path.relative_to(project).as_posix(),'outputs':len(a),'output_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in a.items()}})
print(json.dumps({'status':'authored configuration','ok':True,'recipes':len(results),'double_replay_identical':True,'results':results,'native_execution':False},sort_keys=True,indent=2))
'''
    result=subprocess.run([sys.executable,'-B','-c',command],cwd=destination,text=True,capture_output=True)
    (REPORT/'portable-source-replay.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Portable closure replay failed; inspect log')
    receipt=json.loads(result.stdout);dump(REPORT/'portable-source-replay.json',receipt)
    pins={p.relative_to(destination).as_posix():sha(p) for p in destination.rglob('*') if p.is_file()}
    dump(REPORT/'portable-source-inventory.json',{'status':'authored configuration','files_sha256':pins,'files':len(pins),
          'bytes':sum(p.stat().st_size for p in destination.rglob('*') if p.is_file()),'original_game_pixels_included':False,
          'old_geometry_included':False,'external_image_cache_required':False,'release_accepted':False})

def review_page():
    creatures=json.loads((PROJECT/'content/creatures.json').read_text());cards=[]
    board=Image.new('RGBA',(1000,7*185),(53,50,47,255));draw=ImageDraw.Draw(board)
    for i,unit in enumerate(creatures):
        family='humanoids' if (HERE/'humanoids'/unit).is_dir() else 'animals'
        unitroot=HERE/family/unit;report=REPORT/family/unit
        base=REPORT/'compiled/Content/Sprites/runeterra/targon/creatures'/unit
        holding=Image.open(base/'battle-frames/g02-f000.png').convert('RGBA');crop=(110,130,350,285)
        x=(i%2)*500;y=(i//2)*185;draw.text((x+5,y+5),creatures[unit]['name']['singular'],fill='white');board.alpha_composite(holding.crop(crop),(x,y+25))
        board.alpha_composite(Image.open(unitroot/'portrait-large.png').convert('RGBA'),(x+285,y+40))
        board.alpha_composite(Image.open(unitroot/'map/hold-compact.png').convert('RGBA'),(x+390,y+40))
        prefix='../../runeterra-targon/assets/source/creatures/playable-completion-20261028-v1/'+family+'/'+unit+'/'
        gifs=''.join(f'<figure><img src="{family}/{unit}/g{g:02d}.gif" alt="{unit} group {g}"><figcaption>Native group {g}</figcaption></figure>' for g in [0,5,7,8,11,12,13,20,21,31] if (report/f'g{g:02d}.gif').exists())
        cards.append(f'<section id="{unit}"><h2>{html.escape(creatures[unit]["name"]["singular"])}</h2><div class="icons"><img src="{prefix}portrait-large.png" width="58" height="64"><img src="{prefix}portrait-small.png" width="32" height="32"><img src="{prefix}map/hold-compact.png" width="64" height="64"><img src="{prefix}map/attackLeft-compact.png" width="64" height="64"><img src="{prefix}map/attackRight-compact.png" width="64" height="64"></div><div class="motions">{gifs}</div><details><summary>All native action frames</summary><a href="{family}/{unit}/actions-native.png"><img class="sheet" src="{family}/{unit}/actions-native.png"></a></details></section>')
    board.convert('RGB').save(REPORT/'all-fourteen-native.png')
    body='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Targon painted creature candidates</title><style>body{background:#242321;color:#e7dcc2;font:16px Georgia,serif;margin:2rem}a{color:#d7be77}section{border-top:1px solid #73604b;padding:1rem 0}.motions{display:flex;flex-wrap:wrap;gap:1rem}figure{margin:0;background:#34312e}figure img{display:block;image-rendering:pixelated}.icons img{margin:10px;vertical-align:middle;image-rendering:pixelated}.sheet{max-width:100%;height:auto}summary{cursor:pointer;padding:.8rem}p{max-width:1000px;line-height:1.5}</style><h1>Targon: fourteen painted creature candidates</h1><p><strong>Authored configuration.</strong> Actual painted sources and deterministic native JSON/PNG conversions. These images and GIFs are source-scale views, not in-game screenshots or release acceptance. The coordinator owns selection, staging and native testing.</p><p>Real gait/flap poses, directional physical attacks, hit/defense, progressive death and explicit settled DEAD22 are present. Lunari Prayer and Stellacorn Cure retain their existing finite native roles. Map actors use independently painted compact views and left/right encounter reactions. No old geometry or original-game troop frames are selected.</p><p>Native map idle is a single painted holding frame. Tiny badge/crest details require human comparison; painted motifs are physically attached, but this technical packet does not certify exact emblem fidelity, every artistic transition, native playback, rights or release acceptance. Some old atlas cells were discarded because their silhouettes merged; all selected source cuts and fixed scales are recorded.</p><p><a href="candidate-consumer-and-mutation-tests.json">Consumer and mutation checks</a> · <a href="actual-assembly-determinism.json">Actual assembly replay</a> · <a href="portable-source-replay.json">Portable closure replay</a> · <a href="all-native-map-and-portraits.png">All maps and portraits</a></p><img class="sheet" src="all-fourteen-native.png" alt="All fourteen native-size holding comparisons">'''
    body+=''.join(cards)+'</html>'
    (REPORT/'index.html').write_text(body,encoding='utf-8')

def main():
    assembly_replay()
    with (REPORT/'candidate-verification-final.log').open('w',encoding='utf-8') as f:
        result=subprocess.run([sys.executable,'-B',str(HERE/'verify_candidates.py')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError('Candidate consumer verification failed')
    portable_replay();review_page()
    print('Actual assembly determinism, consumer mutations and portable source replay completed. Review:',REPORT/'index.html')
if __name__=='__main__':main()
