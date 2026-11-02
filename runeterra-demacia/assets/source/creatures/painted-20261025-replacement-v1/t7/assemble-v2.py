"""Pure painted2D Silverwing source assembly. No pose, anatomy or emblem drawing."""
from pathlib import Path
import argparse, hashlib, io, json, re
from pathlib import PurePosixPath
import numpy as np
from PIL import Image
SELF=Path(__file__).resolve(); S=SELF.parent; P=SELF.parents[5]
def safe_input(name):
    assert isinstance(name,str) and name and "\\" not in name and not name.startswith('/'),'Unsafe source path'
    parts=name.split('/')
    for part in parts:
        assert part not in ('','.','..') and not part.endswith((' ','.')) and not any(ord(c)<32 or c in '<>:"|?*' for c in part),'Ambiguous source path'
        assert not re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|CLOCK\$|COM[1-9]|LPT[1-9])',part.split('.')[0]),'Reserved source path'
    path=P
    for part in parts:
        path=path/part;assert not path.is_symlink() and not path.is_junction(),'Linked source path'
    assert path.resolve().is_relative_to(P.resolve()),'Escaped source path'
    return path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def js(value): return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def png(image):
    stream=io.BytesIO();image.save(stream,format='PNG');return stream.getvalue()
def rel(path): return path.relative_to(P).as_posix()
def pin(path): return {'source':rel(path),'sha256':sha(path)}
def painted(entry,pivot):
    image=Image.open(safe_input(entry['source'])).convert('RGBA')
    if entry.get('body_registration'):
        br=entry['body_registration'];expected=[br['source_point'][k]+(pivot[k]-br['target_native_point'][k])/entry['scale']for k in (0,1)];assert max(abs(expected[k]-entry['source_root'][k])for k in (0,1))<1e-6,'Stale measured body registration'
    if entry.get('mask'):
        mask=Image.open(safe_input(entry['mask'])).convert('L');assert mask.size==image.size
        a=np.array(image);a[:,:,3]=np.where(np.array(mask)>0,a[:,:,3],0);image=Image.fromarray(a)
    box=entry['box'];image=image.crop(box);scale=entry['scale'];image=image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(450,400));root=entry['source_root'];out.alpha_composite(image,(pivot[0]-round((root[0]-box[0])*scale),pivot[1]-round((root[1]-box[1])*scale)));return out

def project(image,pivot,scale,mirrored,canvas,anchor):
    sx=-scale if mirrored else scale
    return image.convert('RGBA').transform(tuple(canvas),Image.Transform.AFFINE,(1/sx,0,pivot[0]-anchor[0]/sx,0,1/scale,pivot[1]-anchor[1]/scale),Image.Resampling.BICUBIC)

def projection_measure(image,pivot,scale,mirrored,canvas,anchor):
    pad=128;expanded=project(image,pivot,scale,mirrored,(canvas[0]+2*pad,canvas[1]+2*pad),(anchor[0]+pad,anchor[1]+pad));a=expanded.getchannel('A');inside=a.crop((pad,pad,pad+canvas[0],pad+canvas[1]));return sum(v>=8 for v in a.tobytes())-sum(v>=8 for v in inside.tobytes())

def descriptor(path,raw,canvas):
    h=hashlib.sha256(raw).hexdigest();return {'source':rel(path),'sha256':h,'source_sha256':h,'source_canvas':list(canvas)}

