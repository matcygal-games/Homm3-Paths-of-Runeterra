"""Complete painted Baron Nashor candidate; no shared selections or staging."""
from pathlib import Path
import copy,hashlib,json,sys,importlib.util,base64,io,os
from PIL import Image,ImageOps,ImageDraw
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-world')
ROOT=next(p for p in HERE.parents if (p/'scripts/faction_art_compile.py').is_file())
REPORT=ROOT/'reports/world-baron-nashor-art-20261030-v1'
EXTRACTOR=HERE/'extract_sources_atomic.py'
GROUPS={0:('motion',[4,5,6,7]),1:('motion',[0,1,2,1,3,0]),2:('motion',[0]),3:('combat',[12,0]),4:('combat',[13]),5:('death',[0,1,2,3]),7:('combat',[0,14,15]),8:('combat',[15,14,0]),11:('combat',[0,1,2,3]),12:('combat',[4,5,6,7]),13:('combat',[8,9,10,11]),22:('death',[3])}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def atomic(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True);temp=REPORT/'.atomic'/(hashlib.sha256(str(p).encode()).hexdigest()+'.pending');temp.parent.mkdir(parents=True,exist_ok=True);temp.write_bytes(raw);os.replace(temp,p)
def dump(p,v):atomic(p,(json.dumps(v,indent=2,sort_keys=True)+'\n').encode())
def save(p,im):
 buffer=io.BytesIO();im.save(buffer,format='PNG',compress_level=9);atomic(p,buffer.getvalue())
