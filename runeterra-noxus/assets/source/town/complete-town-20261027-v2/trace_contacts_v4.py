"""Reproducible source-only semantic contact study; never an admission waiver.

Polylines are manually read native wall/plinth/stair-foot contours, rather than
the last opaque pixel of each column. Full state alpha is preserved separately.
These are candidate annotations. Source review and dry support remain explicit.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageChops,ImageFilter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/complete-town-20261027-v2/semantic-v4'
OUT=HERE/'physical-v4'
SIZE=(800,374)
# Native coordinates read against contact-source-grid-0..5 and original layers.
# Every source gets its own contour; different rank architecture is not aliased.
TRACES={
 'villageHall':[(101,153),(123,155),(139,157),(149,158),(158,162),(172,162),(180,159),(195,158)],
 'townHall':[(94,159),(118,161),(144,161),(158,161),(168,162),(185,162),(204,160)],
 'cityHall':[(84,156),(108,158),(134,160),(147,160),(158,162),(180,162),(191,160),(212,159)],
 'capitol':[(79,145),(101,149),(125,152),(147,157),(163,162),(182,160),(201,158),(217,153)],
 'fort':[(230,130),(261,134),(296,135),(334,139),(372,143),(398,145),(414,147),(447,147),(465,145),(507,141),(550,136),(593,137),(616,134)],
 'citadel':[(259,134),(286,139),(321,136),(351,141),(380,145),(409,145),(421,147),(447,147),(465,147),(495,146),(525,140),(554,141),(586,136)],
 'castle':[(204,114),(230,118),(264,125),(294,129),(324,131),(353,135),(383,140),(410,142),(421,145),(449,147),(468,146),(498,143),(531,139),(562,134),(593,127),(619,124),(642,115)],
 'mageGuild1':[(277,150),(294,153),(309,156),(317,156),(324,158),(339,158),(349,153)],
 'mageGuild2':[(263,148),(283,151),(303,154),(320,155),(327,158),(343,158),(359,154),(362,152)],
 'mageGuild3':[(249,149),(274,152),(300,154),(320,155),(328,158),(349,158),(366,154),(376,152)],
 'mageGuild4':[(243,139),(260,143),(280,147),(303,150),(320,153),(330,158),(349,158),(365,154),(383,151)],
 'dwellingLvl1':[(592,158),(608,162),(622,166),(637,171),(648,174),(662,170),(678,167),(693,162)],
 'dwellingUpLvl1':[(586,155),(606,160),(621,164),(638,168),(653,173),(671,169),(686,166),(699,162)],
 'dwellingLvl2':[(97,218),(113,223),(132,229),(149,229),(165,226),(185,222)],
 'dwellingUpLvl2':[(93,214),(111,219),(134,227),(153,228),(174,230),(191,226)],
 'dwellingLvl3':[(12,184),(28,189),(39,193),(47,191),(53,194),(62,201),(71,196),(86,192),(101,186)],
 'dwellingUpLvl3':[(6,171),(22,177),(38,183),(47,179),(58,188),(63,201),(73,193),(87,186),(106,177)],
 'dwellingLvl4':[(474,179),(491,184),(511,188),(533,193),(550,189),(574,183)],
 'dwellingUpLvl4':[(468,165),(486,176),(511,184),(537,192),(555,185),(580,179)],
 'dwellingLvl5':[(253,319),(273,324),(293,325),(308,328),(330,326),(346,320)],
 'dwellingUpLvl5':[(247,312),(266,319),(290,322),(303,325),(310,328),(332,324),(354,318)],
 'dwellingLvl6':[(443,336),(466,341),(490,345),(515,347),(535,344),(555,341),(574,339)],
 'dwellingUpLvl6':[(439,333),(454,336),(477,341),(493,347),(513,345),(536,339),(558,337),(581,334)],
 'special4':[(435,250),(454,260),(469,259),(484,260),(504,255),(520,253)],
 'dwellingLvl7':[(423,253),(446,256),(461,259),(478,261),(497,260),(516,255),(530,251)],
 'dwellingUpLvl7':[(416,243),(436,251),(459,256),(479,261),(501,259),(521,253),(538,246)],
 'tavern':[(10,326),(37,334),(63,341),(89,344),(113,350),(141,354),(168,351),(190,345),(210,338),(224,335)],
 'marketplace':[(539,236),(558,248),(578,250),(595,246),(607,240),(620,243),(643,250),(666,242)],
 'blacksmith':[(584,333),(610,338),(637,344),(662,348),(688,354),(708,355),(735,351),(761,347),(789,341)],
 'resourceSilo':[(633,251),(652,259),(675,264),(695,265),(716,263),(733,259)],
 'special1':[(7,120),(21,122),(39,124),(51,125),(65,126),(76,128)],
 'special2':[(685,166),(702,169),(721,172),(738,172),(749,168)],
 'special3':[(193,204),(200,213),(208,219),(213,220),(215,219),(218,220),(220,223),(223,224),(225,229),(229,230),(244,234),(260,233),(277,234),(300,233),(322,224),(338,217)],
 'shipyard':[(750,175),(762,178),(775,182),(788,187),(795,188)],
 'ship':[(750,174),(762,178),(777,183),(789,187),(795,188)],
 'grail':[(222,141),(227,144),(232,143)],
}

for state in ('special4','dwellingLvl7','dwellingUpLvl7'):
 TRACES[state]=[(x,y+20) for x,y in TRACES[state]]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def alpha(im,t):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
def count(m):return m.histogram()[255]

def main():
 selection=json.loads((HERE/'candidate-access-v2/selection.json').read_text());rows=selection['states']
 if set(TRACES)!={r['state'] for r in rows}:raise ValueError('Missing/extra semantic state')
 layers={};roots={};annotations=[]
 for r in rows:
  state=r['state'];p=ROOT/r['native_layer']
  if sha(p)!=r['native_layer_sha256']:raise ValueError('Changed state '+state)
  im=Image.open(p).convert('RGBA');layers[state]=im
  # The trace band includes the full manually indicated support contour, clipped
  # only to selected body. It never edits or shrinks the actual alpha silhouette.
  trace=Image.new('L',SIZE);ImageDraw.Draw(trace).line(TRACES[state],fill=255,width=4)
  root=ImageChops.multiply(trace,alpha(im,128));roots[state]=root
  if not root.getbbox():raise ValueError('Empty physical trace '+state)
  folder=OUT/state;save(folder/'foundation.png',root);save(folder/'body.png',alpha(im,128));save(folder/'silhouette.png',alpha(im,8))
  annotated=im.copy();color=Image.new('RGBA',SIZE,(20,255,220,0));color.putalpha(root);annotated.alpha_composite(color)
  bb=alpha(im,8).getbbox();save(folder/'contact-review-4x.png',annotated.crop(bb).resize(((bb[2]-bb[0])*4,(bb[3]-bb[1])*4),Image.Resampling.NEAREST))
  annotations.append({'state':state,'layer':r['native_layer'],'layer_sha256':sha(p),'site':r['site'],'depth':r['native_z'],'manual_native_contact_polyline':TRACES[state],'band_width':4,'foundation':str((folder/'foundation.png').relative_to(ROOT)).replace('\\','/'),'foundation_sha256':sha(folder/'foundation.png'),'pixels':count(root),'bbox':list(root.getbbox()),'status':'authored configuration','pixel_review':'Candidate manual contour; dry support and complete physical adequacy remain unaccepted.'})
 sites={s['id']:s for s in selection['sites']};pairs=[]
 for rear,a in sites.items():
  ru=Image.new('L',SIZE)
  for state in a['states']:ru=ImageChops.lighter(ru,roots[state])
  for front,b in sites.items():
   if a['native_z']>=b['native_z']:continue
   bu=Image.new('L',SIZE)
   for state in b['states']:bu=ImageChops.lighter(bu,alpha(layers[state],128))
   hit=ImageChops.multiply(ru,bu)
   if not hit.getbbox():continue
   key=rear+'--'+front;save(REPORT/(key+'-root-intersection.png'),hit)
   combinations=[]
   for rs in a['states']:
    for fs in b['states']:
     inter=ImageChops.multiply(roots[rs],alpha(layers[fs],128))
     if count(inter):combinations.append({'rear_state':rs,'front_state':fs,'pixels':count(inter),'bbox':list(inter.getbbox())})
   scene=Image.open(ROOT/selection['terrain']['native']).convert('RGBA')
   scene.alpha_composite(layers[a['top']]);scene.alpha_composite(layers[b['top']]);marker=Image.new('RGBA',SIZE,(0,255,255,0));marker.putalpha(hit);scene.alpha_composite(marker)
   save(REPORT/(key+'-native-overlay.png'),scene)
   bb=hit.getbbox();crop=(max(0,bb[0]-25),max(0,bb[1]-30),min(800,bb[2]+25),min(374,bb[3]+30))
   save(REPORT/(key+'-context-4x.png'),scene.crop(crop).resize(((crop[2]-crop[0])*4,(crop[3]-crop[1])*4),Image.Resampling.NEAREST))
   pairs.append({'behind':rear,'front':front,'pixels':count(hit),'bbox':list(bb),'mask_sha256':sha(REPORT/(key+'-root-intersection.png')),'state_pairs':combinations,'disposition':'Only original Bastion/College projection has bounded review; current semantic-mask identity must be rechecked.' if (rear,front)==('crownBastion','arcaneAthenaeum') else 'Unapproved physical contact intersection: requires source review or correction. No exemption granted.'})
 write(OUT/'annotations.json',{'status':'authored configuration','script_sha256':sha(Path(__file__)),'whole_master_sha256':sha(HERE/'complete-city-master-v2.png'),'scope':'Manual state-specific native contours; full alpha8 roofs/shadows unchanged. No land/stair/water truth fabricated.','states':annotations})
 write(REPORT/'all-state-contact-intersections.json',{'status':'authored configuration','states':len(rows),'sites':len(sites),'ordinary_land_sites':17,'pairs':pairs,'native_verified':False,'release_accepted':False})
 print(json.dumps({'states':len(rows),'contact_intersection_pairs':len(pairs),'report':str(REPORT)}))

if __name__=='__main__':main()
