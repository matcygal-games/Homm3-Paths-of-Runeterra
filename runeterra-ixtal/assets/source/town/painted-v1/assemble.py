"""Deterministic Ixtal painted town candidate conversion; never generates art/stages.

Requires actual reviewed source roots/door widths in placement-inputs-v1.json.
No missing bitmap or calibration is replaced with a placeholder.
"""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageChops,ImageFilter,ImageDraw

S=Path(__file__).resolve().parent;P=S.parents[3];W=P.parent
R=W/'build/reports/ixtal-implementation-20261026-v1/town';CANVAS=(800,374)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(P).as_posix()
def pin(p):return {'path':rel(p),'sha256':sha(p)}
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def bbox(im):return im.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()

def render():
 plan=json.loads((S/'layout-plan-v6.json').read_text());cal=json.loads((S/'placement-inputs-v1.json').read_text());frames={};placements={};sources={}
 for site in plan['sites']:
  x,y,w,h=site['box'];tx,ty=site['entrance'];items={};limits=[cal['families'][site['id']]['native_door_width']]
  for key in site['states']:
   folder=S/'buildings'/key;c=cal['states'][key];source=P/c['master'];generation=folder/c.get('generation','source-generation-v1.json');im=Image.open(source).convert('RGBA');b=bbox(im);assert b
   root=c['root'];dw=c['door_width']
   for extent,space in [(root[0]-b[0],tx-x-1),(b[2]-root[0],x+w-1-tx),(root[1]-b[1],ty-y-1),(b[3]-root[1],y+h-1-ty)]:
    if extent>0:limits.append(space*dw/extent)
   items[key]=(source,generation,im,b,root,dw)
  native_dw=min(limits)*.995
  for key,(source,generation,im,b,root,dw) in items.items():
   scale=native_dw/dw;size=(max(1,round(im.width*scale)),max(1,round(im.height*scale)));piece=im.resize(size,Image.Resampling.LANCZOS);offset=(round(tx-root[0]*scale),round(ty-root[1]*scale));frame=Image.new('RGBA',CANVAS);frame.alpha_composite(piece,offset);actual=bbox(frame)
   assert actual and actual[0]>=x and actual[1]>=y and actual[2]<=x+w and actual[3]<=y+h,(key,actual,site['box'])
   folder=S/'buildings'/key;out=folder/'native-frame.png';frame.save(out);frames[key]=pin(out);sources[key]=(source,generation)
   placements[key]={'site':site['id'],'source_root':root,'source_door_width':dw,'family_native_door_width':native_dw,'uniform_scale':scale,'offset':list(offset),'native_entrance':site['entrance'],'full_alpha_bbox':list(actual),'calibration_basis':'Measured source entrance and physical door density; one scale family, no independent per-state bbox fill.'}
 dump(S/'placement-calibration-v1.json',{'status':'authored configuration','states':placements,'native_observed':False})
 return plan,frames,sources

