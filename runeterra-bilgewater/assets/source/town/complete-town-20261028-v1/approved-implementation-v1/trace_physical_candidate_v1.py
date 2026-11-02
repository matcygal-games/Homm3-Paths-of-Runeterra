"""Manual painted-contact annotations and conservative path feasibility probe.

These shapes are semantic technical annotations, not game artwork. They bind
unchanged real frames and the genuine protected empty-terrain recovery. A
disconnected probe is reported, never papered over with a body/terrain waiver.
"""
from pathlib import Path
from collections import deque
import json,hashlib,copy
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-v1-attempt2'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def save(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def blank():return Image.new('L',(800,374))
def shape(points,width=1):return {'lines':[{'points':points,'width':width}]}
def trace(v):
 m=blank();d=ImageDraw.Draw(m)
 for p in v.get('polygons',[]):d.polygon([tuple(x) for x in p],fill=255)
 for p in v.get('lines',[]):d.line([tuple(x) for x in p['points']],fill=255,width=p['width'])
 return m

# Each entry traces the actual structural sill/column feet rather than the
# lowest foliage, cast shadow, water spray, or a rectangular guide envelope.
# A door trace follows the depicted front threshold/own entrance stair only.
CONTACTS={
'castle': ([(109,83),(150,91),(190,95),(221,99),(270,106)],[(225,90),(230,96)],(238,102)),
'fort': ([(112,84),(150,92),(188,96),(245,102)],[(187,89),(192,95)],(237,103)),
'citadel': ([(105,83),(150,91),(191,96),(246,103)],[(199,90),(207,96)],(238,103)),
'villageHall': ([(335,120),(365,125),(411,127),(426,123)],[(389,119),(390,130)],(392,134)),
'townHall': ([(310,119),(352,124),(387,127),(421,124)],[(385,118),(390,130)],(392,134)),
'cityHall': ([(307,120),(352,125),(386,128),(423,125)],[(385,119),(390,130)],(392,134)),
'capitol': ([(308,120),(352,125),(387,127),(424,124)],[(386,118),(390,130)],(392,134)),
'mageGuild1': ([(473,125),(498,131),(528,127)],[(501,122),(502,130)],(506,133)),
'mageGuild2': ([(471,126),(496,132),(525,128)],[(501,121),(502,130)],(506,133)),
'mageGuild3': ([(480,125),(501,131),(520,128)],[(500,119),(501,130)],(506,133)),
'dwellingLvl7': ([(97,181),(135,187),(173,187),(191,183)],[(169,181),(190,184)],(200,184)),
'dwellingUpLvl7': ([(98,181),(137,186),(173,186),(192,183)],[(169,181),(190,184)],(200,184)),
'dwellingLvl3': ([(208,179),(242,184),(280,184),(312,180)],[(280,174),(283,183)],(332,184)),
'dwellingUpLvl3': ([(197,180),(240,186),(283,186),(321,182)],[(283,174),(286,184)],(332,184)),
'special4': ([(452,190),(477,199),(502,197),(517,190)],[(479,187),(480,198)],(482,202)),
'special1': ([(599,205),(627,211),(655,211),(697,206)],[(651,200),(651,212)],(620,216)),
'dwellingLvl4': ([(598,205),(627,212),(655,212),(700,206)],[(651,200),(651,213)],(620,216)),
'dwellingUpLvl4': ([(600,211),(625,217),(641,221),(673,220),(704,210)],[(651,197),(650,220)],(620,220)),
'special2': ([(534,145),(554,148),(579,147),(597,142)],[(553,141),(548,151)],(549,154)),
'dwellingLvl6': ([(524,144),(549,148),(579,146),(599,141)],[(550,139),(548,151)],(549,154)),
'dwellingUpLvl6': ([(529,145),(541,151),(555,151),(578,144),(594,141)],[(546,139),(545,152)],(549,155)),
'dwellingLvl5': ([(619,110),(643,113),(673,113),(695,108)],[(655,108),(655,114)],(600,108)),
'dwellingUpLvl5': ([(612,107),(637,110),(665,111),(693,106)],[(655,106),(655,112)],(600,108)),
'resourceSilo': ([(5,215),(36,221),(78,221),(122,215)],[(29,212),(38,221)],(55,228)),
'dwellingLvl1': ([(72,251),(83,253),(100,253),(122,252),(143,248)],[(133,240),(139,249)],(150,250)),
'dwellingUpLvl1': ([(71,251),(82,253),(101,253),(121,252),(142,249)],[(133,240),(139,249)],(150,250)),
'dwellingLvl2': ([(247,275),(280,284),(319,283),(348,275)],[(319,277),(325,285)],(340,299)),
'dwellingUpLvl2': ([(248,276),(283,285),(322,283),(349,276)],[(321,277),(327,285)],(340,299)),
'blacksmith': ([(157,285),(194,294),(236,295),(268,287)],[(239,284),(242,295)],(245,304)),
'special3': ([(4,307),(48,315),(103,315),(162,309)],[(101,304),(105,315)],(174,316)),
'marketplace': ([(356,311),(401,319),(455,320),(502,318),(543,312)],[(368,311),(410,316),(460,318),(523,314)],(552,317)),
'tavern': ([(515,269),(551,279),(593,287),(632,283)],[(622,271),(624,287)],(635,295)),
'grail': ([(325,313),(330,314),(335,312)],[(330,310),(330,314)],(340,316)),
'shipyard': ([(637,309),(667,317),(710,320),(770,313)],[(638,304),(648,306)],(630,307)),
'ship': ([(624,329),(661,346),(707,350),(739,333)],[(638,304),(648,306)],(630,307)),
}

