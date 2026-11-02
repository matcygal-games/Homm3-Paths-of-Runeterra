"""Versioned opposed-support camera annotations; interleave before-contact legs."""
from pathlib import Path
import json,copy,hashlib,sys
from PIL import Image
from split_painted_islands import islands
S=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,obj):
 b=(json.dumps(obj,sort_keys=True,indent=2)+'\n').encode()
 if p.exists()and p.read_bytes()!=b:raise RuntimeError('Preserve earlier source '+str(p))
 if not p.exists():p.write_bytes(b)
# SeaDog's preserved special assembler ledger supplies its exact inspected source keys.
old=json.loads((S/'seaDog/cohort-candidate-v1.json').read_text());plates={}
for f in old['frames']:
 if f['group']in(0,20,21):continue
 name=Path(f['master']).name
 p=S/'seaDog'/name
 if name not in plates:plates[name]={'source':p.relative_to(S).as_posix(),'source_sha256':sha(p),'expected_islands':len(islands(Image.open(p).convert('RGBA'))),'scale':f['plate_pixel_scale'],'poses':{}}
 plates[name]['poses'][f['pose']]={'island':f['source_island_index'],'root':f['source_anatomical_root']}
cfg={'unit':'seaDog','version':2,'battle_canvas':[450,400],'battle_root':[197,266],'plates':plates,'groups':{},'companions':{'pose':'idle','scale':.13,'map_root':[76,60],'encounter_root':[44,60],'portrait_crop':[90,96,265,270]},'unresolved':['Independent native1x opposed gait/root/costume review pending','Displayed paired-turn facing/reposition continuity pending','Native game/crest/artistic/rights acceptance not run'],'excluded_source_keys':[old['excluded_source_island']]}
cfg['groups']={'0':['near0','near1','far2','far0','far1','near2'],'1':['ready','idle'],'2':['ready'],'3':['hurt0','hurt1','ready'],'4':['defend','ready'],'5':['death0','death1','death2','death3'],'7':['ready','turn0','turn1','turn3'],'8':['turn3','turn1','turn0','ready'],'11':['up0','up1','up2','ready'],'12':['front0','front1','front2','ready'],'13':['down0','down1','down2','ready'],'20':['ready','near0'],'21':['near2','ready'],'22':['death3']}
DATA={
 'seaDog':{'near-walk-v2-raw.png':(.116,{'near0':(0,305,781),'near1':(1,930,781),'near2':(2,1580,781)}),'far-walk-v2-raw.png':(.108,{'far0':(0,285,901),'far1':(1,800,901),'far2':(2,1300,901)})},
 'corsair':{'near-walk-v2-raw.png':(.116,{'near0':(0,320,761),'near1':(1,930,761),'near2':(2,1580,761)}),'far-walk-v2-raw.png':(.128,{'far0':(1,450,675),'far1':(0,1120,675),'far2':(2,1810,675)})},
 'pirateMarksman':{'near-walk-v2-raw.png':(.12,{'near0':(0,320,745),'near1':(1,930,745),'near2':(2,1580,745)}),'far-walk-v2-raw.png':(.129,{'far0':(1,450,675),'far1':(0,1120,675),'far2':(2,1810,675)})}}
for unit,data in DATA.items():
 if unit!='seaDog':cfg=json.loads((S/unit/'assembly-config-v2.json').read_text());cfg['version']=3
 cfg['plates']={k:v for k,v in cfg['plates'].items()if k!='walk-v1-raw.png'}
 for name,(scale,poses)in data.items():
  p=S/unit/name;cfg['plates'][name]={'source':p.relative_to(S).as_posix(),'source_sha256':sha(p),'expected_islands':3,'scale':scale,'poses':{label:{'island':i,'root':[x,y]}for label,(i,x,y)in poses.items()}}
 if unit!='seaDog':
  cfg['groups']['0']=['near0','near0','near1','far2','far0','far0','far1','near2'];cfg['groups']['20']=['ready','near0'];cfg['groups']['21']=['near2','ready']
  if unit=='corsair':cfg['groups']['7'][0]='ready';cfg['groups']['8'][-1]='ready'
 cfg['gait_contract']={'sequence':'Contact A, Passing A, Precontact B, Contact B, Passing B, Precontact A','camera':'One fixed plate scale per source; anatomical roots manually annotated','native_motion_approval':False}
 cfg.setdefault('excluded_source_keys',[]).append({'plate':'walk-v1-raw.png','reason':'Earlier broad walk source retained as history; selected explicit opposed support halves replace it.'})
 put(S/unit/f"assembly-config-v{cfg['version']}.json",cfg)
