"""Author measured lesser-Buhru priestess painted keys; no gameplay edits."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg={'unit':'krakenPriest','version':1,'battle_canvas':[450,400],'battle_root':[197,266],'plates':{},'groups':{},'companions':{'pose':'ready','scale':.14,'map_root':[76,60],'encounter_root':[44,60],'portrait_crop':[135,100,260,245]},'unresolved':['Independent source gait/leg-overlap and native1x loop review remains required','Staff/body root continuity and stock body crops need inspection','Native Cure event/cast-phase alignment and both facings have not been observed','Correct regional crest legibility requires independent native-size review','Canonical source-policy and archive admission have not run']}
data={
 'melee-v1-raw.png':(.309,12,{'up0':(0,215,384),'up1':(1,580,384),'up2':(3,970,384),'front0':(5,190,677),'front1':(7,570,677),'front2':(6,970,677),'down0':(8,205,997),'down1':(10,570,997),'down2':(11,970,997)}),
 'reactions-v1-raw.png':(.271,12,{'ready':(0,205,405),'defend':(1,550,413),'hurt0':(2,950,412),'hurt1':(3,1365,414),'turn0':(4,185,742),'turn1':(5,545,740),'turn2':(7,950,741),'turn3':(6,1370,743),'death0':(8,175,993),'death1':(9,545,996),'death2':(10,900,996),'death3':(11,1290,997)}),
 'near-walk-v1-raw.png':(.113,3,{'near0':(1,285,905),'near1':(2,800,905),'near2':(0,1300,905)}),
 'far-walk-v1-raw.png':(.126,3,{'far0':(2,250,987),'far1':(0,690,987),'far2':(1,1120,987)}),
 'cast-v1-raw.png':(.261,12,{'castUpPrep':(1,165,407),'castUpAim':(2,500,409),'castUpRecover':(3,1175,408),'castFrontPrep':(5,165,784),'castFrontAim':(7,500,784),'castFrontRecover':(6,1175,784),'castDownPrep':(9,165,1125),'castDownAim':(11,500,1126),'castDownRecover':(8,1175,1127)})}
for name,(scale,count,entries)in data.items():
    path=HERE/name;cfg['plates'][name]={'source':path.relative_to(SOURCE).as_posix(),'source_sha256':sha(path),'expected_islands':count,'scale':scale,'poses':{label:{'island':i,'root':[x,y]}for label,(i,x,y)in entries.items()}}
cfg['groups']={'0':['near0','near1','near2','far0','far1','far2'],'1':['ready','castFrontPrep'],'2':['ready'],'3':['hurt0','hurt1','ready'],'4':['defend','ready'],'5':['death0','death1','death2','death3'],'7':['ready','turn0','turn1','turn3'],'8':['turn3','turn1','turn0','ready'],'11':['up0','up1','up2','ready'],'12':['front0','front1','front2','ready'],'13':['down0','down1','down2','ready'],'20':['ready','near0'],'21':['far2','ready'],'22':['death3'],'30':['ready','castUpPrep','castUpAim','castUpAim','castUpRecover','ready'],'31':['ready','castFrontPrep','castFrontAim','castFrontAim','castFrontRecover','ready'],'32':['ready','castDownPrep','castDownAim','castDownAim','castDownRecover','ready']}
cfg['excluded_source_keys']=[{'plate':'cast-v1-raw.png','islands':[0,4,10],'reason':'Large intrinsic green glow studies remain unselected. Native Cure provides its spell effect; creature release holds the genuine open-palm blessing pose without creating a projectile or synthetic glow.'},{'pose':'turn2','reason':'Preserved near-front study; selected5-tick halfturn uses ready/right-diagonal/diagonal-front/full-front with explicit holds.'}]
cfg['cast_contract']={'consumer':'Native CastAnimation chooses groups30/31/32 and maxFrames/2 climax, independently of shooter attackClimaxFrame','eight_tick_release_index':4,'selected_release':'Genuine extended open-palm pose held through native Cure effect; no intrinsic bitmap projectile','native_execution':False,'gameplay':'Existing one finite native Cure/action cost and10HP per current priest remain unchanged'}
path=HERE/'assembly-config-v1.json';payload=(json.dumps(cfg,sort_keys=True,indent=2)+'\n').encode()
if path.exists()and path.read_bytes()!=payload:raise RuntimeError('Preserve earlier source config; version correction')
if not path.exists():path.write_bytes(payload)
