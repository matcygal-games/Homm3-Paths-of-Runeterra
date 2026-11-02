"""V3: correct two native attack-group bindings, without repainting any frame."""
from __future__ import annotations
import argparse,copy,hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[4]
NATIVE={'ATTACK_UP':11,'ATTACK_FRONT':12,'ATTACK_DOWN':13}
POSES={'ATTACK_UP':['up0','up1','up2','up3'],'ATTACK_FRONT':['level0','level1','level2','level3']}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def rel(p):return p.relative_to(PROJECT).as_posix()
def checked(name,digest):
 p=(PROJECT/name).resolve()
 if not p.is_relative_to((PROJECT/'assets/source').resolve()) or not p.is_file() or sha(p)!=digest:raise ValueError('Missing, unsafe or changed source '+name)
 return p
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path);args=ap.parse_args();pp=HERE/'attack-group-plan-v3.json';plan=json.loads(pp.read_text())
 if plan['native_constants']!=NATIVE:raise ValueError('Native attack constants disagree with inspected BattleConstants.h')
 oldpath=checked(plan['previous_selection']['path'],plan['previous_selection']['sha256']);old=json.loads(oldpath.read_text())
 for n,h in old['recipe_sha256'].items():checked(n,h)
 expected={(u,s) for u in ['loyalBadgerbear','veteranBadgerbear'] for s in POSES}
 if {(r['unit'],r['semantic']) for r in plan['cohorts']}!=expected or len(plan['cohorts'])!=4:raise ValueError('Expected four complete directional cohorts')
 for r in plan['cohorts']:
  if r['target_group']!=NATIVE[r['semantic']] or r['semantic_poses']!=POSES[r['semantic']] or len(r['frames'])!=4:raise ValueError('Native group and original painted pose semantics disagree')
  for f in r['frames']:checked(f['source'],f['sha256'])
 result=copy.deepcopy(old);result['status']='authored configuration; V3native11UP12FRONT correction; unselected';changed=[]
 pins=[{'path':rel(p),'sha256':sha(p)} for p in [Path(__file__).resolve(),pp,HERE/'REPRODUCE-v3.txt',oldpath]]
 for u in ['loyalBadgerbear','veteranBadgerbear']:
  out=f'Content/Sprites/runeterra/demacia/creatures/{u}/battle.json';prior=checked(old['candidates'][out],old['recipe_sha256'][old['candidates'][out]]);recipe=json.loads(prior.read_text());groups={g['group']:g for g in recipe['groups']}
  for r in [x for x in plan['cohorts'] if x['unit']==u]:
   for i,f in enumerate(r['frames']):
    src=checked(f['source'],f['sha256']);dst=HERE/'native-v3'/u/f"g{r['target_group']:02d}-f{i:03d}.png";dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    groups[r['target_group']]['frames'][i]={'source':rel(dst),'sha256':sha(dst)}
    changed.append({'unit':u,'group':r['target_group'],'frame':i,'semantic':r['semantic'],'semantic_pose':r['semantic_poses'][i],'original_painted_frame':f['source'],'sha256':sha(dst)})
  recipe['producer_inputs']=recipe['producer_inputs']+pins+[{'path':rel(prior),'sha256':sha(prior)}]
  recipe['native_attack_semantics']={'ATTACK_UP':11,'ATTACK_FRONT':12,'ATTACK_DOWN':13,'proof':'Inspected readonlyclient/battle/BattleConstants.h lines74-76; originalposeplan up0..3→11,level0..3→12; actualsourcepixels reviewed separately','native_verified':False}
  recipe['technical_revision']={'version':3,'rule':'Swap complete genuineUP/FRONT contact cohorts only. No repaint, translation, scaling, mirroring, framewarp, corpse/turn/map/encounter/portrait modification. Holding recovery unchanged.','native_verified':False}
  rp=HERE/'candidates-v3'/f'{u}-battle.json';dump(rp,recipe);result['candidates'][out]=rel(rp)
  for g in (11,12):
   for i in range(4):result['units'][u]['frame_sha256'][f'{g}/{i}']=sha(HERE/'native-v3'/u/f'g{g:02d}-f{i:03d}.png')
 result['recipe_sha256']={n:sha(PROJECT/n) for n in result['candidates'].values()};result['attack_group_revision']=changed;dump(HERE/'candidate-selection-v3.json',result)
 receipt={'ok':True,'status':'authored configuration; bounded group-binding repair','selection_sha256':sha(HERE/'candidate-selection-v3.json'),'new_frame_sources':len(changed),'native_constants':NATIVE,'changed_sources':changed,'native_verified':False,'release_accepted':False}
 if args.report:dump(args.report,receipt)
 print(json.dumps({'ok':True,'new_frame_sources':len(changed),'selection_sha256':receipt['selection_sha256']}))
if __name__=='__main__':main()
