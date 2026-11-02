"""Deterministic source-candidate derivation. Never writes canonical selections.

Full inland + Grail composition is reconstructed pixel-for-pixel from NX1.
Predecessors are real newly painted architecture. Optional coast has no approved
placement: genuine cutouts and icons are supplied but game recipes stay blocked.
"""
from pathlib import Path
from copy import deepcopy
import hashlib, json, html
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps
from nx1_plan import SIZE, SITES, ATLAS, COAST_STATES, UNRESOLVED

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
WORKSPACE=ROOT.parent
REPORT=ROOT/'build/reports/approved-nx1-20261029-v1'
CANDIDATE=HERE/'candidate'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def save(p,im):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def rel(p): return Path(p).relative_to(ROOT).as_posix()
def binary(im,t=128): return (im.getchannel('A') if im.mode=='RGBA' else im).point(lambda v:255 if v>=t else 0)
def count(im): return im.histogram()[255]
def polygon(points):
 out=Image.new('L',SIZE);ImageDraw.Draw(out).polygon(points,fill=255);return out
def union(a,b):return ImageChops.lighter(a,b)
def own_bottom(solid,depth=5):
 out=Image.new('L',SIZE);a=solid.load();b=out.load()
 for x in range(SIZE[0]):
  rows=[y for y in range(SIZE[1]) if a[x,y]]
  if rows:
   edge=max(rows)
   for y in range(max(0,edge-depth+1),edge+1):
    if a[x,y]:b[x,y]=255
 return out
