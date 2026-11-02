"""Persist inspected cell maps/camera registrations, not generated content stats."""
from pathlib import Path
import argparse
from PIL import Image
from assemble import HERE,WORKSPACE,PROJECT,sha,record,islands
import copy,json

def plate(filename,row_counts,labels,roots,scale):
    p=HERE/filename;items=islands(Image.open(p).convert('RGBA'))
    if len(items)!=sum(row_counts):raise ValueError('Inspect unexpected connected painted silhouettes '+filename)
    ordered=[];by_y=sorted(enumerate(items),key=lambda q:(q[1]['box'][1]+q[1]['box'][3])/2);offset=0
    for count in row_counts:
        ordered+=sorted(by_y[offset:offset+count],key=lambda q:q[1]['box'][0]);offset+=count
    poses={}
    for label,(index,item),root in zip(labels,ordered,roots):
        if root[1]=='contact':root=[root[0],item['box'][3]]
        poses[label]={'island':index,'inspected_opaque_box':item['box'],'root':root}
    return {'source':filename,'sha256':sha(p),'expected_islands':len(items),'scale':scale,'poses':poses}

def groups(flyer):
    g={'0':['m0','m0','m1','m2','m3','m3','m4','m5'],
       '1':['hold','pain1','pain1','hold','hold'],'2':['hold'],
       '3':['pain0','pain0','pain1','pain1','hold'],
       '4':['defend0','defend0','defend1','defend1','hold'],
       '5':['death0','death0','death1','death1','death2','death2','death3','death3'],
       '7':['hold','quarter','quarter','front','front'],
       '8':['turnJoin','turnJoin','quarter','hold','hold'],
       '22':['death3']}
    for group,angle in [('11','up'),('12','frontHit'),('13','down')]:
        g[group]=[angle+'0',angle+'0',angle+'0',angle+'1',angle+'1',angle+'2',angle+'3','hold']
    if flyer:
        g['20']=['hold','takeoff0','takeoff1','takeoff2','m0']
        g['21']=['m5','landing0','landing1','landing2','hold']
    else:g.update({'20':['hold','m0'],'21':['m5','hold']})
    return g

def native_consumer():
    result={}
    for p in ['client/battle/CreatureAnimation.cpp','client/battle/BattleAnimationClasses.cpp','client/battle/BattleStacksController.cpp']:
        f=WORKSPACE/'vcmi-develop/vcmi-develop'/p;result[p]={'sha256':sha(f),'use':'Read-only native frame/facing/cadence reference; excluded from creature source masters'}
    result['cadence']={'base_fps':10,'moving_ticks':8,'melee_ticks':8,'contact_zero_based':3,'response_ticks':5,'death_ticks':8,'painted_key_holds_explicit':True,'new_shooter_or_cast_groups':False}
    result['turn']={'group7':'TURN_L before facing change','group8':'TURN_R after facing toggle/reposition','canvas_full_mirror_axis':449,'two_hex_position_flip_delta':-14,'group8_first_full_mirror_then_translate_x':-14}
    return result

def bird(unit):
    up=unit=='stormwing'
    loc_roots=[[320,360],[820,360],[1340,360],[320,680],[820,680],[1340,680],[320,1004 if up else 999],[805,1004 if up else 999],[1280,1000 if up else 997]]
    attack_roots=[[260,370],[650,370],[1035,370],[1390,370],[260,690 if up else 675],[650,690 if up else 675],[1035,690 if up else 675],[1390,690 if up else 675],[260,999],[650,999],[1035,999],[1390,999]]
    reaction_roots=([[290,'contact'],[705,'contact'],[1150,'contact'],[1605,'contact']]*2 if up else [[280,'contact'],[620,'contact'],[970,'contact'],[1380,'contact'],[270,'contact'],[600,'contact'],[930,'contact'],[1300,'contact']])
    trans_roots=[[320,498 if up else 487],[820,498 if up else 487],[1340,475 if up else 465],[320,1000 if up else 960],[820,984 if up else 964],[1340,984 if up else 974]]
    P={
      'locomotion':plate(unit+'-locomotion-v1-raw.png',[3,3,3],['m0','m1','m2','m3','m4','m5','hold','quarter','front'],loc_roots,(100/353 if up else 95/316)),
      'attacks':plate(unit+'-attacks-v1-raw.png',[4,4,4],[a+str(i)for a in ['up','frontHit','down']for i in range(4)],attack_roots,(100/252 if up else 95/245)),
      'reactions':plate(unit+'-reactions-v1-raw.png',[4,4],['pain0','pain1','defend0','defend1','death0','death1','death2','death3'],reaction_roots,(100/358 if up else 95/295)),
      'transitions':plate(unit+'-transitions-v1-raw.png',[3,3],['takeoff0','takeoff1','takeoff2','landing0','landing1','landing2'],trans_roots,(100/347 if up else 95/310)),
    }
    # The two rows are independently painted cohorts of the same role camera.
    cp=plate('bird-companions-v1-raw.png',[4,4],['baseMap','baseFidget','baseEncounter','basePortrait','upMap','upFidget','upEncounter','upPortrait'],[[230,452],[610,452],[1000,460],[1350,467],[230,962],[610,962],[1000,963],[1350,978]],1)
    if up:cp['poses']={k:v for k,v in cp['poses'].items()if k.startswith('up')}
    else:cp['poses']={k:v for k,v in cp['poses'].items()if k.startswith('base')}
    P['companions']=cp
    c={'map_pose':'upMap'if up else'baseMap','encounter_pose':'upEncounter'if up else'baseEncounter','portrait_pose':'upPortrait'if up else'basePortrait','scale':36/444 if up else 34/382,'portrait_crop':[1158,497,1525,864]if up else[1165,50,1517,402]}
    cfg={'unit':unit,'version':1,'plates':P,'groups':groups(True),'turn_front':'front','companions':c,'native_consumer':native_consumer(),'limitations':['Authored configuration; native in-game silhouettes, fast playback, recruitment/body crops and shadow composition remain unverified.','Correct regional crest is physically painted; tiny battle/adventure fidelity needs independent native-size appearance approval.','Explicit repeated genuine painted-key holds are timeline cadence, not additional unique painted poses.','Source portrait heads use own painted coastal background; rights and release acceptance remain pending.']}
    record(HERE/unit/'assembly-config-v1.json',cfg)
    print(unit,'configuration authored')

