"""Select a genuinely painted hidden keep terrace, preserving approved BL2."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageChops
import hashlib,json,copy
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/defenses-terrace-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def save(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def main():
 REPORT.mkdir(parents=True,exist_ok=False)
 indexpath=HERE/'states-hidden-support-v3.json';old=json.loads(indexpath.read_text())
 if sha(indexpath)!='86adc4994e4a0944c257fd65c4157ee8d6c316dc8cb3686b0d45ef0afa1cc1ae':raise ValueError('Previous coordinated index changed')
 oldbg=PROJECT/old['background']
 if sha(oldbg)!=old['background_sha256']:raise ValueError('Previous hidden support source changed')
 master=HERE/'defenses-hidden-support-master-v1.png'
 # These are genuine black letterbox rows in the raw built-in imagegen result,
 # not a creative crop of architectural content or a per-building warp.
 content_crop=[0,85,2170,640]
 native=ImageOps.fit(Image.open(master).convert('RGB').crop(content_crop),(195,50),method=Image.Resampling.LANCZOS)
 path=HERE/'defenses-hidden-support-native-v1.png'
 if native.tobytes()!=Image.open(path).convert('RGB').tobytes():raise ValueError('Held one-fit native source changed')
 box=[90,70,285,120];delta=[0,3]
 baseline=Image.open(oldbg).convert('RGBA');proposal=baseline.copy();proposal.paste(native,(box[0]+delta[0],box[1]+delta[1]))
 planned=Image.new('L',(800,374));polygon=[[103,80],[148,85],[189,89],[231,94],[276,102],[280,111],[233,109],[190,104],[147,99],[102,91]]
 ImageDraw.Draw(planned).polygon([tuple(p) for p in polygon],fill=255)
 budget=Image.open(HERE/'approved-full-opaque-budget.png').convert('L');mask=ImageChops.multiply(planned,budget)
 maskpath=HERE/'defenses-selected-hidden-support-mask-v1.png';mask.save(maskpath)
 selected=Image.composite(proposal,baseline,mask);bgpath=HERE/'background-hidden-support-v4.png';selected.save(bgpath)
 scene=selected.copy()
 for key in old['full_scene_states']:
  row=old['states'][key];path=PROJECT/row['frame']
  if sha(path)!=row['frame_sha256']:raise ValueError('Selected building changed')
  scene.alpha_composite(Image.open(path).convert('RGBA'))
 approval=HERE/'approved-full-source-v1.png'
 if scene.convert('RGB').tobytes()!=Image.open(approval).convert('RGB').tobytes():raise ValueError('Approved full changed')
 scene.convert('RGB').save(REPORT/'full-native.png');selected.convert('RGB').save(REPORT/'empty-native.png')
 for label,states in [('base',old['base_scene_states']),('early',['villageHall','fort','tavern','dwellingLvl1'])]:
  image=selected.copy()
  for k in sorted(states,key=lambda k:old['states'][k]['z']):image.alpha_composite(Image.open(PROJECT/old['states'][k]['frame']).convert('RGBA'))
  image.convert('RGB').save(REPORT/(label+'-native.png'))
 new=copy.deepcopy(old);new['cohort']='BL2-approved-hidden-support-v4-source-candidate';new['background']=ref(bgpath)['path'];new['background_sha256']=sha(bgpath)
 ip=HERE/'states-hidden-support-v4.json';save(ip,new)
 receipt={'status':'authored configuration','scope':'Genuine hidden keep-platform candidate; exact approved full and35frames preserved. Actual full physical verification remains pending.',
  'before_background':ref(oldbg),'source_master':ref(master),'raw_content_crop':content_crop,'one_uniform_fit':[195,50],
  'native_source':ref(HERE/'defenses-hidden-support-native-v1.png'),'native_context':box,'whole_painted_crop_registration':delta,
  'source_prompt':ref(HERE/'defenses-hidden-support-prompt-v1.txt'),'context_controls':[ref(HERE/'defenses-empty-context-v1.png'),ref(HERE/'defenses-footing-context-v1.png')],
  'planned_polygon':polygon,'selected_mask':ref(maskpath),'selected_pixels':mask.histogram()[255],
  'new_background':ref(bgpath),'state_index':ref(ip),'approved_full':ref(approval),'approved_full_decoded_RGB_changed_pixels':0,
  'selector':ref(Path(__file__).resolve()),'physical_baseline_passed':False,'native_verified':False}
 save(HERE/'defenses-hidden-support-selection-v1.json',receipt)
 print(json.dumps({'cohort':sha(ip),'background':sha(bgpath),'approved_full':sha(REPORT/'full-native.png'),'selected_pixels':mask.histogram()[255]}))
if __name__=='__main__':main()