def atlas_cut(path,col,row,cols=4,rows=2):
 im=Image.open(path).convert('RGBA');w,h=im.size
 bounds=None
 if path.parent.name=='civic-stages-v1':bounds=([0,378,755,1159,1536] if row==0 else [0,409,763,1158,1536])
 if path.parent.name=='dwelling-stages-v1':bounds=([0,400,770,1135,1536] if row==0 else [0,380,775,1145,1536])
 crop=im.crop((bounds[col] if bounds else col*w//cols,row*h//rows,bounds[col+1] if bounds else (col+1)*w//cols,(row+1)*h//rows))
 # The generated genuine alpha is 252/253 in opaque bodies; normalize to255.
 # Remove near-zero transparent RGB residue, never infer architecture from hue.
 a=crop.getchannel('A').point(lambda v:0 if v<16 else (255 if v>=220 else round((v-16)*255/204)))
 # Discard isolated alpha-noise components, retaining the real contiguous
 # architectural body plus any detached physical flags/shadows >=128pixels.
 active=a.point(lambda v:255 if v>=24 else 0);pix=active.load();seen=set();keep=Image.new('L',active.size);kp=keep.load()
 for yy in range(active.height):
  for xx in range(active.width):
   if not pix[xx,yy] or (xx,yy) in seen:continue
   component=[];todo=[(xx,yy)];seen.add((xx,yy))
   while todo:
    px,py=todo.pop();component.append((px,py))
    for nx,ny in [(px+1,py),(px-1,py),(px,py+1),(px,py-1),(px+1,py+1),(px-1,py-1),(px+1,py-1),(px-1,py+1)]:
     if 0<=nx<active.width and 0<=ny<active.height and pix[nx,ny] and (nx,ny) not in seen:seen.add((nx,ny));todo.append((nx,ny))
   if len(component)>=128:
    for px,py in component:kp[px,py]=255
 a=ImageChops.multiply(a,keep.filter(ImageFilter.MaxFilter(3)))
 crop.putalpha(a);bb=binary(crop,8).getbbox()
 if not bb:raise ValueError('Empty painted atlas cell')
 return crop.crop(bb),list(bb)
def make_layer(subject,box):
 x,y,w,h=box;fitted=ImageOps.contain(subject,(w,h),Image.Resampling.LANCZOS)
 xy=(x+(w-fitted.width)//2,y+h-fitted.height)
 out=Image.new('RGBA',SIZE);out.alpha_composite(fitted,xy)
 # Preserve anti-aliased one-pixel edges/open arches; architecture interiors
 # are opaque so wet pavement/torch reflections cannot bleed through masonry.
 alpha=out.getchannel('A');inside=binary(out).filter(ImageFilter.MinFilter(3));out.putalpha(Image.composite(Image.new('L',SIZE,255),alpha,inside))
 return out,xy,list(fitted.size)
def compose(states,layers,background):
 result=background.convert('RGBA')
 for state in sorted(states,key=lambda s:next(v['z'] for v in SITES.values() if s in v['states'])):
  result.alpha_composite(layers[state])
 return result

def main():
 REPORT.mkdir(parents=True,exist_ok=True)
 canonical={str(p.relative_to(ROOT).as_posix()):sha(p) for p in [ROOT/'content/factions.json',ROOT/'design/town-visuals.json',ROOT/'assets/manifest.json',*(ROOT/'assets/recipes/town').rglob('*.json')]}
 write(HERE/'canonical-readonly-snapshot.json',canonical)
 approved=Image.open(HERE/'approved-native.png').convert('RGBA')
 plate=Image.open(HERE/'empty-plate-v1/master.png').convert('RGB').resize(SIZE,Image.Resampling.LANCZOS)
 save(HERE/'empty-plate-v1/native.png',plate)
 masks={};context_masks={};unionmask=Image.new('L',SIZE)
 for site,info in SITES.items():
  # Body + directly attached support foundation; no rectangular crop ownership.
  mask=union(polygon(info['poly']),polygon(info['foot']))
  masks[site]=mask
 for site,mask in masks.items():
  # Three native pixels retain real painted fringes/torch halo/contact shadow.
  # This context apron is NOT part of the clickable architecture.
  context=mask.filter(ImageFilter.MaxFilter(7))
  others=Image.new('L',SIZE)
  for other,body in masks.items():
   if other!=site:others=union(others,ImageChops.subtract(body,mask))
  context=ImageChops.subtract(context,others)
  context_masks[site]=context;unionmask=union(unionmask,context)
 background=Image.composite(plate,approved.convert('RGB'),unionmask)
 save(HERE/'terrain/background.png',background.convert('RGBA'));save(HERE/'terrain/removal-contours.png',unionmask)
 save(HERE/'terrain/water-mask.png',Image.new('L',SIZE))
 templates={p.relative_to(ROOT).as_posix():load(p) for p in (ROOT/'assets/recipes/town').rglob('*.json')}
 atlas_lookup={state:(name,index) for name,states in ATLAS.items() for index,state in enumerate(states)}
 layers={};rows=[];recipes={};structures={};native_names=load(ROOT/'content/factions.json')['noxus']['town']['buildings']
 for site,info in SITES.items():
  for state in info['states']:
   folder=HERE/'structures'/state;folder.mkdir(parents=True,exist_ok=True)
   if state==info['top']:
    layer=approved.copy();layer.putalpha(context_masks[site]);source=HERE/'approved-master.png'
    conversion={'method':'Exact approved-native RGB through hand-traced body and directly attached foundation contour; no crop-box selection mask.','native_position':[0,0],'native_size':list(SIZE)}
    entrance=list(info['door'])
   else:
    atlas,index=atlas_lookup[state];source=HERE/atlas/'master.png'
    subject,bb=atlas_cut(source,index%4,index//4);save(folder/'painted-cutout.png',subject)
    layer,xy,sz=make_layer(subject,info['variants'][state]);entrance=[xy[0]+sz[0]//2,xy[1]+sz[1]-5]
    conversion={'method':'Genuine different painted predecessor; uniform alpha crop/contain, fixed support baseline.','atlas_cell':[index%4,index//4],'source_crop':bb,'native_position':list(xy),'native_size':sz,'placement_box':list(info['variants'][state])}
   solid=masks[site] if state==info['top'] else binary(layer);body=solid if state==info['top'] else binary(layer,8)
   foundation=ImageChops.multiply(polygon(info['foot']),solid) if state==info['top'] else own_bottom(solid,5)
   door=Image.new('L',SIZE);ImageDraw.Draw(door).rectangle((entrance[0]-2,entrance[1]-2,entrance[0]+2,entrance[1]+2),fill=255)
   open_arch=state in ('fort','citadel')
   if not open_arch:door=ImageChops.multiply(door,solid)
   lane=Image.new('L',SIZE);end=[entrance[0],min(373,entrance[1]+15)]
   ImageDraw.Draw(lane).line([tuple(entrance),tuple(end)],fill=255,width=3)
   area=Image.new('RGBA',SIZE,(255,255,255,0));area.putalpha(solid)
   border=Image.new('RGBA',SIZE,(255,224,90,0));border.putalpha(ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(3)),solid))
   for role,im in [('layer',layer),('area',area),('border',border),('silhouette',body),('foundation',foundation),('door',door),('entry-route',lane)]:save(folder/(role+'.png'),im)
   row={'state':state,'site':site,'label':info['label'],'placement_status':'authored configuration','native_z':info['z'],'native_layer':rel(folder/'layer.png'),'native_layer_sha256':sha(folder/'layer.png'),'painted_master':rel(source),'painted_master_sha256':sha(source),'alpha8_bbox':list(body.getbbox()),'silhouette_pixels':count(body),'foundation_pixels':count(foundation),'door_pixels':count(door),'entrance':entrance,'entry_kind':'open_arch' if open_arch else 'front_threshold','entry_route_end':end,'conversion':conversion,'geometry':{role:{'path':rel(folder/(role+'.png')),'sha256':sha(folder/(role+'.png'))} for role in ('silhouette','foundation','door','entry-route')},'visual_approval_granted':False,'whole_composition_approved':True,'approval_scope':'Full approved composition only; independent layer/state/contour/mapping review pending.'}
   rows.append(row);layers[state]=layer
   structures[state]={'x':0,'y':0,'z':info['z'],'site':site,'entrance':entrance}
   for role in ('animation','area','border'):
    key=f'assets/recipes/town/structures/{state}-{role}.json';recipe=deepcopy(templates[key]);p=folder/('layer.png' if role=='animation' else role+'.png')
    recipe.update(source_sha256=sha(p),sha256=sha(p),source_canvas=list(SIZE),fit='exact',production_status='painted-master-complete' if role=='animation' else 'derived-technical-mask-complete',status='candidate-unselected',visual_approval_granted=False)
    recipe['building_contract'].update(full_canvas_placement={'x':0,'y':0,'z':info['z']},native_ground_contact=list(foundation.getbbox()) if foundation.getbbox() else None,name=native_names[state].get('name',state))
    recipe['generation']={'image_generation_used':role=='animation','provider':'OpenAI built-in image_gen' if role=='animation' else None,'model':'Not exposed by built-in tool','prompt':load(source.with_name('generation.json'))['prompt'] if role=='animation' else None,'method':'Exact authored architectural alpha128 area; one-pixel outward border excludes solid body. No bitmap architecture generated by mask code.','painted_master':rel(source),'painted_master_sha256':sha(source),'generation_record':rel(source.with_name('generation.json')),'generation_record_sha256':sha(source.with_name('generation.json')) if source.with_name('generation.json').is_file() else None,'approved_whole_master':rel(HERE/'approved-master.png'),'approved_whole_master_sha256':sha(HERE/'approved-master.png'),'conversion':conversion,'assembly_script':rel(Path(__file__)),'assembly_script_sha256':sha(Path(__file__)),'candidate_only':True}
    if role=='animation':recipe['groups'][0]['frames'][0].update(source=rel(p),source_sha256=sha(p),sha256=sha(p))
    else:recipe['source']=rel(p)
    recipes[key]=recipe
 # Optional coast: retain source and icon but fail closed for all game conversion.
 for index,state in enumerate(COAST_STATES):
  source=HERE/'coast-stages-v1/master.png';subject,bb=atlas_cut(source,index,0,cols=2,rows=1)
  folder=HERE/'structures'/state;save(folder/'painted-cutout.png',subject)
  # Isolated 800x374 review canvas; this is NOT a native world placement.
  layer,xy,sz=make_layer(subject,(325,140,150,125));layers[state]=layer;save(folder/'unplaced-review.png',layer)
  rows.append({'state':state,'site':'coast','placement_status':'design proposal','native_layer':None,'painted_master':rel(source),'painted_master_sha256':sha(source),'source_crop':bb,'review_only_layer':rel(folder/'unplaced-review.png'),'review_only_sha256':sha(folder/'unplaced-review.png'),'blocker':UNRESOLVED[0]})
  for role in ('animation','area','border'):
   key=f'assets/recipes/town/structures/{state}-{role}.json';recipe=deepcopy(templates[key]);recipe.update(production_status='blocked-unplaced-coastal-variant',status='candidate-unplaced',visual_approval_granted=False,blocker=UNRESOLVED[0]);recipes[key]=recipe
 key='assets/recipes/town/background.json';recipe=deepcopy(templates[key]);source=HERE/'terrain/background.png'
 recipe.update(source=rel(source),source_sha256=sha(source),sha256=sha(source),source_canvas=list(SIZE),fit='exact',production_status='painted-master-complete',status='candidate-unselected',visual_approval_granted=False)
 recipe['generation']={'image_generation_used':True,'provider':'OpenAI built-in image_gen','model':'Not exposed by built-in tool','prompt':load(HERE/'empty-plate-v1/generation.json')['prompt'],'painted_master':rel(HERE/'empty-plate-v1/master.png'),'painted_master_sha256':sha(HERE/'empty-plate-v1/master.png'),'generation_record':rel(HERE/'empty-plate-v1/generation.json'),'generation_record_sha256':sha(HERE/'empty-plate-v1/generation.json') if (HERE/'empty-plate-v1/generation.json').exists() else None,'conversion':'Whole generated clean plate resized uniformly; composited only through exact authored removal contour union. Approved roads/stairs/scenery outside removal contours remain exact. Independent empty-state review pending.','assembly_script':rel(Path(__file__)),'assembly_script_sha256':sha(Path(__file__))};recipes[key]=recipe
 key='assets/recipes/town/buildingIcons.json';recipe=deepcopy(templates[key])
 for frame in recipe['frames']:
  state=frame['building'];im=layers[state];bb=binary(im,8).getbbox();subject=ImageOps.contain(im.crop(bb),(146,66),Image.Resampling.LANCZOS)
  out=Image.new('RGBA',(150,70));out.alpha_composite(subject,((150-subject.width)//2,68-subject.height));p=HERE/'construction'/f'{state}.png';save(p,out);frame.update(source=rel(p),source_sha256=sha(p),sha256=sha(p))
 recipe.update(status='candidate-unselected',visual_approval_granted=False);recipe['generation']={'image_generation_used':False,'method':'Deterministic native150x70 icon crops from the current36new candidate states; sparse native IDs unchanged.','assembly_script':rel(Path(__file__)),'assembly_script_sha256':sha(Path(__file__))};recipes[key]=recipe
 for key,recipe in recipes.items():write(CANDIDATE/'candidate-recipes'/key,recipe)
 write(CANDIDATE/'town-structures.patch.candidate.json',{'status':'authored configuration','candidate_only':True,'structures':structures,'unplaced_states':COAST_STATES,'not_for_blind_merge':True,'canonical_factions_sha256':canonical['content/factions.json']})
 selection={'status':'authored configuration','candidate_only':True,'approved_master':{'path':rel(HERE/'approved-master.png'),'sha256':sha(HERE/'approved-master.png')},'approved_native':{'path':rel(HERE/'approved-native.png'),'sha256':sha(HERE/'approved-native.png')},'canvas':list(SIZE),'ordinary_land_sites':17,'ordinary_count_exception':'Coordinator explicitly confirmed existing Noxus17ordinary on2026-10-29.','optional_coastal_sites':1,'grail_sites':1,'site_count':19,'state_count':36,'placed_state_count':34,'unplaced_states':COAST_STATES,'states':rows,'sites':[{'id':site,'states':v['states'],'top':v['top'],'native_z':v['z'],'contour':v['poly'],'support_contour':v['foot'],'entrance':v['door']} for site,v in SITES.items()]+[{'id':'coast','states':COAST_STATES,'placement_status':'design proposal','blocker':UNRESOLVED[0]}],'recipes':{key:sha(CANDIDATE/'candidate-recipes'/key) for key in recipes},'background':{'path':rel(HERE/'terrain/background.png'),'sha256':sha(HERE/'terrain/background.png')},'unresolved':UNRESOLVED,'runtime_verified':False,'release_accepted':False}
 write(CANDIDATE/'selection.json',selection)
 save(REPORT/'empty-native.png',background)
 complete=[v['top'] for v in SITES.values()]
 modes={'full-with-grail':complete,'full':[v['top'] for k,v in SITES.items() if k!='grail'],'base':[v['states'][0] for k,v in SITES.items() if k!='grail'],'early':['villageHall','fort','dwellingLvl1','tavern'],'barracks-only':['dwellingUpLvl1'],'knife-guild-only':['dwellingUpLvl3'],'t7-support':['special4'],'t7-base':['dwellingLvl7'],'t7-upgrade':['dwellingUpLvl7'],'guild-absent':[s for s in complete if s!='mageGuild4']}
 for name,states in modes.items():save(REPORT/(name+'-native.png'),compose(states,layers,background))
 # Technical overlays are review diagrams only; never production art.
 overlay=approved.convert('RGB');draw=ImageDraw.Draw(overlay)
 for site,info in SITES.items():
  draw.line(info['poly']+[info['poly'][0]],fill=(70,230,210),width=1);draw.line(info['foot']+[info['foot'][0]],fill=(255,216,70),width=1);x,y=info['door'];draw.ellipse((x-2,y-2,x+2,y+2),fill=(255,90,90));draw.text((x+3,y+2),site,fill='white')
 save(REPORT/'contours-and-doors-native.png',overlay)
 cards=''.join(f'<figure><a href="{name}-native.png"><img src="{name}-native.png" width="800" height="374"></a><figcaption>{html.escape(name)}</figcaption></figure>' for name in ['empty',*modes,'contours-and-doors'])
 table=''.join(f'<tr><td>{r["state"]}<br><img src="../../../{rel(HERE/"construction"/(r["state"]+".png"))}" width="150" height="70"></td><td>{r["site"]}</td><td>{r["placement_status"]}</td><td><a href="../../../{r.get("native_layer") or r["review_only_layer"]}">source layer</a>'+(' · <a href="../../../'+rel(HERE/'structures'/r['state']/'area.png')+'">click area</a> · <a href="../../../'+rel(HERE/'structures'/r['state']/'border.png')+'">highlight</a>' if r.get('native_layer') else ' (unplaced review art)')+'</td></tr>' for r in rows)
 page='<!doctype html><meta charset="utf-8"><title>Noxus NX1 candidate decomposition</title><style>body{background:#171519;color:#eee;font:15px system-ui;margin:24px}figure{margin:24px 0}img{display:block;max-width:100%;height:auto;image-rendering:auto}td,th{border:1px solid #655;padding:5px}a{color:#ecd092}</style><h1>Noxus approved NX1: source candidates</h1><p>Authored configuration. Full inland + Grail reconstruction matches the approved painting. This is source assembly, not in-game evidence. The user approved the complete painting; empty/base stages, independent frontage walls, mappings and coastal placement remain subject to review. No canonical files or stages changed.</p><ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in UNRESOLVED)+'</ul>'+cards+'<table><tr><th>State</th><th>Site</th><th>Status</th><th>Layer</th></tr>'+table+'</table>'
 (REPORT/'index.html').write_text(page,encoding='utf-8')
 after={key:sha(ROOT/key) for key in canonical};assert after==canonical,'Canonical input mutation'
 print(json.dumps({'source_candidate':rel(CANDIDATE),'states':len(rows),'placed':len(structures),'unplaced':COAST_STATES,'recipes':len(recipes),'canonical_unchanged':True}))
if __name__=='__main__':main()
