"""Select genuine hidden support repairs while preserving approved BL2 exactly."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps,ImageChops
import hashlib,json,copy
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PROJECT=BASE.parents[3]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1'
SPECS={
 'sailors':{'box':[50,215,170,275],'poly':[(63,241),(146,241),(151,249),(147,256),(114,256),(66,254)]},
 'captains':{'box':[515,120,611,176],'poly':[(529,140),(594,140),(599,147),(586,155),(531,155)]},
 'buhru':{'box':[583,192,727,250],'poly':[(594,212),(709,212),(712,221),(699,229),(602,227)]}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def main():
    approval=json.loads((HERE/'approved-selection.json').read_text())
    index_path=PROJECT/approval['selected_cohort']['path']
    if sha(index_path)!=approval['selected_cohort']['sha256']:raise ValueError('Approved cohort changed')
    old_index=json.loads(index_path.read_text());bgpath=PROJECT/old_index['background']
    if sha(bgpath)!=old_index['background_sha256']:raise ValueError('Approved baseline background changed')
    approved=PROJECT/approval['approved_full']['path']
    if sha(approved)!=approval['approved_full']['sha256']:raise ValueError('Approved full changed')
    budget=Image.open(HERE/'approved-full-opaque-budget.png').convert('L')
    old=Image.open(bgpath).convert('RGB');selected=old.copy();union=Image.new('L',old.size);records={}
    for name,spec in SPECS.items():
        box=spec['box'];size=(box[2]-box[0],box[3]-box[1]);master=HERE/(name+'-hidden-support-master-v2.png')
        crop=ImageOps.fit(Image.open(master).convert('RGB'),size,method=Image.Resampling.LANCZOS)
        native=HERE/(name+'-hidden-support-native-v2.png');crop.save(native)
        canvas=old.copy();canvas.paste(crop,(box[0],box[1]))
        planned=Image.new('L',old.size);ImageDraw.Draw(planned).polygon(spec['poly'],fill=255)
        mask=ImageChops.multiply(planned,budget)
        maskpath=HERE/(name+'-selected-hidden-support-mask-v1.png');mask.save(maskpath)
        selected=Image.composite(canvas,selected,mask);union=ImageChops.lighter(union,mask)
        records[name]={'genuine_master':{'path':rel(master),'sha256':sha(master)},'native_crop':{'path':rel(native),'sha256':sha(native)},
          'prompt':{'path':rel(HERE/(name+'-hidden-support-prompt-v2.txt')),'sha256':sha(HERE/(name+'-hidden-support-prompt-v2.txt'))},
          'native_context':box,'planned_support_polygon':spec['poly'],'actual_selected_mask':{'path':rel(maskpath),'sha256':sha(maskpath)},
          'selected_pixels':mask.histogram()[255],'method':'Genuine painted2D source; one uniform nativecrop conversion and technical masked selection under exact approved opaque full pixels.'}
    output=HERE/'background-hidden-support-v1.png';selected.convert('RGBA').save(output)
    changed=ImageChops.difference(selected,old)
    outside=ImageChops.multiply(changed.convert('L'),ImageChops.invert(budget))
    if outside.getbbox():raise ValueError('Visible approved background pixel changed')
    scene=selected.convert('RGBA')
    for state in old_index['full_scene_states']:
        row=old_index['states'][state];p=PROJECT/row['frame']
        if sha(p)!=row['frame_sha256']:raise ValueError('Approved building changed: '+state)
        scene=Image.alpha_composite(scene,Image.open(p).convert('RGBA'))
    difference=ImageChops.difference(scene.convert('RGB'),Image.open(approved).convert('RGB'))
    if difference.getbbox():raise ValueError('Approved full composite changed')
    scene.convert('RGB').save(REPORT/'approved-full-reproduced-v1.png');selected.save(REPORT/'empty-hidden-support-v1.png')
    new=copy.deepcopy(old_index);new['cohort']='BL2-approved-hidden-support-v1-source-candidate';new['background']=rel(output);new['background_sha256']=sha(output)
    new['approved_full_sha256']=approval['approved_full']['sha256'];new['approved_full_decoded_RGB_changes']=0
    new['physical_layout_status']='Genuine hidden-support candidate; all35 actual semantic contacts/approaches/public collector/negatives still require execution.'
    selectedindex=HERE/'states-hidden-support-v1.json';selectedindex.write_text(json.dumps(new,indent=2)+'\n')
    for name,states in [('base',new['base_scene_states']),('early',['villageHall','fort','tavern','dwellingLvl1']),('coast',new['full_scene_states']+['ship','grail'])]:
        image=selected.convert('RGBA')
        for state in sorted(states,key=lambda k:new['states'][k]['z']):image=Image.alpha_composite(image,Image.open(PROJECT/new['states'][state]['frame']).convert('RGBA'))
        image.convert('RGB').save(REPORT/(name+'-hidden-support-v1.png'))
    result={'status':'authored configuration','approval':approval['approved_full'],'approved_full_RGBA_composition_decoded_RGB_changed_pixels':0,
       'approved_full_reproduced':{'path':rel(REPORT/'approved-full-reproduced-v1.png'),'sha256':sha(REPORT/'approved-full-reproduced-v1.png')},
       'baseline_background':{'path':old_index['background'],'sha256':old_index['background_sha256']},'new_background':{'path':rel(output),'sha256':sha(output)},
       'selected_cohort':{'path':rel(selectedindex),'sha256':sha(selectedindex)},'support_recoveries':records,
       'all35_building_frames_unchanged':True,'background_pixels_changed_outside_approved_opaque_budget':0,
       'physical_baseline_passed':False,'native_verified':False,'release_accepted':False}
    (HERE/'hidden-support-selection-v1.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'approved_full_sha256':result['approved_full_reproduced']['sha256'],'full_changed_pixels':0,'background_sha256':sha(output),'cohort_sha256':sha(selectedindex)}))
if __name__=='__main__':main()
