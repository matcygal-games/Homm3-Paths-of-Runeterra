"""Freeze reviewed V6 actual sources into110 isolated recipes, never canonical."""
from pathlib import Path
from copy import deepcopy
from PIL import Image
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'candidate-final-v12';BASE=HERE/'candidate-final-v10'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def setsrc(r,p):r.update(source=p.relative_to(ROOT).as_posix(),source_sha256=sha(p),sha256=sha(p))
def main():
 s=deepcopy(load(BASE/'selection.json'));index=load(HERE/'native-transforms-v12/states.json');by={r['state']:r for r in index['states']};f=load(BASE/'factions.candidate.json');native=HERE/'terrain/final-native-v12-proposal.png';merge=HERE/'terrain-repairs-v6/merge-receipt-v1.json'
 for r in s['states']:
  q=by[r['state']];r.update(native_layer=q['frame']['path'],native_layer_sha256=q['frame']['sha256'],native_z=q['native_z'],alpha8_bbox=q['alpha8_bbox'],entrance_intent=q['entrance'],actual_physical_record=q)
  if q['transform']:
   bb=q['alpha8_bbox'];r.update(native_position=bb[:2],native_size=[bb[2]-bb[0],bb[3]-bb[1]],composition_rectangle=[bb[0],bb[1],bb[2]-bb[0],bb[3]-bb[1]],selected_whole_source_transform=q['transform'])
  f['noxus']['town']['structures'][r['state']]['z']=q['native_z']
 s['terrain'].update(native=native.relative_to(ROOT).as_posix(),native_sha256=sha(native),bounded_repairs_v6=ref(merge));s['terrain']['fort_caps_v8']=ref(HERE/'terrain-repairs-v8/fort-caps/receipt-v1.json');s['terrain']['landing_connectors_v9']=ref(HERE/'terrain-repairs-v9/landing-connectors/receipt-v1.json');s['terrain']['arena_caps_v10']=ref(HERE/'terrain-repairs-v10/arena-caps/receipt-v1.json');s['terrain']['final_corners_v12']=ref(HERE/'terrain-repairs-v12/final-corners/receipt-v1.json');s['source_contact_roles_v12']=ref(HERE/'physical-roles-v12/annotations.json');pins={}
 for name in s['recipes']:
  r=load(BASE/'candidate-recipes'/name);state=r.get('building');q=by.get(state)
  if name=='assets/recipes/town/background.json':
   setsrc(r,native);r['generation']['bounded_repairs_v6']={'merge':ref(merge),'script':ref(HERE/'compose_repairs_v6.py'),'source_background':load(merge)['base'],'patches':load(merge)['patches'],'menagerie_generation':ref(HERE/'terrain-repairs-v6/menagerie-proposal/generation-record-v2.json'),'crimson_generation':ref(HERE/'terrain/crimson-apron-generation-v6.json'),'geometric_admission':False}
    # bounded Fort cap provenance stays separate from original wholeplate ancestry
  if name=='assets/recipes/town/background.json':r['generation']['fort_caps_v8']={'receipt':ref(HERE/'terrain-repairs-v8/fort-caps/receipt-v1.json'),'generation_record':ref(HERE/'terrain-repairs-v8/fort-caps/generation-record-v1.json'),'script':ref(HERE/'compose_fort_caps_v8.py')}
  if name=='assets/recipes/town/background.json':r['generation']['landing_connectors_v9']={'receipt':ref(HERE/'terrain-repairs-v9/landing-connectors/receipt-v1.json'),'generation_record':ref(HERE/'terrain-repairs-v9/landing-connectors/generation-record-v1.json'),'script':ref(HERE/'compose_landing_connectors_v9.py')}
  if name=='assets/recipes/town/background.json':r['generation']['arena_caps_v10']={'receipt':ref(HERE/'terrain-repairs-v10/arena-caps/receipt-v1.json'),'generation_record':ref(HERE/'terrain-repairs-v10/arena-caps/generation-record-v1.json'),'script':ref(HERE/'compose_arena_caps_v10.py')}
  if name=='assets/recipes/town/background.json':r['generation']['final_corners_v12']={'receipt':ref(HERE/'terrain-repairs-v12/final-corners/receipt-v1.json'),'script':ref(HERE/'compose_final_corners_v12.py')}
  if q and q['transform']:
   folder=(ROOT/q['frame']['path']).parent
   if name.endswith('-animation.json'):
    fr=r['groups'][0]['frames'][0];setsrc(fr,ROOT/q['frame']['path']);r.update(source_sha256=q['frame']['sha256'],sha256=q['frame']['sha256'])
   elif name.endswith('-area.json'):setsrc(r,folder/'area.png')
   elif name.endswith('-border.json'):setsrc(r,folder/'border.png')
   r['generation']['reviewed_whole_source_transform_v6']={'index':ref(HERE/'native-transforms-v12/states.json'),'transform':q['transform'],'source_before':q['source_before'],'actual_selected_frame':q['frame'],'script':ref(HERE/'build_transform_packet_v7.py')}
   r['building_contract']['full_canvas_placement']['z']=q['native_z'];bb=q['alpha8_bbox'];r['building_contract']['native_ground_contact']=[bb[0],bb[1],bb[2]-bb[0],bb[3]-bb[1]]
  if name=='assets/recipes/town/buildingIcons.json':
   for frame in r['frames']:
    q=by[frame['building']]
    if q['construction']:setsrc(frame,ROOT/q['construction']['path'])
   r['generation']['reviewed_whole_source_transform_v6']=ref(HERE/'native-transforms-v12/states.json')
  p=OUT/'candidate-recipes'/name;write(p,r);pins[name]=sha(p)
 s['recipes']=pins;s['source_packet_v6']={'states':ref(HERE/'native-transforms-v12/states.json'),'entries':ref(HERE/'entry-spans-v3/entries.json'),'merge':ref(merge),'script':ref(Path(__file__)),'geometric_admission':False};write(OUT/'selection.json',s);write(OUT/'factions.candidate.json',f)
 # Exact selected-site scenes, including optional states, rather than dictionary-order assumptions.
 report=ROOT/'build/reports/complete-town-20261027-v2/final-v12';report.mkdir(parents=True,exist_ok=True);bg=Image.open(native).convert('RGBA');bg.save(report/'empty-native.png')
 for mode in ('full','base','early','coast','grail','guild-absent'):
  chosen=[site['states'][0] if mode=='base' else site['top'] for site in s['sites'] if site['id'] not in ('coast','grail')]
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  if mode=='coast':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  im=bg.copy()
  for state in sorted(chosen,key=lambda k:by[k]['native_z']):im.alpha_composite(Image.open(ROOT/by[state]['frame']['path']).convert('RGBA'))
  im.save(report/(mode+'-native.png'))
 print(json.dumps({'candidate':ref(OUT/'selection.json'),'factions':ref(OUT/'factions.candidate.json'),'recipes':len(pins),'terrain':ref(native)}))
if __name__=='__main__':main()
