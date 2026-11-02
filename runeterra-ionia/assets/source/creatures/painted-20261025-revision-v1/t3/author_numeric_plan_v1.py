"""Author immutable numeric source-cell coordinates; never reads old rendered art.

Atlas-wide resolution normalization is fixed for every pose from that atlas.
No frame is scaled/fitted/centered from its opaque bounds.
"""
from pathlib import Path
import hashlib,json
from PIL import Image
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def public(name):return name.removesuffix('.png')+'-public.png'
def source(name,scale):
 p=SOURCE/public(name);im=Image.open(p)
 return {'source':p.relative_to(PROJECT).as_posix(),'source_sha256':sha(p),'source_canvas':list(im.size),'scale':scale,'scope':'One fixed atlas-resolution normalization for all poses; no per-frame fitting'}
def grid(unit,key,name,scale,xs,ys,roots_x,grounds,matrix,seed_lift):
 unit['sources'][key]=source(name,scale)
 for row,names in enumerate(matrix):
  for col,semantic in enumerate(names):
   if semantic is None:continue
   # Windows may overlap slightly in blank margins; connected-alpha extraction
   # drops other actors without moving/resizing any part of the selected actor.
   w,h=unit['sources'][key]['source_canvas'];pad=12
   crop=[max(0,xs[col]-pad),max(0,ys[row]-pad),min(w,xs[col+1]+pad),min(h,ys[row+1]+pad)]
   seed=[roots_x[col],grounds[row]-seed_lift]
   if semantic in ('death3','death4','death5'):seed=[roots_x[col],grounds[row]-45]
   unit['poses'][semantic]={'source_key':key,'semantic':semantic,'crop':crop,'root':[roots_x[col],grounds[row]],'seed':seed}
utility=[[None]*6,['fidget0','fidget1','fidget2','fidget3','holding0','holding1'],['hit0','hit1','hit2','defend0','defend1','defend2'],['death0','death1','death2','death3','death4','death5'],[None,None,None,'turnFront0','turnFront1',None]]
units={key:{'sources':{},'poses':{},'portrait_source':'portrait'} for key in ('vastayanScout','vastayanWarrior')}
s=units['vastayanScout'];u=units['vastayanWarrior']
s['sources']['portrait']=source('scout-holding-master-v1.png',1)
s['portrait_crops']={'large':[250,70,700,566],'small':[270,100,650,480]}
u['sources']['portrait']=source('warrior-holding-master-v2.png',1)
u['portrait_crops']={'large':[415,0,823,450],'small':[445,0,825,380]}
for unit,unit_key,filename,scale,grounds in ((s,'vastayanScout','scout-utility-atlas-v1.png',.36,[217,463,700,890,1125]),(u,'vastayanWarrior','warrior-utility-atlas-v2.png',.35,[225,480,717,908,1142])):
 grid(unit,'utility',filename,scale,[0,238,462,690,916,1132,1374],[0,235,468,704,900,1145],[120,350,575,800,1028,1255],grounds,utility,80)
# Final genuine gait variants; every source cell has the same fixed calibration.
for unit,filename,scale in ((s,'scout-gait-atlas-v2.png',.174),(u,'warrior-gait-atlas-v3.png',.180)):
 grid(unit,'gait',filename,scale,[0,520,1035,1536],[0,505,1024],[300,800,1300],[490,997],[[f'walk{i}' for i in range(3)],[f'walk{i}' for i in range(3,6)]],190)
