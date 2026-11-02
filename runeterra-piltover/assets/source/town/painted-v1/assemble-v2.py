"""Deterministic technical conversion of genuine painted Piltover building sources.

No art generation: uniform calibrated scaling, translation, alpha masks and icon crops.
Writes only this candidate source namespace and a uniquely named candidate report.
"""
import hashlib,json,math,shutil,sys
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter,ImageDraw
S=Path(__file__).resolve().parent
P=S.parents[3]
W=P.parent
R=W/'build/reports/piltover-implementation-20261025-v1/town/assembled-v2'
CANVAS=(800,374)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(P).as_posix()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def alpha_box(im):return im.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()
def pin(p):return {'path':rel(p),'sha256':sha(p)}

# Observed frontal-step centre and doorway width as fractions of source width.
# Different provider canvas dimensions require door-based source-density calibration;
# every state at one physical site shares ONE native pixels-per-door-width value.
CAL={
 'capitol':(.478,.145),'cityHall':(.478,.145),'townHall':(.478,.145),'villageHall':(.478,.145),
 'fort':(.49,.24),'citadel':(.49,.24),'castle':(.49,.24),
 'mageGuild1':(.45,.15),'mageGuild2':(.45,.15),'mageGuild3':(.45,.15),
 'tavern':(.48,.17),'marketplace':(.42,.14),'blacksmith':(.45,.27),'resourceSilo':(.38,.16),
 'special3':(.33,.21),'special4':(.39,.14),
 'dwellingLvl1':(.40,.14),'special1':(.40,.14),'dwellingUpLvl1':(.40,.14),
 'dwellingLvl2':(.43,.12),'dwellingUpLvl2':(.43,.12),
 'dwellingLvl3':(.58,.23),'special2':(.58,.23),'dwellingUpLvl3':(.58,.23),
 'dwellingLvl4':(.32,.12),'dwellingUpLvl4':(.32,.12),
 'dwellingLvl5':(.45,.14),'dwellingUpLvl5':(.45,.14),
 'dwellingLvl6':(.36,.11),'dwellingUpLvl6':(.36,.11),
 'dwellingLvl7':(.52,.38),'dwellingUpLvl7':(.52,.38),
 'shipyard':(.48,.15),'ship':(.57,.12),'grail':(.43,.20)}

