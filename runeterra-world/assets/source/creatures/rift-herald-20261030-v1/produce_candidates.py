"""Complete painted Rift Herald candidate; no shared selections or staging."""
from pathlib import Path
import copy,hashlib,json,sys,importlib.util,base64
from PIL import Image,ImageOps,ImageDraw
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-world')
ROOT=PROJECT.parent
REPORT=ROOT/'reports/world-rift-herald-art-20261030-v1'
EXTRACTOR=PROJECT/'assets/source/creatures/painted-v1/northern-desert/extract_sources.py'
GROUPS={0:('motion',[4,5,6,7,8,9,10,11]),1:('motion',[0,1,2,1,3,0]),2:('motion',[0]),3:('combat',[12,0]),4:('combat',[13]),5:('death',[0,1,2,3]),7:('combat',[0,14,15]),8:('combat',[15,14,0]),11:('combat',[0,1,2,3]),12:('combat',[4,5,6,7]),13:('combat',[8,9,10,11]),22:('death',[3])}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def box(im):return im.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()
def main():
 REPORT.mkdir(parents=True,exist_ok=True)
 spec=importlib.util.spec_from_file_location('herald_component_extractor',EXTRACTOR);extract=importlib.util.module_from_spec(spec);spec.loader.exec_module(extract);extract.BASE=HERE.parent;extract.PROJECT=PROJECT
 cohorts={name:extract.process(HERE.name,name,name+'-v1.png',count,4)for name,count in [('motion',12),('combat',16),('death',4)]}
 assert not any(r['principal_touches_source_edge']for rows in cohorts.values()for r in rows),'Whole source actor clipping'
 roots={'battle_root':[218,266],'map_root':[63,56],'encounter_root':[32,56],'portrait_crop':[18,128,866,1129],
 'motion':{'scale':.4,'roots':[[200,339],[560,341],[920,341],[1280,341],[200,685],[560,694],[920,700],[1280,686],[200,1040],[560,1033],[920,1033],[1280,1035]]},
 'combat':{'scale':.4,'roots':[[200,329],[560,323],[920,322],[1280,331],[200,591],[560,577],[920,592],[1280,592],[200,844],[560,848],[920,861],[1280,852],[200,1070],[560,1068],[910,1072],[1280,1076]]},
 'death':{'scale':.28,'roots':[[260,620],[790,627],[1320,605],[1850,602]]},
 'method':'Visually annotated grounded support projections and fixed whole-cohort scales; no per-frame zoom or bodywarp. Four limbs alternate support during heavy grounded crawl. Actual originalHoMM3 control viewed read-only. Portrait uses the complete main painted panel; generated secondary panel stays preserved outside the native crop.'}
 dump(HERE/'pose-roots-v1.json',roots);dump(HERE/'isolated-source-map-v1.json',cohorts)
 masters=[HERE/(name+'-v1.png')for name in ['motion','combat','death','portrait','site']]
 dump(HERE/'generation-ledger-v1.json',{'status': 'authored configuration', 'provider': 'OpenAI built-in imagegen', 'model': 'not exposed', 'method': 'New original painted2D masters from text; combat/death/portrait use only own generatedmotion identityreference. Fixedwholeactor componentisolation, technicalalpha/rootregistration, no3D/paintover/copiedoriginal pixels.', 'canonical_basis': 'Riot2024gameplaypreview establishes Voidgrub-inspired Herald and controlledcharge inLeague. Projectuses one unique living groundedphysicalmelee Herald boss, not a massrecruitable species.', 'project_adaptation': 'Fourgroundedlimbs, layeredpurplechitin, magentaeyenodules, yellowivorytusks andheavyforeclaws. No chargewall damage, flight, burrow, projectile, spawn, piloting, globalsiege buff or free item inferred. RiftPit finite localcacheguard is projectadaptation.', 'lore_sources': ['https://www.leagueoflegends.com/en-us/news/game-updates/2024-gameplay-preview/', 'https://www.leagueoflegends.com/en-us/news/game-updates/patch-14-1-notes/', 'https://www.leagueoflegends.com/en-us/news/dev/dev-cat-cults-rift-mechs-and-baron-s-revamp/'], 'subject_reference': {'title': '2024GameplayPreview / RiftHeraldNormalView', 'author': 'SummonersRiftTeam', 'publication': '2023-11-20', 'accessed': '2026-10-30', 'url': 'https://cmsassets.rgpub.io/sanity/images/dsfx7636/news/58f66a838ea927d3c92afbde52b84687d4ca20e0-439x378.png', 'private_image_sha256': 'fb7be942de4f474ba5e70ef33bbef6f2567b03cb28e078e81d275198fb978563', 'observed': 'Broadpurpleoverlappingcarapace, magentaeye nodules, curvedyellowivoryhorns/tusks, darksegmentedlimbs, upcurledshorttail. Newpaintedinterpretationretains organic mass andshell motifs; officialimagekeptprivate.'}, 'native_style_reference': {'path': 'runeterra-demacia/references/sheets/creature-battle-08.png', 'sha256': '2fe61ce5343485f82784eed774c79ad9bc688a465b3c928b61003f0d50b415ad', 'observed': 'OriginalCastle sword/zealot nativeactioncontrol, compactmattepaint, upperleftlight andsupported articulation; no troop pixels copied.'}, 'rights': 'Newproject-directed generatedart; RiotGames owns relatedRuneterra/Leagueconcepts/designs. No externalrightsapprovalasserted.', 'visual_approval_granted': False}|{'sources':[{'path':rel(p),'sha256':sha(p)}for p in masters]})
 deps=masters+[Path(__file__),EXTRACTOR,HERE/'pose-roots-v1.json',HERE/'isolated-source-map-v1.json',HERE/'generation-ledger-v1.json']+list(HERE.glob('*.prompt.txt'))+[PROJECT/r['image']for rows in cohorts.values()for r in rows]
 def common(master,prompt):return {'production_status':'painted-master-complete-unapproved','generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed','prompt':prompt.read_text(encoding='utf8'),'painted_master':rel(master),'painted_master_sha256':sha(master),'method':'Whole painted actor/component isolation and fixed cohortscale/root registration, no bodypaint, posewarp or individualzoom.'},'production_inputs':[{'path':rel(p),'sha256':sha(p)}for p in sorted(set(deps))]}
 def render(name,i,canvas,root,mult=1,mirror=False):
  row=cohorts[name][i];assert sha(PROJECT/row['image'])==row['sha256'];im=Image.open(PROJECT/row['image']);source_root=roots[name]['roots'][i];scale=roots[name]['scale']*mult
  local=[source_root[n]-row['crop'][n]for n in (0,1)];im=im.resize(tuple(round(v*scale)for v in im.size),Image.Resampling.LANCZOS);offset=[root[n]-round(local[n]*scale)for n in (0,1)]
  if mirror:im=ImageOps.mirror(im);offset[0]=root[0]-(im.width-1-round(local[0]*scale))
  b=box(im);assert b and 0<=offset[0]+b[0]<offset[0]+b[2]<=canvas[0]and 0<=offset[1]+b[1]<offset[1]+b[3]<=canvas[1],(name,i,offset,b)
  result=Image.new('RGBA',canvas);result.alpha_composite(im,tuple(offset));return result
 def descriptor(p,f=0):return {'frame':f,'source':rel(p),'sha256':sha(p),'source_sha256':sha(p),'source_canvas':list(Image.open(p).size)}
 recipes=[];frames=[]
 def recipe(role,data,master=masters[0],prompt=HERE/'motion-v1.prompt.txt'):
  p=HERE/'candidate-recipes'/(role+'.recipe.json');dump(p,{**common(master,prompt),**data});recipes.append(p)
 groups=[]
 for group,(cohort,order)in sorted(GROUPS.items()):
  entries=[]
  for f,i in enumerate(order):
   actual='motion'if(group==3 and f==1)or(group==7 and f==0)or(group==8 and f==2)else cohort
   im=render(actual,i,(450,400),(218,266));p=HERE/'native/battle'/f'g{group:02d}-f{f:03d}.png';save(p,im);entries.append(descriptor(p,f));frames.append({'group':group,'frame':f,'cohort':actual,'source_pose':i,'source':rel(p),'bbox':box(im),'sha256':sha(p)})
  groups.append({'group':group,'generateShadow':1,'generateOverlay':0,'frames':entries})
 recipe('battle',{'recipe_type':'vcmi_animation','output_path':'Content/Sprites/runeterra/world/creatures/riftHerald/battle.json','canvas':[450,400],'pivot':{'x':218,'y':266},'groups':groups})
 entries=[]
 for f,i in enumerate([0,1,2,1,3,0]):
  im=render('motion',i,(96,64),(63,56),.35,True);assert box(im)[0]>=32;p=HERE/'native/map'/f'g00-f{f:03d}.png';save(p,im);entries.append(descriptor(p,f))
 recipe('map',{'recipe_type':'vcmi_animation','output_path':'Content/Sprites/runeterra/world/creatures/riftHerald/map.json','canvas':[96,64],'pivot':{'x':61,'y':56},'groups':[{'group':0,'generateShadow':1,'generateOverlay':0,'frames':entries}]})
 for role,mirror in [('attackLeft',False),('attackRight',True)]:
  im=render('combat',4,(64,64),(31 if mirror else 32,56),.35,mirror);p=HERE/'native'/(role+'.png');save(p,im);recipe(role,{'recipe_type':'raster','output_path':f'Content/Sprites/runeterra/world/creatures/riftHerald/{role}.png','canvas':[64,64],**descriptor(p),'fit':'exact'})
 for role,size in [('large',(58,64)),('small',(32,32))]:
  p=HERE/'native'/(role+'.png');save(p,ImageOps.fit(Image.open(HERE/'portrait-v1.png').convert('RGBA').crop(tuple(roots['portrait_crop'])),size,Image.Resampling.LANCZOS));recipe(role,{'recipe_type':'raster','output_path':f'Content/Sprites/runeterra/world/creatures/riftHerald/{role}.png','canvas':list(size),**descriptor(p),'fit':'exact'},HERE/'portrait-v1.png',HERE/'portrait-v1.prompt.txt')
 site=Image.open(HERE/'site-v1.png').convert('RGBA');b=box(site);assert b and b[0]>0 and b[1]>0 and b[2]<site.width and b[3]<site.height
 actor=site.crop(b);actor.thumbnail((88,88),Image.Resampling.LANCZOS);site=Image.new('RGBA',(96,96));site.alpha_composite(actor,((96-actor.width)//2,94-actor.height));p=HERE/'native/site.png';save(p,site)
 recipe('site',{'recipe_type':'vcmi_animation','output_path':'Content/Sprites/runeterra/world/sites/riftPit/map.json','canvas':[96,96],'pivot':{'x':48,'y':94},'groups':[{'group':0,'generateShadow':1,'generateOverlay':0,'frames':[descriptor(p)]}]},HERE/'site-v1.png',HERE/'site-v1.prompt.txt')
 dump(HERE/'site-calibration.json',{'status':'authored configuration','id':'riftPit','canvas':[96,96],'mask':['VVV','BBB','BAB'],'visitableFrom':['---','---','-+-'],'allowedTerrains':['dirt','rough'],'native_bbox':box(site),'native_sha256':sha(p),'rmg':False,'native_execution':'not_run'})
 assert ImageOps.mirror(Image.open(HERE/'native/attackLeft.png')).tobytes()==Image.open(HERE/'native/attackRight.png').tobytes()
 assert Image.open(HERE/'native/battle/g05-f003.png').tobytes()==Image.open(HERE/'native/battle/g22-f000.png').tobytes()
 sys.path.insert(0,str(ROOT/'scripts'));import faction_art_compile,runeterra_world
 compiler=faction_art_compile.create_compiler('world');outputs={};receipts=[];checks=[]
 for p in recipes:
  data=json.loads(p.read_text());dependencies=runeterra_world.recipe_dependencies(PROJECT,data);a,receipt=compiler.plan(PROJECT,p);b,_=compiler.plan(PROJECT,p);assert a==b
  for key in ['production','master']:
   bad=copy.deepcopy(data)
   if key=='production':bad['production_inputs'][0]['sha256']='0'*64
   else:bad['generation']['painted_master_sha256']='0'*64
   try:runeterra_world.recipe_dependencies(PROJECT,bad)
   except ValueError:pass
   else:raise AssertionError('Source pin mutation accepted')
  for name,raw in a.items():
   assert name not in outputs;outputs[name]=hashlib.sha256(raw).hexdigest();target=REPORT/'compiled-candidates'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
  checks.append({'recipe':rel(p),'dependency_count':len(dependencies),'consumer_privacy':'passed','negative_source_pin_mutations_rejected':2,'double_real_assembly_identical':True});receipts.append(receipt)
 dump(REPORT/'technical-verification.json',{'status':'authored configuration','recipes':[rel(p)for p in recipes],'recipe_count':len(recipes),'compiled_outputs':outputs,'compiled_output_count':len(outputs),'battle_frames':len(frames),'battle_groups':{str(g):len(o)for g,(_,o)in GROUPS.items()},'source_consumer_checks':checks,'source_cross_contamination':0,'whole_actor_clip_count':0,'encounter_pixel_mirror':True,'persistent_corpse_matches_final_death':True,'native_runtime':'not_run','visual_approval_granted':False,'release_accepted':False,'receipts':receipts})
 board=Image.new('RGB',(1050,((len(frames)+4)//5)*160),(65,67,56));draw=ImageDraw.Draw(board)
 for n,r in enumerate(frames):
  x=(n%5)*210;y=(n//5)*160;draw.text((x+4,y+4),f"g{r['group']} f{r['frame']}",fill='white');im=Image.open(PROJECT/r['source']).crop((110,135,320,275));board.paste(im,(x,y+18),im)
 save(REPORT/'native-action-sheet.png',board)
 siteboard=Image.new('RGB',(384,220),(57,63,52));siteboard.paste(site,(5,70),site);zoom=site.resize((192,192),Image.Resampling.NEAREST);siteboard.paste(zoom,(145,10),zoom);save(REPORT/'native-site.png',siteboard)
 payload={str(g):[base64.b64encode((PROJECT/r['source']).read_bytes()).decode()for r in frames if r['group']==g]for g in GROUPS}
 html='''<!doctype html><meta charset="utf-8"><title>Rift Herald painted candidates</title><style>body{background:#20241f;color:#eee;font:16px system-ui;max-width:1080px;margin:auto}img{max-width:100%}canvas{background:#414338;image-rendering:pixelated}button{margin:4px}</style><h1>Rift Herald complete grounded painted action candidate</h1><p>Authored configuration. Unique living grounded two-hex physical-melee boss. No flight, burrow, projectile, charge-wall damage, free spawn or siege buff. Not native gameplay or release acceptance.</p><img src="native-site.png"><img src="native-action-sheet.png"><p>Actual delivered450Ã—400 frames; browser timing is illustrative. Group0 shows eight actual grounded crawl poses; no flight or takeoff groups are supplied. Groups11/12/13 explicitly bind up/front/down attack rows1/2/3.</p><div id="buttons"></div><canvas width="450" height="400"></canvas><p><a href="technical-verification.json">Actual source/consumer and double-assembly evidence</a></p><script>const sets=DATA;let active='0',i=0;const cache={};for(const[g,frames]of Object.entries(sets)){cache[g]=frames.map(s=>{const im=new Image;im.src='data:image/png;base64,'+s;return im});const b=document.createElement('button');b.textContent='Group '+g;b.onclick=()=>{active=g;i=0};document.querySelector('#buttons').append(b)}setInterval(()=>{const c=document.querySelector('canvas'),x=c.getContext('2d');x.clearRect(0,0,450,400);const a=cache[active];x.drawImage(a[i++%a.length],0,0)},180)</script>'''
 (REPORT/'index.html').write_text(html.replace('DATA',json.dumps(payload)),encoding='utf8');print(json.dumps({'recipes':len(recipes),'compiled_outputs':len(outputs),'battle_frames':len(frames),'report':str(REPORT)}))
if __name__=='__main__':main()


