"""Exact all-state projection evidence, presented for individual review only."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageChops
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=HERE/'projection-cases-v1'
REPORT=ROOT/'build/reports/complete-town-20261027-v2/projection-cases-v1'
LEVELS={
 ('throneHall','dwellingAxe'):('Upper left civic hall landing','Lower west knife-guild court','The lower west knife-guild roof projects over the small left return of the elevated civic hall plinth; the hall front stairs remain separate on its right.'),
 ('crownBastion','throneHall'):('Rear elevated bastion foundation ledge','Nearer upper-left civic landing','The near civic hall right roof projects in front of the leftmost rear bastion support ledge; both gate and civic hall front stairs lie outside the intersection.'),
 ('crownBastion','arcaneAthenaeum'):('Rear elevated fortified stone ledge','Lower college court and entrance','The college roof projects before the elevated rear bastion lower wall; the bastion gate/stair and the college front entrance remain separate and exposed.'),
 ('crownBastion','dwellingLegion'):('Rear elevated fortified stone ledge','Lower east barracks courtyard','The lower east barracks roof projects in front of the rear bastion right support edge, leaving barracks front steps and the central bastion gate separate.'),
 ('crownBastion','dwellingRose'):('Rear elevated fortified stone ledge','Lower enclosed menagerie court','The menagerie upper roof projects before the rear bastion lower right wall; both actual menagerie entrances and the bastion main gate remain outside this band.'),
 ('dwellingAxe','dwellingHound'):('Upper west knife-guild workyard','Nearer hound-keeper forecourt','The nearer hound-keeper roof corner projects over the knife-guild far right plinth corner; separate knife-guild stairfoot and kennel entrance must remain exposed.'),
 ('grandMarket','crimsonCitadel'):('Market booth support and paving','Nearer depot stone foundation','The near resource depot left outline projects in front of the market right booth support; this distinct projected contact requires individual architectural review.'),
 ('crimsonCitadel','foundry'):('Resource depot supporting courtyard','Nearer foundry roof line','The near foundry chimney/roof detail projects over a tiny lower depot support corner, outside the depot entrance; individual source review remains required.'),
 ('trifarianHall','dwellingLegion'):('East martial hall stone landing','Nearer barracks courtyard edge','The barracks right roof edge projects before a small lower martial-hall corner, with the actual martial front staircase located farther right and clear.'),
 ('arenaOfValor','dwellingCrimson'):('Arena outer wall support terrace','Nearer crimson hall roof line','The near crimson hall roof tip projects over a few arena outer wall foot pixels, away from the arena actual gate and stairfoot on the left.'),
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def mask(im,t):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
def main():
 selection=json.loads((HERE/'candidate-access-v2/selection.json').read_text());rows={r['state']:r for r in selection['states']};sites={s['id']:s for s in selection['sites']};layers={s:Image.open(ROOT/r['native_layer']).convert('RGBA') for s,r in rows.items()};pairs=json.loads((ROOT/'build/reports/complete-town-20261027-v2/semantic-v4/all-state-contact-intersections.json').read_text())['pairs'];background=Image.open(ROOT/selection['terrain']['native']).convert('RGBA');complete=[s['top'] for s in selection['sites'] if s['id'] not in ('coast','grail')];records=[]
 for pair in pairs:
  rear,front=pair['behind'],pair['front'];folder=OUT/(rear+'--'+front);root=Image.new('L',(800,374));body=Image.new('L',(800,374));silrear=Image.new('L',(800,374));silfront=Image.new('L',(800,374))
  for state in sites[rear]['states']:root=ImageChops.lighter(root,Image.open(HERE/'physical-v4'/state/'foundation.png'));silrear=ImageChops.lighter(silrear,mask(layers[state],8))
  for state in sites[front]['states']:body=ImageChops.lighter(body,mask(layers[state],128));silfront=ImageChops.lighter(silfront,mask(layers[state],8))
  hit=ImageChops.multiply(root,body);save(folder/'foundation-intersection.png',hit);save(folder/'silhouette-intersection.png',ImageChops.multiply(silrear,silfront))
  scene=background.copy();absent=background.copy()
  for state in sorted(complete,key=lambda s:rows[s]['native_z']):
   scene.alpha_composite(layers[state])
   if state!=sites[front]['top']:absent.alpha_composite(layers[state])
  overlay=scene.copy();color=Image.new('RGBA',(800,374),(0,255,220,0));color.putalpha(hit);overlay.alpha_composite(color)
  save(folder/'complete-scene.png',scene);save(folder/'front-absent-scene.png',absent);save(folder/'intersection-overlay.png',overlay)
  rearlevel,frontlevel,reason=LEVELS[(rear,front)]
  case={'kind':'supported-terrace-projection','behind':rear,'front':front,'behind_depth':sites[rear]['native_z'],'front_depth':sites[front]['native_z'],'rear_level':rearlevel,'front_level':frontlevel,'reason':reason,'hidden_pixels':hit.histogram()[255],'hidden_bounds':list(hit.getbbox()),'mask_sha256':sha(folder/'foundation-intersection.png'),'status':'authored configuration','review_state':'Individual physical truth/levels and door/approach guards pending; not approved by this generated record.'}
  write(folder/'source-case.json',case)
  record={'behind':rear,'front':front,'reason':reason,'mask':ref(folder/'foundation-intersection.png'),'source_case':ref(folder/'source-case.json'),'evidence':{'complete_scene':ref(folder/'complete-scene.png'),'front_absent_scene':ref(folder/'front-absent-scene.png'),'intersection_overlay':ref(folder/'intersection-overlay.png')},'silhouette_mask':ref(folder/'silhouette-intersection.png'),'state_pairs':pair['state_pairs'],'reviewed':False};records.append(record)
 write(OUT/'case-index.json',{'status':'authored configuration','cases':records,'warning':'Candidate case records are for individual source-pixel review; no waiver or automatic approval.'});write(REPORT/'case-index.json',{'candidate_index':ref(OUT/'case-index.json'),'cases':len(records),'all_state_contacts_recomputed':True,'approved':False})
 print(json.dumps({'case_count':len(records),'candidate_index':ref(OUT/'case-index.json')}))
if __name__=='__main__':main()