def main():
 plan=json.loads((S/'layout-plan-v2.json').read_text())
 sites=plan['sites']+[dict(plan['coastal_site'],depth=184),dict(plan['optional_grail'],keys=['grail'],door=[508,260],approach=[525,270])]
 assert len(sites)==18 and sum(len(x['keys'])for x in sites)==35
 R.mkdir(parents=True,exist_ok=True)
 land=Image.new('L',CANVAS,255);d=ImageDraw.Draw(land)
 for polygon in plan['water_polygons']:d.polygon([tuple(x)for x in polygon],fill=0)
 landpath=S/'landscape/dry-land-mask.png';land.save(landpath)
 background=S/'landscape/native-rgba.png'
 bg=Image.open(background).convert('RGBA');assert bg.size==CANVAS
 recipes=[];frames={};placements={};outsites=[];deps=[S/'assemble.py',S/'layout-plan-v2.json',background,landpath]
 for site in sites:
  x,y,w,h=site['box'];tx,ty=site['door'];family={};limits=[]
  padding=1 if site['id'] in {'museum','handlers','wardens','rifles','silo','artificers','lifters'} else 4
  for key in site['keys']:
   source=S/'buildings'/key/'master-v1.png';im=Image.open(source).convert('RGBA');box=alpha_box(im)
   assert box and im.getchannel('A').getextrema()==(0,255),(key,'alpha')
   xf,dwf=CAL[key];root=(im.width*xf,box[3]-2);doorw=im.width*dwf
   if site['id']=='coast':root=(box[2]-2,box[3]-2)
   l,t,r,b=box
   # Full opaque/semialpha roof, step and shadow extent, four-pixel internal margin.
   for extent,space in [(root[0]-l,tx-x-padding),(r-root[0],x+w-padding-tx),(root[1]-t,ty-y-padding),(b-root[1],y+h-padding-ty)]:
    if extent>0:limits.append(space*doorw/extent)
   family[key]=(source,im,box,root,doorw)
  native_door_width=min(limits)*.985
  for key,(source,im,box,root,doorw)in family.items():
   scale=native_door_width/doorw
   # Resample the entire genuine painting uniformly. No stretching or separate parts.
   size=(max(1,round(im.width*scale)),max(1,round(im.height*scale)))
   piece=im.resize(size,Image.Resampling.LANCZOS)
   offset=(round(tx-root[0]*scale),round(ty-root[1]*scale))
   frame=Image.new('RGBA',CANVAS);frame.alpha_composite(piece,offset)
   actual=alpha_box(frame);assert actual and actual[0]>=x and actual[1]>=y and actual[2]<=x+w and actual[3]<=y+h,(key,actual,site['box'])
   folder=S/'buildings'/key;fp=folder/'native-frame.png';frame.save(fp)
   mask=frame.getchannel('A').point(lambda a:255 if a>=96 else 0)
   area=Image.new('RGBA',CANVAS);area.paste((255,255,255,255),(0,0),mask);ap=folder/'area.png';area.save(ap)
   edge=ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(3)),mask)
   border=Image.new('RGBA',CANVAS);border.paste((240,210,100,255),(0,0),edge);bp=folder/'border.png';border.save(bp)
   crop=frame.crop(actual)
   def icon(size,name):
    out=Image.new('RGBA',size);small=crop.copy();small.thumbnail((size[0]-6,size[1]-6),Image.Resampling.LANCZOS);out.alpha_composite(small,((size[0]-small.width)//2,size[1]-small.height-3));p=folder/name;out.save(p);return p
   cp=icon((58,64),'campaign.png');ip=icon((150,70),'construction.png')
   gen=json.loads((folder/'source-generation.json').read_text())
   inherited=[source,folder/'source-generation.json',P/gen['prompt']]
   if (folder/'padded-edit-reference.png').exists():inherited.append(folder/'padded-edit-reference.png')
   deps.extend(inherited)
   common={'status':'painted-candidate','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,
    'credits':{'author':'Project-directed OpenAI builtin imagegen; deterministic technical 2D conversion','license':None,'redistribution':'unresolved; release prohibited'},
    'generation':{'image_generation_used':True,'provider':'OpenAI builtin imagegen','model':'not exposed by tool','prompt':(P/gen['prompt']).read_text(),'painted_master':rel(source),'painted_master_sha256':sha(source),'producer':rel(S/'assemble.py'),'producer_sha256':sha(S/'assemble.py'),'prompt_file':gen['prompt'],'source_generation_ledger':rel(folder/'source-generation.json')},
    'dependencies':[pin(p)for p in [S/'assemble.py',S/'layout-plan-v2.json']+inherited]}
   prefix='Content/Sprites/runeterra/piltover/town/structures/'+key
   anim={**common,'recipe_type':'vcmi_animation','canvas':list(CANVAS),'pivot':{'x':tx,'y':ty},'generateShadow':0,'generateOverlay':0,'groups':[{'group':0,'frames':[{'source':rel(fp),'source_sha256':sha(fp),'source_canvas':list(CANVAS)}]}],'output_path':prefix+'.json'}
   rp=S/'recipes'/(key+'-animation.json');dump(rp,anim);recipes.append(rel(rp))
   for suffix,p,size in [('area',ap,CANVAS),('border',bp,CANVAS),('campaign',cp,(58,64))]:
    output=prefix+'_'+suffix+'.png' if suffix!='construction' else 'Content/Sprites/runeterra/piltover/town/construction/'+key+'.png'
    rec={**common,'recipe_type':'raster','source':rel(p),'source_sha256':sha(p),'source_canvas':list(size),'canvas':list(size),'size':list(size),'fit':'exact','require_alpha':True,'output_path':output}
    rp=S/'recipes'/(key+'-'+suffix+'.json');dump(rp,rec);recipes.append(rel(rp))
   frames[key]=pin(fp);placements[key]={'site':site['id'],'source_root':list(root),'source_door_width':doorw,'family_native_door_width':native_door_width,'uniform_scale':scale,'translated_offset':list(offset),'alpha_bbox':list(actual),'native_door':site['door'],'opaque_interior_policy':'provider-painted material; no global alpha key applied'}
  foundation=[[x+4,y+h-10],[x+w-4,y+h-10],[x+w-4,y+h-4],[x+4,y+h-4]]
  outsites.append({'id':'grail'if site['id']=='beacon'else site['id'],'box':site['box'],'states':site['keys'],'entrance':site['door'],'foundation_polygon':foundation,'depth':site['depth'],'intentional_water':site['id']=='coast'})
 # One actual native-ID-indexed HALL consumer; the35 per-state150x70 files stay source-only.
 sys.path.insert(0,str(W/'scripts'))
 import faction_art_compile
 compiler=faction_art_compile.create_compiler('piltover')
 ids=compiler.indexed_building_ids(P)
 indexed={**common,'recipe_type':'indexed_animation','canvas':[150,70],'pivot':{'x':75,'y':35},'generateShadow':0,'generateOverlay':0,'frames':[{'building':key,'frame':index,'source':rel(S/'buildings'/key/'construction.png'),'source_sha256':sha(S/'buildings'/key/'construction.png'),'source_canvas':[150,70]}for key,index in sorted(ids.items(),key=lambda x:x[1])],'output_path':'Content/Sprites/runeterra/piltover/town/buildingIcons.json','generation':{'image_generation_used':True,'provider':'OpenAI builtin imagegen; technical2D conversion','model':'not exposed by tool','prompt':'Every indexed icon derives from its own genuine painted building master and saved exact state prompt. Frame numbers are actual native building IDs, preserving gaps.','painted_master':rel(S/'buildings/capitol/master-v1.png'),'painted_master_sha256':sha(S/'buildings/capitol/master-v1.png'),'producer':rel(S/'assemble.py'),'producer_sha256':sha(S/'assemble.py')},'dependencies':[pin(S/'assemble.py')]+[pin(S/'buildings'/key/name)for key in ids for name in ['master-v1.png','source-generation.json','native-frame.png','construction.png']]}
 rp=S/'recipes/buildingIcons.json';dump(rp,indexed);recipes.append(rel(rp))
 # Background raster source is independently pinned; public export contains no original reference bytes.
 rec={**common,'recipe_type':'raster','source':rel(background),'source_sha256':sha(background),'source_canvas':list(CANVAS),'canvas':list(CANVAS),'size':list(CANVAS),'fit':'exact','require_alpha':False,'output_path':'Content/Sprites/runeterra/piltover/town/background.png','visual_approval_granted':False,'generation':{'image_generation_used':True,'provider':'OpenAI builtin imagegen','model':'not exposed by tool','prompt':(S/'landscape/prompt-v2.txt').read_text(),'prompt_file':rel(S/'landscape/prompt-v2.txt'),'painted_master':rel(S/'landscape/master-v2.png'),'painted_master_sha256':sha(S/'landscape/master-v2.png'),'producer':rel(S/'assemble.py'),'producer_sha256':sha(S/'assemble.py')},'dependencies':[pin(p)for p in [S/'landscape/master-v2.png',S/'landscape/prompt-v2.txt',S/'landscape/master-v1.png',S/'landscape/prompt-v1.txt',S/'assemble.py']]}
 rp=S/'recipes/background.json';dump(rp,rec);recipes.append(rel(rp))
 dump(S/'placement-calibration-v1.json',{'status':'authored configuration','method':'Observed entrance/root and doorway-density calibration; one uniform source scale per state and one physical doorway scale shared by every state of each site. No independent per-state bbox filling.','states':placements})
 dump(S/'layout-acceptance-contract-v1.json',{'canvas':list(CANVAS),'alpha_threshold':8,'background':pin(background),'land_mask':pin(landpath),'sites':outsites,'frames':frames,'roads':plan['roads'],'land_mask_basis':'technical frozen-plan proxy; actual painted foundations and doors require visual review','native_observed':False,'visual_approval_granted':False})
 dump(S/'candidate-recipes.json',{'status':'authored configuration','recipes':recipes,'native_observed':False,'release_accepted':False})
 # Each configuration selects one visible state per plot; none bake functional art into terrain.
 def scene(name,keys):
  im=bg.copy()
  order={k:i for i,s in enumerate(sites)for k in s['keys']}
  for key in sorted(keys,key=lambda k:order[k]):im.alpha_composite(Image.open(P/frames[key]['path']).convert('RGBA'))
  im.save(R/(name+'.png'));return im
 base=[s['keys'][0]for s in sites[:16]];up=[s['keys'][-1]for s in sites[:16]]
 scene('empty',[]);scene('early',['villageHall','fort','dwellingLvl1']);scene('partial',['townHall','citadel','mageGuild1','tavern','marketplace','dwellingLvl1','dwellingLvl2','dwellingLvl3','dwellingLvl4']);scene('all-base',base);scene('all-upgraded',up);scene('coastal',up+['ship']);scene('grail',up+['grail']);scene('full',up+['ship','grail'])
 sheet=Image.new('RGB',(1100,math.ceil(35/5)*180),(29,33,38));draw=ImageDraw.Draw(sheet)
 for i,key in enumerate(frames):
  im=Image.open(P/frames[key]['path']);box=alpha_box(im);piece=im.crop(box);assert piece.width<=210 and piece.height<=150;xx=(i%5)*220;yy=(i//5)*180;sheet.paste(piece,(xx+(220-piece.width)//2,yy+175-piece.height),piece);draw.text((xx+4,yy+3),key,fill='white')
 sheet.save(R/'all35-native-contact.png')
 # Public portability closure excludes private receipts and licensed native inputs.
 deps.extend([S/'landscape/master-v1.png',S/'landscape/master-v2.png',S/'landscape/prompt-v1.txt',S/'landscape/prompt-v2.txt',S/'state-briefs.json'])
 dump(S/'source-inputs.json',{'status':'authored configuration','files':[pin(p)for p in sorted(set(deps))],'native_references':'original Castle measured/viewed privately; their hashes appear in generation ledgers, bytes excluded','official_crest_url':'https://universe.leagueoflegends.com/images/piltover_crest_icon@2x.png','native_observed':False,'release_accepted':False})
 dump(R/'conversion-checks.json',{'status':'authored configuration','ordinary_sites':16,'total_states':35,'actual_alpha_inside_frozen_box':True,'full_canvas':[800,374],'native_observed':False,'visual_approval_granted':False,'recipes':len(recipes),'frames':frames})
 html='<html><head><meta charset="utf-8"><title>Piltover town source candidate</title><style>body{background:#171c24;color:#eee;font:16px sans-serif}img{display:block;max-width:100%;margin:12px 0}figure{margin:16px 0}</style></head><body><h1>Piltover: painted 2D town candidate</h1><p>Authored configuration. Native-size source compositions, not in-game screenshots or release acceptance. Sixteen ordinary plots; optional quay and Grail separately reserved. Every building is an actual independent painted layer.</p>'
 for name in ['empty','early','partial','all-base','all-upgraded','coastal','grail','full','all35-native-contact']:html+='<figure><figcaption>'+name+'</figcaption><img src="'+name+'.png"></figure>'
 (R/'index.html').write_text(html+'</body></html>',encoding='utf-8')
 print(json.dumps({'states':len(frames),'recipes':len(recipes),'report':str(R),'contract_sha256':sha(S/'layout-acceptance-contract-v1.json')}))
if __name__=='__main__':main()
