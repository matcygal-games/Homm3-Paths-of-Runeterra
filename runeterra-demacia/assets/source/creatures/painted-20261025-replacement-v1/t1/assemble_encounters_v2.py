"""Bounded V2 repair: reproject four whole actors for real Demacia64px roles."""
from __future__ import annotations
import argparse,copy,hashlib,json
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def rel(p):return p.relative_to(PROJECT).as_posix()
def checked(name,digest):
 p=(PROJECT/name).resolve()
 if not p.is_relative_to((PROJECT/'assets/source').resolve()) or not p.is_file() or sha(p)!=digest:raise ValueError('Missing, unsafe or changed pinned source: '+name)
 return p
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path);args=ap.parse_args()
 plan_path=HERE/'encounter-plan-v2.json';plan=json.loads(plan_path.read_text())
 if plan['canvas']!=[64,64] or plan['anchor']!=[37,60] or plan['pivot']!=[197,266] or plan['scale']!=.55:raise ValueError('Demacia reviewed encounter contract changed')
 oldpath=checked(plan['previous_selection']['path'],plan['previous_selection']['sha256']);previous=json.loads(oldpath.read_text())
 for name,digest in previous['recipe_sha256'].items():checked(name,digest)
 expected={(u,role) for u in ['loyalBadgerbear','veteranBadgerbear'] for role in ['attackLeft','attackRight']}
 if {(r['unit'],r['role']) for r in plan['encounters']}!=expected or len(plan['encounters'])!=4:raise ValueError('Expected exactly four encounter roles')
 for r in plan['encounters']:
  if r['mirrored']!=(r['role']=='attackRight'):raise ValueError('Native fieldFromSide facing mismatch')
  p=checked(r['parent']['source'],r['parent']['sha256'])
  with Image.open(p) as im:
   if im.mode!='RGBA' or im.size!=(450,400):raise ValueError('Whole parent frame must be450x400RGBA')
 output=copy.deepcopy(previous);output['status']='authored configuration; V2correct64px encounter size and native FromSide facing; unselected'
 sourcepins=[{'path':rel(p),'sha256':sha(p)} for p in [Path(__file__).resolve(),plan_path,HERE/'REPRODUCE-v2.txt',oldpath]]
 sourcepins += [{'path':name,'sha256':digest} for name,digest in previous['recipe_sha256'].items()]
 projections=[]
 for r in plan['encounters']:
  parent=checked(r['parent']['source'],r['parent']['sha256']);im=Image.open(parent).convert('RGBA');sign=-1 if r['mirrored'] else 1;s=plan['scale'];px,py=plan['pivot'];ax,ay=plan['anchor']
  out=im.transform((64,64),Image.Transform.AFFINE,(sign/s,0,px-sign*ax/s,0,1/s,py-ay/s),Image.Resampling.BICUBIC)
  bb=im.getchannel('A').point(lambda v:255 if v>=8 else 0).getbbox();xx=[ax+sign*s*(bb[i]-px) for i in (0,2)];yy=[ay+s*(bb[i]-py) for i in (1,3)]
  if min(xx)<0 or max(xx)>64 or min(yy)<0 or max(yy)>64:raise ValueError('Whole encounter body would clip')
  p=HERE/'native-v2'/r['unit']/(r['role']+'.png');p.parent.mkdir(parents=True,exist_ok=True);out.save(p)
  name=f"Content/Sprites/runeterra/demacia/creatures/{r['unit']}/{r['role']}.png";prior=checked(previous['candidates'][name],previous['recipe_sha256'][previous['candidates'][name]])
  recipe=json.loads(prior.read_text());recipe['source']=rel(p);recipe['source_sha256']=sha(p);recipe['size']=[64,64]
  recipe['projection_contract']={'source':rel(parent),'source_sha256':sha(parent),'source_facing':'right','canvas':[64,64],'anchor':[37,60],'pivot':[197,266],'scale':s,'mirrored':r['mirrored'],'native_field':'mapAttackFromLeft' if r['role']=='attackLeft' else 'mapAttackFromRight','native_required_facing':'right' if r['role']=='attackLeft' else 'left','authored_contact_shift_from_map_equivalent':[-11,0],'basis':'Separate encounter reaction composition calibrated to actual64px original comparison.37,60 is authored composition, not a mandatory native engine pivot.'}
  recipe['producer_inputs']=recipe['producer_inputs']+sourcepins
  recipe['technical_revision']={'version':2,'rule':'ActualDemaciaAvWattak64x64consumer; directly reproject whole450x400parent at uniform0.55scale and authored37,60contact, elevenpixelsleftofmap-equivalent48,60fornativelegibility; attackLeftfacesRIGHT, attackRightfacesLEFT. Neverstretch/cropV1map-sizedPNG. Nativeobservationpending.','native_verified':False}
  rp=HERE/'candidates-v2'/f"{r['unit']}-{r['role']}.json";dump(rp,recipe);output['candidates'][name]=rel(rp)
  projections.append({'unit':r['unit'],'role':r['role'],'source_parent':rel(parent),'sha256':sha(p),'canvas':[64,64],'anchor':[37,60],'scale':s,'authored_contact_shift_from_map_equivalent':[-11,0],'visible_source_alpha8_bounds':list(bb),'projected_alpha8_bounds':[min(xx),min(yy),max(xx),max(yy)],'facing':'left' if r['mirrored'] else 'right'})
 output['recipe_sha256']={name:sha(PROJECT/name) for name in output['candidates'].values()};output['encounter_revision']=projections
 dump(HERE/'candidate-selection-v2.json',output)
 receipt={'ok':True,'status':'authored configuration; unselected source candidate','selection_sha256':sha(HERE/'candidate-selection-v2.json'),'changed_role_count':4,'projections':projections,'native_verified':False,'release_accepted':False}
 if args.report:dump(args.report,receipt)
 print(json.dumps(receipt))
if __name__=='__main__':main()
