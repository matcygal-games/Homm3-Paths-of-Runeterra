"""One independently identified fabric-canopy projection, actual source evidence.

This is an opt-in schema/code proposal, not an admitted complete town baseline.
The narrow source-floor ribbon follows the painted stair and lower civic street;
closed stalls/counter posts occupy a separate real lower foreground footprint.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
OUT=HERE/'market-projection-proposal-v1';OUT.mkdir(exist_ok=False)
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
index_path=HERE/'localized-ground-selection-v2/states.json';index=json.loads(index_path.read_text())
roles_path=HERE/'source-contact-roles-final-v1/role-receipt.json';roles=json.loads(roles_path.read_text())
frames={k:{'path':r['frame'],'sha256':r['frame_sha256']}for k,r in index['states'].items()}
body=Image.open(PROJECT/frames['marketplace']['path']).getchannel('A').point(lambda v:255 if v>=128 else 0)
contours=[[[354,297],[376,301],[405,302],[432,303],[460,302],[488,302],[515,299],[546,296],[548,320],[514,324],[486,326],[451,326],[421,325],[396,322],[372,321],[354,319]]]
outline=Image.new('L',(800,374));d=ImageDraw.Draw(outline)
for ps in contours:d.polygon(list(map(tuple,ps)),fill=255)
footprint=ImageChops.multiply(outline,body)
floor=Image.new('L',(800,374));ImageDraw.Draw(floor).line([(420,263),(420,282),(550,286)],fill=255,width=5)
support=Image.open(HERE/'fixed-floor-registration-study-v1/fixed-source-support.png').convert('L');stairs=Image.open(HERE/'fixed-floor-registration-study-v1/fixed-source-stairs.png').convert('L')
floor=ImageChops.multiply(floor,ImageChops.lighter(support,stairs))
projection=ImageChops.multiply(floor,body)
entry=Image.open(PROJECT/roles['states']['marketplace']['own_entry_contact']['path']).convert('L')
for name,im in [('actual-body',body),('closed-ground',footprint),('source-floor',floor),('occluded-floor',projection),('own-entry-contacts',entry)]:im.save(OUT/(name+'.png'))
row={'state':'marketplace','projection_type':'raised-canopy','source_case':None,'occluded_floor_mask':ref(OUT/'occluded-floor.png'),'closed_ground_mask':ref(OUT/'closed-ground.png'),'source_floor_mask':ref(OUT/'source-floor.png'),'own_entry_contacts_mask':ref(OUT/'own-entry-contacts.png')}
background={'path':index['background'],'sha256':index['background_sha256']}
full=Image.open(PROJECT/background['path']).convert('RGBA');absent=full.copy()
for k in index['full_scene_states']:
 actor=Image.open(PROJECT/frames[k]['path']).convert('RGBA');full.alpha_composite(actor)
 if k!='marketplace':absent.alpha_composite(actor)
full.save(OUT/'full-native.png',compress_level=9,optimize=False);absent.save(OUT/'canopy-absent-native.png',compress_level=9,optimize=False)
overlay=absent.copy();layer=Image.new('RGBA',(800,374),(255,40,170,0));layer.putalpha(projection.point(lambda v:180 if v else 0));overlay=Image.alpha_composite(overlay,layer);overlay.save(OUT/'source-intersection-overlay.png')
case={'kind':'source-ground-projection-v1','state':'marketplace','projection_type':'raised-canopy','frame':frames['marketplace'],'background':background,
 'reason':'Independent native-pixel review confirms pale raised fabric canopy at420268 projects over the actual continuous white main-stair foot and lower civic street; stall soles occupy the distinct lower foreground counter platform at311–320. The canopy is not a ground wall and the actual closed stalls remain blocked.',
 'occupied_level':'Lower foreground closed stalls/counter platform with actual timber soles at311–320',
 'behind_floor_level':'Higher rear main-stair foot and civic street, visible in actual foreground-absent source',
 'floor_observation':'Five-native-pixel ribbon within independently authored actual stair/paving contours, following420263→420282→550286; no cliff, facade face or guessed unseen passage is admitted.',
 'closed_ground_contours':contours,'visible_floor_witnesses':[[420,263],[550,286]],'scene_states':index['full_scene_states'],
 'evidence':{'complete_scene':ref(OUT/'full-native.png'),'cover_absent_scene':ref(OUT/'canopy-absent-native.png'),'intersection_overlay':ref(OUT/'source-intersection-overlay.png')},
 **{k:v for k,v in row.items()if k not in ('state','projection_type','source_case')}}
save(OUT/'source-case.json',case);row['source_case']=ref(OUT/'source-case.json');save(OUT/'projection-record.json',row)
save(OUT/'proposal-receipt.json',{'status':'design proposal','source_index':ref(index_path),'contact_roles':ref(roles_path),'record':ref(OUT/'projection-record.json'),'shared_helper_modified':False,'actual_whole_town_baseline_passed':False,'scope':'Exact bounded independently identified Market fabric-canopy case only; no generic roof/facade permission.'})
print({'record':ref(OUT/'projection-record.json'),'projection_pixels':projection.histogram()[255],'closed_footprint_pixels':footprint.histogram()[255]})
