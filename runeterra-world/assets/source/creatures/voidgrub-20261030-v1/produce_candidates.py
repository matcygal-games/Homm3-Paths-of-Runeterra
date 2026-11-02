"""Own painted-source candidates only; no selection, staging or artistic acceptance."""
from pathlib import Path
import hashlib,json,sys,copy
from PIL import Image,ImageOps,ImageDraw
import numpy as np
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-world')
ROOT=PROJECT.parent
REPORT=ROOT/'reports/world-expansion-art-20261030-v1'
SITES=PROJECT/'assets/source/sites/world-expansion-20261030-v1'
GROUPS={0:('motion',[4,5,8,9,10,11]),1:('motion',[0,1,2,1,3,0]),2:('motion',[0]),3:('motion',[6,0]),4:('motion',[7]),5:('death',[0,1,2,3]),7:('motion',[0,12,13,14]),8:('motion',[14,13,12,0]),11:('combat',[0,1,2,3]),12:('combat',[4,5,6,7]),13:('combat',[8,9,10,11]),22:('death',[3])}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def bbox(im):return im.getchannel('A').point(lambda a:255 if a>=16 else 0).getbbox()
def clean(im):
 a=np.array(im.convert('RGBA'));a[a[:,:,3]<16]=0
 return Image.fromarray(a)
def isolate():
 out={};records=[]
 for name,filename,cols,rows,scale in [('motion','motion-v1.png',4,4,.245),('combat','combat-v2.png',4,3,.27),('death','death-v1.png',4,1,.15)]:
  master=HERE/filename;im=Image.open(master).convert('RGBA');cohort=[]
  for y in range(rows):
   top=round(y*im.height/rows);bottom=round((y+1)*im.height/rows)
   if name=='combat':
    occupied=np.flatnonzero(np.any(np.asarray(im)[top:bottom,:,3]>=16,axis=0))
    spans=[s for s in np.split(occupied,np.where(np.diff(occupied)>1)[0]+1)if len(s)>20]
    assert len(spans)==4,('Expected four separated whole painted actors',name,y)
    boxes=[(max(0,int(s[0])-2),top,min(im.width,int(s[-1])+3),bottom)for s in spans]
   else:boxes=[(round(x*im.width/cols),top,round((x+1)*im.width/cols),bottom)for x in range(cols)]
   for x,cell in enumerate(boxes):
    actor=clean(im.crop(cell));b=bbox(actor);assert b and 0<b[0]<b[2]<actor.width and 0<b[1]<b[3]<actor.height,(name,x,y,b)
    full=(cell[0]+b[0],cell[1]+b[1],cell[0]+b[2],cell[1]+b[3]);actor=actor.crop(b)
    # Roots are visually annotated support projections, not per-pose alpha centres.
    if name=='motion':root=(round(x*im.width/4)+181,round(y*im.height/4)+235)
    elif name=='combat':root=(x*362+181,y*362+[338,310,266][y])
    else:root=(x*543+275,585)
    p=HERE/'isolated'/name/f'{len(cohort):02d}.png';save(p,actor)
    record={'master':rel(master),'master_sha256':sha(master),'source':rel(p),'source_sha256':sha(p),'crop':list(full),'root':list(root),'scale':scale,'index':len(cohort),'cell_edge_contamination':False}
    cohort.append(record);records.append(record)
  out[name]=cohort
 dump(HERE/'isolated-source-map-v1.json',records)
 return out
def render(row,canvas,root,mult=1,mirror=False):
 assert sha(PROJECT/row['source'])==row['source_sha256']
 actor=Image.open(PROJECT/row['source']);scale=row['scale']*mult
 local=[row['root'][n]-row['crop'][n]for n in (0,1)]
 actor=actor.resize(tuple(round(n*scale)for n in actor.size),Image.Resampling.LANCZOS)
 offset=[root[n]-round(local[n]*scale)for n in (0,1)]
 if mirror:actor=ImageOps.mirror(actor);offset[0]=root[0]-(actor.width-1-round(local[0]*scale))
 b=bbox(actor);assert b and 0<=offset[0]+b[0]<offset[0]+b[2]<=canvas[0]and 0<=offset[1]+b[1]<offset[1]+b[3]<=canvas[1],(row,canvas,offset,b)
 result=Image.new('RGBA',canvas);result.alpha_composite(actor,tuple(offset));return result