def main():
 REPORT.mkdir(parents=True,exist_ok=False)
 out=HERE/'physical-v1-attempt2';out.mkdir(exist_ok=False)
 ip=HERE/'states-hidden-support-v2.json';index=json.loads(ip.read_text());bg=PROJECT/index['background']
 old=HERE.parent/'physical-contract-v1/terrain-trace-v4/annotations.json'
 terrain=json.loads(old.read_text());terrain['background']=ref(bg)
 terrain['ancestry']=ref(old)
 terrain['status']='design proposal'
 # Actual previously untraced public stair flights, inspected from the genuine
 # selected empty source. No vertical cliff is promoted into a horizontal pad.
 terrain['stairs_regions'] += [
  {'id':'actual-west-upper-public-flight','polygon':[[172,186],[185,188],[183,204],[174,219],[163,231],[147,231],[151,220],[162,207]]},
  {'id':'actual-west-lower-return-flight','polygon':[[145,249],[166,252],[159,261],[139,278],[119,278],[123,268],[137,257]]},
  {'id':'actual-main-stair-lower-treads','polygon':[[390,267],[459,267],[459,275],[384,275]]},
 ]
 terrain['support_regions'] += [
  {'id':'actual-central-inter-flight-rest','polygon':[[394,176],[409,176],[414,183],[406,186],[395,184]]},
  {'id':'actual-main-stair-upper-rest','polygon':[[398,238],[443,238],[445,244],[398,244]]},
  {'id':'genuine-recovered-sailors-lower-deck-top','polygon':[[67,250],[118,249],[143,249],[147,252],[140,255],[72,254]]},
  {'id':'genuine-recovered-captains-stone-apron-top','polygon':[[530,143],[590,141],[597,145],[586,150],[541,153],[531,151]]},
  {'id':'genuine-recovered-buhru-lower-apron-top','polygon':[[600,214],[704,213],[709,218],[697,221],[605,221]]},
 ]
 # Preserve exact provenance for every newly visible technical support recovery.
 terrain['hidden_support_selection']=ref(HERE/'hidden-support-selection-v2.json')
 save(out/'terrain-annotations.json',terrain)
 masks={}
 for role in ['support','stairs','water']:
  masks[role]=trace({'polygons':[r['polygon'] for r in terrain[role+'_regions']]})
 # The source trace can overlap at a shared edge. An unresolved semantic edge
 # is reported; it is not silently removed merely to make the consumer pass.
 masks['land']=ImageChops.lighter(masks['support'],masks['stairs'])
 for r in terrain['retaining_faces']:
  ImageDraw.Draw(masks['land']).polygon([tuple(p) for p in r['polygon']],fill=255)
 states={};blocked=blank();foundations={}
 for key,row in index['states'].items():
  contact,door,end=CONTACTS[key];a=Image.open(PROJECT/row['frame']).getchannel('A')
  body=a.point(lambda v:255 if v>=128 else 0)
  full=a.point(lambda v:255 if v>=8 else 0)
  record={'contact_interpretation':'Manual actual sill, column, basin or timber contact traced from the selected painted state; incidental foliage and the cast shadow are excluded.',
   'access_kind':'open-site' if key in ['resourceSilo','marketplace','special3','dwellingLvl7','dwellingUpLvl7','shipyard'] else 'moored-vessel' if key=='ship' else 'door',
   'entrance':list(door[0]),'foundation':shape(contact),'door':shape(door,5),'approach':shape([door[-1],list(end)],2)}
  if key in ['shipyard','ship']:
   record['marine_support_kind']='deck-and-pilings' if key=='shipyard' else 'moored-hull'
   record['marine_support']=shape(contact,2)
  foundation=ImageChops.multiply(trace(record['foundation']),full);foundations[key]=foundation
  dm=trace(record['door']);blocked=ImageChops.lighter(blocked,ImageChops.subtract(body,dm))
  for role,mask in [('body',body),('foundation',foundation),('door',dm),('approach',trace(record['approach']))]:mask.save(out/(key+'-'+role+'.png'))
  states[key]=record
 # No body is erased to create a path; permitted openings are only the manual
 # actual doorway/frontage records above. The water/coast is intentionally not
 # a land bridge. This probes the most conservative common source walk graph.
 walk=ImageChops.subtract(ImageChops.lighter(masks['support'],masks['stairs']),blocked)
 points={(x,y) for y in range(374) for x in range(800) if walk.getpixel((x,y))}
 components=[]
 while points:
  seed=points.pop();seen={seed};q=deque([seed])
  while q:
   x,y=q.popleft()
   for p in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if p in points:points.remove(p);seen.add(p);q.append(p)
  components.append(seen)
 components.sort(key=len,reverse=True)
 issues=[]
 for key,f in foundations.items():
  if key in ['shipyard','ship']:continue
  unsupported=ImageChops.subtract(f,masks['support']);onstairs=ImageChops.multiply(f,masks['stairs'])
  if unsupported.getbbox() or onstairs.getbbox():
   issues.append({'state':key,'unsupported_contact_pixels':unsupported.histogram()[255],
    'unsupported_bounds':list(unsupported.getbbox()) if unsupported.getbbox() else None,
    'contact_on_public_stairs':onstairs.histogram()[255]})
 for role,m in masks.items():m.save(out/(role+'.png'))
 scene=Image.open(bg).convert('RGBA')
 for role,color in [('support',(50,220,80)),('stairs',(250,170,20))]:
  overlay=Image.new('RGBA',scene.size,color+(0,));overlay.putalpha(masks[role].point(lambda a:65 if a else 0));scene=Image.alpha_composite(scene,overlay)
 for key,f in foundations.items():
  overlay=Image.new('RGBA',scene.size,(255,0,150,0));overlay.putalpha(f);scene=Image.alpha_composite(scene,overlay)
 scene.convert('RGB').save(REPORT/'all35-contact-plane-study.png')
 receipt={'status':'design proposal','scope':'Conservative manually annotated painted-contact and public-path feasibility probe. No physical baseline or native acceptance.',
  'state_index':ref(ip),'background':ref(bg),'terrain':ref(out/'terrain-annotations.json'),'helper':ref(Path(__file__).resolve()),
  'actual_state_count':len(states),'foundation_findings':issues,
  'walkable_common_components':len(components),'largest_components':[len(c) for c in components[:15]],
  'support_stair_intersection':ImageChops.multiply(masks['support'],masks['stairs']).histogram()[255],
  'support_water_intersection':ImageChops.multiply(masks['support'],masks['water']).histogram()[255],
  'public_consumer_executed':False,'negative_controls_executed':False,'native_verified':False}
 save(out/'state-contact-annotations.json',states);save(REPORT/'feasibility.json',receipt)
 print(json.dumps(receipt))

if __name__=='__main__':main()
