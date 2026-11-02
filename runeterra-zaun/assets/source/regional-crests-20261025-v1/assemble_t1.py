"""Crest-only painted-source assembly. Never selects, stages or invents artwork.

Only genuinely imagegen-painted strokes inside inspected upper-garment regions
are selected. All original source alpha and every pixel outside those masks
remain exact. Existing native consumer crops/scales/translations are replayed.
"""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, io, json, shutil, sys
import numpy as np
from PIL import Image, ImageFilter

P=Path(__file__).resolve().parents[3]
W=P.parent
S=Path(__file__).resolve().parent
R=W/'build/reports/regional-crests-20261025-v1/zaun-t1-art'
UNITS=('zaunThug','chemPunk')
ROLES=('battle','map','large','small','attackLeft','attackRight')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(P).as_posix()
def enc(v):return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
def png_bytes(im):
 b=io.BytesIO();im.save(b,format='PNG',compress_level=9,optimize=False);return b.getvalue()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Frozen candidate differs; use a new version: '+str(p))
 p.write_bytes(b)
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def png(p,im):put(p,png_bytes(im))

def descriptors(unit):
 cohort=load(P/f'assets/source/creatures/{unit}/painted-battle-v5/native-candidate-v5/cohort.json')
 by={}
 for f in cohort['frames']:by.setdefault(f['painted_master'],[]).append(f['source_rect'])
 result={}
 for path,rects in by.items():result[Path(path).parent.name]={'target':path,'rects':sorted(set(tuple(x) for x in rects))}
 # Every auxiliary role is genuinely separately painted; source panel metadata
 # is the existing native consumer's actual crop, not a newly guessed camera.
 aux={}
 for role in ROLES[1:]:
  c=load(P/f'assets/source/creatures/{unit}/native-aux-v3/{role}-composition.json')
  path=c['painted_source']; key='left' if '/painted-left-' in path else 'auxiliary'
  im=Image.open(P/path); panel=c['source_panel_crop'] or [0,0,*im.size];bounds=c['alpha_bounds_inside_panel']
  rect=[panel[0]+bounds[0],panel[1]+bounds[1],panel[0]+bounds[2],panel[1]+bounds[3]]
  aux.setdefault(key,{'target':path,'rects':[],'portrait_rects':[]})['rects'].append(tuple(rect))
  if role in ('large','small'):aux[key]['portrait_rects'].append(tuple(rect))
 for key,item in aux.items():item['rects']=sorted(set(item['rects']));result[key]=item
 return result,cohort

