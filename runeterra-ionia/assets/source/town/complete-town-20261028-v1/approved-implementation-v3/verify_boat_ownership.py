"""Bounded boat-state regression against the genuine absence repair and v2 lock."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageChops
from assemble import HERE,PROJECT,read,dump,ref,sha,image,APPROVED
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v3'

def main():
 old=HERE.parent/'approved-implementation-v2'
 assert sha(old/'integration-packet.json')=='8c6c512efbd7673724662c2dacf2d832c9f53ce847c2beb4ecfd104306086323'
 assert sha(HERE/'approved-full.png')==APPROVED==sha(REPORT/'compiled-approved-full.png')
 recovery=image(HERE/'water-recovery/water-recovery-native.png');points=[(44,198),(45,195),(46,200),(24,190),(24,200),(39,208),(65,215),(52,195),(53,200)]
 background=image(HERE/'prepared/background.png');ship=image(HERE/'prepared/structures/ship/layer.png')
 checks=[]
 for point in points:
  expected=recovery.getpixel((point[0]-12,point[1]-173));row={'native_point':list(point),'genuine_absence_water_RGBA':list(expected),'ship_alpha':ship.getpixel(point)[3],'views':{}}
  for view in ('empty','absent-coast','dock','early','base','middle','grail'):
   actual=image(HERE/'views'/(view+'.png')).getpixel(point);row['views'][view]=actual==expected
  row['pass']=all(row['views'].values()) and row['ship_alpha']>0;checks.append(row)
 unchanged=[]
 for state in read(HERE/'frame-index.json')['frames']:
  if state=='ship':continue
  a=image(HERE/'prepared/structures'/state/'layer.png');b=image(old/'prepared/structures'/state/'layer.png')
  assert a.tobytes()==b.tobytes(),'Unrelated state pixels changed: '+state
  unchanged.append(state)
 delta=ImageChops.difference(background,image(old/'prepared/background.png'));mask=delta.convert('RGB').point(lambda v:255 if v else 0).convert('L').point(lambda v:255 if v else 0)
 bounds=mask.getbbox();assert bounds and bounds[0]>=12 and bounds[1]>=173 and bounds[2]<=86 and bounds[3]<=220
 (REPORT/'boat-ownership').mkdir(exist_ok=True);mask.save(REPORT/'boat-ownership/background-actual-change-mask.png')
 result={'status':'authored configuration','actual_unchanged_approved_full_PNG_sha256':APPROVED,'targeted_genuine_repair':ref(HERE/'water-recovery/water-recovery-native.png'),'source_master':ref(HERE/'water-recovery/water-recovery-master.png'),'executed_prompt':ref(HERE/'water-recovery/water-recovery-executed-prompt.txt'),'all_nine_observed_boat_feature_probes_pass':all(r['pass']for r in checks),'feature_probes':checks,'unrelated34_state_layer_RGBA_unchanged':len(unchanged)==34,'unchanged_states':unchanged,'actual_background_change_bounds':list(bounds),'no_outside_crop_background_changes':True,'artwork_generated_by_code':False,'native_execution':False,'release_accepted':False}
 dump(REPORT/'boat-ownership-receipt.json',result);print(json.dumps({k:result[k]for k in ('all_nine_observed_boat_feature_probes_pass','unrelated34_state_layer_RGBA_unchanged','actual_background_change_bounds')}));return 0 if result['all_nine_observed_boat_feature_probes_pass'] else 2

if __name__=='__main__':raise SystemExit(main())
