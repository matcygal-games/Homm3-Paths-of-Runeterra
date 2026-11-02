"""Portable crest-only painted source composition; never creates anatomy or poses."""
from pathlib import Path
import argparse,copy,hashlib,io,json
import numpy as np
from PIL import Image
SELF=Path(__file__).resolve();P=SELF.parents[4];S=SELF.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dumps(a):return (json.dumps(a,indent=2,sort_keys=True)+'\n').encode()
def pin(p):return {'path':p.relative_to(P).as_posix(),'sha256':sha(p)}
def png(im):
 f=io.BytesIO();im.save(f,format='PNG');return f.getvalue()
def produce(planpath):
 plan=json.loads(planpath.read_text(encoding='utf-8'))
 assert sha(SELF)==plan['producer_sha256'],'Stale portable producer'
 for name,digest in plan['input_sha256'].items():assert sha(P/name)==digest,'Missing/stale input: '+name
 dependencies=[pin(SELF),pin(planpath)]+[{'path':n,'sha256':h}for n,h in sorted(plan['input_sha256'].items())]
 outputs={};summary={}
 for unit,info in plan['units'].items():
  lookup={};entries=[]
  for e in info['entries']:
   a=np.array(Image.open(P/e['preserved_native']['path']).convert('RGBA'));out=a.copy();mask=np.array(Image.open(P/e['mask']).convert('L'))>0;b=e['visible_bbox']
   assert a.shape[:2]==mask.shape
   paint=Image.open(P/e['painted']).convert('RGBA').crop(e['painted_box']).resize((b[2]-b[0],b[3]-b[1]),Image.Resampling.LANCZOS);g=np.array(paint);local=mask[b[1]:b[3],b[0]:b[2]]
   assert int(mask.sum())==int(local.sum()),'Ink outside recorded subject rectangle'
   assert not np.any(mask&(a[:,:,3]<224)),'Ink must remain on solid physical material'
   out[b[1]:b[3],b[0]:b[2]][local,:3]=g[local,:3]
   assert np.array_equal(out[:,:,3],a[:,:,3]);assert np.array_equal(out[~mask],a[~mask])
   dst=S/unit/'candidate-v1'/f"pose-{e['index']:03d}.png";raw=png(Image.fromarray(out));digest=hashlib.sha256(raw).hexdigest();assert digest==e['expected_candidate_sha256'],'Candidate replay changed'
   outputs[dst]=raw;rec={**e,'candidate':{'path':dst.relative_to(P).as_posix(),'sha256':digest},'alpha_exact':True,'outside_mask_rgba_exact':True,'changed_rgb_pixels':int(np.any(out!=a,axis=2).sum())};entries.append(rec)
   for c in e['consumers']:lookup[c['role'],c['frame']]=rec
  generation={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','technical_producer':pin(SELF),'assembly_plan':pin(planpath),'painted_sources':[{'path':n,'sha256':h}for n,h in plan['input_sha256'].items()if '/'+unit+'/'in n and '/painted-'in n],'lineage_audit':plan['lineage_audit'],'method':'Actual imagegen-painted regional crest ink on preserved native painted2D pose contexts. Explicit per-pose masks; exact old alpha/body/root and outside-mask RGBA. No new pose or generated anatomy copied.','native_visual_review':'pending','native_playback':'not_run','release_accepted':False}
  primary=P/generation['painted_sources'][0]['path'];generation['painted_master']=primary.relative_to(P).as_posix();generation['painted_master_sha256']=sha(primary)
  generation['prompt']='\n\n'.join((P/n).read_text(encoding='utf-8')for n in sorted(plan['input_sha256'])if '/'+unit+'/'in n and '/prompt-'in n)
  gp=S/unit/'generation-crest-v1.json';outputs[gp]=dumps(generation);recipes=[]
  for role,template in info['templates'].items():
   rr=json.loads((P/template).read_text());rr['generation']=generation;rr['dependencies']=dependencies;rr['visual_approval_granted']=False;rr['status']='built-unreviewed'
   if rr['recipe_type']=='vcmi_animation':
    for group in rr['groups']:
     for i,f in enumerate(group['frames']):
      rec=lookup[role,f"g{group['group']:02d}-f{i:03d}"];f['source']=rec['candidate']['path'];f['sha256']=rec['candidate']['sha256'];f['source_sha256']=rec['candidate']['sha256']
   else:
    rec=lookup[role,'native'];rr['source']=rec['candidate']['path'];rr['source_sha256']=rec['candidate']['sha256'];rr['sha256']=rec['candidate']['sha256'];rr['source_canvas']=rec['canvas'];rr.pop('crop',None)
   rp=S/f"recipes-{plan['pair']}-v1"/Path(template).name;raw=dumps(rr);outputs[rp]=raw;recipes.append({'path':rp.relative_to(P).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()})
  summary[unit]={'entries':entries,'generation':{'path':gp.relative_to(P).as_posix(),'sha256':hashlib.sha256(outputs[gp]).hexdigest()},'recipes':recipes}
 return outputs,summary
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--pair',choices=('paper','telescope','mirror'),required=True);ap.add_argument('--check',action='store_true');args=ap.parse_args();outputs,summary=produce(S/f'inputs-{args.pair}-v1.json')
 for path,raw in outputs.items():
  if args.check:assert path.read_bytes()==raw,'Stale derived output: '+str(path)
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 if not args.check:(S/f'selection-{args.pair}-v1.json').write_bytes(dumps({'status':'authored configuration','candidate_only':True,'units':summary,'native_execution':False,'release_accepted':False}))
 print(json.dumps({'artifacts':len(outputs),'source_replay_exact':True}))
if __name__=='__main__':main()
