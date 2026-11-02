"""IX1 complete-state candidate. Painted masters only; technical registration.

The approved full inland painting is immutable. Maximum-state visible layers
retain its exact RGBA pixels. Lower states come from newly painted source
atlases, never from scaling/recolouring their upgraded architecture.
"""
from pathlib import Path
import hashlib,json,sys,copy,io
import numpy as np
from PIL import Image,ImageChops,ImageFilter,ImageOps,ImageDraw

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
ROOT=PROJECT.parent
OLD=PROJECT/'assets/source/town/approved-IX1-20261029-v1'
REPORT=ROOT/'reports/ixtal-approved-layout-20261030-v1'
RUNTIME=REPORT/'native-runtime-v2'
SIZE=(800,374)
sys.path.insert(0,str(ROOT/'scripts'))
from faction_art_compile import create_compiler

def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf8')
def rel(p):return p.relative_to(PROJECT).as_posix()
def ref(p):return {'path':rel(p),'sha256':sha(p)}
def save(p,im):
 p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
 return ref(p) if p.is_relative_to(PROJECT) else {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def blank():return Image.new('RGBA',SIZE)

# Atlas cells are genuine separately painted predecessor architecture.
CIVIC=['villageHall','townHall','cityHall','mageGuild1','mageGuild2','mageGuild3','mageGuild4','fort','citadel']
DWELLINGS=['dwellingLvl1','dwellingLvl2','dwellingLvl3','dwellingLvl4','dwellingLvl5','dwellingLvl6','dwellingLvl7','shipyard','ship']

def isolate(path,columns=3,rows=3):
 im=Image.open(path).convert('RGBA');arr=np.array(im);mask=arr[:,:,3]>=128
 if path.name=='guild-left-entry-v1.png':
  # The two lower source foliage fringes touch at the atlas gutter. This
  # annotated3px separator owns only that leaf fringe; roofs/walls/steps stay
  # complete on their respective sides. Original raw master is preserved.
  mask[467:,735:738]=False
 # Connected actor ownership avoids slicing a roof at a nominal atlas cell.
 parents=[];runs=[];previous=[]
 def root(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 for y,row in enumerate(mask):
  edge=np.diff(np.r_[False,row,False].astype(np.int8));starts=np.where(edge==1)[0];ends=np.where(edge==-1)[0];current=[];j=0
  for left,right in zip(starts,ends):
   left,right=int(left),int(right);ident=len(parents);parents.append(ident)
   while j<len(previous) and previous[j][1]<left:j+=1
   k=j
   while k<len(previous) and previous[k][0]<=right:
    p,q=root(ident),root(previous[k][2])
    if p!=q:parents[p]=q
    k+=1
   runs.append((ident,y,left,right));current.append((left,right,ident))
  previous=current
 comps={}
 for ident,y,left,right in runs:comps.setdefault(root(ident),[]).append((y,left,right))
 major=[]
 for component_rows in comps.values():
  if sum(r-l for _,l,r in component_rows)<1000:continue
  box=[min(l for _,l,_ in component_rows),min(y for y,_,_ in component_rows),max(r for _,_,r in component_rows),max(y for y,_,_ in component_rows)+1]
  major.append((box,component_rows))
 if len(major)!=columns*rows:raise ValueError('Atlas needs exact detached actors: '+str(len(major))+' '+str([box for box,_ in major]))
 major.sort(key=lambda r:(r[0][1]+r[0][3])/2);ordered=[]
 for row in range(rows):ordered+=sorted(major[row*columns:row*columns+columns],key=lambda r:r[0][0]+r[0][2])
 frames=[]
 for box,rows in ordered:
  l,t,r,b=box;cut=arr[t:b,l:r].copy();owned=np.zeros(cut.shape[:2],dtype=bool)
  for y,x0,x1 in rows:owned[y-t,x0-l:x1-l]=True
  cut[~owned]=0;cut[:,:,3][owned]=255
  if l<=0 or t<=0 or r>=im.width or b>=im.height:raise ValueError('Actor clipped at source boundary')
  frames.append(Image.fromarray(cut))
 return frames

def recipe(source,output,canvas,*,animation=False,pivot=(0,0),master=None):
 master=master or HERE/'approved-full.png'
 d={'recipe_type':'vcmi_animation' if animation else 'raster','production_status':'painted-master-complete-unapproved',
 'canvas':list(canvas),'output_path':'Content/Sprites/runeterra/ixtal/town/'+output,
 'status':'authored configuration','visual_approval_granted':False,
 'acceptance':'Approved whole composition; all-state source integration. Native and final external acceptance remain separate.',
 'credits':{'author':'Project-directed OpenAI builtin imagegen; technical2D extraction/registration','license':None,'redistribution':'unresolved'},
 'generation':{'image_generation_used':True,'provider':'OpenAI builtin imagegen','model':'not exposed by tool',
 'prompt':'Original Heroes III painted2D Ixtali architecture: warm limestone, jade roofs and cloth, gold physical regional glyphs, low frontal three-quarter upper-left daylight. Approved IX1 maximum pixels preserved; separately painted genuine smaller council/guild/fort and dwelling predecessors. Transparent actors, complete foundations; no Blender/3D or geometric kit.',
 'painted_master':rel(master),'painted_master_sha256':sha(master),'producer':rel(Path(__file__)),'producer_sha256':sha(Path(__file__)),
 'source_generation_ledger':rel(HERE/'source-generation.json'),
 'method':'Exact approved maximum pixels; genuine painted predecessor atlases; uniform scale/crop/alpha registration only. No 3D.'}}
 d['dependencies']=[ref(p) for p in [Path(__file__),HERE/'source-generation.json',*sorted((HERE/'inputs').glob('*')),*sorted((HERE/'masters').glob('*.png'))] if 'rejected' not in p.name]
 if master.with_suffix('.prompt.txt').exists():d['generation']['prompt_file']=rel(master.with_suffix('.prompt.txt'))
 f={'source':rel(source),'source_sha256':sha(source),'source_canvas':list(canvas)}
 if animation:d.update(pivot={'x':pivot[0],'y':pivot[1]},generateShadow=0,generateOverlay=0,groups=[{'group':0,'frames':[f]}])
 else:d.update(f,fit='exact')
 return d

def main():
 REPORT.mkdir(parents=True,exist_ok=True)
 plan=read(HERE/'inputs/decomposition-plan.json')
 approved_path=ROOT/'reports/five-town-concepts-20261029-v1/first-group/ixtal-native-800x374.png'
 if sha(approved_path)!='5ab872fc252396e37982aeed5b45a2f5e09c28ab4c3f928b96ef10d116f1c30e':raise ValueError('Approved IX1 pixels changed')
 approved=Image.open(approved_path).convert('RGBA');save(HERE/'approved-full.png',approved)
 recovered=Image.open(HERE/'inputs/empty-provider-native.png').convert('RGBA')
 design=read(HERE/'inputs/town-visuals-before.json');contracts={k:v['keys'] for k,v in design['sites'].items()}
 site_for={s:k for k,v in contracts.items() for s in v}
 specs={s['site']:s for s in plan['sites']}
 # Canopy Routes is the roofed trail/supply station on a pre-existing public
 # bridge. Its traversable floor is incidental shared circulation, not a
 # constructible wall. Nexus silhouette follows its actual ring and plinth,
 # excluding the empty triangular terrace wedge in the first budget draft.
 specs['canopy']['outline']=[[1,117],[18,111],[28,108],[40,109],[46,113],[51,119],[68,111],[84,108],[99,112],[111,117],[114,126],[103,130],[90,127],[75,123],[61,125],[45,127],[30,126],[13,127],[1,124]]
 specs['wardens']['outline']=[[235,215],[245,216],[254,222],[268,229],[279,241],[283,267],[235,272],[235,247]]
 for site,point in {'guild':[498,125],'fort':[612,111],'guides':[224,262],'wardens':[267,260],'bristlehogs':[147,197],'pakaa':[151,238],'pairofants':[624,224],'canopy':[107,125]}.items():specs[site]['door']=point
 raw_masks={}
 for site,spec in specs.items():
  m=Image.new('L',SIZE);d=ImageDraw.Draw(m)
  for points in [spec['outline'],*spec.get('additional_outlines',[])]:d.polygon([tuple(p) for p in points],fill=255)
  # The first decomposition's two-pixel context apron contained public paving
  # and closed visible route gaps. The independently traced architecture
  # outline itself owns material; adjacent unchanged paving stays in terrain.
  raw_masks[site]=m
 guide=Image.open(HERE/'masters/architecture-matte-guide-v1.png').convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
 total=guide.getchannel('A').point(lambda v:255 if v>=128 else 0).filter(ImageFilter.MaxFilter(3))
 seed_union=Image.new('L',SIZE)
 for m in raw_masks.values():seed_union=ImageChops.lighter(seed_union,m)
 # Provider guide registration is bounded by the authored scene budgets. A
 # displaced invented edge outside this margin never acquires original RGB.
 total=ImageChops.multiply(total,seed_union.filter(ImageFilter.MaxFilter(3)))
 # This source guide supplies alpha only. The accepted painting supplies EVERY
 # selected RGB pixel. Registration/partial views remain independently reviewed.
 bridge=Image.new('L',SIZE);ImageDraw.Draw(bridge).polygon([(0,100),(120,98),(145,116),(211,151),(211,169),(112,144),(0,132)],fill=255)
 total=ImageChops.lighter(ImageChops.subtract(total,bridge),ImageChops.multiply(total,raw_masks['canopy']))
 background=Image.composite(recovered,approved,total);save(HERE/'background.png',background)
 visible_masks={site:Image.new('L',SIZE) for site in specs};remaining=total.copy()
 ordered=sorted(specs,key=lambda s:(specs[s]['native_z'],specs[s]['door'][0]),reverse=True)
 # Architecture may extend beyond the old coarse budget by a few pixels.
 # Nearest traced seed ownership fills only the existing matte, never paints.
 expanded_masks={site:raw_masks[site].copy() for site in specs}
 for radius in range(31):
  for site in ordered:
   expanded=expanded_masks[site]
   own=ImageChops.multiply(remaining,expanded);visible_masks[site]=ImageChops.lighter(visible_masks[site],own);remaining=ImageChops.subtract(remaining,own)
  if remaining.getbbox() is None:break
  expanded_masks={site:m.filter(ImageFilter.MaxFilter(3)) for site,m in expanded_masks.items()}
 if remaining.getbbox() is not None:raise ValueError('Unowned matte-guide architecture: '+str(remaining.getbbox()))
 save(HERE/'architecture-removal-mask.png',total)
 frames={};index={};masters={}
 for site,spec in specs.items():
  state=spec['extracted_state'];im=Image.new('RGBA',SIZE);im.paste(approved,(0,0),visible_masks[site]);im.putalpha(visible_masks[site])
  frames[state]=im;masters[state]=HERE/'approved-full.png'
  index[state]={'site':site,'depth':spec['native_z'],'entrance':spec['door'],'kind':'approved-visible-maximum'}
 guild_names=['mageGuild1','mageGuild2','mageGuild3','mageGuild4']
 atlas_defs=[('civic-predecessors-v1.png',CIVIC,3),('dwelling-coast-predecessors-v1.png',DWELLINGS,3),('guild-left-entry-v1.png',guild_names,2)]
 for name,names,columns in atlas_defs:
  master=HERE/'masters'/name
  for state,cut in zip(names,isolate(master,columns,columns)):
   if name=='civic-predecessors-v1.png' and state in guild_names:continue
   site=site_for[state]
   if site=='coast':continue
   spec=specs[site];maximum=frames[spec['extracted_state']];b=spec['alpha_bbox_xyxy']
   # Smaller predecessor mass sits on the same physically observed entrance
   # terrace. Hall ranks grow in place; all remaining lower states are .78.
   factor={'villageHall':.56,'townHall':.69,'cityHall':.84,'mageGuild1':.56,'mageGuild2':.66,'mageGuild3':.77,'mageGuild4':.88,'fort':.50,'citadel':.65,'dwellingLvl2':.60,'dwellingLvl3':.60,'dwellingLvl7':.58}.get(state,.78)
   target=(max(20,round((b[2]-b[0])*factor)),max(15,round((b[3]-b[1])*factor)))
   cut.thumbnail(target,Image.Resampling.LANCZOS)
   # Source frontal stairs/threshold are at the lower central root.
   predecessor_root={'guides':[204,263],'wardens':[260,b[3]],'bristlehogs':[88,196],'pakaa':[130,242],'pairofants':[713,224]}.get(site,[spec['door'][0],b[3]])
   if site=='hall':predecessor_root=[420,b[3]]
   if site=='guild':predecessor_root=[512,b[3]]
   if state=='fort':predecessor_root=[615,128]
   if state=='citadel':predecessor_root=[625,128]
   x=round(predecessor_root[0]-cut.width/2);y=predecessor_root[1]-cut.height
   if x<0 or y<0 or x+cut.width>800 or y+cut.height>374:raise ValueError('Candidate frame escapes canvas '+state)
   native=blank();native.alpha_composite(cut,(x,y));frames[state]=native;masters[state]=master
   entrance=[predecessor_root[0],predecessor_root[1]-3]
   if site=='guild':entrance=[x+round(cut.width*[.30,.20,.26,.20][guild_names.index(state)]),predecessor_root[1]-3]
   index[state]={'site':site,'depth':spec['native_z'],'entrance':entrance,
    'kind':'independent-painted-predecessor','atlas':rel(master),'factor':factor,'placed_bounds':[x,y,x+cut.width,y+cut.height]}
 # Optional high river inlet is painted as conditional coast scenery, behind
 # the ordinary aviary and Canopy Routes bridge. It never alters inland full.
 coastal=HERE/'masters/coast-scene-v2.png'
 if coastal.exists():
  mask=Image.new('L',SIZE);ImageDraw.Draw(mask).polygon([(0,54),(20,51),(39,61),(67,67),(95,70),(116,64),(151,70),(185,88),(185,109),(159,119),(132,133),(106,130),(84,120),(48,116),(21,111),(0,102)],fill=255)
  canopy=frames['special1'].getchannel('A');hallunatis=frames['dwellingUpLvl6'].getchannel('A')
  # Exclude all regular architecture; the new shore cannot bake either site.
  shore=mask.copy();mask=ImageChops.subtract(mask,ImageChops.lighter(canopy,hallunatis))
  # The genuine new supported gangway passes behind the existing trail-office
  # canopy. Retain its own timber when that office is absent; native z hides
  # it correctly when the office is built. No old roof is incorporated here.
  gangway=Image.new('L',SIZE);ImageDraw.Draw(gangway).polygon([(94,120),(104,111),(118,104),(140,94),(145,95),(119,109),(107,117),(97,123)],fill=255)
  mask=ImageChops.lighter(mask,ImageChops.subtract(ImageChops.multiply(shore,gangway),hallunatis))
  save(HERE/'coast-incorporation-mask.png',mask)
  for state,name in [('shipyard','coast-scene-v2.png'),('ship','coast-with-ship-v1.png')]:
   master=HERE/'masters'/name
   if not master.exists():continue
   im=Image.open(master).convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS);im.putalpha(mask)
   frames[state]=im;masters[state]=master
   index[state]={'site':'coast','depth':92,'entrance':[100,131],'kind':'conditional-painted-inlet','incorporation_mask':ref(HERE/'coast-incorporation-mask.png')}
 recipes={};native_outputs={};compiler=create_compiler('ixtal')
 all_site_alpha={}
 for state,im in frames.items():
  site=index[state]['site'];a=im.getchannel('A').point(lambda v:255 if v>=128 else 0)
  all_site_alpha[site]=ImageChops.lighter(all_site_alpha.get(site,Image.new('L',SIZE)),a)
 for state,im in frames.items():
  folder=HERE/'states'/state;frame=folder/'native.png';save(frame,im)
  a=im.getchannel('A').point(lambda v:255 if v>=128 else 0)
  # Conservative visible click ownership follows actual depth. A rear site
  # never steals a hotspot belonging to any possible foreground upgrade.
  for other,other_alpha in all_site_alpha.items():
   depth=max(index[s]['depth'] for s in frames if index[s]['site']==other)
   if other!=index[state]['site'] and depth>index[state]['depth']:a=ImageChops.subtract(a,other_alpha)
  if not a.getbbox():raise ValueError('Occlusion removed entire clickable building '+state)
  area=Image.new('RGBA',SIZE,(255,255,255,0));area.putalpha(a);save(folder/'area.png',area)
  ring=ImageChops.subtract(a.filter(ImageFilter.MaxFilter(3)),a)
  border=Image.new('RGBA',SIZE,(255,220,96,0));border.putalpha(ring);save(folder/'border.png',border)
  icon=Image.new('RGBA',(150,70));tiny=im.crop(im.getbbox());tiny.thumbnail((144,64),Image.Resampling.LANCZOS);icon.alpha_composite(tiny,((150-tiny.width)//2,(70-tiny.height)//2));save(folder/'icon.png',icon)
  campaign=Image.new('RGBA',(58,64));tiny=im.crop(im.getbbox());tiny.thumbnail((54,60),Image.Resampling.LANCZOS);campaign.alpha_composite(tiny,((58-tiny.width)//2,62-tiny.height));save(folder/'campaign.png',campaign)
  index[state].update(frame=ref(frame),area=ref(folder/'area.png'),border=ref(folder/'border.png'),icon=ref(folder/'icon.png'),campaign=ref(folder/'campaign.png'))
  recipes[state]=recipe(frame,'structures/'+state+'.json',SIZE,animation=True,pivot=tuple(index[state]['entrance']),master=masters[state])
  recipes[state+'-area']=recipe(folder/'area.png','structures/'+state+'_area.png',SIZE,master=masters[state])
  recipes[state+'-border']=recipe(folder/'border.png','structures/'+state+'_border.png',SIZE,master=masters[state])
  recipes[state+'-campaign']=recipe(folder/'campaign.png','structures/'+state+'_campaign.png',(58,64),master=masters[state])
 recipes['background']=recipe(HERE/'background.png','background.png',SIZE)
 # Sparse native BuildingID-indexed construction animation follows the actual
 # selected pipeline, including all original gaps; missing coast remains open.
 icon_template=read(HERE/'inputs/buildingIcons-native-index.json')
 icon_ids={f['building']:f['frame'] for f in icon_template['frames']}
 icons=recipe(HERE/'states/capitol/icon.png','buildingIcons.json',(150,70))
 icons.update(recipe_type='indexed_animation',generateShadow=0,generateOverlay=0,
 frames=[dict(building=s,frame=icon_ids[s],source=rel(HERE/'states'/s/'icon.png'),source_sha256=sha(HERE/'states'/s/'icon.png'),source_canvas=[150,70]) for s in frames])
 icons.pop('source',None);icons.pop('source_sha256',None);icons.pop('source_canvas',None);icons.pop('fit',None)
 recipes['buildingIcons']=icons
 # Only complete recipes are compiled. No missing state aliases or stand-ins.
 receipts=[]
 for name,value in recipes.items():
  path=HERE/'candidate-recipes'/f'{name}.json';dump(path,value)
  if name=='buildingIcons' and set(frames)!=set(site_for):continue
  outputs,receipt=compiler.plan(PROJECT,path);receipts.append(receipt)
  for key,raw in outputs.items():
   dst=RUNTIME/key;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw);native_outputs[key]=sha(dst)
 complete=sorted([s['extracted_state'] for s in plan['sites']],key=lambda s:index[s]['depth'])
 scene=background.copy()
 for s in complete:scene.alpha_composite(frames[s])
 if scene.tobytes()!=approved.tobytes():raise ValueError('Approved full composition changed')
 save(REPORT/'full.png',scene);save(REPORT/'empty.png',background)
 base=[next((s for s in contracts[k] if s in frames),spec['extracted_state']) for k,spec in specs.items() if k!='grail']
 base.sort(key=lambda s:index[s]['depth']);scene=background.copy()
 for s in base:scene.alpha_composite(frames[s])
 save(REPORT/'base.png',scene)
 selections={'ordinary-full':[s for s in complete if index[s]['site']!='grail'],
 'early':['villageHall','fort','tavern','dwellingLvl1'],
 'middle':['townHall','citadel','mageGuild2','tavern','marketplace','blacksmith','dwellingUpLvl1','dwellingLvl2','dwellingLvl3','dwellingLvl4','special1'],
 'coast-full':complete+(['ship'] if 'ship' in frames else [])}
 for name,selected in selections.items():
  scene=background.copy()
  for state in sorted(selected,key=lambda s:index[s]['depth']):scene.alpha_composite(frames[state])
  save(REPORT/(name+'.png'),scene)
 missing=sorted(set(site_for)-set(frames));dump(HERE/'frame-index.json',{'frames':index,'background':ref(HERE/'background.png'),'complete_scene_states':complete,'sites':contracts,'missing':missing})
 dump(REPORT/'conversion.json',{'status':'authored configuration','frames':len(frames),'missing':missing,'maximum_pixel_exact':True,'runtime_directory':RUNTIME.relative_to(ROOT).as_posix(),'runtime_files':len(native_outputs),'runtime':native_outputs,'receipts':receipts,'native_tested':False,'selected':False})
 html='''<!doctype html><meta charset="utf-8"><title>IX1 all-state implementation</title><style>body{background:#202820;color:#eee;font:17px Georgia;max-width:1000px;margin:30px auto}img{max-width:100%}a{color:#edc977}</style><h1>Approved IX1 — complete-state source integration</h1><p>Authored configuration; candidate. Approved full scene retained pixel-exact. Optional coast pending physical placement.</p>'''
 for name in ['empty','early','middle','base','ordinary-full','full','coast-full']:html+=f'<h2>{name}</h2><img src="{name}.png">'
 for site in contracts:
  html+=f'<h2>{site}</h2>'
  for state in contracts[site]:
   if state in frames:
    im=background.copy();im.alpha_composite(frames[state]);save(REPORT/'states'/f'{state}.png',im);html+=f'<h3>{state}</h3><img src="states/{state}.png">'
   else:html+=f'<p>{state}: pending.</p>'
 (REPORT/'index.html').write_text(html,encoding='utf8')
 print(json.dumps({'states':len(frames),'missing':missing,'maximum_pixel_exact':True}))

if __name__=='__main__':main()