def build():
    planpath=S/'inputs-v2.json';plan=json.loads(planpath.read_text());assert sha(SELF)==plan['producer_sha256'],'Stale producer'
    for name,h in plan['input_sha256'].items():assert sha(safe_input(name))==h,'Missing/stale source: '+name
    dependencies=[pin(SELF),pin(planpath)]+[{'source':n,'sha256':h}for n,h in sorted(plan['input_sha256'].items())];outputs={};selection={}
    for unit,job in plan['units'].items():
        assert re.fullmatch(r'[A-Za-z][A-Za-z0-9]*',unit),'Unsafe unit ID'
        pivot=job['pivot'];native={};frames={};frame_rows=[];recipes=[]
        for entry in job['frames']:
            key=entry['group'],entry['frame'];assert key not in native
            image=painted(entry,pivot);raw=png(image);path=S/unit/'candidate-v2/native'/f'g{key[0]:02d}-f{key[1]:03d}.png';outputs[path]=raw;native[key]=image;frames[key]=descriptor(path,raw,(450,400));frame_rows.append({**entry,'native':frames[key]})
        assert {str(g):sum(k[0]==g for k in native)for g in sorted({k[0]for k in native})}==plan['groups']
        assert native[22,0].tobytes()==native[5,5].tobytes()!=native[2,0].tobytes(),'DEAD22 must continue grounded corpse'
        for i in range(3):assert native[7,i].tobytes()==native[8,2-i].tobytes(),'Halfturn8 must reverse genuine7 after native facingflip'
        assert native[7,0].tobytes()==native[8,2].tobytes()==native[2,0].tobytes(),'Turn endpoints must settle exactly to holding'
        gen={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','painted_master':job['holding_master'],'painted_master_sha256':sha(P/job['holding_master']),'painted_action_masters':[pin(P/n)for n in job['masters']],'prompt':'\n\n'.join((P/n).read_text()for n in job['prompts']),'technical_producer':pin(SELF),'assembly_plan':pin(planpath),'lineage':job['lineage'],'method':'Fresh genuine painted2D identities and articulated actions; connected-actor isolation with real2px antialias margin. One source-pixel-density scale per action atlas cohort, physical perpose roots; fixed450x400canvas220,266pivot. No 3D/old render/pose manipulation or code-drawn crest. Genuine native7 halfturn reversed as8; exact final5 corpse supplies22.','native_visual_review':'pending','native_playback':'not_run','release_accepted':False}
        common={'unit':unit,'production_status':'painted-master-complete-unapproved','status':'built-unreviewed','visual_approval_granted':False,'acceptance':'authored configuration; independent source review, native playback, final art and rights pending','credits':{'new_art':'OpenAI built-in imagegen fresh painted2D; Codex technical isolation/assembly','character_design':'Riot Games','redistribution':'unresolved'},'generation':gen,'dependencies':dependencies}
        allrecipes={'battle':{**common,'recipe_type':'vcmi_animation','canvas':[450,400],'pivot':{'x':pivot[0],'y':pivot[1]},'generateShadow':1,'generateOverlay':1,'output_path':f'Content/Sprites/runeterra/demacia/creatures/{unit}/battle.json','groups':[{'group':int(g),'frames':[frames[int(g),i]for i in range(n)]}for g,n in plan['groups'].items()]}}
        maps=[]
        for i,entry in enumerate(job['map_frames']):
            image=painted(entry,pivot);raw=png(image);path=S/unit/'candidate-v2/native-map-parents'/f'neutral-{i:03d}.png';outputs[path]=raw;parent=descriptor(path,raw,(450,400));raw=png(project(image,pivot,job['map_scale'],False,(96,64),(80,60)));path=S/unit/'candidate-v2/adventure'/f'map-{i:03d}.png';outputs[path]=raw
            assert projection_measure(image,pivot,job['map_scale'],False,(96,64),(80,60))==0
            maps.append({**descriptor(path,raw,(96,64)),'projection_contract':{'source':parent['source'],'source_sha256':parent['sha256'],'pivot':pivot,'scale':job['map_scale'],'mirrored':False,'canvas':[96,64],'anchor':[80,60]}})
        allrecipes['map']={**common,'recipe_type':'vcmi_animation','canvas':[96,64],'pivot':{'x':80,'y':60},'generateShadow':2,'generateOverlay':0,'output_path':f'Content/Sprites/runeterra/demacia/creatures/{unit}/map.json','groups':[{'group':0,'frames':maps}]}
        for role,mirrored in [('attackLeft',False),('attackRight',True)]:
            key=tuple(job['encounter_frame']);image=native[key];assert projection_measure(image,pivot,job['encounter_scale'],mirrored,(64,64),(32,60))==0
            raw=png(project(image,pivot,job['encounter_scale'],mirrored,(64,64),(32,60)));path=S/unit/'candidate-v2/adventure'/f'{role}.png';outputs[path]=raw
            allrecipes[role]={**common,'recipe_type':'raster','size':[64,64],'fit':'stretch','require_alpha':True,'output_path':f'Content/Sprites/runeterra/demacia/creatures/{unit}/{role}.png',**descriptor(path,raw,(64,64)),'projection_contract':{'source':frames[key]['source'],'source_sha256':frames[key]['sha256'],'pivot':pivot,'scale':job['encounter_scale'],'mirrored':mirrored,'source_facing':'right','canvas':[64,64],'anchor':[32,60]}}
        for role,size in [('large',[58,64]),('small',[32,32])]:
            path=P/job['portrait_source'];allrecipes[role]={**common,'recipe_type':'raster','size':size,'fit':'stretch','require_alpha':False,'output_path':f'Content/Sprites/runeterra/demacia/creatures/{unit}/{role}.png','source':rel(path),'source_sha256':sha(path),'source_canvas':list(Image.open(path).size),'crop':job['portrait_crops'][role]}
        gp=S/unit/'candidate-v2/generation.json';outputs[gp]=js(gen)
        for role,recipe in allrecipes.items():
            path=S/'recipes-v2'/f'{unit}-{role}.json';raw=js(recipe);outputs[path]=raw;recipes.append({'role':role,'path':rel(path),'sha256':hashlib.sha256(raw).hexdigest()})
        selection[unit]={'recipes':recipes,'frames':frame_rows,'generation':{'path':rel(gp),'sha256':hashlib.sha256(outputs[gp]).hexdigest()},'pivot':pivot,'action_source_scale':job['action_source_scale'],'map_scale':job['map_scale'],'encounter_scale':job['encounter_scale']}
    return outputs,selection

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();outputs,selection=build()
    for path,raw in outputs.items():
        assert path.resolve().is_relative_to(S.resolve()) and not path.is_symlink(),'Unsafe candidate output'
        if args.check:assert path.read_bytes()==raw,'Stale derived source: '+str(path)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    if not args.check:(S/'selection-v2.json').write_bytes(js({'status':'authored configuration','candidate_only':True,'units':selection,'native_execution':False,'visual_approval_granted':False,'release_accepted':False}))
    print(json.dumps({'pure_artifacts':len(outputs),'recipes':sum(len(e['recipes'])for e in selection.values()),'native_frames':sum(len(e['frames'])for e in selection.values()),'exact_check':True}))
if __name__=='__main__':main()
