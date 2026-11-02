"""Explicit measured living-shellfolk source proposal; no gameplay changes."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent
cfg=json.loads((SOURCE/'corsair/assembly-config-v1.json').read_text());cfg['unit']='shellshotGunner'
scales={'shots':.26,'reactions':.23,'walk':.166,'melee':.215}
for name,plate in cfg['plates'].items():
    plate['source']=plate['source'].replace('corsair/','shellshotGunner/');plate['source_sha256']=hashlib.sha256((SOURCE/plate['source']).read_bytes()).hexdigest();plate['scale']=scales[name]
roots={
 'shots':{'shootUpDraw':(3,205,343),'shootUpAim':(1,605,342),'shootUpRecoil':(2,1440,343),'shootFrontDraw':(4,205,626),'shootFrontAim':(6,605,626),'shootFrontRelease':(5,1000,626),'shootFrontRecoil':(7,1450,628),'shootDownDraw':(10,205,911),'shootDownAim':(8,605,909),'shootDownRelease':(9,1000,913),'shootDownRecoil':(11,1450,910)},
 'reactions':{'ready':(0,205,353),'defend':(3,605,353),'hurt0':(1,1000,353),'hurt1':(2,1440,353),'turn0':(4,210,657),'turn1':(5,620,657),'turn2':(6,1010,657),'turn3':(7,1440,657),'death0':(8,205,909),'death1':(9,605,907),'death2':(10,1000,917),'death3':(11,1440,924)},
 'walk':{'walk0':(1,210,466),'walk1':(2,735,466),'walk2':(0,1275,466),'walk3':(4,210,965),'walk4':(3,735,965),'walk5':(5,1275,966)},
 'melee':{'up0':(1,190,358),'up1':(0,585,358),'up2':(2,995,358),'front0':(4,190,655),'front1':(7,585,655),'front2':(5,995,654),'down0':(9,190,974),'down1':(11,585,970),'down2':(8,995,973)}}
for plate,entries in roots.items():cfg['plates'][plate]['poses']={name:{'island':i,'root':[x,y]}for name,(i,x,y)in entries.items()}
p=HERE/'up-release-repair-v1-raw.png';cfg['plates']['upperReleaseRepair']={'source':p.relative_to(SOURCE).as_posix(),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'expected_islands':1,'scale':.102,'poses':{'shootUpRelease':{'island':0,'root':[650,1025]}}}
for group,names in [('11',['up0','up1','up2','ready']),('12',['front0','front1','front2','ready']),('13',['down0','down1','down2','ready']),('7',['ready','turn1','turn2','turn3']),('8',['turn3','turn2','turn1','ready'])]:cfg['groups'][group]=names
cfg['companions']={'pose':'ready','scale':.112,'map_root':[76,60],'encounter_root':[44,60],'portrait_crop':[165,95,325,255]}
cfg['projectile']['scale']=.09
cfg['excluded_source_keys']=[{'plate':'shots','island':0,'reason':'Upper muzzle flash reaches source border; independent complete release painting replaces it'},{'pose':'turn0','reason':'Halfturn begins and ends at identical native HOLDING source'}]
cfg['muzzle_measurements']={'status':'design proposal','source_release_index':3,'native_attackClimaxFrame':4,'upper':{'pose':'shootUpRelease','source_barrel_end':[1000,390],'source_root':[650,1025],'fixed_scale':.102,'native_offset':[36,-65]},'middle':{'pose':'shootFrontRelease','source_barrel_end':[1151,465],'source_root':[1000,626],'fixed_scale':.26,'native_offset':[39,-42]},'lower':{'pose':'shootDownRelease','source_barrel_end':[1140,860],'source_root':[1000,913],'fixed_scale':.26,'native_offset':[36,-14]},'native_alignment':'not_run'}
cfg['unresolved']=['Independent native-size gait/support and root continuity review remains required','Native same-hex projectile origins and both facings have not been observed','Compact map/encounter body footprints need inspection against actual object anchors','Correct shell-cloth crest legibility requires independent native-size review','Canonical source-policy and archive admission have not run']
path=HERE/'assembly-config-v1.json';data=(json.dumps(cfg,sort_keys=True,indent=2)+'\n').encode()
if path.exists()and path.read_bytes()!=data:raise RuntimeError('Preserve prior config; version repair')
if not path.exists():path.write_bytes(data)
