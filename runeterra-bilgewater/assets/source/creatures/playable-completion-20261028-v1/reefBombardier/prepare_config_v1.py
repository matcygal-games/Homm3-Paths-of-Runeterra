"""Measured living-shellfolk upgrade config; no canonical gameplay edits."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent
cfg=json.loads((SOURCE/'shellshotGunner/assembly-config-v1.json').read_text());cfg['unit']='reefBombardier'
scales={'shots':.238,'reactions':.228,'walk':.164,'melee':.205,'upperReleaseRepair':.105}
for name,plate in cfg['plates'].items():
    plate['source']=plate['source'].replace('shellshotGunner/','reefBombardier/');plate['source_sha256']=hashlib.sha256((SOURCE/plate['source']).read_bytes()).hexdigest();plate['scale']=scales[name]
roots={
 'shots':{'shootUpDraw':(3,205,341),'shootUpAim':(1,605,341),'shootUpRecoil':(2,1450,341),'shootFrontDraw':(4,205,636),'shootFrontAim':(5,605,635),'shootFrontRelease':(7,1000,635),'shootFrontRecoil':(6,1450,637),'shootDownDraw':(8,205,922),'shootDownAim':(9,605,921),'shootDownRelease':(10,1000,925),'shootDownRecoil':(11,1450,925)},
 'reactions':{'ready':(0,205,356),'defend':(3,605,356),'hurt0':(1,1000,356),'hurt1':(2,1450,356),'turn0':(4,210,663),'turn1':(5,620,663),'turn2':(6,1010,663),'turn3':(7,1450,663),'death0':(8,205,916),'death1':(9,605,919),'death2':(10,1000,922),'death3':(11,1450,928)},
 'walk':{'walk0':(0,210,480),'walk1':(2,735,478),'walk2':(1,1275,480),'walk3':(3,210,968),'walk4':(4,735,970),'walk5':(5,1275,969)},
 'melee':{'up0':(1,190,368),'up1':(0,585,368),'up2':(2,995,367),'front0':(4,190,668),'front1':(6,585,668),'front2':(5,995,667),'down0':(8,190,973),'down1':(10,585,972),'down2':(9,995,974)},
 'upperReleaseRepair':{'shootUpRelease':(0,665,1040)}}
for plate,entries in roots.items():cfg['plates'][plate]['poses']={name:{'island':i,'root':[x,y]}for name,(i,x,y)in entries.items()}
cfg['companions']={'pose':'ready','scale':.11,'map_root':[76,60],'encounter_root':[44,60],'portrait_crop':[165,92,325,255]};cfg['projectile']['scale']=.10
cfg['muzzle_measurements']={'status':'design proposal','source_release_index':3,'native_attackClimaxFrame':4,'upper':{'pose':'shootUpRelease','source_barrel_end':[1050,400],'source_root':[665,1040],'fixed_scale':.105,'native_offset':[40,-67]},'middle':{'pose':'shootFrontRelease','source_barrel_end':[1150,465],'source_root':[1000,635],'fixed_scale':.238,'native_offset':[36,-40]},'lower':{'pose':'shootDownRelease','source_barrel_end':[1140,860],'source_root':[1000,925],'fixed_scale':.238,'native_offset':[33,-15]},'native_alignment':'not_run'}
path=HERE/'assembly-config-v1.json';data=(json.dumps(cfg,sort_keys=True,indent=2)+'\n').encode()
if path.exists()and path.read_bytes()!=data:raise RuntimeError('Preserve previous config; version correction')
if not path.exists():path.write_bytes(data)