def main():
 REPORT.mkdir(parents=True,exist_ok=True);index=isolate();recipes=[];frames=[]
 masters=[HERE/n for n in ['motion-v1.png','combat-v2.png','death-v1.png','portrait-v1.png']]
 ledger={'status':'authored configuration','provider':'OpenAI built-in imagegen','model':'not exposed','art_process':'New painted2D from text and own generated motion reference only. No3D, fanart or original-game pixels used. Whole actor technical isolation/scale/registration only.','lore_sources':['https://www.leagueoflegends.com/en-au/news/game-updates/2024-gameplay-preview/','https://www.leagueoflegends.com/en-us/news/game-updates/patch-14-1-notes/'],'canonical_basis':'Voidgrubs are small Void creatures from the Rift. Purple segmented body, amber horn and pink luminous sensory nodes are visual inspiration.','project_adaptation':'Grounded six-proleg melee crawler; no canonical hovering, tower buff, summon or Voidmite mechanics. Wild fauna carries no manufactured regional crest.','original_game_reference':'Native creature-battle-03 sheet inspected read-only for compact scale, upper-left light and textured2D rendering. Not used as pixels or generation input.','sources':[{'path':rel(p),'sha256':sha(p)}for p in masters],'visual_approval_granted':False,'rights':'Generated project-directed artwork; Runeterra/League and related designs belong to Riot Games. No third-party fanart used; no external rights approval asserted.'}
 dump(HERE/'generation-ledger-v1.json',ledger)
 dependencies=masters+[HERE/'generation-ledger-v1.json',HERE/'isolated-source-map-v1.json',Path(__file__)]+sorted(HERE.glob('*.prompt.txt'))+[PROJECT/r['source']for rows in index.values()for r in rows]
 def common(master,prompt):return {'production_status':'painted-master-complete-unapproved','generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed','prompt':prompt.read_text(encoding='utf8'),'painted_master':rel(master),'painted_master_sha256':sha(master),'method':'Whole painted actor extraction and fixed cohort registration; no per-frame fitting, warping or artistic acceptance.'},'production_inputs':[{'path':rel(p),'sha256':sha(p)}for p in sorted(set(dependencies))]}
 def desc(p,frame=0):return {'frame':frame,'source':rel(p),'source_sha256':sha(p),'sha256':sha(p),'source_canvas':list(Image.open(p).size)}
 def recipe(role,data,master=masters[0],prompt=HERE/'motion-v1.prompt.txt',folder=HERE):
  p=folder/'candidate-recipes'/(role+'.recipe.json');dump(p,{**common(master,prompt),**data});recipes.append(p);return p
 groups=[]
 for group,(cohort,order)in sorted(GROUPS.items()):
  entries=[]
  for f,i in enumerate(order):
   im=render(index[cohort][i],(450,400),(220,266));p=HERE/'native/battle'/f'g{group:02d}-f{f:03d}.png';save(p,im);entries.append(desc(p,f));frames.append({'group':group,'frame':f,'source':rel(p),'source_pose':i,'cohort':cohort,'bbox':bbox(im),'sha256':sha(p)})
  groups.append({'group':group,'generateShadow':1,'generateOverlay':0,'frames':entries})
 recipe('battle',{'recipe_type':'vcmi_animation','output_path':'Content/Sprites/runeterra/world/creatures/voidgrub/battle.json','canvas':[450,400],'pivot':{'x':220,'y':266},'groups':groups})
 entries=[]
 for f,i in enumerate([0,1,2,1,3,0]):
  im=render(index['motion'][i],(96,64),(67,56),.58,True);assert bbox(im)[0]>=32
  p=HERE/'native/map'/f'g00-f{f:03d}.png';save(p,im);entries.append(desc(p,f))
 recipe('map',{'recipe_type':'vcmi_animation','output_path':'Content/Sprites/runeterra/world/creatures/voidgrub/map.json','canvas':[96,64],'pivot':{'x':67,'y':56},'groups':[{'group':0,'generateShadow':1,'generateOverlay':0,'frames':entries}]})
 for role,mirror in [('attackLeft',False),('attackRight',True)]:
  im=render(index['combat'][4],(64,64),(31 if mirror else 32,56),.58,mirror);p=HERE/'native'/(role+'.png');save(p,im)
  recipe(role,{'recipe_type':'raster','output_path':f'Content/Sprites/runeterra/world/creatures/voidgrub/{role}.png','canvas':[64,64],**desc(p),'fit':'exact'})
 for role,size in [('large',(58,64)),('small',(32,32))]:
  p=HERE/'native'/(role+'.png');save(p,ImageOps.fit(Image.open(masters[3]).convert('RGBA'),size,Image.Resampling.LANCZOS))
  recipe(role,{'recipe_type':'raster','output_path':f'Content/Sprites/runeterra/world/creatures/voidgrub/{role}.png','canvas':list(size),**desc(p),'fit':'exact'},masters[3],HERE/'portrait-v1.prompt.txt')
 assert Image.open(HERE/'native/battle/g22-f000.png').tobytes()==Image.open(HERE/'native/battle/g05-f003.png').tobytes()
 assert Image.open(HERE/'native/battle/g22-f000.png').tobytes()!=Image.open(HERE/'native/battle/g02-f000.png').tobytes()
 for id,terrains,mask in [('voidBurrow',['rough','dirt'],['VVV','BBB','BAB']),('petricitePillar',['grass','dirt'],['VVV','VBV','BAB']),('targonianFoothills',['rough','snow'],['VVV','VBV','BAB'])]:
  folder=SITES/id;master=folder/'master-v1.png';im=clean(Image.open(master));b=bbox(im);assert b and min(b[:2])>0 and b[2]<im.width and b[3]<im.height
  actor=im.crop(b);actor.thumbnail((88,88),Image.Resampling.LANCZOS);native=Image.new('RGBA',(96,96));native.alpha_composite(actor,((96-actor.width)//2,94-actor.height));p=folder/'native-v1.png';save(p,native)
  site_common=common(master,folder/'prompt-v1.txt');site_common['production_inputs']=[{'path':rel(p),'sha256':sha(p)}for p in [master,folder/'prompt-v1.txt',Path(__file__)]]
  rp=folder/'recipe-candidate.json';dump(rp,{**site_common,'recipe_type':'vcmi_animation','output_path':f'Content/Sprites/runeterra/world/sites/{id}/map.json','canvas':[96,96],'pivot':{'x':48,'y':94},'groups':[{'group':0,'generateShadow':1,'generateOverlay':0,'frames':[desc(p)]}]});recipes.append(rp)
  dump(folder/'calibration.json',{'status':'authored configuration','native_canvas':[96,96],'native_bbox':bbox(native),'mask':mask,'visitableFrom':['---','---','-+-'],'terrains':terrains,'rmg':False,'visual_approval_granted':False,'painted_master_sha256':sha(master),'native_sha256':sha(p),'generated_from':'New project-directed painted2D text prompt, no third-party pixels.','rights':'Runeterra motifs belong to Riot Games; external rights approval not asserted.'})
 sys.path.insert(0,str(ROOT/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('world');outputs={};receipts=[]
 for p in recipes:
  a,receipt=compiler.plan(PROJECT,p);b,_=compiler.plan(PROJECT,p);assert a==b,'Real double assembly mismatch'
  for name,data in a.items():
   assert name not in outputs;outputs[name]=hashlib.sha256(data).hexdigest();target=REPORT/'compiled-candidates'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  receipts.append(receipt)
 dump(REPORT/'technical-verification.json',{'status':'authored configuration','recipes':[rel(p)for p in recipes],'recipe_count':len(recipes),'compiled_output_count':len(outputs),'double_real_assembly_byte_identical':True,'outputs':outputs,'receipts':receipts,'source_cells':sum(len(v)for v in index.values()),'whole_actor_clip_count':0,'source_cross_cell_contamination':0,'native_execution':'not_run','visual_approval_granted':False,'release_accepted':False,'facing':'Native attackFromLeft actor facesRIGHT; attackFromRight mirrors toLEFT. Map facesLEFT.','limitations':['Generated pose anatomy varies slightly; cadence and attack contact require native observation.','Death collapses into a lower inert body instead of a side-lying corpse.','Sites are static adventure sprites, not animated environments.']})
 # Display-only contact sheets; these are never selected as game graphics.
 board=Image.new('RGB',(960,((len(frames)+5)//6)*112),(65,67,56));draw=ImageDraw.Draw(board)
 for n,r in enumerate(frames):
  x=(n%6)*160;y=(n//6)*112;draw.text((x+3,y+3),f"g{r['group']} f{r['frame']}",fill='white');im=Image.open(PROJECT/r['source']).crop((140,190,300,290));board.paste(im,(x,y+13),im)
 save(REPORT/'voidgrub-native-actions.png',board)
 siteboard=Image.new('RGB',(960,248),(57,63,52));d=ImageDraw.Draw(siteboard)
 for n,id in enumerate(['voidBurrow','petricitePillar','targonianFoothills']):
  im=Image.open(SITES/id/'native-v1.png');x=n*320;d.text((x+4,4),id,fill='white');siteboard.paste(im,(x+8,65),im);zoom=im.resize((192,192),Image.Resampling.NEAREST);siteboard.paste(zoom,(x+112,30),zoom)
 save(REPORT/'site-native-board.png',siteboard)
 # Local browser playback of actual delivered frames, not a simulation of native timing.
 import base64
 payload={str(g):[base64.b64encode((PROJECT/r['source']).read_bytes()).decode()for r in frames if r['group']==g]for g in GROUPS}
 html='''<!doctype html><meta charset="utf-8"><title>World painted candidates</title><style>body{background:#20241f;color:#eee;font:16px system-ui;max-width:1080px;margin:auto}img{max-width:100%}canvas{background:#414338;image-rendering:pixelated}button{margin:4px}</style><h1>World expansion painted candidates</h1><p>Authored configuration. New painted2D sources; nine candidate recipes assembled twice with identical bytes. No native gameplay, rights approval or release acceptance claimed.</p><h2>Three sites at native and 2× size</h2><img src="site-native-board.png"><h2>Voidgrub genuine source poses at native size</h2><img src="voidgrub-native-actions.png"><p>Browser playback uses actual generated450×400 frames. Timing is illustrative; native cadence/contact is unobserved. Grounded crawl is project adaptation. Wild fauna has no artificial crest.</p><div id="buttons"></div><canvas id="view" width="450" height="400"></canvas><p><a href="technical-verification.json">Double-assembly hashes and receipts</a></p><script>const sets=DATA;let active='0',i=0;const cache={};for(const[g,frames]of Object.entries(sets)){cache[g]=frames.map(s=>{const im=new Image;im.src='data:image/png;base64,'+s;return im});const b=document.createElement('button');b.textContent='Group '+g;b.onclick=()=>{active=g;i=0};document.querySelector('#buttons').append(b)}setInterval(()=>{const c=document.querySelector('canvas'),x=c.getContext('2d');x.clearRect(0,0,450,400);const a=cache[active];x.drawImage(a[i++%a.length],0,0)},160)</script>'''
 (REPORT/'index.html').write_text(html.replace('DATA',json.dumps(payload)),encoding='utf8')
 print(json.dumps({'status':'authored configuration','recipes':len(recipes),'compiled_outputs':len(outputs),'battle_frames':len(frames),'report':str(REPORT)}))
if __name__=='__main__':main()
