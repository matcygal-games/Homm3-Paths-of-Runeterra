"""Pure fixed-camera preview propagation from exact before/crest battle frames."""
from pathlib import Path
import argparse,copy,hashlib,io,json
from PIL import Image
SELF=Path(__file__).resolve();S=SELF.parent;P=S.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(a):return(json.dumps(a,indent=2,sort_keys=True)+'\n').encode()
def pin(p):return{'path':p.relative_to(P).as_posix(),'sha256':sha(p)}
def png(im):
 s=io.BytesIO();im.save(s,format='PNG');return s.getvalue()
def project(image,camera):
 out=Image.new('RGBA',(100,130));out.paste(image.crop(camera['source_union']).resize(tuple(camera['resized_union']),Image.Resampling.LANCZOS),tuple(camera['offset']));return out
def build(planpath):
 plan=json.loads(planpath.read_text());assert sha(SELF)==plan['producer_sha256'],'Stale preview producer'
 for n,h in plan['input_sha256'].items():assert sha(P/n)==h,'Missing/stale preview source: '+n
 deps=[pin(SELF),pin(planpath)]+[{'path':n,'sha256':h}for n,h in sorted(plan['input_sha256'].items())];outputs={};records=[]
 for unit,job in plan['units'].items():
  r=json.loads((P/job['template']).read_text());generation=json.loads((P/job['crest_generation']).read_text());generation['preview_source_derivative']={'producer':pin(SELF),'plan':pin(planpath),'method':'Exact existing stable preview camera applied to original and crest-edited battle frames. Original baseline PNG RGBA replay exact; no anatomy or new poses synthesized.','camera':job['camera']};r['generation']=generation;r['dependencies']=deps;r['visual_approval_granted']=False;r['status']='built-unreviewed'
  by={(x['group'],x['frame']):x for x in job['frames']};destinations={}
  for group in r['groups']:
   for i,frame in enumerate(group['frames']):
    row=by[group['group'],i];old=project(Image.open(P/row['original_battle']).convert('RGBA'),job['camera']);expected=Image.open(P/row['original_preview']).convert('RGBA');assert old.tobytes()==expected.tobytes(),'Original preview camera drift'
    new=project(Image.open(P/row['candidate_battle']).convert('RGBA'),job['camera']);assert old.getchannel('A').tobytes()==new.getchannel('A').tobytes(),'Preview silhouette drift';raw=png(new);checksum=hashlib.sha256(raw).hexdigest();dst=S/'preview-followup-v1'/unit/f'frame-{checksum[:24]}.png';outputs[dst]=raw;destinations[str(dst)]=checksum
    frame['source']=dst.relative_to(P).as_posix();frame['source_sha256']=checksum;frame['sha256']=checksum
  rp=S/'recipes-preview-followup-v1'/f'{unit}-preview.json';raw=js(r);outputs[rp]=raw;records.append({'unit':unit,'recipe':rp.relative_to(P).as_posix(),'recipe_sha256':hashlib.sha256(raw).hexdigest(),'old_live_recipe_sha256':job['old_live_recipe_sha256'],'unique_frame_outputs':len(destinations),'baseline_camera_rgba_exact':True,'new_alpha_exact':True})
 return outputs,records
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cohort',required=True);ap.add_argument('--check',action='store_true');a=ap.parse_args();plan=S/f'inputs-previews-{a.cohort}-v1.json';outputs,records=build(plan)
 for path,raw in outputs.items():
  if a.check:assert path.read_bytes()==raw,'Changed preview output: '+str(path)
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 if not a.check:(S/f'selection-previews-{a.cohort}-v1.json').write_bytes(js({'status':'authored configuration','candidate_only':True,'preview_recipes':records,'native_execution':False,'release_accepted':False}))
 print(json.dumps({'preview_artifacts':len(outputs),'baseline_and_new_alpha_exact':True}))
if __name__=='__main__':main()