def compact_bird(unit,version=2):
    cfg=json.loads((HERE/unit/'assembly-config-v1.json').read_text());cfg['version']=version
    cfg['plates']['locomotion']['poses']['sideControl']=cfg['plates']['locomotion']['poses'].pop('hold')
    up=unit=='stormwing';c=cfg['plates']['companions'];prefix='up'if up else'base'
    c['scale']=100/444 if up else 95/382
    c['poses']['hold']=copy.deepcopy(c['poses'][prefix+'Map']);c['poses']['hold']['root']=[210,962 if up else 452]
    c['poses']['fidget']=copy.deepcopy(c['poses'][prefix+'Fidget']);c['poses']['fidget']['root']=[590,962 if up else 452]
    if version>=3:c['poses'][prefix+'Encounter']['root'][0]=950 if version>=4 else 970
    cfg['groups']['1']=['hold','fidget','fidget','hold','hold']
    cfg['compact_holding_registration']={'method':'Genuinely painted near-frontal folded-wing holding/fidget at unchanged95/100px physical height. No full battle cohort reduction or tail crop.','native_preview_crop':[170,155,270,275],'earlier_side_holding_preserved_as_control':True}
    record(HERE/unit/f'assembly-config-v{version}.json',cfg);print(unit,'compact holding version',version,'authored')

def leviathan(unit):
    up=unit=='elderShoreLeviathan'
    locroots=[[350,'contact'],[850,'contact'],[1360,'contact']]*2+[[350,'contact'],[850,'contact'],[1315,'contact']]
    hitroots=[[x,'contact']for _ in range(3)for x in [270,660,1040,1420]]
    reactionroots=[[x,'contact']for _ in range(2)for x in [280,720,1160,1600]]
    P={
      'locomotion':plate(unit+'-locomotion-v1-raw.png',[3,3,3],['m0','m1','m2','m3','m4','m5','sideControl','quarter','front'],locroots,102/296 if up else 95/275),
      'attacks':plate(unit+'-attacks-v1-raw.png',[4,4,4],[a+str(i)for a in ['up','frontHit','down']for i in range(4)],hitroots,.42 if up else .40),
      'reactions':plate(unit+'-reactions-v1-raw.png',[4,4],['pain0','pain1','defend0','defend1','death0','death1','death2','death3'],reactionroots,102/294 if up else 95/285),
    }
    compact=plate('leviathan-compact-holding-v3-raw.png',[2,2],['baseHold','baseFidget','upHold','upFidget'],[[380,565],[960,565],[390,1134],[960,1134]],102/544 if up else 95/540)
    compact['poses']={'hold':compact['poses']['upHold'if up else'baseHold'],'fidget':compact['poses']['upFidget'if up else'baseFidget']}
    P['compact_holding']=compact
    cp=plate('leviathan-companions-v1-raw.png',[4,4],['baseMap','baseMapFidget','baseEncounter','basePortrait','upMap','upMapFidget','upEncounter','upPortrait'],[[235,413],[672,414],[1118,420],[1550,400],[238,863],[681,859],[1131,870],[1560,846]],1)
    prefix='up'if up else'base';cp['poses']={k:v for k,v in cp['poses'].items()if k.startswith(prefix)};P['companions']=cp
    c={'map_pose':prefix+'Map','encounter_pose':prefix+'Encounter','portrait_pose':prefix+'Portrait','scale':31/404 if up else 30/367,'portrait_crop':[1350,424,1774,848]if up else[1344,24,1765,445]}
    g=groups(False);g['1']=['hold','fidget','fidget','hold','hold']
    cfg={'unit':unit,'version':1,'plates':P,'groups':g,'turn_front':'front','companions':c,'native_consumer':native_consumer(),'compact_holding_registration':{'method':'New genuine exact-frontal four-grounded-paw pose, tail curled/occluded behind body. Same95/102px physical height as full battle cohort; no whole-unit reduction or clipping.','native_preview_crop':[170,155,270,275],'excluded_raws':['leviathan-compact-holding-v1-raw.png: erroneous biped grasping crest','leviathan-compact-holding-v2-raw.png: correct quadruped but three-quarter footprint still too broad']},'limitations':['Authored configuration; native in-game fast playback, action transitions and battle/shadow composition remain unverified.','Correct crest is physically painted; tiny native-size appearance and stronger upgrade readability need independent approval.','Holding is genuinely front-facing to fit the actual stock creature-window crop; all locomotion/strikes retain genuine broader three-quarter anatomy.','Repeated genuine painted-key holds express native cadence, not extra unique art. Rights and release acceptance remain pending.']}
    record(HERE/unit/'assembly-config-v1.json',cfg);print(unit,'four-limbed full candidate configuration authored')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('unit',choices=['cliffwing','stormwing','shoreLeviathan','elderShoreLeviathan']);p.add_argument('--compact',action='store_true');p.add_argument('--version',type=int,default=2);a=p.parse_args()
    if 'Leviathan'in a.unit:leviathan(a.unit)
    else:compact_bird(a.unit,a.version)if a.compact else bird(a.unit)
