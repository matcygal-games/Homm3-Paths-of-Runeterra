"""Portable genuine painted crest composition; never synthesizes poses/anatomy."""
from pathlib import Path
import argparse,hashlib,io,json
import numpy as np
from PIL import Image,ImageDraw
SELF=Path(__file__).resolve();S=SELF.parent;P=SELF.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(v):return(json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def png(im):
 f=io.BytesIO();im.save(f,format='PNG');return f.getvalue()
def pin(p):return{'path':p.relative_to(P).as_posix(),'sha256':sha(p)}
def stamp(im,size,angle):
 v=im.resize((size[0]*6,size[1]*6),Image.Resampling.NEAREST)
 if angle:v=v.rotate(-angle,Image.Resampling.NEAREST,expand=True)
 return v.resize((round(v.width/6),round(v.height/6)),Image.Resampling.NEAREST)
def holding(a,e):
 v=e['pilot'];glyph=Image.open(P/v['painted_glyph']).convert('RGBA')
 if e['unit']=='mirrorArchmage':
  glyph=Image.open(P/v['raw_painted_edit']).convert('RGBA').crop(v['source_roi']).crop(v['glyph_bbox_in_roi']);glyph.putalpha(255)
 st=np.array(stamp(glyph,v['native_mark_size'],v['native_rotation_clockwise']));x,y=v['native_position']
 field=Image.new('L',(a.shape[1],a.shape[0]));ImageDraw.Draw(field).polygon(v['native_field_polygon'],fill=255)
 surface=(np.array(field)>0)&(a[:,:,3]>=224);alpha=st[:,:,3].astype(float)/255;alpha*=surface[y:y+st.shape[0],x:x+st.shape[1]]
 out=a.copy();region=out[y:y+st.shape[0],x:x+st.shape[1],:3];region[:]=np.round(st[:,:,:3]*alpha[:,:,None]+region*(1-alpha[:,:,None])).astype('uint8');return out
def project(im,c):
 out=Image.new('RGBA',(100,130));out.paste(im.crop(c['source_union']).resize(tuple(c['resized_union']),Image.Resampling.LANCZOS),tuple(c['offset']));return out
def produce():
 planpath=S/'inputs.json';plan=json.loads(planpath.read_text());assert sha(SELF)==plan['producer_sha256'],'Stale producer'
 for n,h in plan['input_sha256'].items():assert sha(P/n)==h,'Missing/stale source: '+n
 deps=[pin(SELF),pin(planpath)]+[{'path':n,'sha256':h}for n,h in sorted(plan['input_sha256'].items())];outputs={};summary={}
 for unit,info in plan['units'].items():
  lookup={};entries=[];by_original={}
  for e in info['entries']:
   a=np.array(Image.open(P/e['original']).convert('RGBA'));mask=np.array(Image.open(P/e['mask']).convert('L'))>0
   if e.get('pilot'):out=holding(a,e)
   else:
    b=e['native_box'];g=np.array(Image.open(P/e['painted']).convert('RGBA').crop(e['painted_box']).resize((b[2]-b[0],b[3]-b[1]),Image.Resampling.NEAREST));out=a.copy();local=mask[b[1]:b[3],b[0]:b[2]];assert int(local.sum())==int(mask.sum());out[b[1]:b[3],b[0]:b[2]][local,:3]=g[local,:3]
   assert np.array_equal(a[:,:,3],out[:,:,3]),'Body alpha drift';assert np.array_equal(a[~mask],out[~mask]),'Outside material mask drift';assert not np.any(mask&(a[:,:,3]<224)),'Mark leaves solid physical material'
   raw=png(Image.fromarray(out));h=hashlib.sha256(raw).hexdigest();assert h==e['expected_sha256'],'Candidate replay drift'
   dst=S/unit/'native'/f"pose-{e['index']:03d}.png";outputs[dst]=raw;rec={'index':e['index'],'candidate':{'path':dst.relative_to(P).as_posix(),'sha256':h},'original':e['original'],'mask':e['mask'],'consumers':e['consumers'],'changed_rgb_pixels':int(np.any(a!=out,axis=2).sum()),'occluded':not bool(np.any(a!=out))};entries.append(rec);by_original[e['original']]=(Image.fromarray(out),rec)
   for c in e['consumers']:lookup[c['role'],c['frame']]=rec
  generation={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','painted_master':info['painted_master'],'painted_master_sha256':sha(P/info['painted_master']),'prompt':'\n\n'.join((P/n).read_text()for n in info['prompts']),'technical_producer':pin(SELF),'assembly_plan':pin(planpath),'lineage_audit':info['lineage_audit'],'method':'Genuine per-pose painted regional crest on existing physical wing/case/robe. NEAREST samples painted mark only; exact original body alpha, nonmark pixels, roots and actions. Six approved holding attachments replayed from painted ink and fixed material fields.','native_visual_review':'pending','native_playback':'not_run','release_accepted':False}
  gp=S/unit/'generation.json';outputs[gp]=js(generation);recipes=[]
  for role,t in info['templates'].items():
   r=json.loads((P/t['path']).read_text());r['generation']=generation;r['dependencies']=deps;r['visual_approval_granted']=False;r['status']='built-unreviewed'
   if role=='preview':
    by={(e['group'],e['frame']):e for e in info['preview']['frames']}
    for group in r['groups']:
     for i,f in enumerate(group['frames']):
      z=by[group['group'],i];old=project(Image.open(P/z['original_battle']).convert('RGBA'),info['preview']['camera']);assert old.tobytes()==Image.open(P/z['original_preview']).convert('RGBA').tobytes(),'Original preview camera drift'
      new=project(by_original[z['original_battle']][0],info['preview']['camera']);assert old.getchannel('A').tobytes()==new.getchannel('A').tobytes();raw=png(new);h=hashlib.sha256(raw).hexdigest();dst=S/unit/'preview'/f'frame-{h[:24]}.png';outputs[dst]=raw;f['source']=dst.relative_to(P).as_posix();f['source_sha256']=h;f['sha256']=h
   elif r['recipe_type']=='vcmi_animation':
    for group in r['groups']:
     for i,f in enumerate(group['frames']):
      rec=lookup[role,f"g{group['group']:02d}-f{i:03d}"];f['source']=rec['candidate']['path'];f['source_sha256']=rec['candidate']['sha256'];f['sha256']=rec['candidate']['sha256']
   else:
    rec=lookup[role,'native'];r['source']=rec['candidate']['path'];r['source_sha256']=rec['candidate']['sha256'];r['sha256']=rec['candidate']['sha256'];r['source_canvas']=list(by_original[rec['original']][0].size);r.pop('crop',None)
   rp=S/'recipes'/Path(t['path']).name;raw=js(r);outputs[rp]=raw;recipes.append({'path':rp.relative_to(P).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'old_live_recipe_sha256':t['old_live_recipe_sha256']})
  summary[unit]={'entries':entries,'recipes':recipes,'generation':{'path':gp.relative_to(P).as_posix(),'sha256':hashlib.sha256(outputs[gp]).hexdigest()},'roles':sorted(info['templates'])}
 return outputs,summary
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();outputs,summary=produce()
 for path,raw in outputs.items():
  if a.check:assert path.read_bytes()==raw,'Stale derived output: '+str(path)
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 if not a.check:(S/'selection.json').write_bytes(js({'status':'authored configuration','candidate_only':True,'units':summary,'native_execution':False,'visual_approval_granted':False,'release_accepted':False}))
 print(json.dumps({'public_artifacts':len(outputs),'source_replay_exact':True}))
if __name__=='__main__':main()
