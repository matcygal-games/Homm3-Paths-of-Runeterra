"""Pure painted atlas isolation, uniform calibration and native resource assembly.

No anatomy/poses/crests are drawn by this program. Only actual selected painted
pixels are isolated and uniformly scaled onto fixed native canvases.
"""
from pathlib import Path
import argparse,hashlib,io,json
import numpy as np
from PIL import Image,ImageOps
SELF=Path(__file__).resolve();S=SELF.parent;P=SELF.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(v):return(json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def png(im):
 f=io.BytesIO();im.save(f,format='PNG');return f.getvalue()
def pin(p):return{'path':p.relative_to(P).as_posix(),'sha256':sha(p)}
def project(image,pivot,scale,mirrored=False,canvas=(96,64),anchor=(80,60)):
 sx=-scale if mirrored else scale
 return image.convert('RGBA').transform(canvas,Image.Transform.AFFINE,(1/sx,0,pivot[0]-anchor[0]/sx,0,1/scale,pivot[1]-anchor[1]/scale),Image.Resampling.BICUBIC)
def painted_frame(e,pivot,multiplier):
 im=Image.open(P/e['source']).convert('RGBA')
 if e.get('mask'):
  mask=Image.open(P/e['mask']).convert('L');assert mask.size==im.size;v=np.array(im);v[:,:,3]=np.where(np.array(mask)>0,v[:,:,3],0);im=Image.fromarray(v)
 box=e['box'];crop=im.crop(box);scale=e['scale']*multiplier;size=[max(1,round(crop.width*scale)),max(1,round(crop.height*scale))];crop=crop.resize(size,Image.Resampling.LANCZOS);out=Image.new('RGBA',(450,400));root=e['source_root'];origin=[pivot[0]-round((root[0]-box[0])*scale),pivot[1]-round((root[1]-box[1])*scale)];out.alpha_composite(crop,origin);return out
def descriptor(path,raw,canvas):
 h=hashlib.sha256(raw).hexdigest();return{'source':path.relative_to(P).as_posix(),'sha256':h,'source_sha256':h,'source_canvas':list(canvas)}
def build():
 planpath=S/'inputs.json';plan=json.loads(planpath.read_text());assert sha(SELF)==plan['producer_sha256'],'Stale producer'
 for n,h in plan['input_sha256'].items():assert sha(P/n)==h,'Missing/stale producer input: '+n
 dependencies=[pin(SELF),pin(planpath)]+[{'path':n,'sha256':h}for n,h in sorted(plan['input_sha256'].items())];outputs={};selection={}
 for unit,job in plan['units'].items():
  pivot=job['pivot'];native={};frames={};frame_rows=[]
  for e in job['frames']:
   key=e['group'],e['frame'];assert key not in native;im=painted_frame(e,pivot,job['native_calibration']);raw=png(im);path=S/unit/'candidate-v1/native'/f"g{key[0]:02d}-f{key[1]:03d}.png";outputs[path]=raw;native[key]=im;frames[key]=descriptor(path,raw,(450,400));frame_rows.append({'group':key[0],'frame':key[1],'source':e['source'],'source_crop':e['box'],'source_root':e['source_root'],'scale':e['scale']*job['native_calibration'],'native':frames[key],'action':e['action']})
  assert {str(g):sum(1 for k in native if k[0]==g)for g in sorted({k[0]for k in native})}==plan['groups'],'Wrong native action counts'
  assert png(native[2,0])==png(native[2,1]),'Ordinary holding must remain static'
  gen={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','painted_master':job['masters'][0],'painted_master_sha256':sha(P/job['masters'][0]),'painted_action_masters':[pin(P/n)for n in job['masters']],'prompt':'\n\n'.join((P/n).read_text()for n in job['prompts']),'technical_producer':pin(SELF),'assembly_plan':pin(planpath),'lineage':job['lineage'],'method':'Fresh coherent painted2D identities/actions. Intact connected-actor extraction retaining source RGBA plus2px antialias margin; no anatomy/pose synthesis. Single uniform source-unit scale with one documented whole-cohort native calibration, measured physical source-root registration, unchanged native pivots. Static holding only; genuine flight, attacks, reactions, turns and grounded death.','native_visual_review':'pending','native_playback':'not_run','release_accepted':False}
  gp=S/unit/'candidate-v1/generation.json';outputs[gp]=js(gen);common={'unit':unit,'production_status':'painted-master-complete-unapproved','status':'built-unreviewed','visual_approval_granted':False,'acceptance':'authored configuration; final human art, native playback and redistribution pending','credits':{'author':'OpenAI built-in imagegen original painted2D; Codex technical conversion','license':'unreviewed','redistribution':'unresolved'},'generation':gen,'dependencies':dependencies};recipes=[]
  r={**common,'recipe_type':'vcmi_animation','canvas':[450,400],'pivot':dict(zip(('x','y'),pivot)),'generateShadow':1,'generateOverlay':1,'output_path':f'Content/Sprites/runeterra/ionia/creatures/{unit}/battle.json','groups':[{'group':int(g),'frames':[frames[int(g),i]for i in range(n)]}for g,n in plan['groups'].items()]}
  allrecipes={'battle':r};maps=[]
  for i in range(6):
   image=native[0,i];new=project(image,pivot,job['adventure_scale']);raw=png(new);dst=S/unit/'candidate-v1/adventure'/f'map-{i:03d}.png';outputs[dst]=raw;contract={'source':frames[0,i]['source'],'source_sha256':frames[0,i]['source_sha256'],'pivot':pivot,'scale':job['adventure_scale'],'mirrored':False,'anchor':[80,60],'canvas':[96,64]};maps.append({**descriptor(dst,raw,(96,64)),'projection_contract':contract})
  allrecipes['map']={**common,'recipe_type':'vcmi_animation','canvas':[96,64],'pivot':{'x':80,'y':60},'generateShadow':0,'generateOverlay':0,'output_path':f'Content/Sprites/runeterra/ionia/creatures/{unit}/map.json','groups':[{'group':0,'frames':maps}]}
  for role,mirrored in(('attackLeft',True),('attackRight',False)):
   parent=job['encounter_frame'];key=tuple(parent);new=project(native[key],pivot,job['adventure_scale'],mirrored);raw=png(new);dst=S/unit/'candidate-v1/adventure'/f'{role}.png';outputs[dst]=raw;contract={'source':frames[key]['source'],'source_sha256':frames[key]['source_sha256'],'pivot':pivot,'scale':job['adventure_scale'],'mirrored':mirrored,'source_facing':'right','anchor':[80,60],'canvas':[96,64]};allrecipes[role]={**common,'recipe_type':'raster','size':[96,64],'fit':'exact','require_alpha':True,'output_path':f'Content/Sprites/runeterra/ionia/creatures/{unit}/{role}.png',**descriptor(dst,raw,(96,64)),'projection_contract':contract}
  for role,size in(('large',(58,64)),('small',(32,32))):
   portrait=job['portrait_highres'][role];foreground=Image.open(P/portrait['source']).convert('RGBA').crop(portrait['crop']);foreground=ImageOps.fit(foreground,size,Image.Resampling.LANCZOS,centering=tuple(portrait.get('centering',[.5,.5])));background=Image.open(P/portrait['scene']).convert('RGBA').crop(portrait['scene_crop']);final=ImageOps.fit(background,size,Image.Resampling.LANCZOS);final.alpha_composite(foreground);final=final.convert('RGB').convert('RGBA');raw=png(final);dst=S/unit/'candidate-v1/portraits'/f'{role}.png';outputs[dst]=raw;allrecipes[role]={**common,'recipe_type':'raster','size':list(size),'fit':'exact','require_alpha':False,'portrait_composition':portrait,'output_path':f'Content/Sprites/runeterra/ionia/creatures/{unit}/{role}.png',**descriptor(dst,raw,size)}
  for role,r in allrecipes.items():
   dst=S/'recipes-v1'/f'{unit}-{role}.json';raw=js(r);outputs[dst]=raw;recipes.append({'role':role,'path':dst.relative_to(P).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()})
  selection[unit]={'recipes':recipes,'frames':frame_rows,'generation':{'path':gp.relative_to(P).as_posix(),'sha256':hashlib.sha256(outputs[gp]).hexdigest()},'pivot':pivot,'native_calibration':job['native_calibration'],'adventure_scale':job['adventure_scale']}
 return outputs,selection
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();outputs,sel=build()
 for p,raw in outputs.items():
  if a.check:assert p.read_bytes()==raw,'Stale derived source: '+str(p)
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 if not a.check:(S/'selection-v1.json').write_bytes(js({'status':'authored configuration','candidate_only':True,'units':sel,'native_execution':False,'visual_approval_granted':False,'release_accepted':False}))
 print(json.dumps({'pure_artifacts':len(outputs),'candidate_recipes':sum(len(v['recipes'])for v in sel.values()),'native_frames':sum(len(v['frames'])for v in sel.values()),'exact_check':True}))
if __name__=='__main__':main()
