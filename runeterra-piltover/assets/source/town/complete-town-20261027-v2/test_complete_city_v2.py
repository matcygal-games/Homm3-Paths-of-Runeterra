"""Actual candidate-consumer regressions; mutation pixels are never artwork."""
from pathlib import Path
from contextlib import contextmanager
from copy import deepcopy
import hashlib,json,sys,unittest
from PIL import Image,ImageChops,ImageDraw
S=Path(__file__).resolve().parent;P=S.parents[3];W=P.parent
R=P/'build/reports/complete-town-20261027-v2/derivation-contact-repair-v1'
F=R/'technical-consumer/runeterra-piltover'
sys.path.insert(0,str(W/'scripts'))
import faction_town_layout as layout
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def encoded(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
EVIDENCE=[]

class ActualCity(unittest.TestCase):
 def setUp(self):
  self.saved={};self.plan=load(F/(S/'layout-acceptance-contract-v2.json').relative_to(P));self.content=load(S/'native-content-geometry.candidate-v2.json');self.design=load(F/'design/town-visuals.json')
 def tearDown(self):
  for p,data in self.saved.items():p.write_bytes(data)
 def write(self,p,data):
  if p not in self.saved:self.saved[p]=p.read_bytes()
  p.write_bytes(data)
 def save_image(self,p,im):
  import io
  b=io.BytesIO();im.save(b,format='PNG');self.write(p,b.getvalue())
 def reference_image(self,reference,im):
  p=F/reference['path'];self.save_image(p,im);reference['sha256']=sha(p)
 def bind_contract(self):
  p=F/(S/'layout-acceptance-contract-v2.json').relative_to(P);self.write(p,encoded(self.plan));self.design['layout_contract']['sha256']=sha(p);self.write(F/'design/town-visuals.json',encoded(self.design))
 def inspect(self,name,expected=None):
  self.bind_contract();errors,deps=layout.inspect(F,self.content,'piltover');EVIDENCE.append({'case':name,'errors':errors,'dependencies':len(deps),'expected_substring':expected})
  if expected:self.assertTrue(any(expected in e for e in errors),errors)
  else:self.assertEqual(errors,[])
  return errors
 def test_actual_204_dependency_consumer(self):self.inspect('actual candidate geometry')
 def test_exact_whole_master_visible_pixels(self):
  master=Image.open(S/'complete-town-native-v2.png').convert('RGBA');traces=load(S/'silhouette-traces-v1.json')['sites'];counts={}
  import numpy as np
  for site,t in traces.items():
   mask=np.asarray(Image.open(S/'masks/master-visible'/(site+'.png')))>0
   frame=np.asarray(Image.open(S/'frames'/site/(t['master_state']+'.png')).convert('RGBA'))
   self.assertTrue(np.array_equal(frame[mask],np.asarray(master)[mask]),site);counts[site]=int(mask.sum())
  EVIDENCE.append({'case':'all 18 master-visible cuts retain exact approved RGBA','visible_pixel_counts':counts})
 def test_actual_displaced_building_and_masks(self):
  state='blacksmith';dx,dy=0,20
  def shift(im):
   out=Image.new(im.mode,im.size);out.paste(im,(dx,dy));return out
  ref=self.plan['frames'][state];self.reference_image(ref,shift(Image.open(F/ref['path']).convert('RGBA')))
  record=self.plan['silhouette_plan']['states'][state]
  for name in ['body_mask','foundation_mask','door_mask','approach_mask']:self.reference_image(record[name],shift(Image.open(F/record[name]['path'])))
  record['entrance']=[record['entrance'][0]+dx,record['entrance'][1]+dy]
  site=next(s for s in self.plan['sites']if state in s['states']);self.reference_image(site['silhouette_mask'],shift(Image.open(F/site['silhouette_mask']['path'])))
  site['box'][0]+=dx;site['box'][1]+=dy;site['entrance']=[site['entrance'][0]+dx,site['entrance'][1]+dy]
  structure=self.content['factions']['piltover']['town']['structures'][state]
  a=load(F/'assets/generated/Content/Sprites'/structure['animation']);groups=layout.fp.utility('identity').animation_groups(a,complete=True)
  selected=F/'assets/generated/Content/Sprites'/(a.get('basepath','')+groups[0][0]);self.write(selected,(F/ref['path']).read_bytes())
  complete=Image.open(F/self.plan['background']['path']).convert('RGBA')
  for key in self.plan['silhouette_plan']['complete_scene_states']:complete.alpha_composite(Image.open(F/self.plan['frames'][key]['path']).convert('RGBA'))
  self.reference_image(self.plan['silhouette_plan']['complete_scene'],complete)
  self.inspect('real forge and every own physical mask translated 20px, source/generated/hash pins rebound','foundation lacks level support')
 def test_forged_actual_body_mask(self):
  ref=self.plan['silhouette_plan']['states']['blacksmith']['body_mask'];im=Image.open(F/ref['path']).convert('L');x,y=im.getbbox()[:2]
  import numpy as np
  yy,xx=np.argwhere(np.asarray(im)>0)[0];im.putpixel((int(xx),int(yy)),0);self.reference_image(ref,im)
  self.inspect('changed body annotation with rebound hash, actual frame unchanged','Body mask differs')
 def test_real_connected_street_through_forge(self):
  ref=self.plan['silhouette_plan']['paths_mask'];im=Image.open(F/ref['path']).convert('L')
  import numpy as np
  points=np.argwhere(np.asarray(im)>0);target=(122,281);yy,xx=min(points,key=lambda p:abs(int(p[1])-target[0])+abs(int(p[0])-target[1]));d=ImageDraw.Draw(im);d.line([(int(xx),int(yy)),(target[0],int(yy)),target],fill=255)
  self.reference_image(ref,im);self.inspect('connected actual street deliberately crosses opaque forge body','Global path passes through')
 def test_disconnected_actual_approach(self):
  import numpy as np
  records=self.plan['silhouette_plan']['states'];state=max(records,key=lambda n:int(np.count_nonzero(np.asarray(Image.open(F/records[n]['approach_mask']['path'])))))
  ref=records[state]['approach_mask'];im=Image.open(F/ref['path']).convert('L');points=np.argwhere(np.asarray(im)>0);a=points[0];b=max(points,key=lambda p:abs(int(p[0])-int(a[0]))+abs(int(p[1])-int(a[1])));self.assertGreater(abs(int(a[0])-int(b[0]))+abs(int(a[1])-int(b[1])),1)
  bad=Image.new('L',(800,374));bad.putpixel((int(a[1]),int(a[0])),255);bad.putpixel((int(b[1]),int(b[0])),255);self.reference_image(ref,bad)
  self.inspect('actual approach reduced to two disconnected endpoints','disconnected components: approach '+state)
 def test_native_depth_consumer(self):
  self.content['factions']['piltover']['town']['structures']['cityHall']['z']+=1
  self.inspect('real content native z disagrees with selected physical city','Physical site depth must equal')
 def test_complete_scene_pixel_binding(self):
  ref=self.plan['silhouette_plan']['complete_scene'];im=Image.open(F/ref['path']).convert('RGBA');r,g,b,a=im.getpixel((0,0));im.putpixel((0,0),(r^1,g,b,a));self.reference_image(ref,im)
  self.inspect('complete scene single changed pixel with rebound own hash','Complete town scene does not match')
 def test_all_35_new_construction_icons(self):
  recipe=load(S/'recipes-v2/buildingIcons.json');states=set(load(S/'frame-registration-v1.json')['states']);self.assertEqual({f['building']for f in recipe['frames']},states);self.assertEqual(len(recipe['frames']),35)
  for row in recipe['frames']:
   self.assertIn('complete-town-20261027-v2',row['source']);im=Image.open(P/row['source']);self.assertEqual(im.size,(150,70));self.assertIsNotNone(im.getchannel('A').getbbox())
  EVIDENCE.append({'case':'all 35 actual native building IDs use new architecture construction cards','count':35})

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(ActualCity);result=unittest.TextTestRunner(verbosity=2).run(suite)
 (R/'negative-controls-v3.json').write_bytes(encoded({'status':'authored configuration','consumer_sha256':sha(W/'scripts/faction_town_layout.py'),'contract_sha256':sha(S/'layout-acceptance-contract-v2.json'),'tests_run':result.testsRun,'passed':result.wasSuccessful(),'cases':EVIDENCE,'native_executed':False,'release_accepted':False}))
 raise SystemExit(0 if result.wasSuccessful()else 2)
