"""Technical fixed-camera assembly from clean fresh painted Ionian T1 sources.
No old mesh/render pixels, private references or authoring reports are read.
"""
from pathlib import Path
from copy import deepcopy
import json,hashlib,io,importlib.util
import numpy as np
from PIL import Image,ImageDraw
SELF=Path(__file__).resolve();A=SELF.parent;N=A/"compiled-v2";S=A.parent
P=next(p for p in SELF.parents if p.name=='runeterra-ionia')
spec=importlib.util.spec_from_file_location('ionia_t1_components',A/'components.py')
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
pspec=importlib.util.spec_from_file_location('ionia_t1_projection',A/'projection_v1.py');PROJ=importlib.util.module_from_spec(pspec);pspec.loader.exec_module(PROJ)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def pin(p):return {'path':p.relative_to(P).as_posix(),'sha256':sha(p)}
def enc(v):return(json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode('utf8')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG',compress_level=9,optimize=False);return b.getvalue()
def put(p,v):
 assert p.resolve().is_relative_to(S.resolve())
 b=v if isinstance(v,bytes) else enc(v);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Immutable candidate changed; version before editing: '+str(p))
 p.write_bytes(b)
def category(cohort):return 'walk' if cohort.startswith('compact-walk') else cohort.split('-')[0]
def validate_generation(u,c):
 folder=S/u/c;g=load(folder/'generation.json');master=folder/'master.png';im=Image.open(master)
 assert g['image_generation_used']is True and g['model_id_exposed']is False
 assert g['old_guided_action_frames_used_as_inputs']is False
 assert g['painted_master']==master.relative_to(P).as_posix() and g['painted_master_sha256']==sha(master)
 assert g['prompt']+'\n'==(folder/'prompt-as-sent.txt').read_text(encoding='utf8')
 assert g['prompt_file']==pin(folder/'prompt-as-sent.txt')
 assert im.mode=='RGBA' and not im.info and digest(im.tobytes())==g['decoded_rgba_sha256']
 return g
def crop_sheet(u,cohort,camera):
 g=validate_generation(u,cohort);master=S/u/cohort/'master.png';im=Image.open(master).convert('RGBA')
 cat=category(cohort);columns,rows=camera['cohort_layouts'][cat];components=C.ordered_components(im,columns,rows)
 cal=camera['calibration_index'][cat];control=components[cal];bodyheight=control['box'][3]-control['box'][1]
 if cat=='melee':bodyheight=camera['melee_body_calibration_source_height'][u]
 target=camera['adventure']['parent_whole_figure_height']if cat=='auxiliary' else camera['units'][u]['battle_body_height']
 scale=target/bodyheight;offset=C.support_x(control)-(cal%columns+.5)*im.width/columns
 root=camera['battle']['root']
 canvas=camera['battle']['canvas']
 frames=[];records=[]
 for i,component in enumerate(components):
  canvas=camera['battle']['canvas']
  crop,support,box=C.isolate(im,component);size=(round(crop.width*scale),round(crop.height*scale))
  scaled=crop.resize(size,Image.Resampling.LANCZOS)
  source_root=((i%columns+.5)*im.width/columns+offset,component['box'][3]-1)
  dest=(round(root[0]-(source_root[0]-box[0])*scale),round(root[1]-(source_root[1]-box[1])*scale))
  if min(dest)<0 or dest[0]+size[0]>canvas[0]or dest[1]+size[1]>canvas[1]:
   raise ValueError('Complete native figure would clip: '+str((u,cohort,i,dest,size,canvas)))
  out=Image.new('RGBA',tuple(canvas),(0,0,0,0));out.alpha_composite(scaled,dest)
  parent_pin=None;projection_contract=None
  if cat=='auxiliary':
   parent=N/u/cohort/f'parent-{i:03d}.png';put(parent,png(out));parent_pin=pin(parent)
   proof=PROJ.measure(out,tuple(root),.5,False)
   if proof['opaque_pixels_outside_canvas']:raise ValueError('Native adventure projection clips: '+str((u,i,proof)))
   out=PROJ.project(out,tuple(root),.5,False);canvas=camera['adventure']['canvas']
   projection_contract={'source':parent_pin['path'],'source_sha256':parent_pin['sha256'],'pivot':root,'scale':.5,'mirrored':False,'anchor':camera['adventure']['root'],'canvas':canvas,'source_facing':camera['adventure']['source_facings'].get(str(i),'right'),'source_kind':'independently painted compact action source registered on450x400; no old3D pixels'}
  native=N/u/cohort/f'pose-{i:03d}.png';mask=N/u/cohort/f'pose-{i:03d}-aa-support.png'
  put(native,png(out));put(mask,png(support))
  frames.append(out);records.append({'pose':i,'master':pin(master),'component_core_bbox':component['box'],'component_core_pixels':component['pixels'],'source_isolation_crop':box,'aa_support_mask':pin(mask),'uniform_sheet_scale':scale,'source_root':list(source_root),'native_root':root,'native_canvas':canvas,'destination':list(dest),'scaled_whole_size':list(size),'native_visible_bbox':list(out.getbbox()),'native':pin(native),'no_mirror_stretch_warp_or_pose_generation':True,'projection_contract':projection_contract,'full_parent':parent_pin})
 reg=N/u/cohort/'registration.json'
 put(reg,{'status':'authored configuration','unit':u,'cohort':cohort,'master':pin(master),'layout':[columns,rows],'calibration_pose':cal,'calibration_source_body_height':bodyheight,'target_native_height':target,'uniform_sheet_scale':scale,'common_source_x_offset':offset,'root_policy':camera['root_policy'],'frames':records})
 return reg,records
def portraits(u,camera):
 master=S/u/'identity-v1/master.png';validate_generation(u,'identity-v1');im=Image.open(master).convert('RGBA');rows=[]
 for role,size in [('large',[58,64]),('small',[32,32])]:
  box=camera['portrait_crops'][u][role];crop=im.crop(box);scale=min(size[0]/crop.width,size[1]/crop.height)
  crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
  out=Image.new('RGBA',tuple(size),(0,0,0,0));out.alpha_composite(crop,((size[0]-crop.width)//2,(size[1]-crop.height)//2))
  p=N/u/'portraits'/(role+'.png');put(p,png(out));rows.append({'role':role,'master':pin(master),'crop':box,'uniform_contain':True,'native':pin(p),'native_canvas':size})
 reg=N/u/'portraits/registration.json';put(reg,rows);return reg,rows
def main():
 camera=load(A/'camera-contract-v2.json');contract=load(S/'authored-contracts-v1.json')
 inputs={p.relative_to(P).as_posix():sha(p)for p in [SELF,A/'components.py',A/'projection_v1.py',A/'camera-contract-v2.json',S/'authored-contracts-v1.json']}
 sources={};generations=[];registrations=[]
 for u,settings in camera['units'].items():
  sources[u]={}
  for cohort in ['identity-v1']+settings['cohorts']:
   folder=S/u/cohort;g=validate_generation(u,cohort);generations.append(pin(folder/'generation.json'))
   for n in ['master.png','generation.json','prompt-as-sent.txt']:
    p=folder/n;inputs[p.relative_to(P).as_posix()]=sha(p)
   if cohort!='identity-v1':
    reg,records=crop_sheet(u,cohort,camera);sources[u][category(cohort)]=records
    registrations.append(pin(reg));inputs[reg.relative_to(P).as_posix()]=sha(reg)
    for record in records:
     for k in ['native','aa_support_mask','full_parent']:
      if record.get(k):inputs[record[k]['path']]=record[k]['sha256']
  reg,rows=portraits(u,camera);sources[u]['portraits']=rows;registrations.append(pin(reg));inputs[reg.relative_to(P).as_posix()]=sha(reg)
  for row in rows:inputs[row['native']['path']]=row['native']['sha256']
 # All own-painted artistic ancestry is live and public; private official/native
 # references are inspection-only records with exact hashes, not replay inputs.
 for gp in generations:
  for ref in load(P/gp['path'])['input_references']:
   ancestor=ref.get('public_pixel_equivalent')
   if ancestor:assert inputs.get(ancestor['path'])==ancestor['sha256']
 recipepins=[]
 for u,settings in camera['units'].items():
  for role,fields in contract['units'][u]['roles'].items():
   recipe={k:deepcopy(fields[k])for k in ['recipe_type','output_path','canvas','size','pivot','generateOverlay','generateShadow','require_alpha','fit','movement','shot_release']if k in fields}
   recipe.update(unit=u,status='built-unreviewed',production_status='painted-master-complete-unapproved',visual_approval_granted=False,
     credits={'author':'OpenAI builtin imagegen; project-directed original2D identity/action authoring and deterministic conversion','license':None,'redistribution':'unresolved; release prohibited'},
     acceptance='Authored configuration source candidate. Native camera/motion/crest UI and final art/rights acceptance remain separate.',
     dependencies=[{'path':n,'sha256':h}for n,h in sorted(inputs.items())])
   sheet='identity-v1'if role in ('large','small')else next(c for c in settings['cohorts']if category(c)==('general'if role=='battle'else'auxiliary'))
   g=load(S/u/sheet/'generation.json')
   recipe['generation']={k:deepcopy(g[k])for k in ['image_generation_used','provider','model','model_id_exposed','prompt','painted_master','painted_master_sha256']}
   recipe['generation'].update(generation_record=pin(S/u/sheet/'generation.json'),technical_producer=pin(SELF),supplementary_painted_sources=[pin(S/u/c/'master.png')for c in ['identity-v1']+settings['cohorts']],no3Dmodelling_or_rendering=True,old_guided_action_frames_used_as_inputs=False)
   if role in ('battle','map'):
    groups=[]
    if role=='battle':
     for group in fields['groups']:
      mapping=camera['group_source_map'][str(group['group'])];records=[sources[u][mapping['cohort']][i]for i in mapping['indices']]
      assert len(records)==group['frames']
      groups.append({'group':group['group'],'action':mapping['cohort']+' genuine painted poses','frames':[{'source':r['native']['path'],'source_sha256':r['native']['sha256'],'sha256':r['native']['sha256'],'source_canvas':r['native_canvas']}for r in records]})
    else:
     records=sources[u]['auxiliary'][:6];groups=[{'group':0,'action':'six genuine compact adventure gait phases','frames':[{'source':r['native']['path'],'source_sha256':r['native']['sha256'],'sha256':r['native']['sha256'],'source_canvas':r['native_canvas'],'projection_contract':r['projection_contract']}for r in records]}]
    recipe['groups']=groups
   else:
    record=next(r for r in sources[u]['portraits']if r['role']==role)if role in ('large','small')else sources[u]['auxiliary'][6 if role=='attackLeft' else 7]
    source=record['native'];recipe.update(source=source['path'],source_sha256=source['sha256'],sha256=source['sha256'],source_canvas=record['native_canvas'],fit='exact')
    if role.startswith('attack'):recipe['projection_contract']=record['projection_contract']
   p=S/'recipes-v2'/(u+'-'+role+'.json');put(p,recipe)
   recipepins.append({'path':p.relative_to(P).as_posix(),'sha256':sha(p),'active_recipe':fields['original_active_recipe'],'before_live_sha256':fields['before_live_sha256']})
 selection={'status':'authored configuration','candidate_only':True,'units':list(camera['units']),'producer':pin(SELF),'camera_contract':pin(A/'camera-contract-v2.json'),'authored_contract':pin(S/'authored-contracts-v1.json'),'generation_records':generations,'registrations':registrations,'direct_live_input_pins':[{'path':n,'sha256':h}for n,h in sorted(inputs.items())],'recipes':recipepins,'no_private_inputs':True,'no_old_guided_pixels':True,'no_runtime_or_release_acceptance':True}
 put(S/'candidate-selection-v2.json',selection)
 print(json.dumps({'selection_sha256':sha(S/'candidate-selection-v2.json'),'recipes':len(recipepins),'direct_live_inputs_per_recipe':len(inputs)},indent=2))
if __name__=='__main__':main()

