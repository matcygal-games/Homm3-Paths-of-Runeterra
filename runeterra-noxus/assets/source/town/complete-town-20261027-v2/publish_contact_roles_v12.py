"""Source-backed own-entry tread role correction; preserve every structural foot."""
from pathlib import Path
from copy import deepcopy
from PIL import Image,ImageChops
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'physical-roles-v12'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 p=HERE/'native-transforms-v7/states.json';index=deepcopy(json.loads(p.read_text()));rolespath=HERE/'geometry-final-v2/source-verified-entry-contact-roles-v1/index.json';roles=json.loads(rolespath.read_text());by={r['state']:r for r in index['states']};result=[]
 for source in roles['states']:
  state=source['state'];r=by[state];oldref=source['original_full_root'];roleref=source['classified_actual_own_entry_bottom_contact'];treadref=source['complete_own_horizontal_treads']
  for a in [oldref,roleref,treadref]:assert sha(ROOT/a['path'])==a['sha256']
  assert r['foundation_mask']==oldref and r['own_treads_mask']==treadref;old=Image.open(ROOT/oldref['path']).convert('L');role=Image.open(ROOT/roleref['path']).convert('L');treads=Image.open(ROOT/treadref['path']).convert('L')
  assert not ImageChops.subtract(role,old).getbbox() and not ImageChops.subtract(role,treads).getbbox();assert role.histogram()[255]==source['pixels'];new=ImageChops.subtract(old,role);assert ImageChops.lighter(new,role).tobytes()==old.tobytes();assert new.getbbox()
  folder=OUT/state;folder.mkdir(parents=True,exist_ok=True);dest=folder/'foundation.png';new.save(dest,compress_level=9);owned=folder/'classified-own-entry-contact.png';role.save(owned,compress_level=9)
  r['foundation_mask']=ref(dest);r['actual_foundation_pixels']=new.histogram()[255];r['complete_structural_and_entry_contact_mask']=oldref;r['complete_physical_contact_pixels']=old.histogram()[255];r['entry_contact_role_mask']=ref(owned);r['contact_role_correction']={'authority':roles['authority'],'exact_source_role':source['role'],'reviewed_role_index':ref(rolespath),'original_complete_contact':oldref,'classified_own_entry_pixels':source['pixels'],'all_nonentry_wall_plinth_contacts_preserved':True,'full_door_treads_body_silhouette_frame_unchanged':True,'complete_contact_union_exact':True};result.append({'state':state,'structural_foundation':ref(dest),'entry_contact':ref(owned),'original_complete_contact':oldref,'classified_entry_pixels':source['pixels'],'structural_pixels':r['actual_foundation_pixels'],'complete_union_exact':True})
 index['base_state_index']=ref(p);index['script']=ref(Path(__file__));index['source_contact_role_partition']=ref(rolespath);target=HERE/'native-transforms-v12/states.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(index,indent=2)+'\n');OUT.mkdir(parents=True,exist_ok=True);(OUT/'annotations.json').write_text(json.dumps({'status':'authored configuration','scope':'Exact source-backed partition ONLY attached own-entry treads versus structural foundation; every original physical contact remains in structural OR entry role. No wall/plinth omitted; all36 source frames/fullentries unchanged.','source_role_index':ref(rolespath),'base_index':ref(p),'new_index':ref(target),'states':result,'native_verified':False,'release_accepted':False},indent=2)+'\n');print(json.dumps({'index':ref(target),'partitioned_entry_pixels':sum(x['classified_entry_pixels']for x in result),'states':result}))
if __name__=='__main__':main()
