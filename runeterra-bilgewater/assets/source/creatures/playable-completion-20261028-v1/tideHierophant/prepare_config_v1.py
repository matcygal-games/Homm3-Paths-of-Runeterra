"""Measured Tide Hierophant painted action keys; no gameplay/selection edits."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg={'unit':'tideHierophant','version':1,'battle_canvas':[450,400],'battle_root':[197,266],'plates':{},'groups':{},'companions':{'pose':'ready','scale':.135,'map_root':[76,60],'encounter_root':[44,60],'portrait_crop':[118,80,255,242]},'unresolved':['Independent source gait/leg-overlap and native1x loop review remains required','Staff/body camera/root continuity and stock body crops need inspection','Displayed native turn-flip continuity has not been verified','Native Cure event/cast-phase alignment and both facings have not been observed','Correct regional crest legibility requires independent native-size review','Canonical source-policy and archive admission have not run']}
data={
 'melee-v1-raw.png':(.29,12,{'up0':(0,210,405),'up1':(2,580,405),'up2':(3,970,405),'front0':(5,190,693),'front1':(7,570,693),'front2':(6,970,693),'down0':(8,205,1010),'down1':(10,570,1010),'down2':(11,970,1010)}),
 'reactions-v1-raw.png':(.247,11,{'ready':(0,195,417),'defend':(1,550,421),'hurt0':(2,950,419),'hurt1':(3,1365,422),'turn0':(4,185,749),'turn1':(6,545,749),'turn2':(7,950,749),'turn3':(5,1370,749),'death0':(8,175,1000),'death1':(9,545,1000)}),
 'corpse-repair-v1-raw.png':(.105,2,{'death2':(0,790,449),'death3':(1,790,941)}),
 'near-walk-v2-raw.png':(.103,3,{'near0':(0,290,963),'near1':(1,800,963),'near2':(2,1300,963)}),
 'far-walk-v1-raw.png':(.119,3,{'far0':(2,280,956),'far1':(0,780,956),'far2':(1,1290,956)}),
 'cast-v1-raw.png':(.247,12,{'castUpPrep':(0,165,406),'castUpAim':(2,500,406),'castUpRelease':(1,835,406),'castUpRecover':(3,1180,406),'castFrontPrep':(4,165,779),'castFrontAim':(7,500,779),'castFrontRelease':(5,835,779),'castFrontRecover':(6,1180,779),'castDownPrep':(8,165,1127),'castDownAim':(10,500,1127),'castDownRelease':(11,835,1127),'castDownRecover':(9,1180,1127)})}
for name,(scale,count,entries)in data.items():
 p=HERE/name;cfg['plates'][name]={'source':p.relative_to(SOURCE).as_posix(),'source_sha256':sha(p),'expected_islands':count,'scale':scale,'poses':{label:{'island':i,'root':[x,y]}for label,(i,x,y)in entries.items()}}
cfg['groups']={'0':['near0','near1','near2','far0','far1','far2'],'1':['ready','castFrontPrep'],'2':['ready'],'3':['hurt0','hurt1','ready'],'4':['defend','ready'],'5':['death0','death1','death2','death3'],'7':['ready','turn0','turn1','turn3'],'8':['turn3','turn1','turn0','ready'],'11':['up0','up1','up2','ready'],'12':['front0','front1','front2','ready'],'13':['down0','down1','down2','ready'],'20':['ready','near0'],'21':['far2','ready'],'22':['death3'],'30':['ready','castUpPrep','castUpAim','castUpRelease','castUpRecover','ready'],'31':['ready','castFrontPrep','castFrontAim','castFrontRelease','castFrontRecover','ready'],'32':['ready','castDownPrep','castDownAim','castDownRelease','castDownRecover','ready']}
cfg['excluded_source_keys']=[{'plate':'reactions-v1-raw.png','islands':[10],'reason':'Two final fallen bodies touch in original atlas; combined island excluded and replaced by independently generated separated corpse repair.'},{'plate':'near-walk-v1-raw.png','reason':'Rightmost extended toe touches source edge; entire plate superseded by reframed near-walk-v2.'},{'pose':'turn2','reason':'Preserved intermediate front study; source turn review remains pending.'}]
cfg['cast_contract']={'consumer':'Native CastAnimation uses maxFrames/2 climax; eighttick release index4','selected_release':'Genuine nonglow extended palm at climax; native Cure supplies VFX','native_execution':False,'gameplay':'Existing single finite native Cure action and15HP upgrade unchanged'}
p=HERE/'assembly-config-v1.json';b=(json.dumps(cfg,sort_keys=True,indent=2)+'\n').encode()
if p.exists()and p.read_bytes()!=b:raise RuntimeError('Preserve earlier source config')
if not p.exists():p.write_bytes(b)
