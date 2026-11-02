"""Replay seven new painted town states with exact preserved Demacia converters.
Only candidate source recipes and a named report sandbox are written. No active
recipe, design/content, manifest, stage or original reference is mutated.
"""
from pathlib import Path
import argparse,json,hashlib,io,shutil,sys
from PIL import Image
SELF=Path(__file__).resolve();S=SELF.parent;P=next(x for x in SELF.parents if x.name=='runeterra-demacia')
sys.path.insert(0,str(S/'pipeline-v1'))
from raster import convert as raster
from animation import assemble as animation
from town_masks import convert as masks
from indexed_animation import assemble as indexed
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'path':p.relative_to(P).as_posix(),'sha256':sha(p)}
def load(p):return json.loads(p.read_text(encoding='utf8'))
def enc(v):return(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf8')
def put(p,b,immutable=False):
 b=b if isinstance(b,bytes)else enc(b);p.parent.mkdir(parents=True,exist_ok=True)
 if immutable and p.exists()and p.read_bytes()!=b:raise ValueError('Version candidate before changing: '+str(p))
 p.write_bytes(b)
def png(im):
 b=io.BytesIO();im.save(b,format='PNG',compress_level=9);return b.getvalue()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--work-root',default='build/reports/demacia-replacement-replay-v1');args=parser.parse_args();work=(P/args.work_root).resolve()
 if not work.is_relative_to((P/'build/reports').resolve()):raise ValueError('Candidate work root must stay in thisproject build/reports')
 F=work/'runeterra-demacia';F.mkdir(parents=True,exist_ok=True);contract=load(S/'replay-contract-v1.json');inputs={SELF.relative_to(P).as_posix():sha(SELF),(S/'replay-contract-v1.json').relative_to(P).as_posix():sha(S/'replay-contract-v1.json')};receipts=[];candidate={};native={};registration=[]
 def add(p):inputs[p.relative_to(P).as_posix()]=sha(p)
 for m in contract['pipeline_modules']:
  q=m['snapshot'];assert sha(P/q['path'])==q['sha256']==m['exact_original_sha256'];add(P/q['path'])
 for q in contract['additional_inputs']:
  assert sha(P/q['path'])==q['sha256'];add(P/q['path'])
 for k,row in contract['affected_states'].items():
  folder=(P/row['raw_painted']['path']).parent;master=folder/'master.png';g=load(folder/'generation.json');crop=load(folder/'prepared-master-generation.json');im=Image.open(master).convert('RGBA')
  assert g['image_generation_used']is True and g['no3D_or_old_render_input']is True and g['model_id_exposed']is False
  assert g['painted_master_sha256']==sha(master)and g['prompt']+'\n'==(folder/'prompt-as-sent.txt').read_text(encoding='utf8')and not Image.open(master).info
  assert crop['crop']==list(im.getbbox())and png(im.crop(crop['crop']))==(folder/'prepared-master.png').read_bytes()
  for p in [master,folder/'generation.json',folder/'prompt-as-sent.txt',folder/'prepared-master.png',folder/'prepared-master-generation.json']:add(p)
  registration.append({'state':k,'prepared_master':pin(folder/'prepared-master.png'),'whole_original_master':pin(master),'candidate_box':row['candidate_box'],'canonical_copy_note':'rootcopiespreparedbytes toNEW assets/source/town/buildings/state/master-vN.png; oldmasters retained'})
 for name,h in list(inputs.items()):
  q=F/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/name,q)
 bg=load(P/contract['background_template']['path']);bgr=F/'assets/recipes/town-background-raster.json';put(bgr,bg);receipts.append(raster(F,bgr));hall={}
 for row in contract['unchanged_templates']:
  data=load(P/row['template']['path']);target=F/row['canonical_recipe'];put(target,data);receipt=raster(F,target);receipts.append(receipt)
  assert receipt['outputs'][0]['sha256']==row['expected_output_sha256']
  if row['role']=='hall-icon':hall[row['state']]=(target,receipt['outputs'][0])
 for k,row in contract['affected_states'].items():
  box=row['candidate_box'];pivot={'x':box[0]+box[2]//2,'y':box[1]+box[3],'basis':'Authored town placement; actual click and ground integration review pending'};master=row['canonical_prepared_master'];root='Content/Sprites/runeterra/demacia/town/structures/'+k
  r={'recipe_type':'raster','source':master['path'],'source_sha256':master['sha256'],'output_path':root+'-frame.png','size':box[2:],'fit':'contain','require_alpha':True,'canvas':[800,374],'position':box[:2],'pivot':pivot}
  name='assets/recipes/town-'+k+'-raster.json';rp=F/name;put(rp,r);receipt=raster(F,rp);receipts.append(receipt);frame=receipt['outputs'][0];native[k]=frame
  forms={'raster':r,'animation':{'recipe_type':'vcmi_animation','output_path':root+'.json','canvas':[800,374],'pivot':pivot,'depends_on':[name],'groups':[{'group':0,'frames':[{'source':frame['source'],'sha256':frame['sha256'],'generated_by':name}]}]},'masks':{'recipe_type':'town_masks','source':frame['source'],'source_sha256':frame['sha256'],'generated_by':name,'producer_sha256':sha(rp),'depends_on':[name],'output_area':root+'_area.png','output_border':root+'_border.png','canvas':[800,374],'pivot':pivot}}
  base={'recipe_type':'raster','source':master['path'],'source_sha256':master['sha256'],'fit':'contain','require_alpha':True}
  forms['campaign']={**base,'output_path':root+'_campaign.png','size':[58,64]};forms['hall-icon']={**base,'output_path':'Content/Sprites/runeterra/demacia/town/construction/'+k+'.png','size':[150,70],'content_box':[7,3,136,64],'background':contract['hall_icon_ground']}
  for role,data in forms.items():
   f=F/'assets/recipes'/('town-'+k+'-'+role+'.json');put(f,data);candidate[f.name]=data
   if role=='raster':continue
   receipt={'animation':animation,'masks':masks,'campaign':raster,'hall-icon':raster}[role](F,f);receipts.append(receipt)
   if role=='hall-icon':hall[k]=(f,receipt['outputs'][0])
 frames=[];depends=[]
 for k,(producer,row)in sorted(hall.items()):
  name=producer.relative_to(F).as_posix();depends.append(name);frames.append({'frame':contract['native_building_ids'][k],'source':row['source'],'sha256':row['sha256'],'generated_by':name,'producer_sha256':sha(producer)})
 atlas={'recipe_type':'indexed_animation','output_path':'Content/Sprites/runeterra/demacia/town/buildingsIcons.json','canvas':[150,70],'depends_on':sorted(depends),'frames':sorted(frames,key=lambda x:x['frame'])};f=F/'assets/recipes/town-construction-icons.json';put(f,atlas);receipts.append(indexed(F,f));candidate[f.name]=atlas
 # Every actual consumed publicinput is directlyavailable andpinned. Prospective
 # canonicalproducer edges are executed inside F, never against old activefiles.
 recipes=[];guards={Path(x['path']).name:x['sha256']for x in contract['before_recipe_guards']}
 for name,r in sorted(candidate.items()):
  r['dependencies']=[{'path':n,'sha256':h}for n,h in sorted(inputs.items())];out=S/'recipes-v1'/name;put(out,r,True);recipes.append({'path':out.relative_to(P).as_posix(),'sha256':sha(out),'active_recipe':'assets/recipes/'+name,'before_live_sha256':guards[name]})
 inventory={p.relative_to(F/'assets/generated').as_posix():sha(p)for p in sorted((F/'assets/generated').rglob('*'))if p.is_file()};put(work/'runtime-output-inventory.json',inventory);put(work/'actual-converter-receipts.json',receipts);put(S/'native-registration-v1.json',registration,True)
 selection={'status':'authored configuration','candidate_only':True,'producer':pin(SELF),'replay_contract':pin(S/'replay-contract-v1.json'),'recipes':recipes,'direct_live_input_pins':[{'path':n,'sha256':h}for n,h in sorted(inputs.items())],'prepared_master_registration':pin(S/'native-registration-v1.json'),'actual_runtime_output_count':len(inventory),'affected_states':list(contract['affected_states']),'unaffected_state_count':28,'canonical_master_copy_required':True,'no_active_source_stage_native_or_finalart_acceptance':True};put(S/'candidate-selection-v1.json',selection,True)
 print(json.dumps({'selection':pin(S/'candidate-selection-v1.json'),'candidate_recipes':len(recipes),'runtime_outputs':len(inventory),'direct_live_inputs':len(inputs)},indent=2))
if __name__=='__main__':main()
