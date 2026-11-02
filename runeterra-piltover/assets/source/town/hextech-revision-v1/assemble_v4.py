"""Painted Piltover V4 technical source-candidate assembly. No generation or staging."""
import argparse,hashlib,json,math,sys
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter,ImageDraw
S=Path(__file__).resolve().parent;P=S.parents[3];W=P.parent;OLD=P/'assets/source/town/painted-v1'
R=W/'build/reports/piltover-implementation-20261025-v1/hextech-revision-v1/town'
CANVAS=(800,374)
EDIT_CAL={'blacksmith':([620,1028],400),'special3':([590,889],365),'resourceSilo':([477,1192],200),'dwellingLvl5':([565,1067],176),'dwellingUpLvl5':([606,1107],189),'dwellingLvl6':([451,1215],138),'dwellingUpLvl6':([422,1310],129),'dwellingLvl7':([680,947],480),'dwellingUpLvl7':([671,1040],490)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(P).as_posix()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def pin(p):return {'path':rel(p),'sha256':sha(p)}
def bbox(im):return im.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()
def source_for(key):
 if key in EDIT_CAL:
  suffix='v4b'if key=='dwellingLvl7'else'v4';folder=S/'buildings'/key
  return folder/f'master-{suffix}.png',folder/f'source-generation-{suffix}.json'
 folder=OLD/'buildings'/key
 return folder/'master-v1.png',folder/'source-generation.json'
def render():
 plan=json.loads((S/'layout-plan-v4.json').read_text());legacy=json.loads((OLD/'placement-calibration-v1.json').read_text())['states']
 sites=plan['sites']+[plan['coastal_site'],plan['optional_grail']];frames={};placements={};sources={}
 for site in sites:
  x,y,w,h=site['box'];tx,ty=site['door'];requested=legacy[site['keys'][0]]['family_native_door_width']*site['family_enlargement'];limits=[requested];items={}
  if site['id']=='coast':
   for key in site['keys']:
    frame=Image.open(OLD/'buildings'/key/'native-frame.png').convert('RGBA');out=S/'buildings'/key/'native-frame.png';out.parent.mkdir(parents=True,exist_ok=True);frame.save(out);frames[key]=pin(out);placements[key]={'site':site['id'],'method':'Whole unchanged existing own dock/ship/gangway composition retained at same anchor','native_anchor':site['door'],'alpha_bbox':list(bbox(frame))};sources[key]=source_for(key)
   continue
  for key in site['keys']:
   source,gen=source_for(key);im=Image.open(source).convert('RGBA');b=bbox(im);assert b
   root,dw=EDIT_CAL[key]if key in EDIT_CAL else(legacy[key]['source_root'],legacy[key]['source_door_width'])
   for extent,space in [(root[0]-b[0],tx-x-1),(b[2]-root[0],x+w-1-tx),(root[1]-b[1],ty-y-1),(b[3]-root[1],y+h-1-ty)]:
    if extent>0:limits.append(space*dw/extent)
   items[key]=(source,gen,im,b,root,dw)
  native_dw=min(limits)*.995
  for key,(source,gen,im,b,root,dw)in items.items():
   scale=native_dw/dw;size=(max(1,round(im.width*scale)),max(1,round(im.height*scale)));piece=im.resize(size,Image.Resampling.LANCZOS);offset=(round(tx-root[0]*scale),round(ty-root[1]*scale));frame=Image.new('RGBA',CANVAS);frame.alpha_composite(piece,offset);box=bbox(frame)
   assert box and box[0]>=x and box[1]>=y and box[2]<=x+w and box[3]<=y+h,(key,box,site['box'])
   folder=S/'buildings'/key;folder.mkdir(parents=True,exist_ok=True);out=folder/'native-frame.png';frame.save(out);frames[key]=pin(out);sources[key]=(source,gen)
   oldbox=legacy[key]['alpha_bbox'];placements[key]={'site':site['id'],'source_root':root,'source_door_width':dw,'requested_family_native_door_width':requested,'family_native_door_width':native_dw,'requested_enlargement':site['family_enlargement'],'source_uniform_scale':scale,'source_uniform_offset':list(offset),'native_anchor':site['door'],'alpha_bbox':list(box),'previous_native_bbox':oldbox,'visible_width_ratio':(box[2]-box[0])/(oldbox[2]-oldbox[0]),'visible_height_ratio':(box[3]-box[1])/(oldbox[3]-oldbox[1]),'basis':'Whole-master uniform scaling around measured frontal step/root. Shared doorway density per physical family, no independent state bbox filling.'}
 dump(S/'placement-calibration-v4.json',{'status':'authored configuration','states':placements,'native_observed':False})
 return plan,sites,frames,placements,sources
def previews(plan,sites,frames,bg,suffix):
 order={k:i for i,s in enumerate(sites)for k in s['keys']}
 def scene(name,keys):
  im=bg.copy()
  for key in sorted(keys,key=lambda k:order[k]):im.alpha_composite(Image.open(P/frames[key]['path']).convert('RGBA'))
  im.save(R/(name+suffix+'.png'));return im
 base=[s['keys'][0]for s in sites[:16]];up=[s['keys'][-1]for s in sites[:16]]
 scene('empty',[]);scene('early',['villageHall','fort','dwellingLvl1']);scene('partial',['townHall','citadel','mageGuild1','tavern','marketplace','dwellingLvl1','dwellingLvl2','dwellingLvl3','dwellingLvl4']);scene('all-base',base);scene('all-upgraded',up);scene('coastal',up+['ship']);scene('grail',up+['grail']);scene('full',up+['ship','grail'])
 sheet=Image.new('RGB',(1100,7*180),(29,33,38));draw=ImageDraw.Draw(sheet)
 for i,key in enumerate(frames):
  im=Image.open(P/frames[key]['path']);b=bbox(im);crop=im.crop(b);assert crop.width<=210 and crop.height<=150,(key,crop.size);xx=(i%5)*220;yy=(i//5)*180;sheet.paste(crop,(xx+(220-crop.width)//2,yy+175-crop.height),crop);draw.text((xx+4,yy+3),key,fill='white')
 sheet.save(R/('all35-native-contact'+suffix+'.png'))
def finish(plan,sites,frames,placements,sources):
 background=S/'landscape/native-rgba-v4.png';bg=Image.open(background).convert('RGBA');assert bg.size==CANVAS
 land=Image.new('RGBA',CANVAS,(255,255,255,255));draw=ImageDraw.Draw(land)
 for polygon in plan['water_polygons']:draw.polygon([tuple(p)for p in polygon],fill=(0,0,0,255))
 landpath=S/'landscape/dry-land-mask-v4.png';land.save(landpath)
 recipes=[];closure={S/'assemble_v4.py',S/'layout-plan-v4.json',S/'placement-calibration-v4.json',background,S/'landscape/master-v4.png',S/'landscape/prompt-v4.txt',S/'landscape/source-generation-v4.json'};icons={}
 def common(key):
  source,generation=sources[key];g=json.loads(generation.read_text());paths=[S/'assemble_v4.py',S/'layout-plan-v4.json',S/'placement-calibration-v4.json',source,generation,P/g['prompt']]
  # Expand all actual own-reference ancestors explicitly; no original-game image bytes.
  if key in EDIT_CAL:
   paths.extend([OLD/'buildings'/key/'master-v1.png',OLD/'buildings'/key/'source-generation.json',P/json.loads((OLD/'buildings'/key/'source-generation.json').read_text())['prompt']])
   parent=g.get('parent_state')
   if parent:paths.extend(sources[parent])
   if key=='dwellingLvl7':paths.extend([S/'buildings/dwellingLvl7/master-v4.png',S/'buildings/dwellingLvl7/source-generation-v4.json',S/'buildings/dwellingLvl7/prompt-v4.txt',S/'buildings/dwellingLvl7/uncrop-edit-target.png'])
  if key in ('ship','shipyard'):paths.extend([OLD/'buildings'/key/'native-frame.png',OLD/'gangway/master-v1.png',OLD/'gangway/prompt-v1.txt',OLD/'gangway/source-generation.json',OLD/'assemble.py',OLD/'layout-plan-v3.json'])
  closure.update(paths)
  return {'status':'painted-candidate','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'credits':{'author':'Project-directed OpenAI builtin imagegen; deterministic technical2D conversion','license':None,'redistribution':'unresolved; release prohibited'},'generation':{'image_generation_used':True,'provider':'OpenAI builtin imagegen','model':'not exposed by tool','prompt':(P/g['prompt']).read_text(),'prompt_file':g['prompt'],'painted_master':rel(source),'painted_master_sha256':sha(source),'producer':rel(S/'assemble_v4.py'),'producer_sha256':sha(S/'assemble_v4.py'),'source_generation_ledger':rel(generation)},'dependencies':[pin(p)for p in sorted(set(paths))]}
 for site in sites:
  for key in site['keys']:
   folder=S/'buildings'/key;frame=Image.open(P/frames[key]['path']).convert('RGBA');b=bbox(frame);alpha=frame.getchannel('A').point(lambda a:255 if a>=96 else 0);area=Image.new('RGBA',CANVAS);area.paste((255,255,255,255),(0,0),alpha);area.save(folder/'area-v4.png');edge=ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(3)),alpha);border=Image.new('RGBA',CANVAS);border.paste((240,210,100,255),(0,0),edge);border.save(folder/'border-v4.png')
   crop=frame.crop(b)
   for size,name in [((58,64),'campaign-v4.png'),((150,70),'construction-v4.png')]:
    im=Image.new('RGBA',size);piece=crop.copy();piece.thumbnail((size[0]-6,size[1]-6),Image.Resampling.LANCZOS);im.alpha_composite(piece,((size[0]-piece.width)//2,size[1]-piece.height-3));im.save(folder/name)
   c=common(key);prefix='Content/Sprites/runeterra/piltover/town/structures/'+key
   recipe={**c,'recipe_type':'vcmi_animation','canvas':list(CANVAS),'pivot':{'x':site['door'][0],'y':site['door'][1]},'generateShadow':0,'generateOverlay':0,'groups':[{'group':0,'frames':[{'source':frames[key]['path'],'source_sha256':frames[key]['sha256'],'source_canvas':list(CANVAS)}]}],'output_path':prefix+'.json'}
   rp=S/'recipes-v4'/(key+'-animation.json');dump(rp,recipe);recipes.append(rel(rp))
   for role,name,size in [('area','area-v4.png',CANVAS),('border','border-v4.png',CANVAS),('campaign','campaign-v4.png',(58,64))]:
    source=folder/name;recipe={**c,'recipe_type':'raster','canvas':list(size),'size':list(size),'source_canvas':list(size),'source':rel(source),'source_sha256':sha(source),'fit':'exact','require_alpha':True,'output_path':prefix+'_'+role+'.png'};rp=S/'recipes-v4'/(key+'-'+role+'.json');dump(rp,recipe);recipes.append(rel(rp))
   icons[key]=folder/'construction-v4.png'
 sys.path.insert(0,str(W/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('piltover');ids=compiler.indexed_building_ids(P)
 c=common('capitol');c['dependencies']=[pin(p)for p in sorted(closure)]+[pin(p)for p in icons.values()]
 recipe={**c,'recipe_type':'indexed_animation','canvas':[150,70],'pivot':{'x':75,'y':35},'generateShadow':0,'generateOverlay':0,'frames':[{'building':key,'frame':index,'source':rel(icons[key]),'source_sha256':sha(icons[key]),'source_canvas':[150,70]}for key,index in sorted(ids.items(),key=lambda x:x[1])],'output_path':'Content/Sprites/runeterra/piltover/town/buildingIcons.json'}
 rp=S/'recipes-v4/buildingIcons.json';dump(rp,recipe);recipes.append(rel(rp))
 g=json.loads((S/'landscape/source-generation-v4.json').read_text());recipe={**c,'recipe_type':'raster','canvas':list(CANVAS),'size':list(CANVAS),'source_canvas':list(CANVAS),'source':rel(background),'source_sha256':sha(background),'fit':'exact','require_alpha':False,'output_path':'Content/Sprites/runeterra/piltover/town/background.png','generation':{'image_generation_used':True,'provider':'OpenAI builtin imagegen','model':'not exposed by tool','prompt':(S/'landscape/prompt-v4.txt').read_text(),'prompt_file':rel(S/'landscape/prompt-v4.txt'),'painted_master':rel(S/'landscape/master-v4.png'),'painted_master_sha256':sha(S/'landscape/master-v4.png'),'producer':rel(S/'assemble_v4.py'),'producer_sha256':sha(S/'assemble_v4.py'),'source_generation_ledger':rel(S/'landscape/source-generation-v4.json')}}
 rp=S/'recipes-v4/background.json';dump(rp,recipe);recipes.append(rel(rp));assert len(recipes)==142
 outsites=[]
 for site in sites:
  x,y,w,h=site['box'];outsites.append({'id':'grail'if site['id']=='beacon'else site['id'],'box':site['box'],'states':site['keys'],'entrance':site['door'],'foundation_polygon':[[x+1,y+h-4],[x+w-1,y+h-4],[x+w-1,y+h-1],[x+1,y+h-1]],'depth':site['depth'],'intentional_water':site['id']=='coast'})
 dump(S/'layout-acceptance-contract-v4.json',{'canvas':list(CANVAS),'alpha_threshold':8,'background':pin(background),'land_mask':pin(landpath),'sites':outsites,'frames':frames,'roads':plan['roads'],'land_mask_basis':'Frozen-plan technical proxy; actual native source compositions inspected separately','native_observed':False,'visual_approval_granted':False})
 dump(S/'candidate-recipes-v4.json',{'status':'authored configuration','recipes':recipes,'native_observed':False,'release_accepted':False});dump(S/'source-inputs-v4.json',{'status':'authored configuration','files':[pin(p)for p in sorted(closure)],'licensed_reference_bytes_exported':False,'native_observed':False})
 previews(plan,sites,frames,bg,'-v4')
 html='<html><head><meta charset="utf-8"><title>Piltover V4 hextech town</title><style>body{background:#171c24;color:#eee;font:16px sans-serif}img{display:block;max-width:100%;margin:12px 0}</style></head><body><h1>Piltover V4: enlargement and hextech</h1><p>Authored configuration. Native-size source compositions, no native screenshot/release claim. Original35masters preserved;9genuine painted edits,16ordinarysites, optionalcoast/Grail. All35 construction/mask/border/campaign sources and real indexedHALL updated together.</p>'
 for name in ['current-compiled-full','full-v4','empty-v4','early-v4','partial-v4','all-base-v4','all-upgraded-v4','coastal-v4','grail-v4','all35-native-contact-v4']:html+='<h2>'+name+'</h2><img src="'+name+'.png">'
 (R/'index.html').write_text(html+'</body></html>',encoding='utf-8');print(json.dumps({'status':'authored configuration','states':35,'recipes':142,'contract_sha256':sha(S/'layout-acceptance-contract-v4.json')}))
def main():
 a=argparse.ArgumentParser();a.add_argument('--geometry-only',action='store_true');args=a.parse_args();R.mkdir(parents=True,exist_ok=True);plan,sites,frames,placements,sources=render()
 if args.geometry_only:
  previews(plan,sites,frames,Image.open(OLD/'landscape/native-rgba.png').convert('RGBA'),'-actual-masters-before-bg');print(json.dumps({'actual_states_measured':len(frames),'background':'old V3 context only; new V4 background still required','geometry_only':True}))
 else:finish(plan,sites,frames,placements,sources)
if __name__=='__main__':main()