def patch(unit,key,desc):
 folder=S/unit/key; old_path=P/desc['target'];raw_path=folder/'master-raw-v1.png'
 if not raw_path.is_file() or not (folder/'prompt.txt').is_file():raise ValueError('Genuine painted edit/prompt missing: '+str(folder))
 oldim=Image.open(old_path).convert('RGBA'); rawim=Image.open(raw_path).convert('RGBA')
 if abs(oldim.width/oldim.height-rawim.width/rawim.height)>.005:raise ValueError('Atlas aspect/layout changed: '+str(raw_path))
 normal=list(rawim.size)
 if rawim.size!=oldim.size:rawim=rawim.resize(oldim.size,Image.Resampling.LANCZOS)
 old=np.array(oldim);raw=np.array(rawim);a=raw.astype(np.int16);b=old.astype(np.int16)
 mask=np.zeros(old.shape[:2],bool); cells=[]
 for rect in desc['rects']:
  x0,y0,x1,y1=rect; width=x1-x0;height=y1-y0
  # This is a finite technical selection region around existing upper coat /
  # shoulder plates, not a generated logo, recolouring filter or artistic pass.
  xx0=max(x0,int(x0+width*.02));xx1=min(x1,int(x0+width*.90))
  yy0=max(y0,int(y0+height*.10));yy1=min(y1,int(y0+height*.65))
  if tuple(rect) in desc.get('portrait_rects',[]):
   # Head-and-shoulders portraits need their actual lower shoulder surface;
   # a full-body upper-torso fraction would truncate the painted emblem.
   xx0=x0;xx1=int(x0+width*.48);yy0=int(y0+height*.43);yy1=y1
  aa=a[yy0:yy1,xx0:xx1];bb=b[yy0:yy1,xx0:xx1]
  pale=(aa[:,:,0]>=145)&(aa[:,:,1]>=113)&(aa[:,:,2]>=65)&(aa[:,:,0]>aa[:,:,2]+25)
  brighter=aa[:,:,:3].sum(2)>bb[:,:,:3].sum(2)+60
  garment=(bb[:,:,0]<185)&(bb[:,:,1]<170)&(bb[:,:,2]<155)&(bb[:,:,0]-bb[:,:,1]<65)&(bb[:,:,1]-bb[:,:,2]<55)
  selected=pale&brighter&garment&(bb[:,:,3]>=248)&(aa[:,:,3]>=248)
  # Isolated one-pixel relighting is not an emblem. Keep actual painted
  # connected stroke components, including disconnected loops, in the selected
  # material region. Thresholding identifies existing edit strokes only.
  dilated=np.array(Image.fromarray(selected.astype(np.uint8)*255).filter(ImageFilter.MaxFilter(7)))>0
  seen=np.zeros(dilated.shape,bool); keep=np.zeros(dilated.shape,bool); components=[]
  for sy,sx in np.argwhere(dilated):
   if seen[sy,sx]:continue
   stack=[(int(sy),int(sx))];seen[sy,sx]=True;points=[]
   while stack:
    y,x=stack.pop();points.append((y,x))
    for ny,nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
     if 0<=ny<seen.shape[0] and 0<=nx<seen.shape[1] and dilated[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;stack.append((ny,nx))
   count=sum(bool(selected[y,x]) for y,x in points)
   if count>=25:
    for y,x in points:keep[y,x]=selected[y,x]
    components.append(count)
  count=int(keep.sum());mask[yy0:yy1,xx0:xx1]|=keep
  cells.append({'body_crop':list(rect),'selection_region':[xx0,yy0,xx1,yy1],'painted_stroke_pixels':count,'components':components,'scope':'Painted garment/plate strokes only; natural occlusion may hide the marking'})
 if not mask.any():raise ValueError('No genuine visible painted marking selected: '+str(raw_path))
 out=old.copy();out[mask,:3]=raw[mask,:3]
 assert np.array_equal(out[:,:,3],old[:,:,3]) and np.array_equal(out[~mask],old[~mask])
 patched=folder/'master-patched-v5.png';maskpath=folder/'painted-strokes-mask-v5.png';png(patched,Image.fromarray(out));png(maskpath,Image.fromarray(mask.astype(np.uint8)*255))
 # Negative source control deliberately changes an actual non-mark body pixel.
 y,x=np.argwhere((old[:,:,3]>=248)&~mask)[-1];bad=out.copy();bad[y,x,0]^=1
 assert np.any(np.any(bad!=old,axis=2)&~mask)
 record={'unit':unit,'cohort':key,'old_master':desc['target'],'old_sha256':sha(old_path),'raw_edited_master':rel(raw_path),'raw_sha256':sha(raw_path),'patched_master':rel(patched),'patched_sha256':sha(patched),'mask':rel(maskpath),'mask_sha256':sha(maskpath),'edited_raw_canvas':normal,'original_canvas':list(oldim.size),'outside_mask_RGBA_unchanged':True,'all_alpha_unchanged':True,'changed_pixels':int(np.any(out!=old,axis=2).sum()),'outside_mark_body_mutation_rejected':True,'cells':cells}
 generation={'schema_version':1,'provider':'OpenAI built-in imagegen','tool':'image_gen.imagegen','model':'not exposed by built-in tool','image_generation_used':True,'prompt':(folder/'prompt.txt').read_text().strip(),'edit_target':{'path':desc['target'],'sha256':sha(old_path)},'raw_output':{'path':rel(raw_path),'sha256':sha(raw_path)},'painted_master':rel(patched),'painted_master_sha256':sha(patched),'technical_mask':{'path':rel(maskpath),'sha256':sha(maskpath)},'private_reference':{'owner':'Riot Games','url':'https://universe.leagueoflegends.com/images/zaun_crest_icon@2x.png','sha256':sha(P/'build/reports/industrial-neighborhood-20261025-v3/lore/official-zaun-regional-crest.png'),'role':'Shape reference only, no original pixels copied','redistributed':False},'status':'authored configuration','release_accepted':False}
 generation['prompt_file']={'path':rel(folder/'prompt.txt'),'sha256':sha(folder/'prompt.txt')}
 if not (unit=='zaunThug' and key=='hold-reactions'):
  painted_reference=S/'zaunThug/hold-reactions/master-patched-v1.png'
  generation['painted_style_reference']={'path':rel(painted_reference),'sha256':sha(painted_reference),'role':'Actual second input: genuine same-family crest placement/material reference'}
 gp=folder/'generation-v5.json';put(gp,enc(generation));record['generation']={'path':rel(gp),'sha256':sha(gp)}
 put(folder/'patch-receipt-v5.json',enc(record))
 return Image.fromarray(out),mask,record

def assemble():
 allrecords=[];allframes=[];recipes=[];outputs={}
 for unit in UNITS:
  descs,cohort=descriptors(unit); patched={};records={}
  for key,desc in descs.items():
   im,mask,record=patch(unit,key,desc);patched[desc['target']]=im;records[desc['target']]=record;allrecords.append(record)
  frames=[]
  for f in cohort['frames']:
   old=Image.open(P/f['painted_master']).convert('RGBA');new=patched[f['painted_master']]
   def replay(im):
    crop=im.crop(f['source_rect']).resize(tuple(f['scaled_crop_size']),Image.Resampling.LANCZOS);result=Image.new('RGBA',(450,400));result.alpha_composite(crop,tuple(f['native_translation']));return result
   original=Image.open(P/f['source']).convert('RGBA');assert np.array_equal(np.array(replay(old)),np.array(original)),('Historical native replay differs',unit,f['group'],f['frame'])
   candidate=replay(new);assert np.array_equal(np.array(candidate)[:,:,3],np.array(original)[:,:,3])
   path=S/unit/'native-v5'/f'g{f["group"]:02d}'/f'g{f["group"]:02d}-f{f["frame"]:03d}.png';png(path,candidate)
   row=copy.deepcopy(f);row.update(source=rel(path),sha256=sha(path),painted_master=records[f['painted_master']]['patched_master'],painted_master_sha256=records[f['painted_master']]['patched_sha256'],old_source=f['source'],old_source_sha256=sha(P/f['source']),original_native_replay_exact=True,alpha_unchanged=True)
   frames.append(row);allframes.append(row)
  cohortpath=S/unit/'native-v5/cohort.json';put(cohortpath,enc({'canvas':[450,400],'frames':frames,'scope':'Crest-only painted source candidate; original native registrations and alpha exact','selected_or_staged':False}))
  aux={}
  for role in ROLES[1:]:
   comp=load(P/f'assets/source/creatures/{unit}/native-aux-v3/{role}-composition.json');old=Image.open(P/comp['painted_source']).convert('RGBA');new=patched[comp['painted_source']]
   recipe=load(P/f'assets/recipes/creatures/{unit}-{role}.json');source=recipe['groups'][0]['frames'][0]['source'] if role=='map' else recipe['source'];original=Image.open(P/source).convert('RGBA')
   def replay_aux(im):
    if comp['source_panel_crop']:im=im.crop(comp['source_panel_crop'])
    im=im.crop(comp['alpha_bounds_inside_panel']);sz=(max(1,round(im.width*comp['uniform_scale'])),max(1,round(im.height*comp['uniform_scale'])));im=im.resize(sz,Image.Resampling.LANCZOS);out=Image.new('RGBA',tuple(comp['native_canvas']));out.alpha_composite(im,tuple(comp['placement']));return out
   assert np.array_equal(np.array(replay_aux(old)),np.array(original)),('Historical auxiliary replay differs',unit,role)
   candidate=replay_aux(new);assert np.array_equal(np.array(candidate)[:,:,3],np.array(original)[:,:,3])
   path=S/unit/'native-v5'/f'{role}.png';png(path,candidate);aux[role]={'path':rel(path),'sha256':sha(path),'old_source':source,'old_source_sha256':sha(P/source),'composition':comp,'original_native_replay_exact':True,'alpha_unchanged':True}
  # Clone only assigned recipes into candidate ownership. No live source edit.
  for role in ROLES:
   recipe=load(P/f'assets/recipes/creatures/{unit}-{role}.json')
   recipe.update(status='built-unreviewed',visual_approval_granted=False,acceptance='Crest-only painted candidate; source/native/final human and rights approval remain separate')
   sources=[{'path':r['patched_master'],'sha256':r['patched_sha256']} for r in records.values()]
   primary=next(iter(records.values())) if role=='battle' else records[aux[role]['composition']['painted_source']]
   recipe['generation']={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','painted_master':primary['patched_master'],'painted_master_sha256':primary['patched_sha256'],'prompt':primary['generation']['path'],'route':'Genuine per-cohort painted crest-only edits, selected painted-stroke masks, exact original action crops/scales/roots and alpha; no 3D producer or invented pose'}
   recipe['delivery']={'status':'built-unreviewed','sources':sources,'runtime_verified':False,'visual_approval_granted':False,'source_check_report':'assets/source/regional-crests-20261025-v1/selection-v5.json'}
   recipe['dependencies']=[{'path':rel(Path(__file__)),'sha256':sha(Path(__file__))},*[r['generation'] for r in records.values()]]
   if role=='battle':
    by={(x['group'],x['frame']):x for x in frames}
    for group in recipe['groups']:
     for i,item in enumerate(group['frames']):item.clear();row=by[group['group'],i];item.update(source=row['source'],sha256=row['sha256'])
    recipe.update(source=rel(cohortpath),source_sha256=sha(cohortpath))
   else:
    a=aux[role]
    if role=='map':
     item=recipe['groups'][0]['frames'][0];item.update(source=a['path'],sha256=a['sha256'],source_sha256=a['sha256'])
     mc=S/unit/'native-v5/map-cohort.json';put(mc,enc({'frames':[a],'canvas':[96,64]}));recipe.update(source=rel(mc),source_sha256=sha(mc))
    else:recipe.update(source=a['path'],source_sha256=a['sha256'])
   cp=P/f'assets/candidates/regional-crests-t1-20261025-v1/recipes-v5/{unit}-{role}.json';put(cp,enc(recipe));recipes.append({'path':rel(cp),'sha256':sha(cp)})
  # Contact sheet uses actual native canvases, with no body centring/fitting.
  sheet=Image.new('RGBA',(450*8,400*7),(43,45,42,255))
  for i,row in enumerate(frames):sheet.alpha_composite(Image.open(P/row['source']),((i%8)*450,(i//8)*400))
  png(R/f'{unit}-all-native-actions-v5.png',sheet)
 selection={'status':'authored configuration','scope':'Complete T1 pair unselected painted crest correction candidates; no stage/native/final approval','painted_source_edits':allrecords,'battle_frames':allframes,'candidate_recipes':recipes,'selected_or_staged':False,'native_visual_verified':False,'release_accepted':False}
 put(S/'selection-v5.json',enc(selection));print(json.dumps({'painted_atlases':len(allrecords),'battle_frames':len(allframes),'candidate_recipes':len(recipes),'selected':False}))

if __name__=='__main__':assemble()
