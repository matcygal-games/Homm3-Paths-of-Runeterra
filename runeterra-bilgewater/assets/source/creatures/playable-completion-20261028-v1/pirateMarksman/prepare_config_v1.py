"""Author the measured upgrade source config; no content/design regeneration."""
from pathlib import Path
import json,copy,hashlib
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent
cfg=json.loads((SOURCE/'corsair/assembly-config-v1.json').read_text());cfg['unit']='pirateMarksman'
for name,plate in cfg['plates'].items():
    plate['source']=plate['source'].replace('corsair/','pirateMarksman/')
    plate['source_sha256']=hashlib.sha256((SOURCE/plate['source']).read_bytes()).hexdigest()
    plate['scale']=.18 if name=='walk'else .225
roots={
 'shots':{'shootUpDraw':(1,165,386),'shootUpAim':(2,500,390),'shootUpRelease':(0,825,399),'shootUpRecoil':(3,1175,397),'shootFrontDraw':(4,165,783),'shootFrontAim':(5,500,784),'shootFrontRelease':(6,825,784),'shootFrontRecoil':(7,1175,784),'shootDownDraw':(8,165,1151),'shootDownAim':(10,500,1150),'shootDownRelease':(11,825,1152),'shootDownRecoil':(9,1175,1154)},
 'reactions':{'ready':(0,165,451),'defend':(2,510,449),'hurt0':(1,825,449),'hurt1':(3,1175,451),'turn0':(5,180,850),'turn1':(6,510,852),'turn2':(7,840,852),'turn3':(4,1170,852),'death0':(8,175,1142),'death1':(9,500,1139),'death2':(10,825,1137),'death3':(11,1140,1133)},
 'walk':{'walk0':(0,300,499),'walk1':(1,785,504),'walk2':(2,1300,501),'walk3':(4,305,983),'walk4':(3,785,984),'walk5':(5,1300,986)},
 'melee':{'up0':(0,170,400),'up1':(1,510,403),'up2':(2,840,403),'up3':(3,1180,404),'front0':(4,180,787),'front1':(6,510,788),'front2':(5,840,788),'front3':(7,1180,791),'down0':(8,170,1155),'down1':(11,510,1157),'down2':(10,840,1157),'down3':(9,1180,1158)}}
for plate,entries in roots.items():
    cfg['plates'][plate]['poses']={name:{'island':i,'root':[x,y]}for name,(i,x,y)in entries.items()}
cfg['groups']['7']=['ready','turn1','turn2','turn3'];cfg['groups']['8']=['turn3','turn2','turn1','ready']
cfg['excluded_source_keys']=[{'pose':'turn0','reason':'Rearward three-quarter study preserved, not selected; native halfturn begins at identical HOLDING pose'}]
cfg['companions']['portrait_crop']=[94,84,264,268]
cfg['muzzle_measurements']={'status':'design proposal','source_release_index':3,'native_attackClimaxFrame':4,'upper':{'pose':'shootUpRelease','source_barrel_end':[960,75],'source_root':[825,399],'fixed_scale':.225,'native_offset':[30,-73]},'middle':{'pose':'shootFrontRelease','source_barrel_end':[1015,512],'source_root':[825,784],'fixed_scale':.225,'native_offset':[43,-61]},'lower':{'pose':'shootDownRelease','source_barrel_end':[994,1025],'source_root':[825,1152],'fixed_scale':.225,'native_offset':[38,-29]},'native_alignment':'not_run'}
cfg['unresolved']=["Opposite support and gait continuity require complete motion review","Native halfturn/body root continuity needs observation; source first/last boundaries equal HOLDING","Native same-hex muzzle origins and both facings have not been observed","Exact crest legibility and face/head continuity require independent native-size review","Canonical integration and source-policy admission have not run"]
path=HERE/'assembly-config-v1.json';data=(json.dumps(cfg,sort_keys=True,indent=2)+'\n').encode()
if path.exists()and path.read_bytes()!=data:raise RuntimeError('Preserve earlier config; version correction')
if not path.exists():path.write_bytes(data)
