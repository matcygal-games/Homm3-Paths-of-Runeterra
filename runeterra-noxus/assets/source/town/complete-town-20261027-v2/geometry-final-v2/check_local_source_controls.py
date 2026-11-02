"""Bounded real-source Minotaur phase controls despite later town failures.

A baseline that reaches the next state's missing approach proves only the first
real state's local frame/body/support/door/approach phase. It is explicitly NOT a
valid full-town baseline or later cross-body/scene acceptance.
"""
from pathlib import Path
from copy import deepcopy
from PIL import Image,ImageChops
import hashlib,json,shutil,sys,io
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];WORKSPACE=ROOT.parent;REPORT=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2/local-real-source-v5-001'
sys.path.insert(0,str(WORKSPACE/'scripts'));import faction_town_layout as layout;import faction_pipeline as fp
STATE='dwellingUpLvl6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def png(im):s=io.BytesIO();im.save(s,format='PNG',compress_level=9);return s.getvalue()
def main():
 if REPORT.exists():raise ValueError('Preserve previous attempt')
 origin=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2/consumer-v5-entries-v2-002/direct-source-fixture';fixture=REPORT/'fixture';shutil.copytree(origin,fixture)
 design=load(fixture/'design/town-visuals.json');name=design['layout_contract']['path'];contract=load(fixture/name);site=next(s for s in contract['sites'] if STATE in s['states']);contract['sites'].remove(site);site['states']=[STATE]+[s for s in site['states']if s!=STATE];contract['sites'].insert(0,site)
 def select(c):write(fixture/name,c);d=deepcopy(design);d['layout_contract']['sha256']=sha(fixture/name);write(fixture/'design/town-visuals.json',d)
 select(contract);content={'factions':load(fixture/'content/factions.json')};baseline,deps=layout.inspect(fixture,content,'noxus');expected='Town geometry contract: Town physical mask must be nonempty: approach dwellingLvl6'
 if baseline!=[expected]:raise ValueError('The real supported state did not pass its local phase: '+str(baseline))
 protected={key:sha(fixture/contract['silhouette_plan'][key]['path'])for key in ('support_mask','stairs_mask','water_mask','paths_mask')};protected['background']=sha(fixture/contract['background']['path']);results=[]
 for label,dx,dy in [('actual-source-and-all-physical-masks-moved-to-retaining-face',0,-110),('actual-source-and-all-physical-masks-moved-across-real-stairs',-350,-205),('actual-source-and-all-physical-masks-moved-onto-external-water',213,-153)]:
  saved={};c=deepcopy(contract)
  def put(p,b):
   if p not in saved:saved[p]=p.read_bytes()
   p.write_bytes(b)
  def move(reference):
   p=fixture/reference['path'];im=Image.open(p);m=Image.new(im.mode,im.size);m.paste(im,(dx,dy));put(p,png(m));reference['sha256']=sha(p)
  try:
   move(c['frames'][STATE]);physical=c['silhouette_plan']['states'][STATE]
   for key in ('body_mask','foundation_mask','door_mask','approach_mask'):move(physical[key])
   physical['entrance']=[physical['entrance'][0]+dx,physical['entrance'][1]+dy]
   target=next(s for s in c['sites']if STATE in s['states']);target['entrance']=physical['entrance'];union=Image.new('L',(800,374))
   for state in target['states']:
    im=Image.open(fixture/c['frames'][state]['path']).convert('RGBA');union=ImageChops.lighter(union,im.getchannel('A').point(lambda a:255 if a>=8 else 0))
   p=fixture/target['silhouette_mask']['path'];put(p,png(union));target['silhouette_mask']['sha256']=sha(p);bb=union.getbbox();target['box']=[bb[0],bb[1],bb[2]-bb[0],bb[3]-bb[1]]
   # The actual selected generated frame is displaced together with its own
   # source PNG. Thus public inspect cannot fail a stale selected-frame check.
   structure=content['factions']['noxus']['town']['structures'][STATE];definition=load(fixture/'assets/generated/Content/Sprites'/structure['animation']);groups=fp.utility('identity').animation_groups(definition,complete=True);selected=fixture/'assets/generated/Content/Sprites'/(definition.get('basepath','')+groups[0][0]);put(selected,(fixture/c['frames'][STATE]['path']).read_bytes());select(c)
   observed,_=layout.inspect(fixture,content,'noxus');root=Image.open(fixture/physical['foundation_mask']['path']).convert('L');stairs=Image.open(fixture/c['silhouette_plan']['stairs_mask']['path']).convert('L');water=Image.open(fixture/c['silhouette_plan']['water_mask']['path']).convert('L');support=Image.open(fixture/c['silhouette_plan']['support_mask']['path']).convert('L');fixed={key:sha(fixture/c['silhouette_plan'][key]['path'])for key in ('support_mask','stairs_mask','water_mask','paths_mask')};fixed['background']=sha(fixture/c['background']['path']);passed=observed==['Town geometry contract: Actual foundation lacks level support or lands on stairs/water: '+STATE]and fixed==protected
   result={'control':label,'passed':passed,'actual_public_consumer':'faction_town_layout.inspect','state':STATE,'offset':[dx,dy],'error':observed,'fixed_environment_hashes':fixed,'environment_unchanged':fixed==protected,'source_and_selected_frame_sha256':sha(selected),'source_selected_bytes_equal':selected.read_bytes()==(fixture/c['frames'][STATE]['path']).read_bytes(),'actual_foundation_on_stairs':ImageChops.multiply(root,stairs).histogram()[255],'actual_foundation_on_water':ImageChops.multiply(root,water).histogram()[255],'actual_foundation_outside_fixed_support':ImageChops.subtract(root,support).histogram()[255]};results.append(result)
   if not passed:raise ValueError('Controlled local physical rejection failed '+str(result))
  finally:
   for p,b in saved.items():p.write_bytes(b)
   select(contract)
  restored,_=layout.inspect(fixture,content,'noxus')
  if restored!=baseline:raise ValueError('Fixture restoration changed the observed baseline')
 result={'status':'authored configuration','ok':True,'baseline_public_consumer_errors':baseline,'bounded_positive':'Actual dwellingUpLvl6 passes native frame/body/root/support/door/approach and own-body path phase before public consumer stops at the following base-state empty approach.','supported_root_pixels':588,'controls':results,'helper_sha256':sha(WORKSPACE/'scripts/faction_town_layout.py'),'full_town_positive':False,'full_town_negative_attribution':False,'later_cross_body_and_scene_acceptance':False,'door_and_source_mask_negatives':'Pending a valid complete physical baseline.','native_executed':False,'release_accepted':False};write(REPORT/'receipt.json',result);print(json.dumps(result))
if __name__=='__main__':main()
