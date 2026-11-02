"""Reproduce V2 from saved genuine painted edits. No active recipe/stage writes."""
from pathlib import Path
from copy import deepcopy
import argparse,hashlib,json
import numpy as np
from PIL import Image,ImageOps,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
WORKSPACE=PROJECT.parent
STATES=('villageHall','townHall','cityHall','capitol')
POLYGONS={
 'villageHall':[(120,65),(280,15),(435,40),(510,170),(495,270),(120,265)],
 'townHall':[(140,58),(300,45),(380,130),(402,188),(365,200),(135,181),(105,155)],
 'cityHall':[(255,13),(445,8),(498,95),(476,145),(286,133),(205,110)],
 'capitol':[(100,60),(215,30),(303,100),(326,187),(290,204),(120,210),(65,166)],
}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
rel=lambda p:Path(p).relative_to(PROJECT).as_posix()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9,optimize=False)
def same(a,b):return np.array_equal(np.array(a),np.array(b))
def icon_fit(im,size,conversion):
 fitted=ImageOps.contain(im.crop(conversion['source_crop_xyxy']),(size[0]-8,size[1]-8),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',size);canvas.alpha_composite(fitted,((size[0]-fitted.width)//2,(size[1]-fitted.height)//2));return canvas
def native(im,conversion):
 fit=ImageOps.contain(im.crop(conversion['source_crop_xyxy']),tuple(conversion['composition_rectangle'][2:]),Image.Resampling.LANCZOS)
 assert list(fit.size)==conversion['fit_size'],'unchanged fit required'
 x,y,w,h=conversion['composition_rectangle'];layer=Image.new('RGBA',(800,374));layer.alpha_composite(fit,(x+(w-fit.width)//2,y+h-fit.height));return layer
def descriptor(path):
 with Image.open(path) as im:size=list(im.size)
 return {'source':rel(path),'source_sha256':sha(path),'source_canvas':size}

def prepare(report):
 report=Path(report).resolve()
 if not report.is_relative_to((WORKSPACE/'build/reports/regional-crests-20261025-v1/bandle-town-art').resolve()):raise ValueError('report outside assigned lane')
 report.mkdir(parents=True,exist_ok=True)
 targets=read(HERE/'targets.json');active={name:sha(PROJECT/name) for name in targets['unchanged_active_inputs']}
 producer={'path':rel(Path(__file__)),'sha256':sha(__file__)}
 rows=[];bindings=[];layers={};old_layers={};consumed={rel(HERE/'targets.json'):sha(HERE/'targets.json'),producer['path']:producer['sha256']}
 for state in STATES:
  info=targets['states'][state];folder=HERE/state;master=PROJECT/info['original_master'];assert sha(master)==info['original_sha256']
  original=Image.open(master).convert('RGBA');box=info['target_crop_xyxy'];crop=original.crop(box)
  provider_path=folder/'provider-edit-v2.png';assert sha(provider_path)==info['provider_sha256']
  provider=Image.open(provider_path).convert('RGBA');assert abs(provider.width/provider.height-crop.width/crop.height)<0.005
  edit=provider.resize(crop.size,Image.Resampling.LANCZOS)
  mask=Image.new('L',crop.size);ImageDraw.Draw(mask).polygon(POLYGONS[state],fill=255);mask=mask.filter(ImageFilter.GaussianBlur(1.2))
  # Restrict technical assembly to near-opaque roof material (the originals
  # include alpha254 painted cores). Never alter
  # the old outline, translucent edges or transparent hidden RGB.
  mask=Image.fromarray(np.where(np.array(crop)[:,:,3]>=240,np.array(mask),0).astype('uint8'))
  save(folder/'painted-surface-mask.png',mask)
  edited=Image.composite(edit,crop,mask);edited.putalpha(crop.getchannel('A'));candidate=original.copy();candidate.paste(edited,(box[0],box[1]))
  a,b=np.array(original),np.array(candidate);changed=np.any(a!=b,axis=2)
  full_mask=Image.new('L',original.size);full_mask.paste(mask,(box[0],box[1]));allowed=np.array(full_mask)>0
  assert np.array_equal(a[:,:,3],b[:,:,3]);assert not np.any(changed & ~allowed);assert not np.any(changed & (a[:,:,3]==0))
  candidate_path=folder/'master-candidate-v2.png';save(candidate_path,candidate)
  baseline=HERE/f'inputs/recipes/structures/{state}-animation.json';recipe=read(baseline);conversion=recipe['generation']['conversion']
  old_source=PROJECT/recipe['groups'][0]['frames'][0]['source'];old_layer=Image.open(old_source).convert('RGBA');assert same(old_layer,native(original,conversion))
  layer=native(candidate,conversion);assert same(layer.getchannel('A'),old_layer.getchannel('A'));save(folder/'layer.png',layer);layers[state]=layer;old_layers[state]=old_layer
  for role in ('area','border','campaign'):
   old_recipe=read(HERE/f'inputs/recipes/structures/{state}-{role}.json');old_file=PROJECT/old_recipe['source']
   if role=='campaign':
    old=Image.open(old_file).convert('RGBA');assert same(old,icon_fit(original,(58,64),conversion));new=icon_fit(candidate,(58,64),conversion);assert same(old.getchannel('A'),new.getchannel('A'));save(folder/'campaign.png',new)
   else:(folder/(role+'.png')).write_bytes(old_file.read_bytes())
   consumed[rel(old_file)]=sha(old_file)
  old_icon=old_source.parent/'hall-icon.png';assert same(Image.open(old_icon).convert('RGBA'),icon_fit(original,(150,70),conversion));new_icon=icon_fit(candidate,(150,70),conversion)
  assert same(Image.open(old_icon).getchannel('A'),new_icon.getchannel('A'));save(folder/'hall-icon.png',new_icon)
  inputs=[master,baseline,provider_path,folder/'edit-target-crop.png',folder/'prompt-v2.txt',folder/'painted-surface-mask.png',HERE/'targets.json',Path(__file__),old_source,old_icon]
  for role in ('area','border','campaign'):
   before_recipe=HERE/f'inputs/recipes/structures/{state}-{role}.json'
   inputs.extend((before_recipe,PROJECT/read(before_recipe)['source']))
  generation=deepcopy(recipe['generation']);generation['original_generation_prompt']=generation['prompt'];generation.update(painted_master=rel(candidate_path),painted_master_sha256=sha(candidate_path),prompt=(folder/'prompt-v2.txt').read_text(encoding='utf-8'))
  generation['regional_crest_revision']={'revision':'bandle-hall-crest-legibility-v2','method':'Genuine built-in imagegen painted civic roof field; strict technical mask assembly, no code-drawn crest or3D',
   'producer':producer,'inputs':[{'path':rel(p),'sha256':sha(p)} for p in inputs],
   'official_reference_url':'https://universe.leagueoflegends.com/images/bandle_city_crest_icon@2x.png','official_reference_sha256':'141482169c3b1994fef7f338abc4a22897574b831bcfd0437f905f9462233ac5','access_date':'2026-10-25',
   'official_reference_private_not_bundled':True,'visual_approval_granted':False,'redistribution_approved':False}
  for role in ('animation','area','border','campaign'):
   old=HERE/f'inputs/recipes/structures/{state}-{role}.json';value=read(old)
   if role=='animation':value['groups'][0]['frames']=[descriptor(folder/'layer.png')]
   else:value.update(descriptor(folder/(role+'.png')))
   value['generation']=deepcopy(generation);value['visual_approval_granted']=False
   dest=HERE/f'recipes/structures/{state}-{role}.json';write(dest,value);bindings.append({'active':f'assets/recipes/town/structures/{state}-{role}.json','candidate':rel(dest),'sha256':sha(dest)})
   consumed[rel(old)]=sha(old)
  for file in inputs:consumed[rel(file)]=sha(file)
  coords=np.argwhere(np.any(np.array(layer)!=np.array(old_layer),axis=2));bounds=[int(coords[:,1].min()),int(coords[:,0].min()),int(coords[:,1].max()+1),int(coords[:,0].max()+1)]
  rows.append({'state':state,'original_master':rel(master),'original_sha256':sha(master),'candidate_master':rel(candidate_path),'candidate_sha256':sha(candidate_path),'master_alpha_exact':True,'outside_mask_RGBA_exact':True,'native_alpha_exact':True,
   'native_changed_bbox_xyxy':bounds,'changed_master_pixels':int(changed.sum()),'area_bytes_exact':sha(folder/'area.png')==sha(PROJECT/read(HERE/f'inputs/recipes/structures/{state}-area.json')['source']),
   'border_bytes_exact':sha(folder/'border.png')==sha(PROJECT/read(HERE/f'inputs/recipes/structures/{state}-border.json')['source']),'native_crest_legibility_review':'pending root review','visual_approval_granted':False})
 baseline=HERE/'inputs/recipes/buildingIcons.json';icons=read(baseline)
 icons['generation']['regional_crest_revision']={'revision':'bandle-hall-crest-legibility-v2','producer':producer,
  'inputs':[{'path':rel(baseline),'sha256':sha(baseline)},{'path':rel(HERE/'targets.json'),'sha256':sha(HERE/'targets.json')}],
  'scope':'Only four Hall frame source descriptors change; all other indexed frames preserved','visual_approval_granted':False}
 for frame in icons['frames']:
  if frame['building'] in STATES:frame.update(descriptor(HERE/frame['building']/'hall-icon.png'))
  consumed[frame['source']]=sha(PROJECT/frame['source'])
 path=HERE/'recipes/buildingIcons.json';write(path,icons);bindings.append({'active':'assets/recipes/town/buildingIcons.json','candidate':rel(path),'sha256':sha(path),'scope':'four Hall source descriptors only'})
 consumed[rel(baseline)]=sha(baseline)
 # Candidate-only documentation context. Report imagery is not an input needed
 # to reproduce the candidate masters/recipes and never substitutes for native.
 design=read(HERE/'inputs/design/town-visuals.json');faction=read(HERE/'inputs/content/factions.json')['bandlecity'];structures=faction['town']['structures'];background=PROJECT/design['terrain']['native']
 for hall in STATES:
  for variant in ('before','candidate'):
   canvas=Image.open(background).convert('RGBA');chosen=[]
   for site in design['sites']:
    if site['id'] in ('coast','grailOrnament'):continue
    chosen.append(hall if site['id']=='hall' else site['states'][0 if hall in STATES[:2] else -1])
   for state in sorted(chosen,key=lambda s:structures[s]['z']):
    if state==hall:image=old_layers[state] if variant=='before' else layers[state]
    else:image=Image.open(PROJECT/design['sites'][next(i for i,s in enumerate(design['sites']) if state in s['states'])]['selected_state_art'][state]['native_layer']).convert('RGBA')
    canvas.alpha_composite(image,(structures[state]['x'],structures[state]['y']))
   save(report/f'{hall}-{variant}-native.png',canvas)
 sheet=Image.new('RGB',(840,520),(48,43,36));draw=ImageDraw.Draw(sheet)
 for i,state in enumerate(STATES):
  x=i*210;draw.text((x+5,5),state,fill='white')
  for row,im in enumerate((old_layers[state],layers[state])):
   crop=im.crop((175,42,280,142));sheet.paste(crop,(x+8,25+row*115),crop);draw.text((x+117,55+row*115),'before' if row==0 else 'V2',fill='white')
  crop=layers[state].crop((175,42,280,142)).resize((210,200),Image.Resampling.NEAREST);sheet.paste(crop,(x,280),crop)
 save(report/'hall-native-review-sheet-v2.png',sheet)
 for name,pin in active.items():assert sha(PROJECT/name)==pin,'active source changed during candidate assembly: '+name
 files={rel(p):sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='selection.json'}
 selection={'status':'authored configuration','candidate_only':True,'revision':'bandle-hall-crest-legibility-v2','producer':producer,'consumed_inputs':consumed,'states':rows,'recipe_bindings':bindings,'files':files,
  'active_inputs_before_after_sha256':active,'active_inputs_unchanged':True,'native_executed':False,'visual_approval_granted':False,'redistribution_approved':False}
 write(HERE/'selection.json',selection);write(report/'assembly-receipt-v2.json',selection)
 print(json.dumps({'states':len(rows),'recipes':len(bindings),'project_local_consumed_inputs':len(consumed),'active_inputs_unchanged':True,'candidate_only':True}))

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args();prepare(args.report)
