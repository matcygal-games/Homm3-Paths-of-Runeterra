"""Apply exactly three independently confirmed non-bearing role corrections.

Actor pixels are never changed. No terrain mask, desired support result, crop,
registration or negative-control input is read by this source-material writer.
"""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
OUT=HERE/'source-contact-roles-final-v1';OUT.mkdir(exist_ok=False)
PRIOR=HERE/'ownership-contact-roles-v3'
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def points(im):
 b=im.getbbox();return [[x,y]for y in range(b[1],b[3])for x in range(b[0],b[2])if im.getpixel((x,y))]if b else[]
annotation=json.loads((PRIOR/'annotations.json').read_text());prior=json.loads((PRIOR/'role-receipt.json').read_text())
corrections={'dwellingLvl5':[[698,111],[699,111]],'dwellingUpLvl1':[[145,241]]}
rows={}
for key,row in prior['states'].items():
 folder=OUT/key;folder.mkdir();struct=Image.open(PRIOR/key/'structural-foundation.png').convert('L');entry=Image.open(PRIOR/key/'own-entry-contact.png').convert('L')
 for xy in corrections.get(key,[]):
  if not struct.getpixel(tuple(xy)):raise ValueError('Expected confirmed non-bearing observation missing')
  struct.putpixel(tuple(xy),0)
 complete=ImageChops.lighter(struct,entry)
 if ImageChops.multiply(struct,entry).getbbox():raise ValueError('Contact roles overlap')
 for role,im in [('structural-foundation',struct),('own-entry-contact',entry),('complete-contact',complete)]:im.save(folder/(role+'.png'))
 annotation['states'][key]['foundation']={'pixels':points(struct)}
 if key in corrections:
  annotation['states'][key]['nonbearing_anatomy_preserved']=corrections[key]
  annotation['states'][key]['nonbearing_explanation']=('Long outboard decorative banner/flagstaff endpoints have no shoe or visible cap; complete staff remains actor anatomy.'if key=='dwellingLvl5'else'Raised right outer timber frame/cornice at145241 is seven pixels above actual lower material toe at140248 and has no shaft to a sole at145248; complete frame remains actor anatomy.')
 rows[key]={**row,'structural_foundation':ref(folder/'structural-foundation.png'),'own_entry_contact':ref(folder/'own-entry-contact.png'),'complete_contact':ref(folder/'complete-contact.png'),'structural_contact_pixels':len(points(struct)),'own_entry_contact_pixels':len(points(entry)),'complete_contact_pixels':len(points(complete))}
annotation['contact_role_partition']=rows
annotation['independent_nonbearing_role_corrections']={'ancestor':ref(PRIOR/'role-receipt.json'),'reviewer':'/root/ionia_creature_delivery','exact_role_pixels':corrections,'actual_actor_pixels_removed':0,'terrain_or_desired_result_read':False,'all35_states_retained':True}
annotation['selected_editable_sources']+= [ref(PRIOR/'role-receipt.json'),ref(PRIOR/'annotations.json'),ref(Path(__file__))]
(OUT/'annotations.json').write_text(json.dumps(annotation,indent=2,sort_keys=True)+'\n')
receipt={**prior,'states':rows,'independent_nonbearing_role_corrections':annotation['independent_nonbearing_role_corrections'],'status':'authored configuration','all35states_retained':len(rows)==35,'whole_physical_baseline_passed':False}
(OUT/'role-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print({'role_receipt':ref(OUT/'role-receipt.json'),'annotations':ref(OUT/'annotations.json'),'exact_nonbearing_roles_removed':3,'actors_modified':0})
