"""Technical reduction of fifteen genuine painted mechanic symbols; no procedural art."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,io
from PIL import Image
SELF=Path(__file__).resolve();S=SELF.parent;P=next(x for x in SELF.parents if x.name=='runeterra-ionia')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'path':p.relative_to(P).as_posix(),'sha256':sha(p)}
def load(p):return json.loads(p.read_text(encoding='utf8'))
def enc(v):return(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf8')
def put(p,b):
 b=b if isinstance(b,bytes)else enc(b);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists()and p.read_bytes()!=b:raise ValueError('Version immutable symbol candidate before changing: '+str(p))
 p.write_bytes(b)
def png(im):
 b=io.BytesIO();im.save(b,format='PNG',compress_level=9);return b.getvalue()
def main():
 contract=load(S/'authored-contract-v1.json');inputs={p.relative_to(P).as_posix():sha(p)for p in [SELF,S/'authored-contract-v1.json']};generation=[];native={};records=[]
 assert len(contract['heroes'])==15
 for u,row in sorted(contract['heroes'].items()):
  f=S/u/'v1';g=load(f/'generation.json');im=Image.open(f/'master.png').convert('RGBA')
  assert g['image_generation_used']is True and g['model_id_exposed']is False and g['no3D_or_procedural_art_input']is True
  assert g['painted_master']==(f/'master.png').relative_to(P).as_posix()and sha(f/'master.png')==g['painted_master_sha256']
  assert g['prompt']+'\n'==(f/'prompt-as-sent.txt').read_text(encoding='utf8')and not Image.open(f/'master.png').info and im.getextrema()[3]==(255,255)
  for p in [f/'master.png',f/'generation.json',f/'prompt-as-sent.txt']:inputs[p.relative_to(P).as_posix()]=sha(p)
  for ref in g['input_references']:
   pins=([ref['public_pixel_equivalent']]if 'public_pixel_equivalent'in ref else[])+ref.get('parent_provenance',[])
   for q in pins:
    assert sha(P/q['path'])==q['sha256'];inputs[q['path']]=q['sha256']
  generation.append(pin(f/'generation.json'));native[u]={}
  for consumer in row['consumers']:
   role=consumer['role'];size=consumer['size'];assert size==([44,44]if role=='specialtyLarge'else[32,32])
   out=im.resize(tuple(size),Image.Resampling.LANCZOS);p=S/'native-v1'/u/(role+'.png');put(p,png(out));inputs[p.relative_to(P).as_posix()]=sha(p);native[u][role]=pin(p)
   records.append({'hero':u,'role':role,'source_master':pin(f/'master.png'),'whole_canvas':list(im.size),'native':pin(p),'size':size,'technical_operation':'whole painted square uniformly resized, no crop/filter/frame/newglyph'})
 reg=S/'native-v1/registration.json';put(reg,records);inputs[reg.relative_to(P).as_posix()]=sha(reg)
 recipes=[]
 for u,row in sorted(contract['heroes'].items()):
  g=load(S/u/'v1/generation.json')
  for c in row['consumers']:
   src=native[u][c['role']]
   r={'hero':u,'role':'hero-'+c['role'],'recipe_type':'raster','output_path':c['output_path'],'production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'source':src['path'],'source_sha256':src['sha256'],'sha256':src['sha256'],'source_canvas':c['size'],'size':c['size'],'fit':'exact','credits':deepcopy(g['credits']),'generation':{k:deepcopy(g[k])for k in ['image_generation_used','provider','model','model_id_exposed','prompt','painted_master','painted_master_sha256']},'dependencies':[{'path':n,'sha256':h}for n,h in sorted(inputs.items())],'icon_semantics':row['specialty_text']['description'],'mechanic_exact_dictionary':row['specialty'],'acceptance':'authored configuration source candidate; nativeUI/humanart/rights remain separate'}
   r['generation'].update(generation_record=pin(S/u/'v1/generation.json'),technical_producer=pin(SELF),no3D_or_procedural_art_input=True)
   p=S/'recipes-v1'/(u+'-'+c['role']+'.json');put(p,r);recipes.append({'path':p.relative_to(P).as_posix(),'sha256':sha(p),'active_recipe':c['active_recipe'],'before_live_sha256':c['before_live_sha256']})
 selection={'status':'authored configuration','candidate_only':True,'producer':pin(SELF),'authored_contract':pin(S/'authored-contract-v1.json'),'recipes':recipes,'generation_records':generation,'native_registration':pin(reg),'direct_live_input_pins':[{'path':n,'sha256':h}for n,h in sorted(inputs.items())],'heroes':list(sorted(contract['heroes'])),'native_or_final_art_or_rights_acceptance':False}
 put(S/'candidate-selection-v1.json',selection);print(json.dumps({'selection':pin(S/'candidate-selection-v1.json'),'recipes':len(recipes),'direct_live_inputs_per_recipe':len(inputs)},indent=2))
if __name__=='__main__':main()
