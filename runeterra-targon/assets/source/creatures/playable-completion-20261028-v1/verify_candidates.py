"""Meaningful candidate consumer and mutation checks. Does not launch a game."""
from __future__ import annotations
import copy,hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageChops,ImageOps
from assemble_humanoids import HERE,PROJECT,ROOT,REPORT,dump,sha

sys.path.insert(0,str(ROOT/'scripts'))
from faction_art_compile import create_compiler
sys.path.insert(0,str(PROJECT/'scripts'))
from creature_art_policy import recipe_errors
COMPILER=create_compiler('targon')

def image_bytes(raw):
    import io
    return Image.open(io.BytesIO(raw)).convert('RGBA')

def normalized_mask(image):
    a=np.asarray(image.getchannel('A'))>128
    yy,xx=np.nonzero(a)
    if not len(xx):raise AssertionError('Empty body')
    x=int(round(float(xx.mean())));y=int(round(float(yy.mean())))
    out=np.zeros((500,600),dtype=bool)
    yy2=yy-y+250;xx2=xx-x+300
    good=(yy2>=0)&(yy2<500)&(xx2>=0)&(xx2<600)
    out[yy2[good],xx2[good]]=True
    return out

def movement_articulates(images):
    masks=[normalized_mask(im) for im in images]
    if len({hashlib.sha256(im.tobytes()).hexdigest() for im in images})<4:return False
    changes=[]
    for a in masks[1:]:
        best=1.0
        for dy in range(-2,3):
            for dx in range(-2,3):
                b=np.roll(a,(dy,dx),(0,1));union=(masks[0]|b).sum()
                score=float((masks[0]^b).sum())/max(1,int(union));best=min(best,score)
        changes.append(best)
    return max(changes,default=0)>.025

def consume(recipe,outputs):
    name=recipe['output_path'];animation=json.loads(outputs[name])
    assert len(animation.get('sequences',[]))==len(recipe['groups']),'Native sequence loss'
    groups={}
    for sequence in animation['sequences']:
        group=sequence['group'];frames=[]
        for filename in sequence['frames']:
            path=str(Path(name).parent/filename).replace('\\','/')
            assert path in outputs,'Native sequence points at missing frame'
            im=image_bytes(outputs[path]);assert list(im.size)==recipe['canvas'],'Canvas drift'
            a=np.asarray(im.getchannel('A'));assert a.max()>240,'No opaque body'
            frames.append(im)
        groups[group]=frames
    if name.endswith('/battle.json'):
        required={0,1,2,3,4,5,7,8,11,12,13,20,21,22}
        assert required.issubset(groups),'Required actual battle roles missing'
        assert groups[22][0].tobytes()==groups[5][-1].tobytes(),'DEAD22 must equal settled DEATH endpoint'
        assert movement_articulates(groups[0]),'Movement is repeated or only rigid translations'
        for g in [11,12,13]:
            assert len(groups[g])>=4,'Native contact frame4 absent'
            assert groups[g][3].tobytes()!=groups[2][0].tobytes(),'Melee contact is idle'
        assert len({im.tobytes() for im in groups[7]})>=3,'First turn half lacks painted angle changes'
        assert len(groups[8])>=2,'Second turn half absent'
        hold=groups[2][0].getbbox();corpse=groups[22][0].getbbox()
        assert corpse[2]-corpse[0]>corpse[3]-corpse[1],'Corpse remains upright'
        assert corpse[3]-corpse[1]<(hold[3]-hold[1])*.90,'Corpse silhouette did not settle'
        corpse_alpha=np.asarray(groups[22][0].getchannel('A'));ys,_=np.nonzero(corpse_alpha>64)
        assert abs((int(ys.max())+1)-267)<=1,'Settled corpse contact floats above native ground'
        for frames in groups.values():
            for im in frames:
                a=np.asarray(im.getchannel('A'))>64
                assert not(a[0].any() or a[-1].any() or a[:,0].any() or a[:,-1].any()),'Battle anatomy clips canvas'
    elif name.endswith('/map.json'):
        for frames in groups.values():
            for im in frames:
                a=np.asarray(im.getchannel('A'))>64
                assert not(a[0].any() or a[-1].any() or a[:,0].any() or a[:,-1].any()),'Adventure silhouette clips canvas'
                if im.width==96:assert not a[:,:32].any(),'3-column canvas has hidden pixels outside 2-column mask'
    return groups

