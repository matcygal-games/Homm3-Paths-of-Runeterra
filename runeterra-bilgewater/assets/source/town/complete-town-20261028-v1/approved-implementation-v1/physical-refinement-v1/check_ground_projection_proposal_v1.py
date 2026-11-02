"""Executed actual-source controls for the proposed bounded ground semantics.

These validate the opt-in validator and intrusion predicates on real native
BL2 source pixels. They are NOT all35 positive consumer/negative-control passes.
All modified permission/floor/footprint references and source cases are repinned.
"""
from pathlib import Path
from copy import deepcopy
import sys,json,hashlib,importlib.util
import numpy as np
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5];WORKSPACE=PROJECT.parent
OUT=HERE/'projection-controls-v1';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_town_layout as layout
spec=importlib.util.spec_from_file_location('proposed_ground',HERE/'ground_projection_proposal_v1.py');proposed=importlib.util.module_from_spec(spec);spec.loader.exec_module(proposed)
spec=importlib.util.spec_from_file_location('binder',HERE/'bind_contract.py');binder=importlib.util.module_from_spec(spec);spec.loader.exec_module(binder)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def read(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
index=read(HERE/'localized-ground-selection-v2/states.json');anno=read(HERE/'source-contact-roles-final-v1/annotations.json')
images={k:Image.open(PROJECT/r['frame']).convert('RGBA')for k,r in index['states'].items()}
bodies={k:im.getchannel('A').point(lambda v:255 if v>=128 else 0)for k,im in images.items()}
physical={k:tuple(binder.trace(r[n])for n in ('foundation','door','approach'))for k,r in anno['states'].items()}
support=Image.open(HERE/'fixed-floor-registration-study-v1/fixed-source-support.png').convert('L');stairs=Image.open(HERE/'fixed-floor-registration-study-v1/fixed-source-stairs.png').convert('L')
land=Image.open(HERE/'public-source-ground-v2/land.png').convert('L');land=ImageChops.lighter(land,support)
water=Image.open(HERE/'public-source-ground-v2/water.png').convert('L')
record=read(HERE/'market-projection-proposal-v1/projection-record.json')
base_case=read(PROJECT/record['source_case']['path'])
contract={'frames':{k:{'path':r['frame'],'sha256':r['frame_sha256']}for k,r in index['states'].items()},'background':{'path':index['background'],'sha256':index['background_sha256']},'silhouette_plan':{'ground_projection_cases':[record]}}
base_hash=sha(WORKSPACE/'scripts/faction_town_layout.py');checks=[]
def validate(c):return proposed.validate_ground_projection_cases(layout,PROJECT,c,images,physical,bodies,support,stairs,land,water,set())
def check(name,fn,expected=None):
 try:
  result=fn();passed=expected is None;error=None
 except ValueError as exc:
  error=str(exc);passed=expected is not None and expected in error;result=None
 checks.append({'check':name,'passed':passed,'expected_rejection_contains':expected,'actual_error':error})
 if not passed:raise AssertionError(checks[-1])
 return result
default=deepcopy(contract);default['silhouette_plan'].pop('ground_projection_cases')
unchanged=check('default-no-opt-in-keeps-all35-full-source-bodies',lambda:validate(default))
if any(unchanged[k].tobytes()!=bodies[k].tobytes()for k in bodies):raise AssertionError('Default changed')
blockers=check('actual-source-Market-canopy-proposal-admitted',lambda:validate(contract))
if blockers['marketplace'].getpixel((420,268)):raise AssertionError('Raised canopy still blocks independently observed floor')
ground=Image.open(PROJECT/record['closed_ground_mask']['path']).convert('L')
foundation,door,_=physical['marketplace'];body=bodies['marketplace'];source_floor=Image.open(PROJECT/record['source_floor_mask']['path']).convert('L')
def nearest(mask,target):
 ys,xs=np.nonzero(np.asarray(mask)>0)
 return min(zip(map(int,xs),map(int,ys)),key=lambda p:abs(p[0]-target[0])+abs(p[1]-target[1]))
wall=nearest(ImageChops.subtract(ground,ImageChops.lighter(door,foundation)),(420,316))
frontage=nearest(ImageChops.subtract(ImageChops.multiply(door,body),foundation),(545,315))
def repinned_permission(name,target):
 folder=OUT/name;folder.mkdir();case=deepcopy(base_case);row=deepcopy(record)
 floor=source_floor.copy();ImageDraw.Draw(floor).line([(550,286),target],fill=255,width=1)
 projection=ImageChops.multiply(floor,body)
 floor.save(folder/'source-floor.png');projection.save(folder/'occluded-floor.png')
 for key,filename in [('source_floor_mask','source-floor.png'),('occluded_floor_mask','occluded-floor.png')]:case[key]=row[key]=ref(folder/filename)
 save(folder/'source-case.json',case);row['source_case']=ref(folder/'source-case.json')
 c=deepcopy(contract);c['silhouette_plan']['ground_projection_cases']=[row]
 save(folder/'repinned-contract.json',c);return c
check('fully-repinned-permission-cannot-open-real-closed-stall-wall',lambda:validate(repinned_permission('wall-intrusion',wall)),'closed ground wall/footprint')
check('fully-repinned-permission-cannot-open-visible-frontage',lambda:validate(repinned_permission('frontage-intrusion',frontage)),'visible frontage/entry')
# Existing intrusion checks must use the conservative returned ground blocker,
# not a foundation seam. Use a real foreground quay path into the closed stall.
wall_path=Image.new('L',(800,374));ImageDraw.Draw(wall_path).line([(550,318),wall],fill=255,width=1)
frontage_path=Image.new('L',(800,374));ImageDraw.Draw(frontage_path).line([(550,318),frontage],fill=255,width=1)
wall_path.save(OUT/'actual-ground-wall-intrusion-path.png');frontage_path.save(OUT/'actual-other-frontage-intrusion-path.png')
def wall_predicate():
 if layout._intersects(wall_path,ImageChops.subtract(blockers['marketplace'],door)):raise ValueError('Actual source ground wall still rejects intruding global path')
def frontage_predicate():
 if layout._intersects(frontage_path,blockers['marketplace']):raise ValueError('Actual source frontage still rejects other-building approach')
check('real-ground-wall-intrusion-remains-rejected',wall_predicate,'ground wall still rejects')
check('real-other-frontage-intrusion-remains-rejected',frontage_predicate,'frontage still rejects')
folder=OUT/'sparse-footprint';folder.mkdir();case=deepcopy(base_case);row=deepcopy(record);foundation.save(folder/'ground.png');row['closed_ground_mask']=case['closed_ground_mask']=ref(folder/'ground.png');save(folder/'source-case.json',case);row['source_case']=ref(folder/'source-case.json');sparse=deepcopy(contract);sparse['silhouette_plan']['ground_projection_cases']=[row];save(folder/'repinned-contract.json',sparse)
check('repinned-sparse-sole-mask-cannot-replace-closed-occupied-floor',lambda:validate(sparse),'actual source contour/body')
unknown=deepcopy(contract);unknown['silhouette_plan']['ground_projection_cases'][0]['projection_type']='anything-goes-roof'
check('unknown-projection-type-rejected',lambda:validate(unknown),'Unknown or duplicate')
if sha(WORKSPACE/'scripts/faction_town_layout.py')!=base_hash:raise ValueError('Shared helper changed during bounded controls; rerun against fresh helper')
receipt={'status':'authored configuration','scope':'Executed opt-in proposal validator and actual source-ground intrusion predicates only. This is not a complete all35 town baseline or meaningful whole-town displaced/stair/water/path-cut control suite.','base_shared_helper_sha256':base_hash,'proposal_helper':ref(HERE/'ground_projection_proposal_v1.py'),'record':ref(HERE/'market-projection-proposal-v1/projection-record.json'),'actual_source_witnesses':{'ground_wall':list(wall),'visible_frontage':list(frontage),'raised_canopy': [420,268]},'checks':checks,'passed':sum(r['passed']for r in checks),'failed':sum(not r['passed']for r in checks),'all35_actual_bodies_retained_in_default':True,'shared_helper_or_actors_modified':False,'whole_physical_baseline_passed':False}
save(OUT/'receipt.json',receipt);print(json.dumps({'checks':len(checks),'passed':receipt['passed'],'failed':receipt['failed'],'receipt':ref(OUT/'receipt.json')}))
