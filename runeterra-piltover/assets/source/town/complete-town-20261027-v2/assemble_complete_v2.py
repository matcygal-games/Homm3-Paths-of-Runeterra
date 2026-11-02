"""Derive review candidates from the approved whole city, never stage/publish.

Full-state visible pixels are exact master cuts. Genuine atlas paintings supply
predecessors and bounded occluded reconstruction only. No model/render pipeline.
"""
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image,ImageChops,ImageDraw,ImageFilter

S=Path(__file__).resolve().parent
P=S.parents[3]
W=P.parent
R=P/'build/reports/complete-town-20261027-v2/derivation-v1'
SIZE=(800,374)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path):return path.relative_to(P).as_posix()
def ref(path):return {'path':rel(path),'sha256':sha(path)}
def dump(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def polygon(points):
 image=Image.new('L',SIZE)
 ImageDraw.Draw(image).polygon([tuple(p)for p in points],fill=255)
 return image
def save_mask(path,image):path.parent.mkdir(parents=True,exist_ok=True);image.convert('L').save(path);return ref(path)
def a8(image):return image.getchannel('A').point(lambda a:255 if a>=8 else 0)
def bbox(image):return a8(image).getbbox()

def read_atlas(site,calibration):
 c=calibration['families'][site]
 path=S/'family-atlases'/site/'atlas-v1.png'
 image=Image.open(path).convert('RGBA')
 result={}
 for state,item in c['states'].items():
  index=item['cell'];col=index%c['columns'];row=index//c['columns']
  box=(round(col*image.width/c['columns']),round(row*image.height/c['rows']),round((col+1)*image.width/c['columns']),round((row+1)*image.height/c['rows']))
  panel=image.crop(box)
  # Source alpha admission removes only faint atlas haze, retaining RGB and
  # actual building antialiasing. Full-state master pixels are never filtered.
  alpha=panel.getchannel('A').point(lambda a:0 if a<32 else 255 if a>=248 else a)
  panel.putalpha(alpha)
  out=S/'panels'/site/(state+'.png');out.parent.mkdir(parents=True,exist_ok=True);panel.save(out)
  result[state]=(panel,item['root'],c['scale'],out)
 return result

def render():
 master=Image.open(S/'complete-town-native-v2.png').convert('RGBA')
 traces=json.loads((S/'silhouette-traces-v1.json').read_text())['sites']
 program=json.loads((S/'functional-program-v2.json').read_text())['sites']
 calibration=json.loads((S/'atlas-calibration-v1.json').read_text())
 order=sorted(traces,key=lambda site:traces[site]['depth'])
 outlines={site:polygon(traces[site]['polygon'])for site in order}
 atlas={site:read_atlas(site,calibration)for site in calibration['families']}
 # Keep one uniform density per painted family, bounded by the actual approved
 # complete-building envelope. No state is cropped or independently box-fitted.
 for site,states in atlas.items():
  x0,y0,x1,y1=outlines[site].getbbox();tx,ty=traces[site].get('registration_root',traces[site]['door']);limits=[next(iter(states.values()))[2]]
  for state,(panel,root,scale,path)in states.items():
   b=bbox(panel)
   for distance,space in [(root[0]-b[0],tx-x0),(b[2]-root[0],x1-tx),(root[1]-b[1],ty-y0),(b[3]-root[1],y1-ty)]:
    if distance>0:limits.append(space/distance)
  density=min(limits)*.997
  atlas[site]={state:(panel,root,density,path)for state,(panel,root,_,path)in states.items()}
 actual={};details={};sites={s['id']:s for s in program};whole_visible=Image.new('L',SIZE)
 for i,site in enumerate(order):
  data=traces[site];front=Image.new('L',SIZE)
  for name in order[i+1:]:front=ImageChops.lighter(front,outlines[name])
  visible=ImageChops.subtract(outlines[site],front)
  hidden=ImageChops.multiply(outlines[site],front)
  whole_visible=ImageChops.lighter(whole_visible,visible)
  for state in sites[site]['states']:
   candidate=Image.new('RGBA',SIZE)
   if site in atlas:
    panel,root,scale,panelpath=atlas[site][state]
    size=(max(1,round(panel.width*scale)),max(1,round(panel.height*scale)))
    projected=panel.resize(size,Image.Resampling.LANCZOS)
    registration=data.get('registration_root',data['door'])
    offset=(round(registration[0]-root[0]*scale),round(registration[1]-root[1]*scale))
    candidate.alpha_composite(projected,offset)
   if state==data['master_state']:
    # Exact original visible RGB; no independently restyled atlas may replace it.
    exact=master.copy();exact.putalpha(visible)
    reconstruction=candidate.copy()
    reconstruction.putalpha(ImageChops.multiply(candidate.getchannel('A'),hidden))
    reconstruction.alpha_composite(exact)
    candidate=reconstruction
    method='Exact whole-master visible pixels plus genuinely painted atlas hidden-face reconstruction'
   elif site=='coast' and state=='shipyard':
    # Exact shared pier/office, with the moored vessel absent. Whole dock/hull
    # ownership is refined explicitly before freeze; atlas is absence study only.
    dock=polygon([[700,333],[700,315],[711,309],[716,296],[723,294],[731,301],[734,318],[728,333],[716,337]])
    candidate=master.copy();candidate.putalpha(ImageChops.multiply(dock,visible))
    method='Exact approved-master independent dock/office cut; no boat pixels'
   else:
    method='Genuinely painted predecessor of the same new whole-city architecture, uniformly registered'
   if bbox(candidate) is None:raise ValueError('Empty architecture '+state)
   target=S/'frames'/site/(state+'.png');target.parent.mkdir(parents=True,exist_ok=True);candidate.save(target)
   actual[state]=ref(target)
   details[state]={'site':site,'method':method,'bbox':list(bbox(candidate)),'door':data['door'],'approach':data['approach'],'depth':data['depth'],'master_visible_pixel_count':visible.histogram()[255] if state==data['master_state'] else 0,'generated_max_panel_is_not_visible_body':True}
  save_mask(S/'masks/master-visible'/(site+'.png'),visible)
  save_mask(S/'masks/master-hidden'/(site+'.png'),hidden)
  save_mask(S/'masks/master-outlines'/(site+'.png'),outlines[site])
 empty=Image.open(S/'family-atlases/empty-terrain/atlas-v2.png').convert('RGBA')
 factor=max(800/empty.width,374/empty.height);size=(round(empty.width*factor),round(empty.height*factor));empty=empty.resize(size,Image.Resampling.LANCZOS);xx=(size[0]-800)//2;yy=(size[1]-374)//2;empty=empty.crop((xx,yy,xx+800,yy+374))
 # Keep approved unowned streets/scenery exactly. Painted absence reconstruction
 # is used only in the functional architecture's conservative removal envelope.
 absence=Image.new('L',SIZE)
 crops=json.loads((S/'master-crop-plan.json').read_text())['boxes']
 draw=ImageDraw.Draw(absence)
 for box in crops.values():draw.rectangle(tuple(box),fill=255)
 absence=absence.filter(ImageFilter.MaxFilter(9))
 background=Image.composite(empty,master,absence)
 background.save(S/'background-native-v1.png')
 save_mask(S/'masks/functional-absence.png',absence)
 save_mask(S/'masks/master-visible-union.png',whole_visible)
 dump(S/'frame-registration-v1.json',{'status':'authored configuration','states':details,'native_observed':False})
 return master,background,traces,program,actual

def previews(master,background,traces,program,frames):
 R.mkdir(parents=True,exist_ok=True)
 sites={s['id']:s for s in program}
 order=sorted(traces,key=lambda site:traces[site]['depth'])
 developed=[traces[site]['master_state']for site in order if site not in ('coast','grail')]
 def scene(name,states):
  im=background.copy()
  for state in sorted(states,key=lambda key:next(traces[s['id']]['depth']for s in program if key in s['states'])):im.alpha_composite(Image.open(P/frames[state]['path']).convert('RGBA'))
  im.save(R/(name+'.png'));return im
 scene('empty',[])
 scene('early',['villageHall','fort','dwellingLvl1'])
 scene('partial',['townHall','citadel','mageGuild1','tavern','marketplace','dwellingLvl1','dwellingLvl2','dwellingLvl3','dwellingLvl4'])
 scene('all-base',[sites[site]['states'][0]for site in order if site not in ('coast','grail')])
 full=scene('developed-cityhall',developed)
 scene('coastal',developed+['ship'])
 scene('grail',developed+['grail'])
 complete=scene('complete-master-state',developed+['ship','grail'])
 scene('capitol',[state for state in developed if state!='cityHall']+['capitol'])
 scene('without-council',[state for state in developed if state!='cityHall'])
 scene('without-rifles',[state for state in developed if state!='dwellingUpLvl2'])
 scene('without-forge',[state for state in developed if state!='blacksmith'])
 master.save(R/'approved-master.png')
 diff=ImageChops.difference(complete.convert('RGB'),master.convert('RGB'))
 h=diff.convert('L').histogram()
 dump(R/'master-comparison-v1.json',{'status':'authored configuration','exact_equal_pixels':h[0],'total_pixels':800*374,'exact_equal_fraction':h[0]/(800*374),'scope':'Whole-master visible pixel retention comparison, not visual/native acceptance','remaining':'Trace/reconstruction/geometry review pending'})
 html='<html><head><meta charset="utf-8"><title>Piltover whole-master derivation</title><style>body{background:#1b2028;color:#eee;font:16px sans-serif}img{display:block;width:800px;max-width:100%;margin:16px 0}</style></head><body><h1>Piltover whole-master derivation candidates</h1><p>Authored configuration; exact approved-master visible cuts, genuine lower architecture, painted absence/hidden reconstruction. Geometry/pixel review in progress. No canonical selection or native claim.</p>'
 for name in ['approved-master','complete-master-state','developed-cityhall','empty','early','partial','all-base','capitol','coastal','grail','without-council','without-rifles','without-forge']:html+='<h2>'+name+'</h2><img src="'+name+'.png">'
 (R/'index.html').write_text(html+'</body></html>',encoding='utf-8')

if __name__=='__main__':
 values=render();previews(*values)
 print(json.dumps({'status':'authored configuration','states':len(values[-1]),'stage_modified':False,'remaining':'Source-composition and silhouette/support/path geometry review; recipe/contract integration not yet frozen.'}))
