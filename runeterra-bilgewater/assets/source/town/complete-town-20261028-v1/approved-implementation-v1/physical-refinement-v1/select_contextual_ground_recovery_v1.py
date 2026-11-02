"""Apply frozen genuinely painted floor recoveries only below opaque actors."""
from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
OUT=HERE/'contextual-ground-recovery-v1'
SOURCE_PLAN=HERE/'complete-ground-recoveries-v1/plan.json'
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
plan_path=SOURCE_PLAN;plan=json.loads(plan_path.read_text())
index=json.loads((PROJECT/plan['source_index']['path']).read_text())
ground=Image.open(PROJECT/index['background']).convert('RGBA')
size=ground.size
full_alpha=Image.new('L',size)
for key in index['full_scene_states']:
 a=Image.open(PROJECT/index['states'][key]['frame']).getchannel('A').point(lambda v:255 if v==255 else 0)
 full_alpha=ImageChops.lighter(full_alpha,a)
master=Image.open(OUT/'master-raw.png').convert('RGBA')
ratio=800/master.width
scaled_master=master.resize((800,math.ceil(master.height*ratio)),Image.Resampling.LANCZOS)
registered=scaled_master.crop((0,0,800,374))
registered.save(OUT/'registered-native.png',compress_level=9,optimize=False)
recovered=ground.copy();rows={}
union=Image.new('L',size)
for key,row in plan['plots'].items():
 polygon=Image.new('L',size);ImageDraw.Draw(polygon).polygon(list(map(tuple,row['polygon'])),fill=255)
 box=polygon.getbbox();w,h=box[2]-box[0],box[3]-box[1]
 canvas=registered.copy()
 scale=ratio
 selected=ImageChops.multiply(polygon,full_alpha)
 recovered=Image.composite(canvas,recovered,selected)
 for name,im in [('painted-native',canvas),('frozen-plane',polygon),('selected-opaque-source',selected)]:im.save(OUT/(key+'-'+name+'.png'),compress_level=9,optimize=False)
 union=ImageChops.lighter(union,selected)
 rows[key]={'source':ref(OUT/(key+'-painted-native.png')),'plane':ref(OUT/(key+'-frozen-plane.png')),'selection':ref(OUT/(key+'-selected-opaque-source.png')),'whole_uniform_scale':scale,'native_box':list(box),'selected_pixels':sum(bool(v)for v in selected.get_flattened_data()),'observation':row['observation']}
bg=OUT/'background.png';recovered.save(bg,compress_level=9,optimize=False)
index['background']=ref(bg)['path'];index['background_sha256']=ref(bg)['sha256']
scenes={}
for name,keys in [('empty',[]),('base',index['base_scene_states']),('full',index['full_scene_states'])]:
 scene=recovered.copy()
 for k in keys:scene.alpha_composite(Image.open(PROJECT/index['states'][k]['frame']).convert('RGBA'))
 p=OUT/(name+'-native.png');scene.save(p,compress_level=9,optimize=False);scenes[name]=ref(p)
approved=Image.open(PROJECT/plan['approved_full']['path']).convert('RGBA')
full=Image.open(PROJECT/scenes['full']['path']).convert('RGBA')
difference=ImageChops.difference(full,approved)
changed=sum(any(v)for v in difference.getdata())
if changed:raise ValueError('Locked full pixels changed: '+str(changed))
(OUT/'states.json').write_text(json.dumps(index,indent=2,sort_keys=True)+'\n')
receipt={'status':'authored configuration','frozen_plan':ref(plan_path),'contextual_master':ref(OUT/'master-raw.png'),'contextual_prompt':ref(OUT/'prompt.txt'),'registered_native':ref(OUT/'registered-native.png'),'states':ref(OUT/'states.json'),'background':ref(bg),'plots':rows,'scenes':scenes,'approved_full_rgba_changed_pixels':changed,'architectural_frames_modified':False,'whole_physical_baseline_claimed':False}
(OUT/'selection-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps({'states':receipt['states'],'full_changed':changed,'plots':{k:v['selected_pixels']for k,v in rows.items()}}))