def box(im):return im.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()
def main():
 REPORT.mkdir(parents=True,exist_ok=True)
 spec=importlib.util.spec_from_file_location('baron_component_extractor',EXTRACTOR);extract=importlib.util.module_from_spec(spec);spec.loader.exec_module(extract);extract.BASE=HERE.parent;extract.PROJECT=PROJECT
 cohorts={name:extract.process(HERE.name,name,name+'-v1.png',count,2 if name=='death' else 4)for name,count in [('motion',8),('combat',16),('death',4)]}
 assert not any(r['principal_touches_source_edge']for rows in cohorts.values()for r in rows),'Whole source actor clipping'
 roots={'battle_root':[218,266],'map_root':[63,56],'encounter_root':[35,56],
 'motion':{'scale':.46,'roots':[[300,438],[743,438],[1186,438],[1629,438],[300,828],[743,829],[1186,829],[1629,830]]},
 'combat':{'scale':.58,'roots':[[250,256],[634,258],[1018,260],[1402,258],[250,499],[634,499],[1018,503],[1402,503],[250,747],[634,746],[1018,745],[1402,746],[250,1006],[634,997],[1018,1001],[1402,1006]]},
 'death':{'scale':.32,'roots':[[400,555],[1120,571],[400,921],[1120,914]]},
 'method':'Visually annotated lowest supporting coil projections in full painted source sheets. Uniform fixed whole-cohort scales; no per-frame fitting, body painting or pose warping. Every movement pose remains ground-supported. Death two-by-two sheet uses one cohort scale to preserve anatomical size while the neck and coils collapse.'}
 dump(HERE/'pose-roots-v1.json',roots);dump(HERE/'isolated-source-map-v1.json',cohorts)
 masters=[HERE/(name+'-v1.png')for name in ['motion','combat','death','portrait','site']]
 source_masters=masters+[HERE/'identity-study-v0.png']
 dump(HERE/'generation-ledger-v1.json',{'status':'authored configuration','provider':'OpenAI built-in imagegen','model':'not exposed','method':'Original painted 2D pose masters generated from text and the own motion master for identity. No 3D, original troop pixels or third-party artwork used as generation input. Technical alpha-component isolation preserves original painted RGB and core alpha.','sources':[{'path':rel(p),'sha256':sha(p)}for p in source_masters],'identity_reference_chain':{'motion-v1.png':'identity-study-v0.png','combat-v1.png':'motion-v1.png','death-v1.png':'motion-v1.png','portrait-v1.png':'motion-v1.png','site-v1.png':None},'lore_sources':['https://www.leagueoflegends.com/en-au/news/dev/dev-cat-cults-rift-mechs-and-baron-s-revamp/','https://www.leagueoflegends.com/en-gb/news/game-updates/patch-14-1-notes/'],'canonical_basis':'Riot describes Baron Nashor as a Voidborn wyrm and late-game objective with a pit. The native unique grounded melee boss and slithering locomotion are project adaptations; no pit-changing spells or siege aura is inferred.','project_adaptation':'Living grounded two-hex physical-melee unique Voidborn boss. Purple-plum armored rearing serpent with connected heavy ground coils, pale ribbed underside, multiple magenta eyes, ivory mandibles and two foreclaws. Finite NashorPit is a project encounter. No flight, burrow teleport, obstacle crossing, acid shooting, regeneration, immunity, spells or siege/global buff imported.','rights':'New project-directed generated art; Riot Games owns related Runeterra and League concepts and designs. No external rights approval asserted.','visual_approval_granted':False})
 deps=source_masters+[Path(__file__),EXTRACTOR,HERE/'pose-roots-v1.json',HERE/'isolated-source-map-v1.json',HERE/'generation-ledger-v1.json']+list(HERE.glob('*.prompt.txt'))+[PROJECT/r['image']for rows in cohorts.values()for r in rows]
 def common(master,prompt):return {'production_status':'painted-master-complete-unapproved','generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed','prompt':prompt.read_text(encoding='utf8'),'painted_master':rel(master),'painted_master_sha256':sha(master),'method':'Whole painted actor/component isolation and fixed cohort scale/root registration; no body painting, pose warping or per-frame zoom.'},'production_inputs':[{'path':rel(p),'sha256':sha(p)}for p in sorted(set(deps))]}
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
 recipe('battle',{'recipe_type':'vcmi_animation','output_path':'Content/Sprites/runeterra/world/creatures/baronNashor/battle.json','canvas':[450,400],'pivot':{'x':218,'y':266},'groups':groups})
 entries=[]
 for f,i in enumerate([0,1,2,1,3,0]):
  im=render('motion',i,(96,64),(63,56),.28,True);assert box(im)[0]>=32;p=HERE/'native/map'/f'g00-f{f:03d}.png';save(p,im);entries.append(descriptor(p,f))
 recipe('map',{'recipe_type':'vcmi_animation','output_path':'Content/Sprites/runeterra/world/creatures/baronNashor/map.json','canvas':[96,64],'pivot':{'x':63,'y':56},'groups':[{'group':0,'generateShadow':1,'generateOverlay':0,'frames':entries}]})
 for role,mirror in [('attackLeft',False),('attackRight',True)]:
  im=render('combat',4,(64,64),(28 if mirror else 35,56),.3,mirror);p=HERE/'native'/(role+'.png');save(p,im);recipe(role,{'recipe_type':'raster','output_path':f'Content/Sprites/runeterra/world/creatures/baronNashor/{role}.png','canvas':[64,64],**descriptor(p),'fit':'exact'})
 for role,size in [('large',(58,64)),('small',(32,32))]:
  p=HERE/'native'/(role+'.png');save(p,ImageOps.fit(Image.open(HERE/'portrait-v1.png').convert('RGBA'),size,Image.Resampling.LANCZOS));recipe(role,{'recipe_type':'raster','output_path':f'Content/Sprites/runeterra/world/creatures/baronNashor/{role}.png','canvas':list(size),**descriptor(p),'fit':'exact'},HERE/'portrait-v1.png',HERE/'portrait-v1.prompt.txt')
 site=Image.open(HERE/'site-v1.png').convert('RGBA');b=box(site);assert b and b[0]>0 and b[1]>0 and b[2]<site.width and b[3]<site.height
 actor=site.crop(b);actor.thumbnail((88,88),Image.Resampling.LANCZOS);site=Image.new('RGBA',(96,96));site.alpha_composite(actor,((96-actor.width)//2,94-actor.height));p=HERE/'native/site.png';save(p,site)
 recipe('site',{'recipe_type':'vcmi_animation','output_path':'Content/Sprites/runeterra/world/sites/nashorPit/map.json','canvas':[96,96],'pivot':{'x':48,'y':94},'groups':[{'group':0,'generateShadow':1,'generateOverlay':0,'frames':[descriptor(p)]}]},HERE/'site-v1.png',HERE/'site-v1.prompt.txt')
 dump(HERE/'site-calibration.json',{'status':'authored configuration','id':'nashorPit','canvas':[96,96],'mask':['VVV','BBB','BAB'],'visitableFrom':['---','---','-+-'],'allowedTerrains':['rough','dirt'],'native_bbox':box(site),'native_sha256':sha(p),'rmg':False,'native_execution':'not_run'})
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
 board=Image.new('RGB',(1600,((len(frames)+4)//5)*205),(65,67,56));draw=ImageDraw.Draw(board)
 for n,r in enumerate(frames):
  x=(n%5)*320;y=(n//5)*205;draw.text((x+4,y+4),f"g{r['group']} f{r['frame']}",fill='white');im=Image.open(PROJECT/r['source']).crop((60,90,380,275));board.paste(im,(x,y+15),im)
 save(REPORT/'native-action-sheet.png',board)
 siteboard=Image.new('RGB',(384,220),(57,63,52));siteboard.paste(site,(5,70),site);zoom=site.resize((192,192),Image.Resampling.NEAREST);siteboard.paste(zoom,(145,10),zoom);save(REPORT/'native-site.png',siteboard)
 payload={str(g):[base64.b64encode((PROJECT/r['source']).read_bytes()).decode()for r in frames if r['group']==g]for g in GROUPS}
 html='''<!doctype html><meta charset="utf-8"><title>Baron Nashor painted candidates</title><style>body{background:#20241f;color:#eee;font:16px system-ui;max-width:1080px;margin:auto}img{max-width:100%}canvas{background:#414338;image-rendering:pixelated}button{margin:4px}</style><h1>Baron Nashor complete painted action candidate</h1><p>Authored configuration. Grounded living two-hex physical-melee unique Voidborn boss. No flight, obstacle crossing, burrow teleport, acid shooting, regeneration, immunity, spells or siege/global buff. Not an ordinary recruitable creature. Not native gameplay or release acceptance.</p><img src="native-site.png"><img src="native-action-sheet.png"><p>Actual delivered450Ãƒâ€”400 frames; browser timing is illustrative. Group0 shows grounded coil undulation; no flight or takeoff/landing groups. Four distinct idle poses are reused in a six-frame loop.</p><div id="buttons"></div><canvas width="450" height="400"></canvas><p><a href="technical-verification.json">Actual source/consumer and double-assembly evidence</a></p><script>const sets=DATA;let active='0',i=0;const cache={};for(const[g,frames]of Object.entries(sets)){cache[g]=frames.map(s=>{const im=new Image;im.src='data:image/png;base64,'+s;return im});const b=document.createElement('button');b.textContent='Group '+g;b.onclick=()=>{active=g;i=0};document.querySelector('#buttons').append(b)}setInterval(()=>{const c=document.querySelector('canvas'),x=c.getContext('2d');x.clearRect(0,0,450,400);const a=cache[active];x.drawImage(a[i++%a.length],0,0)},180)</script>'''
 (REPORT/'index.html').write_text(html.replace('DATA',json.dumps(payload)),encoding='utf8');print(json.dumps({'recipes':len(recipes),'compiled_outputs':len(outputs),'battle_frames':len(frames),'report':str(REPORT)}))
if __name__=='__main__':main()
