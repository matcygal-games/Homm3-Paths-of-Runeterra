"""Apply coordinator-authorized whole-state Fort/Citadel registration only.

The selected fully built Castle scene stays exact. All prior35 inputs are
preserved; this writes2 replacement states and records every derived source.
"""
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter
import hashlib,json,copy
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/lower-defense-registration-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def save(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def icon(layer,size):
 crop=layer.crop(layer.getchannel('A').getbbox());crop.thumbnail((size[0]-4,size[1]-4),Image.Resampling.LANCZOS)
 out=Image.new('RGBA',size);out.alpha_composite(crop,((size[0]-crop.width)//2,(size[1]-crop.height)//2));return out
def main():
 REPORT.mkdir(parents=True,exist_ok=False);out=HERE/'lower-defense-registration-v1';out.mkdir(exist_ok=False)
 ip=HERE/'states-hidden-support-v4.json';old=json.loads(ip.read_text())
 if sha(ip)!='c624cadb61d776c8b99cdf569c48c6589751e7050beb0e4486a6c7be94d1b387':raise ValueError('Held keep terrace cohort changed')
 new=copy.deepcopy(old);records={}
 for state,dy in [('fort',-2),('citadel',-1)]:
  row=old['states'][state];before=PROJECT/row['frame'];raw=PROJECT/row['source'];matte=PROJECT/row['alpha_mask']
  for p,k in [(before,'frame_sha256'),(raw,'source_sha256'),(matte,'alpha_mask_sha256')]:
   if sha(p)!=row[k]:raise ValueError('Held lower state source changed: '+state)
  original=Image.open(before).convert('RGBA');a=original.getchannel('A');bbox=a.getbbox()
  if bbox[1]+dy<0 or bbox[3]+dy>374:raise ValueError('Whole variant would clip an actual visible pixel')
  registered=Image.new('RGBA',(800,374));delta=[row['delta'][0],row['delta'][1]+dy]
  registered.alpha_composite(Image.open(raw).convert('RGBA'),tuple(delta))
  alpha=Image.new('L',(800,374));alpha.paste(Image.open(matte).convert('L'),(0,dy));registered.putalpha(alpha)
  translated=Image.new('RGBA',(800,374));translated.paste(original,(0,dy))
  visible=alpha.point(lambda x:255 if x else 0);d=ImageChops.difference(registered.convert('RGB'),translated.convert('RGB'));r,g,b=d.split();drift=ImageChops.multiply(ImageChops.lighter(ImageChops.lighter(r,g),b),visible)
  if drift.getbbox():raise ValueError('Registered visible RGB differs from actual unchanged painted source')
  folder=out/state;folder.mkdir();registered.save(folder/'layer.png');alpha.save(folder/'alpha.png')
  full=alpha.point(lambda a:255 if a>=8 else 0);area=Image.new('RGBA',(800,374));area.putalpha(full);area.save(folder/'area.png')
  edge=ImageChops.subtract(full.filter(ImageFilter.MaxFilter(3)),full.filter(ImageFilter.MinFilter(3)));border=Image.new('RGBA',(800,374),(255,235,80,0));border.putalpha(edge);border.save(folder/'border.png')
  icon(registered,(58,64)).save(folder/'campaign.png');icon(registered,(150,70)).save(folder/'construction.png')
  current=new['states'][state];current['delta']=delta;current['entrance']=[row['entrance'][0],row['entrance'][1]+dy]
  current['alpha_mask']=ref(folder/'alpha.png')['path'];current['alpha_mask_sha256']=sha(folder/'alpha.png')
  current['alpha_bounds']=list(alpha.getbbox());current['visible_pixels']=full.histogram()[255]
  for role,name in [('frame','layer.png'),('area','area.png'),('border','border.png'),('campaign','campaign.png'),('construction','construction.png')]:current[role]=ref(folder/name)['path'];current[role+'_sha256']=sha(folder/name)
  records[state]={'before_frame':ref(before),'after_frame':ref(folder/'layer.png'),'before_source_delta':row['delta'],'after_source_delta':delta,'whole_registration_change':[0,dy],'painted_source':ref(raw),'before_matte':ref(matte),'after_matte':ref(folder/'alpha.png'),'visible_pixels_clipped':0,'visible_RGB_changed_after_registration':0,
   'construction_icon_unchanged':sha(PROJECT/row['construction'])==sha(folder/'construction.png'),'campaign_icon_unchanged':sha(PROJECT/row['campaign'])==sha(folder/'campaign.png')}
 for key,row in old['states'].items():
  if key not in records and row!=new['states'][key]:raise ValueError('Unrelated state changed')
 bg=Image.open(PROJECT/new['background']).convert('RGBA')
 for label,states in [('full',new['full_scene_states']),('base',new['base_scene_states']),('early',['villageHall','fort','tavern','dwellingLvl1']),('citadel-without-leviathan',[s if s!='castle' else 'citadel' for s in new['full_scene_states'] if s!='dwellingUpLvl7'])]:
  scene=bg.copy()
  for key in sorted(states,key=lambda k:new['states'][k]['z']):scene.alpha_composite(Image.open(PROJECT/new['states'][key]['frame']).convert('RGBA'))
  scene.convert('RGB').save(REPORT/(label+'-native.png'))
 if sha(REPORT/'full-native.png')!='4f8cac4f1801ed366e0bacd4934084e9b76e0d25c282b3f3b36fda3835cd0712':raise ValueError('Selected approved full changed')
 new['cohort']='BL2-approved-hidden-support-v5-lower-defense-registration';new['lower_state_registration_source']=ref(out/'registration-inputs.json') if (out/'registration-inputs.json').exists() else None
 # Bind the written input receipt before selecting its cohort pointer.
 inputs={'status':'authored configuration','coordinator_authorization':'Root explicitly authorizes Fort up2px / Citadel up1px, subject to actual complete silhouette/support/entry/click checks; selected fully built Castle/full locked to4f8.',
  'input_cohort':ref(ip),'helper':ref(Path(__file__).resolve()),'states':records,'unchanged_state_count':33,'unchanged_selected_top_state_count':16,'approved_full_changed_pixels':0,'physical_baseline_passed':False,'native_verified':False}
 save(out/'registration-inputs.json',inputs);new['lower_state_registration_source']=ref(out/'registration-inputs.json');save(HERE/'states-hidden-support-v5.json',new)
 print(json.dumps({'cohort':sha(HERE/'states-hidden-support-v5.json'),'changed_states':list(records),'33others_unchanged':True,'approved_full':sha(REPORT/'full-native.png')}))
if __name__=='__main__':main()
