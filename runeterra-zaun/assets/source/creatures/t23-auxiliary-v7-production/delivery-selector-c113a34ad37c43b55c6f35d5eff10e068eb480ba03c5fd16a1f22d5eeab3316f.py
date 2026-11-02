"""Own T2/T3 genuine auxiliary palette edits; technical crop/resample only.

Prepares20 independently reviewable candidates without canonical selection.
Frozen256 battle frames, original auxiliary sources and other owners stay read-only.
"""
from pathlib import Path
import argparse,hashlib,io,json,os,shutil,re
from PIL import Image,ImageDraw

ROOT=Path(os.environ.get('ZAUN_T23_ROOT',Path(__file__).resolve().parents[1])).resolve()
REVIEW=ROOT/'review/t23-auxiliary-palette-v7-20261021'
UNITS=('chemRavager','mutantBerserker','chemtechConstruct','reinforcedConstruct')
ROLES=('map','large','small','attackLeft','attackRight')
SIZES={'map':(96,64),'large':(58,64),'small':(32,32),'attackLeft':(64,64),'attackRight':(64,64)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def checked(record):
 if not isinstance(record,dict) or not isinstance(record.get('path'),str):raise ValueError('Pinned project-relative path required')
 value=record['path'];parts=value.split('/')
 if '\\' in value or ':' in value or any(p in ('','.','..') or p.endswith((' ','.')) or p.split('.')[0].upper() in ('CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]) for p in parts):raise ValueError('Unsafe project-relative path')
 path=(ROOT/value).resolve()
 if not path.is_relative_to(ROOT) or not path.is_file() or not re.fullmatch('[0-9a-f]{64}',str(record.get('sha256',''))) or sha(path)!=record['sha256']:raise ValueError('Changed or missing source pin: '+value)
 return path
def stable_bytes(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=data:raise ValueError('Preserve previous candidate: '+str(p))
 else:p.write_bytes(data)
def dump(p,data):stable_bytes(p,(json.dumps(data,indent=2,sort_keys=True)+'\n').encode())
def png(p,im):
 b=io.BytesIO();im.save(b,format='PNG');stable_bytes(p,b.getvalue())
def protected():
 before=json.loads((REVIEW/'before-pins.json').read_text())
 for e in before['canonical_recipes']:
  if sha(ROOT/e['path'])!=e['sha256']:raise ValueError('Canonical source changed during candidate work: '+e['path'])
 f=json.loads((ROOT/before['battle_freeze']['path']).read_text())
 if sha(ROOT/before['battle_freeze']['path'])!=before['battle_freeze']['sha256']:raise ValueError('Battle freeze changed')
 for e in f['pins']:
  if sha(ROOT/e['path'])!=e['sha256']:raise ValueError('Frozen battle source changed: '+e['path'])
 return before
def save(record):
 protected();d=json.loads(Path(record).read_text());u=d['unit']
 if u not in UNITS or d['version']!=7:raise ValueError('Unowned source')
 folder=ROOT/f'assets/source/creatures/{u}/painted-auxiliary-v7'
 if d.get('attempt'):
  if d['attempt']!='separated-v2':raise ValueError('Unsupported own targeted attempt')
  folder=folder/d['attempt']
 master=folder/'auxiliary-master.png';source=Path(d['generated_path'])
 stable_bytes(master,source.read_bytes())
 im=Image.open(master)
 meta={**d,'status':'authored configuration; unselected genuine auxiliary painting','master':pin(master),'image_generation_used':True,
  'provider':'OpenAI built-in image_gen','model':None,'model_note':'The tool did not expose its model identifier.',
  'inputs':[{'path':str(Path(p).resolve()),'sha256':sha(Path(p))}for p in d['inputs']],
  'geometry':{'size':list(im.size),'mode':im.mode,'alpha_extrema':list(im.getchannel('A').getextrema())},
  'rights':'unresolved; release prohibited','visual_approval_granted':False,'final_art_acceptance':False}
 dump(folder/'generation.json',meta);protected();return {'unit':u,'master':pin(master),'size':im.size,'canonical_changed':False}
def crops(u):
 if u=='chemRavager':return {'map':[590,0,1030,552],'large':[0,552,512,1024],'small':[512,580,1088,1024],'attackLeft':[1060,0,1536,552],'attackRight':[0,0,525,552]}
 return {'map':[540 if u=='mutantBerserker' else 570,0,1024,512],'large':[0,512,512,1024],'small':[512,512,1024,1024],
  'attackLeft':[1024 if u=='mutantBerserker' else 0,0,1536 if u=='mutantBerserker' else 512,512],
  'attackRight':[0 if u=='mutantBerserker' else 1024,0,512 if u=='mutantBerserker' else 1536,512]}
def fit(panel,size,role):
 alpha=panel.getchannel('A');box=alpha.point(lambda a:255 if a>=8 else 0).getbbox()
 if not box:raise ValueError('Empty actual painted panel')
 if role in ('map','attackLeft','attackRight'):
  b=alpha.point(lambda a:255 if a>=128 else 0).getbbox()
  if not b or b[0]<=0 or b[1]<=0 or b[2]>=panel.width or b[3]>=panel.height:raise ValueError('Complete view clipped at panel boundary: '+role)
 part=panel.crop(box);scale=min(size[0]/part.width,size[1]/part.height)
 if role=='map':scale=min(scale,48/part.height,56/part.width)
 part=part.resize((max(1,round(part.width*scale)),max(1,round(part.height*scale))),Image.Resampling.LANCZOS)
 out=Image.new('RGBA',size)
 xy=((size[0]-part.width)//2,(size[1]-part.height)//2)
 if role=='map':xy=(64-part.width//2,64-part.height)
 out.alpha_composite(part,xy)
 return out,{'source_alpha_box':list(box),'uniform_scale':scale,'offset':list(xy),'technical_operation':'Alpha-preserving rectangular panel crop, uniform resample and canvas placement only'}
def prepare():
 import zaun_t57_atlas as atlas
 if (REVIEW/'twenty-candidates.json').exists():
  # Resume the explicitly pinned producer, even when a later selector revision
  # changes this helper. Never overwrite accepted/prepared pixels on a rerun.
  receipt=REVIEW/'selection-receipt.json'
  if receipt.exists():reviewed_selection(checked(json.loads(receipt.read_text())['source_review']))
  else:protected()
  inventory=json.loads((REVIEW/'twenty-candidates.json').read_text())
  checked(inventory['native_comparison'])
  if len(inventory['cohorts'])!=4 or len(inventory['native_outputs'])!=20:raise ValueError('Incomplete saved candidate set')
  for cp in inventory['cohorts']:
   cohort=json.loads(checked(cp).read_text())
   for key in ('master','generation','producer','selector','frozen_battle_cohort'):checked(cohort[key])
   for item in cohort['outputs']:
    checked(item['native']);checked(item['source_panel'])
  return {'candidate_outputs':20,'resumed':True,'candidate_inventory':pin(REVIEW/'twenty-candidates.json'),'canonical_changed':False}
 before=protected();all_outputs=[];cohorts=[]
 producer=ROOT/'assets/source/creatures/t23-auxiliary-v7-production'/('producer-'+sha(Path(__file__))+'.py')
 stable_bytes(producer,Path(__file__).read_bytes())
 selector=producer.with_name('selector-'+sha(ROOT/'scripts/zaun_t57_atlas.py')+'.py')
 stable_bytes(selector,(ROOT/'scripts/zaun_t57_atlas.py').read_bytes())
 for u in UNITS:
  folder=ROOT/f'assets/source/creatures/{u}/painted-auxiliary-v7'
  master_folder=folder/'separated-v2' if (folder/'separated-v2/auxiliary-master.png').exists() else folder
  master=master_folder/'auxiliary-master.png';im=Image.open(master).convert('RGBA')
  if im.size!=(1536,1024):raise ValueError('Uninspected auxiliary viewport: '+str(im.size))
  generation=master_folder/'generation.json';gen=json.loads(generation.read_text())
  if gen['master']!=pin(master):raise ValueError('Master metadata changed')
  battle_recipe=ROOT/f'assets/recipes/creatures/{u}-battle.json';br=json.loads(battle_recipe.read_text());outputs=[]
  labels,found=atlas.components(im,threshold=128)
  rows,extras=atlas.assign_rows(found,[3,3],minimum_area=1500)
  ordered=[b for row in rows for b in row];ownership=atlas.ownership(labels,ordered,extras)
  indices={'map':1,'large':3,'small':4,'attackLeft':2 if u in UNITS[:2] else 0,'attackRight':0 if u in UNITS[:2] else 2}
  for role in ROLES:
   source_panel=folder/(role+'-source-panel.png')
   panel,selection=atlas.subject(im,labels,ordered[indices[role]],extras,ordered,cell_ownership=ownership)
   if role in ('map','attackLeft','attackRight') and selection['opaque_touches_source_edge']:raise ValueError('Clipped complete painted source view: '+u+'/'+role)
   box=selection['source_bbox'];png(source_panel,panel)
   native,transform=fit(panel,SIZES[role],role);source=folder/'native-candidate'/(role+'.png');png(source,native)
   old=ROOT/f'assets/recipes/creatures/{u}-{role}.json';recipe=json.loads(old.read_text())
   stable_bytes(REVIEW/'before-canonical'/old.name,old.read_bytes())
   record={'unit':u,'role':role,'native':pin(source),'size':list(native.size),'painted_master':pin(master),'source_panel':pin(source_panel),'source_master_crop':box,'source_selection':selection,'source_cell_index':indices[role],'transform':transform,'previous_recipe':pin(old)}
   outputs.append(record);all_outputs.append(record)
   recipe.update({'production_status':'source-prepared-unselected','status':'authored configuration','visual_approval_granted':False,
    'generation':{**gen,'painted_master':pin(master)['path'],'painted_master_sha256':sha(master),'route':'Genuine palette/equipment edit of independent auxiliary painting; separate original map/portrait/encounter poses retained. Technical crop and uniform resample only.'},
    'credits':{'author':'OpenAI built-in image_gen; project-directed own-source edits','license':None,'redistribution':'unresolved; release prohibited'}})
   recipe.pop('crop',None);recipe.pop('source_review',None);recipe.pop('delivery',None)
   if role=='map':
    map_cohort=folder/'native-map/cohort-v7.json';dump(map_cohort,{'unit':u,'cohort':'map','status':'authored configuration; candidate unselected','native_canvas':[96,64],'master':pin(master),'source_panel':pin(source_panel),'source_master_crop':box,'transform':transform,'frames':[pin(source)],'visual_approval_granted':False})
    recipe['source']=map_cohort.relative_to(ROOT).as_posix();recipe['source_sha256']=sha(map_cohort)
    frames=recipe['groups'][0]['frames'];assert len(recipe['groups'])==1 and recipe['groups'][0]['group']==0 and len(frames)==1
    frames[0].update({'source':source.relative_to(ROOT).as_posix(),'sha256':sha(source),'source_sha256':sha(source)})
   else:recipe['source']=source.relative_to(ROOT).as_posix();recipe['source_sha256']=sha(source)
   dump(REVIEW/'candidate-recipes'/old.name,recipe)
  cp=folder/'auxiliary-cohort-v7.json';dump(cp,{'unit':u,'status':'authored configuration; genuine auxiliary candidates unselected','master':pin(master),'generation':pin(generation),'producer':pin(producer),'selector':pin(selector),'painted_figure_count':6,'unused_painted_cell':5,'selection_rule':'Three independently painted complete top views; separate bottom portraits; unused bottom-right body excluded. Original RGBA preserved inside nearest-body atlas cells. No alpha cleanup, recolor, mirrored view or battle-frame map.','frozen_battle_cohort':{'path':br['source'],'sha256':br['source_sha256']},'outputs':outputs,'visual_approval_granted':False,'final_art_acceptance':False,'rights':'unresolved; release prohibited'})
  cohorts.append(pin(cp))
 board=Image.new('RGB',(1100,4*190),(52,54,51));d=ImageDraw.Draw(board)
 for row,u in enumerate(UNITS):
  br=json.loads((ROOT/f'assets/recipes/creatures/{u}-battle.json').read_text());c=json.loads((ROOT/br['source']).read_text());native=Image.open(ROOT/c['groups']['2'][0]['source']).convert('RGBA').crop((90,130,280,282));board.paste(native,(0,row*190+25),native);d.text((0,row*190+3),u+' frozen battle',fill='white')
  for col,role in enumerate(ROLES):
   im=Image.open(ROOT/f'assets/source/creatures/{u}/painted-auxiliary-v7/native-candidate/{role}.png').convert('RGBA');x=215+col*170;y=row*190+45;board.paste(im,(x,y),im);d.text((x,row*190+15),role+' native',fill='white')
 board_path=REVIEW/'twenty-native-candidates-with-frozen-battle.png';png(board_path,board)
 result={'status':'authored configuration; twenty genuine edited auxiliary candidates; canonical selection pending','cohorts':cohorts,'native_outputs':all_outputs,'native_comparison':pin(board_path),'output_count':20,'frozen_battle_frames':256,'canonical_recipes_unchanged':True,'visual_approval_granted':False,'final_art_acceptance':False,'rights_acceptance':False}
 dump(REVIEW/'twenty-candidates.json',result);protected();return {'candidate_outputs':20,'cohorts':cohorts,'native_comparison':pin(board_path),'candidate_inventory':pin(REVIEW/'twenty-candidates.json'),'canonical_changed':False}

def reviewed_selection(review_path):
 """Validate all twenty exact sources before planning any canonical write."""
 if review_path is None:raise ValueError('Explicit independent source review required')
 rp=Path(review_path).resolve()
 if not rp.is_relative_to(ROOT) or not rp.is_file():raise ValueError('Review must be saved inside project')
 review=json.loads(rp.read_text(encoding='utf-8'))
 reviewer=review.get('reviewer')
 if not isinstance(reviewer,str) or not reviewer.strip() or any(n in reviewer for n in ('zaun_t23_finish','zaun_creatures_a')):raise ValueError('Named independent reviewer required')
 if review.get('scope')!='source selection only' or review.get('source_ready') is not True:raise ValueError('Affirmative source-only review required')
 for key in ('visual_approval_granted','final_art_acceptance','runtime_verified','release_accepted'):
  if review.get(key) is not False:raise ValueError('Final acceptance must remain false')
 if review.get('redistribution')!='unresolved; release prohibited':raise ValueError('Rights remain unresolved')
 inventory_path=checked(review['candidate_inventory'])
 if inventory_path!=REVIEW/'twenty-candidates.json':raise ValueError('Wrong candidate inventory')
 inventory=json.loads(inventory_path.read_text(encoding='utf-8'))
 if inventory.get('output_count')!=20 or inventory.get('visual_approval_granted') is not False:raise ValueError('Exact20 unaccepted candidates required')
 if review.get('comparison')!=inventory['native_comparison']:raise ValueError('Review must bind exact native comparison')
 checked(review['comparison'])
 if set(review.get('units',{}))!=set(UNITS):raise ValueError('All four units must be independently reviewed')
 expected_candidates={f'review/t23-auxiliary-palette-v7-20261021/candidate-recipes/{u}-{role}.json'for u in UNITS for role in ROLES}
 candidate_pins=review.get('candidate_recipes',[])
 if len(candidate_pins)!=20 or {p.get('path')for p in candidate_pins}!=expected_candidates:raise ValueError('Independent review must bind exact twenty candidate recipes')
 for item in candidate_pins:checked(item)
 before=json.loads((REVIEW/'before-pins.json').read_text(encoding='utf-8'))
 battle=checked(before['battle_freeze']);freeze=json.loads(battle.read_text(encoding='utf-8'))
 for item in freeze['pins']:checked(item)
 originals={v['path']:v['sha256'] for v in before['canonical_recipes']}
 plans=[]
 for u in UNITS:
  folder=ROOT/f'assets/source/creatures/{u}/painted-auxiliary-v7'
  cp=folder/'auxiliary-cohort-v7.json';cohort=json.loads(cp.read_text(encoding='utf-8'));ur=review['units'][u]
  if ur.get('cohort')!=pin(cp) or not ur.get('findings'):raise ValueError('Review must bind exact cohort and actual findings')
  if cohort.get('unit')!=u or cohort.get('painted_figure_count')!=6 or cohort.get('visual_approval_granted') is not False:raise ValueError('Wrong source-only six-figure cohort')
  for key in ('master','generation','producer','selector'):checked(cohort[key])
  generation=json.loads(checked(cohort['generation']).read_text(encoding='utf-8'))
  if generation.get('master')!=cohort['master'] or generation.get('provider')!='OpenAI built-in image_gen' or generation.get('image_generation_used') is not True or not generation.get('prompt') or not generation.get('returned_provenance'):raise ValueError('Actual provider/prompt/provenance/master binding required')
  for item in generation['inputs']:
   ip=Path(item['path'])
   if not ip.is_absolute() or not ip.is_file() or sha(ip)!=item['sha256']:raise ValueError('Changed generation input')
  frozen_recipe=ROOT/f'assets/recipes/creatures/{u}-battle.json';br=json.loads(frozen_recipe.read_text(encoding='utf-8'))
  if pin(frozen_recipe)['sha256']!=originals[frozen_recipe.relative_to(ROOT).as_posix()] or cohort['frozen_battle_cohort']!={'path':br['source'],'sha256':br['source_sha256']}:raise ValueError('Frozen battle selection changed')
  checked(cohort['frozen_battle_cohort'])
  outputs=cohort.get('outputs',[])
  if len(outputs)!=5 or {item['role']for item in outputs}!=set(ROLES) or set(ur.get('outputs',{}))!=set(ROLES):raise ValueError('All five distinct auxiliary outputs required')
  for item in outputs:
   role=item['role'];expected=folder/'native-candidate'/f'{role}.png'
   if item.get('unit')!=u or checked(item['native'])!=expected or ur['outputs'][role]!=item['native']:raise ValueError('Review output ownership/pin mismatch')
   checked(item['source_panel'])
   with Image.open(expected) as im:
    if im.size!=SIZES[role] or im.mode!='RGBA' or not im.getchannel('A').getbbox():raise ValueError('Wrong or empty native auxiliary image')
   old=ROOT/f'assets/recipes/creatures/{u}-{role}.json';backup=REVIEW/'before-canonical'/old.name
   if not backup.is_file() or sha(backup)!=originals[old.relative_to(ROOT).as_posix()]:raise ValueError('Historical canonical source changed')
   candidate=REVIEW/'candidate-recipes'/old.name;recipe=json.loads(candidate.read_text(encoding='utf-8'));original=json.loads(backup.read_text(encoding='utf-8'))
   for key in ('id','unit','output_path','canvas','recipe_type','role','require_alpha','fit','required_groups','size','pivot','attack_semantics','acceptance','required_before_conversion','footprint','depends_on','frame_contract','generateOverlay','generateShadow'):
    if recipe.get(key)!=original.get(key):raise ValueError('Native recipe contract changed: '+key)
   if [(g.get('group'),g.get('action'),len(g.get('frames',[])))for g in recipe.get('groups',[])]!=[(g.get('group'),g.get('action'),len(g.get('frames',[])))for g in original.get('groups',[])]:raise ValueError('Native animation action contract changed')
   if recipe.get('production_status')!='source-prepared-unselected':raise ValueError('Candidate unexpectedly selected')
   if role=='map':
    checked({'path':recipe['source'],'sha256':recipe['source_sha256']})
    groups=recipe.get('groups',[])
    if len(groups)!=1 or groups[0]['group']!=0 or len(groups[0]['frames'])!=1 or groups[0]['frames'][0].get('source')!=item['native']['path'] or groups[0]['frames'][0].get('source_sha256')!=item['native']['sha256']:raise ValueError('Map source/frame mismatch')
   elif {'path':recipe.get('source'),'sha256':recipe.get('source_sha256')}!=item['native']:raise ValueError('Raster source mismatch')
   selector_hash=sha(Path(__file__));selector_pin={'path':'assets/source/creatures/t23-auxiliary-v7-production/delivery-selector-'+selector_hash+'.py','sha256':selector_hash}
   dependencies=[pin(cp),pin(candidate),pin(rp),pin(inventory_path),review['comparison'],cohort['master'],cohort['generation'],cohort['producer'],cohort['selector'],cohort['frozen_battle_cohort'],item['source_panel'],selector_pin]
   if role=='map':dependencies.append(item['native'])
   recipe.update(production_status='delivered',status='built-unreviewed',visual_approval_granted=False,dependencies=dependencies,
    source_review={**pin(rp),'reviewer':reviewer,'source_ready':True,'visual_approval_granted':False,'final_art_acceptance':False},
    delivery={'cohort':cp.relative_to(ROOT).as_posix(),'cohort_sha256':sha(cp),'sources':[item['native']], 'source_review':pin(rp),'selector':selector_pin,'status':'built-unreviewed','visual_approval_granted':False})
   raw=(json.dumps(recipe,indent=2,sort_keys=True)+'\n').encode()
   if sha(old)!=sha(backup) and old.read_bytes()!=raw:raise ValueError('Canonical source changed outside own selection: '+old.name)
   plans.append((old,raw))
 if len(plans)!=20:raise ValueError('Exact twenty recipe selection required')
 return plans,review,rp

def deliver(review_path):
 plans,review,rp=reviewed_selection(review_path)
 snapshot=ROOT/'assets/source/creatures/t23-auxiliary-v7-production'/('delivery-selector-'+sha(Path(__file__))+'.py')
 stable_bytes(snapshot,Path(__file__).read_bytes())
 before={p:p.read_bytes()for p,_ in plans};changed=[]
 try:
  for path,raw in plans:
   if path.read_bytes()==raw:continue
   temp=path.with_name(path.name+'.t23-selection-tmp');temp.write_bytes(raw);temp.replace(path);changed.append(path)
 except Exception:
  for path in changed:path.write_bytes(before[path])
  raise
 receipt={'status':'authored configuration; built-unreviewed','source_review':pin(rp),'selector':pin(snapshot),'selected_count':20,'changed_count':len(changed),'recipes':[pin(p)for p,_ in plans], 'visual_approval_granted':False,'final_art_acceptance':False,'runtime_verified':False,'release_accepted':False,'redistribution':'unresolved; release prohibited'}
 dump(REVIEW/('selection-receipt.json'if changed else'selection-idempotency-receipt.json'),receipt)
 return receipt

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('save','prepare','deliver','check-review'));p.add_argument('record',nargs='?');a=p.parse_args()
 print(json.dumps(save(a.record)if a.command=='save'else prepare()if a.command=='prepare'else deliver(a.record)if a.command=='deliver'else {'valid_source_review':bool(reviewed_selection(a.record))},indent=2))
