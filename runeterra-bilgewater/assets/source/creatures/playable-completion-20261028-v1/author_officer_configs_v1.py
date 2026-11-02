"""Hand-annotated officer source keys, fixed plate cameras, no game-source edits."""
from pathlib import Path
import json,hashlib
SOURCE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
DATA={
'boardingCaptain':{
 'reactions-v1-raw.png':(.245,12,{'ready':(0,175,370),'defend':(2,550,370),'hurt0':(1,900,370),'hurt1':(3,1280,370),'turn0':(4,175,750),'turn1':(5,550,750),'turn2':(6,905,750),'turn3':(7,1260,750),'death0':(8,175,1010),'death1':(9,550,1010),'death2':(10,865,1017),'death3':(11,1245,1017)}),
 'melee-v1-raw.png':(.275,11,{'up0':(0,175,430),'up1':(1,550,430),'up2':(2,920,430),'front0':(5,175,758),'front1':(7,550,758),'front2':(6,920,758),'down0':(8,175,1067)}),
 'down-repair-v1-raw.png':(.15,2,{'down1':(1,540,690),'down2':(0,1515,690)}),
 'near-walk-v1-raw.png':(.13,3,{'near0':(0,375,690),'near1':(2,1120,690),'near2':(1,1810,690)}),
 'far-walk-v1-raw.png':(.14,3,{'far0':(1,375,673),'far1':(0,1120,673),'far2':(2,1810,673)})},
'fleetVeteran':{
 'reactions-v1-raw.png':(.24,11,{'ready':(0,180,385),'defend':(2,550,385),'hurt0':(1,910,385),'hurt1':(3,1290,385),'turn0':(4,180,778),'turn1':(5,550,778),'turn2':(6,910,778),'turn3':(7,1260,778),'death0':(8,180,1051),'death1':(9,550,1051)}),
 'corpse-repair-v1-raw.png':(.09,2,{'death2':(0,750,539),'death3':(1,750,1001)}),
 'melee-v1-raw.png':(.293,9,{'up0':(2,240,392),'up1':(1,750,392),'up2':(0,1250,392),'front0':(3,240,746),'front1':(5,750,746),'front2':(4,1250,746),'down0':(6,240,1071),'down1':(8,750,1071),'down2':(7,1250,1071)}),
 'near-walk-v1-raw.png':(.131,3,{'near0':(1,380,690),'near1':(2,1120,690),'near2':(0,1810,690)}),
 'far-walk-v1-raw.png':(.142,3,{'far0':(1,380,675),'far1':(0,1120,675),'far2':(2,1810,675)})}}
for unit,plates in DATA.items():
 cfg={'unit':unit,'version':1,'battle_canvas':[450,400],'battle_root':[197,266],'plates':{},'groups':{},'companions':{'pose':'ready','scale':.145,'map_root':[76,60],'encounter_root':[44,60],'portrait_crop':[130,5,240,140]},'unresolved':['Independent actual1x gait/leg-ownership and costume/root continuity review pending','Displayed native paired-turn facing/reposition continuity not yet verified','Stock body preview/companions require bounded pixel inspection','Regional crest native1x legibility and artistic acceptance remain pending','Canonical source/archive admission and native gameplay not run']}
 for name,(scale,count,entries)in plates.items():
  p=SOURCE/unit/name;cfg['plates'][name]={'source':p.relative_to(SOURCE).as_posix(),'source_sha256':sha(p),'expected_islands':count,'scale':scale,'poses':{label:{'island':i,'root':[x,y]}for label,(i,x,y)in entries.items()}}
 cfg['groups']={'0':['near0','near1','near2','far0','far1','far2'],'1':['ready','turn0'],'2':['ready'],'3':['hurt0','hurt1','ready'],'4':['defend','ready'],'5':['death0','death1','death2','death3'],'7':['ready','turn0','turn1','turn3'],'8':['turn3','turn1','turn0','ready'],'11':['up0','up1','up2','ready'],'12':['front0','front1','front2','ready'],'13':['down0','down1','down2','ready'],'20':['ready','near0'],'21':['far2','ready'],'22':['death3']}
 cfg['excluded_source_keys']=[{'pose':'turn2','reason':'Preserved near-front pose study; turn phase consumer review pending.'}]
 if unit=='boardingCaptain':cfg['excluded_source_keys'].append({'plate':'melee-v1-raw.png','islands':[10],'reason':'Lower contact and recovery touch; combined source island excluded and independently painted separated down-repair source used.'})
 else:cfg['excluded_source_keys'].append({'plate':'reactions-v1-raw.png','islands':[10],'reason':'Two fallen bodies touch; combined island excluded and independent two-row corpse source used.'})
 p=SOURCE/unit/'assembly-config-v1.json';b=(json.dumps(cfg,sort_keys=True,indent=2)+'\n').encode()
 if p.exists()and p.read_bytes()!=b:raise RuntimeError('Preserve earlier source config '+unit)
 if not p.exists():p.write_bytes(b)
