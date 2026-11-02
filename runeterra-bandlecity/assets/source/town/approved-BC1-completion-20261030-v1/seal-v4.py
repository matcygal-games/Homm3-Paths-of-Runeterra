"""Seal BC1 candidate source/recipes and produce coordinator-only patches."""
from pathlib import Path
import copy, hashlib, importlib.util, json
from PIL import Image,ImageChops,ImageDraw

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
ROOT=PROJECT.parent
OLD=HERE.parent/'approved-BC1-20261029-v1'
REV=HERE/'sealed-v4'
REPORT=ROOT/'reports/bandle-BC1-completion-20261030-v7'
read=lambda p:json.loads(Path(p).read_bytes())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:Path(p).relative_to(PROJECT).as_posix()
def dump(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);raw=(json.dumps(d,sort_keys=True,indent=2)+'\n').encode()
 if p.exists() and p.read_bytes()!=raw:raise ValueError('Sealed candidate changed: '+str(p))
 if not p.exists():p.write_bytes(raw)
def save(p,im):
 import io
 b=io.BytesIO();im.save(b,format='PNG');raw=b.getvalue();p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=raw:raise ValueError('Sealed image changed: '+str(p))
 if not p.exists():p.write_bytes(raw)

def main():
 states=read(REPORT/'states.json');positions=read(REPORT/'structure-position-patch.json')
 design=copy.deepcopy(read(PROJECT/'design/town-visuals.json'))
 faction=read(PROJECT/'content/factions.json')
 current=read(OLD/'decomposition-plan.json');doors={s['site']:s['door'] for s in current['sites']}
 files={Path(__file__),HERE/'assemble-v7.py',OLD/'decomposition-plan.json',OLD/'approved-native.png',OLD/'background.png',OLD/'empty-provider-v1.png',
        HERE/'civic-states-v1.png',HERE/'dwelling-states-v1.png',HERE/'optional-sites-v1.png',HERE/'generation-ledger.json'}
 for site in current['sites']:files.add(OLD/'sites'/site['site']/'maximum-state.png')
 layers={k:Image.open(PROJECT/v['layer']).convert('RGBA') for k,v in states.items()}
 bindings=[];recipe_paths=[]
 for source in sorted((HERE/'recipes-v8').glob('*.json')):
  name=source.stem
  target=REV/'recipes'/('structures/'+source.name if name not in ('background','buildingIcons') else source.name)
  target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists():target.write_bytes(source.read_bytes())
  if target.read_bytes()!=source.read_bytes():raise ValueError('Recipe draft changed')
  active='assets/recipes/town/'+('structures/'+source.name if name not in ('background','buildingIcons') else source.name)
  bindings.append({'candidate':rel(target),'active':active,'sha256':sha(target)})
  files.update([source,target]);recipe_paths.append(rel(target))
 for site in design['sites']:
  owned=[states[s] for s in site['states']];boxes=[r['bounds'] for r in owned]
  box=[min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
  rect=[box[0],box[1],box[2]-box[0],box[3]-box[1]]
  z=positions[site['states'][0]]['z']
  site.update(composition_rectangle=rect,center=[(box[0]+box[2])//2,(box[1]+box[3])//2],native_z=z,layer_origin=[0,0],selected_state_art={})
  site.pop('native_state_z',None)
  for state in site['states']:
   layer=layers[state];r=states[state];reg=r['registration'];master=HERE/reg['painted_master'] if 'painted_master' in reg else OLD/'approved-native.png'
   row={'state':state,'site':site['id'],'master':rel(master),'master_sha256':sha(master),
        'native_layer':r['layer'],'native_layer_sha256':r['sha256'],'native_z':positions[state]['z'],
        'composition_rectangle':rect,'click_bbox':list(layer.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()),'click_pixels':layer.getchannel('A').point(lambda a:255 if a>=128 else 0).histogram()[255],
        'source_crop_xyxy':reg.get('sheet_crop',[0,0,800,374]),'fit_size':reg.get('size',[box[2]-box[0],box[3]-box[1]]),
        'footing_water_pixels':0,'visual_approval_granted':False}
   site['source'][state]=rel(master);site['sha256'][state]=sha(master);site['selected_state_art'][state]=row
   if positions[state]['z']!=z:site.setdefault('native_state_z',{})[state]=positions[state]['z']
   faction['bandlecity']['town']['structures'][state].update(positions[state])
   files.add(master);files.update((HERE/'states-v7'/state).glob('*.png'))
 water_polygon=[[748,352],[766,348],[799,348],[799,373],[748,373]]
 water=Image.new('L',(800,374));ImageDraw.Draw(water).polygon(water_polygon,fill=255)
 save(HERE/'water-annotation.png',water);files.add(HERE/'water-annotation.png')
 terrain={'master':rel(OLD/'empty-provider-v1.png'),'master_sha256':sha(OLD/'empty-provider-v1.png'),
          'native':rel(HERE/'background-v7.png'),'native_sha256':sha(HERE/'background-v7.png'),
          'water_polygon':water_polygon,'annotation':'Approved inland BC1 ground is dry; optional foreground shipyard supplies its own painted water nook at the right edge. Land foundation profiles stay above this optional shoreline.'}
 design.update(terrain=terrain,recipe_paths=recipe_paths,status='authored configuration',art_status='built-unreviewed',visual_approval_granted=False,
    layout_note='BC1 approved whole-town master retained exactly; 16 original land sites, seven dwelling pairs, independently painted predecessor states and optional grounded dock/Grail. Full silhouettes, fixed entrances and state-wide depth order derived before conversion.')
 plan={'status':'authored configuration','sites':{}}
 for site in design['sites']:
  x,y,w,h=site['composition_rectangle']
  point=[doors.get(site['id'],site['center'])[0],y+h]
  if site['id']=='dwelling2':point=[119,y+h]
  if site['id']=='dwelling7':point=[710,y+h]
  plan['sites'][site['id']]={'ground_approach':point,'actual_full_silhouette_box':site['composition_rectangle'],'states':site['states']}
 dump(REV/'placement-plan.json',plan);files.add(REV/'placement-plan.json')
 # Preserve the complete reviewed RGB and input provenance beside the selected revision.
 for name,source in [('complete-design/native.png',OLD/'approved-native.png'),('complete-design/master.png',ROOT/'reports/five-town-concepts-20261029-v1/first-group/bandlecity-full-v2.png'),('background/extracted-provider-master-v1.png',OLD/'empty-provider-v1.png')]:
  target=REV/name;target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists():target.write_bytes(source.read_bytes())
  files.add(target)
 dump(REV/'complete-design/review-checkpoint.json',{'source_pixel_review_before_extraction':True,'complete_native_sha256':sha(OLD/'approved-native.png'),'approval':'User approved all five complete-town designs on29October2026; no individual native state acceptance implied.'})
 dump(REV/'background/generation.json',{'image_generation_used':True,'provider':'OpenAI built-in imagegen','input_complete_design_sha256':sha(OLD/'approved-native.png'),'method':'Painted empty plate; exact approved surrounding pixels outside removal silhouette restored by deterministic composition.'})
 files.update([REV/'complete-design/review-checkpoint.json',REV/'background/generation.json',HERE/'background-v7.png',REV/'support_annotations.py'])
 spec=importlib.util.spec_from_file_location('bc1_support',REV/'support_annotations.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 support,support_files=module.prepare(design,layers);files.update(support_files)
 if not support['ok']:raise ValueError('Support findings: '+str([r for r in support['states'] if r['errors']]))
 selection={'schema_version':1,'revision':'approved-BC1-completion-20261030-v1','status':'authored configuration','visual_approval_granted':False,
   'sites':design['sites'],'terrain':terrain,'recipe_bindings':bindings,'files':{rel(p):sha(p) for p in sorted(files)},
   'preparation_policy':'Candidate source selection only. Coordinator integrates exact recipe/content/design patches; no staging or native acceptance.'}
 dump(REV/'selection.json',selection)
 design['selected_sources']={'path':rel(REV/'selection.json'),'sha256':sha(REV/'selection.json'),
    'terrain_master':terrain['master'],'terrain_master_sha256':terrain['master_sha256'],'terrain_native':terrain['native'],'terrain_native_sha256':terrain['native_sha256']}
 dump(REV/'town-visuals.candidate.json',design);dump(REV/'factions.candidate.json',faction)
 print(json.dumps({'states':len(states),'bindings':len(bindings),'dependencies':len(files),'support_ok':support['ok']}))
if __name__=='__main__':main()
