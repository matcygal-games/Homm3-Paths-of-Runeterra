"""Whole lower-form placement study on FIXED actual source floor planes.

This never edits a terrain mask, role contour, frame or approved full source.
It reports bounded rigid alternatives only, for explicit source-owner adoption.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
OUT=HERE/'fixed-floor-registration-study-v2';OUT.mkdir(exist_ok=False)
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
index_path=HERE/'localized-ground-selection-v3/states.json';index=json.loads(index_path.read_text())
roles_path=HERE/'source-contact-roles-final-v2/role-receipt.json';roles=json.loads(roles_path.read_text())
support=Image.open(HERE/'public-source-ground-v2/support.png').convert('L');stairs=Image.open(HERE/'public-source-ground-v2/stairs.png').convert('L')
extra=Image.open(HERE/'localized-ground-selection-v3/all-selected-source-floor-tops.png').convert('L')
support=ImageChops.lighter(support,extra);stairs=ImageChops.subtract(stairs,extra)
support.save(OUT/'fixed-source-support.png');stairs.save(OUT/'fixed-source-stairs.png')
arr=np.asarray(support)>0;records={}
for key,row in index['states'].items():
 foot=Image.open(PROJECT/roles['states'][key]['structural_foundation']['path']).convert('L');ys,xs=np.nonzero(np.asarray(foot)>0)
 fixed=key in index['full_scene_states']or key in ('ship','shipyard','grail')
 candidates=[]
 if not fixed:
  for dy in range(-5,11):
   for dx in range(-5,6):
    tx=xs+dx;ty=ys+dy
    if tx.min()<0 or tx.max()>=800 or ty.min()<0 or ty.max()>=374:continue
    bad=int((~arr[ty,tx]).sum());candidates.append({'offset':[dx,dy],'unsupported_pixels':bad,'distance':abs(dx)+abs(dy)})
 candidates.sort(key=lambda r:(r['unsupported_pixels'],r['distance'],r['offset'][1],r['offset'][0]))
 current=int((~arr[ys,xs]).sum())
 records[key]={'current_unsupported':current,'approved_full_form_or_marine_fixed':fixed,'best_bounded_whole_offsets':candidates[:8]}
report={'status':'design proposal','source_index':ref(index_path),'contact_roles':ref(roles_path),'fixed_support':ref(OUT/'fixed-source-support.png'),'fixed_stairs':ref(OUT/'fixed-source-stairs.png'),'full_selected_forms_unchanged':True,'frames_or_contacts_or_terrain_modified':False,'states':records}
(OUT/'study.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:({'current':v['current_unsupported'],'best':v['best_bounded_whole_offsets'][:2]}if not v['approved_full_form_or_marine_fixed']else {'current':v['current_unsupported'],'fixed':True})for k,v in records.items()if v['current_unsupported']}))
