"""Pin selected BL2 full pixels and exact occlusion budget before hidden repairs."""
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import hashlib,json
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PROJECT=BASE.parents[3]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1'
APPROVED='4f8cac4f1801ed366e0bacd4934084e9b76e0d25c282b3f3b36fda3835cd0712'
COHORT='f3ebfb8dccde5e045cb4c7e60ac9c0be347bec456911b3d8ed93e87560f9d213'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    full=PROJECT/'build/reports/complete-town-20261028-v1/derived-v2/full-native.png'
    indexpath=BASE/'derived-v2/states.json'
    if sha(full)!=APPROVED or sha(indexpath)!=COHORT:raise ValueError('Approved scene/cohort drift')
    index=json.loads(indexpath.read_text())
    background=PROJECT/index['background']
    if sha(background)!=index['background_sha256']:raise ValueError('Background drift')
    scene=Image.open(background).convert('RGBA');opaque=Image.new('L',(800,374));pins=[];per_site={}
    for state in index['full_scene_states']:
        record=index['states'][state];path=PROJECT/record['frame']
        if sha(path)!=record['frame_sha256']:raise ValueError('Approved layer drift: '+state)
        layer=Image.open(path).convert('RGBA')
        scene=Image.alpha_composite(scene,layer)
        mask=layer.getchannel('A').point(lambda a:255 if a==255 else 0)
        opaque=ImageChops.lighter(opaque,mask)
        site=record['site'];per_site[site]=mask
        pins.append({'state':state,'path':record['frame'],'sha256':record['frame_sha256'],'z':record['z']})
    if scene.convert('RGB').tobytes()!=Image.open(full).convert('RGB').tobytes():raise ValueError('Approved full does not match selected source composition')
    opaque.save(HERE/'approved-full-opaque-budget.png')
    for site in ('sailors','captains','buhru'):
        per_site[site].save(HERE/(site+'-approved-opaque-budget.png'))
    image=Image.open(background).convert('RGBA')
    tint=Image.new('RGBA',image.size,(255,200,20,0));tint.putalpha(opaque.point(lambda a:80 if a else 0));Image.alpha_composite(image,tint).convert('RGB').save(REPORT/'hidden-repair-budget-study.png')
    record={'status':'authored configuration','selection':'User selected Bilgewater BL2 / Fully built; no visible changes requested.',
       'approved_full':{'path':rel(full),'sha256':APPROVED},'selected_cohort':{'path':rel(indexpath),'sha256':COHORT},
       'background':{'path':index['background'],'sha256':index['background_sha256']},
       'approved_full_decoded_RGB_reproduced_exactly':True,'approved_native_layers':pins,
       'hidden_background_repair_budget':{'path':rel(HERE/'approved-full-opaque-budget.png'),'sha256':sha(HERE/'approved-full-opaque-budget.png'),'opaque_pixels':opaque.histogram()[255],
          'rule':'Background pixel changes may occur only beneath alpha255 pixels in the exact approved full native state list. Every final full composite must retain all approved decoded RGB pixels.'},
       'unresolved_support_sites':['sailors','captains','buhru'],
       'restriction':'No clipped feet, support masks over cliff/water, relaxed public checks or invisible functional placeholders. Genuine terrain repair is allowed only where the approved full remains exactly identical; otherwise report exact conflict.',
       'native_verified':False,'release_accepted':False}
    (HERE/'approved-selection.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'approved_full_SHA':APPROVED,'opaque_pixels':record['hidden_background_repair_budget']['opaque_pixels'],'selection_record_SHA':sha(HERE/'approved-selection.json')}))
if __name__=='__main__':main()
