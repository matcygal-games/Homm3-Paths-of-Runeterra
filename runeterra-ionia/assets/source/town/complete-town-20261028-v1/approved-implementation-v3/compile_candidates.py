"""Actual configured town compiler replay, strictly into own candidate outputs."""
from pathlib import Path
import hashlib,json,sys,io
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-ionia')
WORKSPACE=PROJECT.parent
sys.path.insert(0,str(WORKSPACE/'scripts'))
from faction_art_compile import create_compiler
from assemble import fit,read,dump,ref,rel,sha,image
PREFIX='Content/Sprites/runeterra/ionia/'
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v3'
def main():
 index=read(HERE/'frame-index.json');compiler=create_compiler('ionia');ids=compiler.indexed_building_ids(PROJECT)
 source_root=HERE/'prepared';recipes=HERE/'recipes';recipes.mkdir(exist_ok=True)
 background=image(source_root/'background.png')
 for state,key in [('village','villageHall'),('fort','castle')]:
  actor=image(source_root/'structures'/key/'layer.png');sprite=actor.crop(actor.getchannel('A').getbbox())
  for variant in ('normal','built'):
   for size,canvas in [('large',(58,64)),('small',(48,32))]:
    panel=background.resize(canvas,Image.Resampling.LANCZOS);small=fit(sprite,(canvas[0]-2,canvas[1]-3));panel.alpha_composite(small,((canvas[0]-small.width)//2,canvas[1]-small.height))
    if variant=='built':
     d=ImageDraw.Draw(panel);d.line((canvas[0]-10,2,canvas[0]-3,9),fill=(210,48,32),width=2);d.line((canvas[0]-10,9,canvas[0]-3,2),fill=(210,48,32),width=2)
    p=source_root/'icons'/f'{state}_{variant}_{size}.png';p.parent.mkdir(exist_ok=True);panel.save(p)
 dependencies=[ref(HERE/'art-source-inputs.json'),ref(HERE/'compile_candidates.py'),ref(HERE/'frame-index.json'),*read(HERE/'art-source-inputs.json')['dependencies']]
 for p in sorted(source_root.rglob('*.png')):dependencies.append(ref(p))
 dump(HERE/'source-inputs.json',{'status':'authored configuration','method':'Immutable user-selected genuine painted2D IL4 whole town; exact deterministic technical decomposition and independent genuine development paintings. No 3D dependencies. Formal physical/native/rights review remains separate.','dependencies':dependencies})
 common={'status':'painted-candidate','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'generation':{'image_generation_used':False,'method':'Deterministic extraction from user-selected genuine painted2D whole town; raw master/prompt ancestry and technical source record are pinned. No authored-pixel repaint.','source_record':ref(HERE/'source-inputs.json')},'inputs':[ref(HERE/'source-inputs.json')],'acceptance':'User selected IL4 fully-built pixels; engineering, native visual/click and redistribution acceptance remain separate.'}
 records=[]
 def descriptor(p):return {'source':rel(p),'source_sha256':sha(p),'source_canvas':list(Image.open(p).size)}
 def save(name,body):
  p=recipes/name;dump(p,{**common,**body});records.append({'candidate':rel(p),'canonical':'assets/recipes/town/'+name,'sha256':sha(p),'before_sha256':sha(PROJECT/'assets/recipes/town'/name),'output_path':body['output_path']})
 def raster(name,p,out,technical=False):save(name,{'recipe_type':'raster','canvas':list(Image.open(p).size),'fit':'exact','require_alpha':True,'output_path':PREFIX+out,**descriptor(p),**({'production_status':'derived-technical-mask-complete'}if technical else{})})
 raster('background.png.json',source_root/'background.png','town/background.png')
 for state in index['frames']:
  folder=source_root/'structures'/state;d=descriptor(folder/'layer.png')
  save('structures_'+state+'.json.json',{'recipe_type':'vcmi_animation','canvas':[800,374],'pivot':{'x':0,'y':0},'groups':[{'group':0,'frames':[{**d,'sha256':d['source_sha256']}]}],'output_path':PREFIX+'town/structures/'+state+'.json'})
  for role in ('area','border','campaign'):raster('structures_'+state+'_'+role+'.png.json',folder/(role+'.png'),'town/structures/'+state+'_'+role+'.png',role!='campaign')
 save('buildingIcons.json.json',{'recipe_type':'indexed_animation','canvas':[150,70],'pivot':{'x':0,'y':0},'frames':[{**descriptor(source_root/'structures'/s/'icon.png'),'building':s,'frame':ids[s]}for s in sorted(index['frames'],key=lambda s:ids[s])],'output_path':PREFIX+'town/buildingIcons.json'})
 for state in ('village','fort'):
  for variant in ('normal','built'):
   for size in ('large','small'):
    name=f'{state}_{variant}_{size}.png';raster('icons_'+name+'.json',source_root/'icons'/name,'town/icons/'+name)
 # Preserve the five actual existing painted2D adventure-map producers exactly.
 for p in sorted((PROJECT/'assets/recipes/town').glob('map_*.json.json')):
  q=recipes/p.name;q.write_bytes(p.read_bytes());r=read(q);records.append({'candidate':rel(q),'canonical':'assets/recipes/town/'+p.name,'sha256':sha(q),'before_sha256':sha(p),'output_path':r['output_path'],'preserved':True})
 assert len(records)==155
 outputs={};plans=[];outroot=REPORT/'compiled'
 for r in records:
  products,receipt=compiler.plan(PROJECT,PROJECT/r['candidate'])
  for name,data in products.items():
   if name in outputs:raise ValueError('Duplicate output '+name)
   q=outroot/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);outputs[name]=hashlib.sha256(data).hexdigest()
  plans.append({'recipe':r['candidate'],'recipe_sha256':r['sha256'],'receipt':receipt})
 layers={}
 for s in index['frames']:
  definition=read(outroot/(PREFIX+'town/structures/'+s+'.json'));seq=definition['sequences'][0];frame=seq['frames'][0];layers[s]=Image.open(outroot/'Content/Sprites'/definition.get('basepath','')/frame).convert('RGBA')
 compiled=image(outroot/(PREFIX+'town/background.png'))
 for s in index['complete_scene_states']:compiled.alpha_composite(layers[s])
 approved=image(HERE/'approved-full.png');exact=compiled.tobytes()==approved.tobytes();assert exact
 compiled.save(REPORT/'compiled-approved-full.png')
 dump(HERE/'recipe-index.json',{'status':'authored configuration','recipes':records,'recipe_count':155,'preserved_map_producers':5,'canonical_writes':False})
 dump(REPORT/'compiler-receipt.json',{'status':'authored configuration','actual_compiler':{'path':'scripts/faction_art_compile.py','sha256':sha(WORKSPACE/'scripts/faction_art_compile.py')},'native_building_id_library':{'path':'vcmi-develop/vcmi-develop/config/buildingsLibrary.json','sha256':sha(WORKSPACE/'vcmi-develop/vcmi-develop/config/buildingsLibrary.json')},'recipe_count':len(records),'output_count':len(outputs),'outputs':outputs,'plans':plans,'compiled_decoded_RGBA_exact':exact,'approved_full':ref(HERE/'approved-full.png'),'compiled_full_PNG_sha256':sha(REPORT/'compiled-approved-full.png'),'compiled_full_PNG_bytes_exact':(REPORT/'compiled-approved-full.png').read_bytes()==(HERE/'approved-full.png').read_bytes(),'compiled_RGBA_sha256':hashlib.sha256(compiled.tobytes()).hexdigest(),'approved_RGBA_sha256':hashlib.sha256(approved.tobytes()).hexdigest(),'native_execution':False,'canonical_writes':False,'physical_acceptance':False,'release_accepted':False})
 print(json.dumps({'recipes':len(records),'outputs':len(outputs),'compiled_RGBA_exact':exact,'canonical_writes':False}))
if __name__=='__main__':main()