def main():
    results=[];errors=[];mutations=[]
    recipes=sorted((HERE/'proposed-recipes').glob('*/*.json'))
    for path in recipes:
        recipe=json.loads(path.read_text());label=path.relative_to(HERE).as_posix()
        try:
            policy=recipe_errors(PROJECT,recipe,set());assert not policy,'; '.join(policy)
            outputs,receipt=COMPILER.plan(PROJECT,path)
            again,_=COMPILER.plan(PROJECT,path);assert outputs==again,'Actual compiler double replay differs'
            if recipe['recipe_type']=='vcmi_animation':consume(recipe,outputs)
            else:
                im=image_bytes(outputs[recipe['output_path']]);assert list(im.size)==recipe['canvas']
                if recipe['output_path'].endswith(('attackLeft.png','attackRight.png')):
                    a=np.asarray(im.getchannel('A'))>64
                    assert not(a[0].any() or a[-1].any() or a[:,0].any() or a[:,-1].any()),'Encounter reaction clips canvas'
                    if im.width==96:assert not a[:,:32].any(),'Encounter reaction hidden outside mask'
            results.append({'recipe':label,'ok':True,'outputs':len(outputs),'double_replay_identical':True})
        except Exception as exc:errors.append({'recipe':label,'error':str(exc)})
    # Mutate actual valid animation definitions / frames in memory and require
    # the consumer to reject them; no canonical files or source pixels changed.
    battle=next((HERE/'proposed-recipes').glob('rakkorTrailguard/battle.json'))
    recipe=json.loads(battle.read_text());outputs,_=COMPILER.plan(PROJECT,battle)
    def must_reject(label,rec,out):
        try:consume(rec,out)
        except Exception as exc:mutations.append({'mutation':label,'rejected':True,'reason':str(exc)})
        else:errors.append({'mutation':label,'error':'Consumer accepted defective mutation'})
    changed=copy.deepcopy(outputs);native=json.loads(changed[recipe['output_path']]);seq={s['group']:s for s in native['sequences']}
    source=str(Path(recipe['output_path']).parent/seq[2]['frames'][0]).replace('\\','/')
    dead=str(Path(recipe['output_path']).parent/seq[22]['frames'][0]).replace('\\','/')
    changed[dead]=changed[source];must_reject('DEAD22 replaced by upright holding',recipe,changed)
    changed=copy.deepcopy(outputs)
    for file in seq[0]['frames']:changed[str(Path(recipe['output_path']).parent/file).replace('\\','/')]=changed[source]
    must_reject('All moving frames replaced by idle',recipe,changed)
    changed=copy.deepcopy(outputs);contact=str(Path(recipe['output_path']).parent/seq[12]['frames'][3]).replace('\\','/')
    changed[contact]=changed[source];must_reject('Native melee contact4 replaced by idle',recipe,changed)
    changed=copy.deepcopy(outputs)
    for file in seq[7]['frames']:changed[str(Path(recipe['output_path']).parent/file).replace('\\','/')]=changed[source]
    must_reject('First turn half replaced by side-view idle',recipe,changed)
    changed=copy.deepcopy(outputs);im=image_bytes(changed[dead]);shifted=Image.new('RGBA',im.size,(0,0,0,0));shifted.alpha_composite(im,(0,-15))
    import io
    stream=io.BytesIO();shifted.save(stream,format='PNG');changed[dead]=stream.getvalue()
    lastdeath=str(Path(recipe['output_path']).parent/seq[5]['frames'][-1]).replace('\\','/')
    changed[lastdeath]=stream.getvalue();must_reject('DEAD and death endpoint translated15px above ground',recipe,changed)
    # Actual provenance policy rejects reintroduced geometry, independently of
    # successful PNG compilation or a truthful image_generation_used flag.
    defective=copy.deepcopy(recipe);defective['editable_scene']={'source':'assets/source/history/rejected.blend'}
    rejected=recipe_errors(PROJECT,defective,set())
    if rejected:mutations.append({'mutation':'Reintroduced old geometry lineage','rejected':True,'reason':rejected[0]})
    else:errors.append({'mutation':'Geometry lineage','error':'Policy accepted forbidden source'})
    report={'status':'authored configuration','ok':not errors,'executed_recipe_checks':len(results),'expected_recipe_count':88,
            'consumer':'Actual regional compiler JSON/frame outputs plus native group/footprint semantics',
            'results':results,'mutation_controls':mutations,'errors':errors,'native_execution':False,
            'art_or_release_acceptance_granted':False}
    dump(REPORT/'candidate-consumer-and-mutation-tests.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['results']},indent=2))
    return 2 if errors else 0
if __name__=='__main__':raise SystemExit(main())