def derive(plan,frames,sources):
 background=S/'landscape/native-rgba-v1.png';bg=Image.open(background).convert('RGBA');assert bg.size==CANVAS
 recipes=[];icons={};deps={S/'assemble.py',S/'layout-plan-v6.json',S/'placement-inputs-v1.json',S/'placement-calibration-v1.json',S/'composition/master-v1.png',S/'composition/prompt-v1.txt',S/'composition/source-generation-v1.json'}
 visited=set()
 def ancestry(path):
  if path in visited:return
  visited.add(path);deps.add(path)
  if path.suffix!='.json':return
  g=json.loads(path.read_text())
  if isinstance(g,dict) and isinstance(g.get('prompt'),str):deps.add(P/g['prompt'])
  def walk(value):
   if isinstance(value,dict):
    if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str):
     ref=P/value['path'];assert ref.is_file() and sha(ref)==value['sha256'];ancestry(ref)
    for child in value.values():walk(child)
   elif isinstance(value,list):
    for child in value:walk(child)
  walk(g)
 for key,(master,generation) in sources.items():deps.add(master);ancestry(generation)
 def common(key):
  master,generation=sources[key];g=json.loads(generation.read_text());return {'status':'painted-candidate','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'credits':{'author':'Project-directed OpenAI builtin imagegen; deterministic technical2D conversion','license':None,'redistribution':'unresolved; release prohibited'},'generation':{'image_generation_used':True,'provider':'OpenAI builtin imagegen','model':'not exposed by tool','prompt':(P/g['prompt']).read_text(),'prompt_file':g['prompt'],'painted_master':rel(master),'painted_master_sha256':sha(master),'producer':rel(S/'assemble.py'),'producer_sha256':sha(S/'assemble.py'),'source_generation_ledger':rel(generation)},'dependencies':[pin(p) for p in sorted(deps)]}
 for site in plan['sites']:
  for key in site['states']:
   folder=S/'buildings'/key;frame=Image.open(P/frames[key]['path']).convert('RGBA');alpha=frame.getchannel('A').point(lambda a:255 if a>=96 else 0);area=Image.new('RGBA',CANVAS);area.paste((255,255,255,255),(0,0),alpha);area.save(folder/'area.png');edge=ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(3)),alpha);border=Image.new('RGBA',CANVAS);border.paste((240,210,100,255),(0,0),edge);border.save(folder/'border.png')
   crop=frame.crop(bbox(frame))
   for size,name in [((58,64),'campaign.png'),((150,70),'construction.png')]:
    im=Image.new('RGBA',size);piece=crop.copy();piece.thumbnail((size[0]-6,size[1]-6),Image.Resampling.LANCZOS);im.alpha_composite(piece,((size[0]-piece.width)//2,size[1]-piece.height-3));im.save(folder/name)
   c=common(key);prefix='Content/Sprites/runeterra/ixtal/town/structures/'+key;rp=S/'recipes'/(key+'-animation.json')
   dump(rp,{**c,'recipe_type':'vcmi_animation','canvas':list(CANVAS),'pivot':{'x':site['entrance'][0],'y':site['entrance'][1]},'generateShadow':0,'generateOverlay':0,'groups':[{'group':0,'frames':[{'source':frames[key]['path'],'source_sha256':frames[key]['sha256'],'source_canvas':list(CANVAS)}]}],'output_path':prefix+'.json'});recipes.append(rel(rp))
   for role,size in [('area',CANVAS),('border',CANVAS),('campaign',(58,64))]:
    source=folder/(role+'.png');rp=S/'recipes'/(key+'-'+role+'.json');dump(rp,{**c,'recipe_type':'raster','canvas':list(size),'size':list(size),'source_canvas':list(size),'source':rel(source),'source_sha256':sha(source),'fit':'exact','require_alpha':True,'output_path':prefix+'_'+role+'.png'});recipes.append(rel(rp))
   icons[key]=folder/'construction.png'
 sys.path.insert(0,str(W/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('ixtal');ids=compiler.indexed_building_ids(P);assert set(ids)==set(frames)
 c=common('capitol');c['dependencies'].extend(pin(p) for p in icons.values());rp=S/'recipes/buildingIcons.json'
 dump(rp,{**c,'recipe_type':'indexed_animation','canvas':[150,70],'pivot':{'x':75,'y':35},'generateShadow':0,'generateOverlay':0,'frames':[{'building':key,'frame':index,'source':rel(icons[key]),'source_sha256':sha(icons[key]),'source_canvas':[150,70]} for key,index in sorted(ids.items(),key=lambda kv:kv[1])],'output_path':'Content/Sprites/runeterra/ixtal/town/buildingIcons.json'});recipes.append(rel(rp))
 g=json.loads((S/'landscape/source-generation-v1.json').read_text());master=P/g['painted_master'];rp=S/'recipes/background.json'
 dump(rp,{**c,'recipe_type':'raster','canvas':list(CANVAS),'size':list(CANVAS),'source_canvas':list(CANVAS),'source':rel(background),'source_sha256':sha(background),'fit':'exact','require_alpha':False,'output_path':'Content/Sprites/runeterra/ixtal/town/background.png','generation':{'image_generation_used':True,'provider':'OpenAI builtin imagegen','model':'not exposed by tool','prompt':(P/g['prompt']).read_text(),'prompt_file':g['prompt'],'painted_master':rel(master),'painted_master_sha256':sha(master),'producer':rel(S/'assemble.py'),'producer_sha256':sha(S/'assemble.py'),'source_generation_ledger':rel(S/'landscape/source-generation-v1.json')},'dependencies':[pin(p) for p in sorted(deps|{master,S/'landscape/source-generation-v1.json',P/g['prompt']})]});recipes.append(rel(rp));assert len(recipes)==142
 land=Image.new('RGBA',CANVAS,(255,255,255,255));draw=ImageDraw.Draw(land)
 for poly in plan['water_polygons']:draw.polygon([tuple(p) for p in poly],fill=(0,0,0,255))
 landpath=S/'landscape/dry-land-mask-v1.png';land.save(landpath)
 dump(S/'layout-acceptance-contract-v1.json',{'canvas':list(CANVAS),'alpha_threshold':8,'background':pin(background),'land_mask':pin(landpath),'sites':[{k:v for k,v in s.items() if k in {'id','box','states','entrance','foundation_polygon','depth','intentional_water'}} for s in plan['sites']],'frames':frames,'roads':plan['road_graph'],'land_mask_basis':'Frozen-plan technical proxy; actual native pixels reviewed separately','native_observed':False,'visual_approval_granted':False})
 dump(S/'candidate-recipes-v1.json',{'status':'authored configuration','recipes':recipes,'native_observed':False,'release_accepted':False})
 order={k:s['depth'] for s in plan['sites'] for k in s['states']}
 base=[s['states'][0] for s in plan['sites'][:16]];up=[s['states'][-1] for s in plan['sites'][:16]]
 for name,keys in [('empty',[]),('early',['villageHall','fort','dwellingLvl1']),('partial',['townHall','citadel','mageGuild2','tavern','marketplace','dwellingLvl1','dwellingLvl2','dwellingLvl3','dwellingLvl4']),('ordinary-base',base),('ordinary-upgraded',up),('coastal',up+['ship']),('grail',up+['grail']),('full',up+['ship','grail'])]:
  im=bg.copy()
  for key in sorted(keys,key=lambda k:order[k]):im.alpha_composite(Image.open(P/frames[key]['path']).convert('RGBA'))
  im.save(R/(name+'-v2.png'))
 print(json.dumps({'status':'authored configuration','states':len(frames),'candidate_recipes':len(recipes),'contract_sha256':sha(S/'layout-acceptance-contract-v1.json'),'native_observed':False}))

if __name__=='__main__':
 plan,frames,sources=render()
 if '--geometry-only' not in sys.argv:derive(plan,frames,sources)