# These source contracts are set after direct atlas inspection, not opaque fits.
grid(s,'shoot','scout-shoot-atlas-v1.png',.300,[0,260,515,775,1040,1295,1536],[0,365,700,1024],[125,385,640,900,1160,1410],[353,663,997],[[f'shoot{angle}{i}' for i in range(6)] for angle in ('Upper','Middle','Lower')],120)
grid(u,'shoot','warrior-shoot-atlas-v2.png',.290,[0,265,520,780,1045,1300,1536],[0,370,740,1024],[125,385,640,900,1160,1410],[362,704,1012],[[f'shoot{angle}{i}' for i in range(6)] for angle in ('Upper','Middle','Lower')],120)
# Melee atlas calibration is intentionally explicit and reviewed before freezing.
grid(s,'melee','scout-melee-atlas-v2.png',.340,[0,410,780,1150,1510,1870,2172],[0,267,511,724],[190,580,950,1310,1690,2040],[260,505,720],[[f'melee{angle}{i}' for i in range(6)] for angle in ('Upper','Middle','Lower')],100)
grid(u,'melee','warrior-melee-atlas-v2.png',.305,[0,300,600,900,1200,1500,1794],[0,320,610,877],[155,450,750,1050,1350,1650],[314,605,866],[[f'melee{angle}{i}' for i in range(6)] for angle in ('Upper','Middle','Lower')],110)
# Source heel/sole contact coordinates measured on the painted sheet. These
# register the physical floor; they never change scale or fit body bounds.
for unit,grounds in ((s,[893,879,879,882,884,879]),(u,[911,903,906,903,901,906])):
 for index,y in enumerate(grounds):unit['poses']['death'+str(index)]['root'][1]=y
for name in ('meleeMiddle0','meleeMiddle5'):s['poses'][name]['root'][1]=523
gait_path=SOURCE/'gait-registration-v2.json';gait=json.loads(gait_path.read_text())
for unit_id,unit in units.items():
 unit['sources'].pop('gait',None);unit['sources'].update(gait['sources'][unit_id]);unit['poses'].update(gait['poses'][unit_id])
plan={'status':'authored configuration','scope':'Fresh painted2D T3 source candidates only, no active selections or native approval','contracts_sha256':sha(SOURCE/'native-contracts-v1.json'),'battle_canvas':[450,400],'battle_pivot':[197,266],'adventure_fixed_projection':{'scale':.5,'anchor':[80,60],'canvas':[96,64],'map_facing':'left, compact genuine fidget/holding poses reflected about fixed root'},'unit_camera':'Consistent painted elevated three-quarter side view and upper-left light; per-atlas source-resolution calibration is fixed across all its cells','turn_contract':'g7 holding -> three-quarter front -> frontal boundary; g8 genuine reverse after native engine flip; unused back studies preserved','units':units,'projectile':{**source('painted-arrow-master-v1.png',1),'crop':[165,245,2010,458],'native_length':28,'angles_degrees':[90,45,0,-45,-90],'scope':'Fresh painted ordinary physical arrow; single uniform reduction and fixed rotations, no old arrow pixels'}}
scene=PROJECT/'assets/source/town/landscape-v2/master.png'
parents=[PROJECT/'assets/source/town/landscape-v1/master.png',PROJECT/'assets/source/town/landscape-v1/prompt.txt',PROJECT/'assets/source/town/landscape-v2/prompt.txt',SOURCE/'portrait-scene-provenance-v1.json']
plan['portrait_scene']={'source':scene.relative_to(PROJECT).as_posix(),'source_sha256':sha(scene),'source_canvas':list(Image.open(scene).size),'ancestry_pins':[{'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)} for p in parents],'crops':{'vastayanScout':{'large':[20,0,740,795],'small':[20,0,740,720]},'vastayanWarrior':{'large':[1150,0,1790,706],'small':[1150,0,1790,640]}}}
plan['gait_registration']={'source':gait_path.relative_to(PROJECT).as_posix(),'source_sha256':sha(gait_path),'scope':'Exact decodedRGBA match to fresh whole6 pose review; final native motion and art approval pending'}
path=SOURCE/'assembly-plan-v1.json';path.write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n');print(json.dumps({'plan_sha256':sha(path),'units':{k:len(v['poses']) for k,v in units.items()}}))
