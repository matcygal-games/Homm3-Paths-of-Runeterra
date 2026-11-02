"""Unselected structural reference after user visual rejection. No art acceptance."""
from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'coherent-paving-repaint-v1';REPORT=ROOT/'build/reports/complete-town-20261027-v2/coherent-paving-repaint-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True);base=HERE/'terrain/final-native-v14-proposal.png';assert sha(base)=='5787c1646a08f3e8cf0c115cc5b10024f7595ef96f9571511d28786ef326cec7';indexpath=HERE/'native-transforms-v14/states.json';assert sha(indexpath)=='e5101798a4336583495f9fbcb04ad780e54cca81275677b94e191ac69f233023';index=json.loads(indexpath.read_text());receiptpath=ROOT/'build/reports/complete-town-20261027-v2/east-descent-coast-proposal/receipt-v2.json';receipt=json.loads(receiptpath.read_text());bg=Image.open(base).convert('RGBA');before=bg.copy();allowed=Image.new('L',bg.size);parts=[]
 for r in receipt['patches']:
  p=ROOT/r['rgba_patch']['path'];assert sha(p)==r['rgba_patch']['sha256'];im=Image.open(p).convert('RGBA');xy=r['native_box'][:2];bg.alpha_composite(im,xy);mask=Image.new('L',(800,374));mask.paste(im.getchannel('A').point(lambda a:255 if a else 0),xy);allowed=ImageChops.lighter(allowed,mask)
  for state in index['states']:
   body=Image.open(ROOT/state['frame']['path']).convert('RGBA').getchannel('A').point(lambda a:255 if a>=128 else 0);foot=Image.open(ROOT/state['foundation_mask']['path']).convert('L');assert not ImageChops.multiply(body,mask).getbbox();assert not ImageChops.multiply(foot,mask).getbbox()
  parts.append({'name':r['name'],'rgba':ref(p),'native_box':r['native_box'],'alpha_preserved_exact':True})
 assert not ImageChops.multiply(ImageChops.difference(bg,before).convert('RGB'),ImageChops.invert(allowed).convert('RGB')).getbbox();peer=HERE/'terrain-repairs-v14/east-descent-coast-proposal/terrain-proposal-rebased-on-v14.png';assert bg.tobytes()==Image.open(peer).convert('RGBA').tobytes();dest=OUT/'reference-empty-native.png';bg.save(dest,compress_level=9);bg.save(REPORT/'reference-empty-native.png');by={r['state']:r for r in index['states']};sites=json.loads((HERE/'candidate-final-v14/selection.json').read_text())['sites']
 for mode in ['full','base','early','coast','grail','guild-absent']:
  chosen=[site['states'][0]if mode=='base'else site['top']for site in sites if site['id']not in ('coast','grail')]
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  if mode=='coast':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  im=bg.copy()
  for state in sorted(chosen,key=lambda a:by[a]['native_z']):im.alpha_composite(Image.open(ROOT/by[state]['frame']['path']).convert('RGBA'))
  im.save(REPORT/('reference-'+mode+'-native.png'),compress_level=9)
 pins={}
 for r in index['states']:
  for key in ['frame','foundation_mask','body_mask','silhouette_mask','door_mask','own_treads_mask','painted_master']:
   q=r[key];assert sha(ROOT/q['path'])==q['sha256'];pins[q['path']]=q['sha256']
 result={'status':'design proposal','selection':'UNSELECTED STRUCTURAL REFERENCE ONLY; user rejected paving appearance. Final admission/staging/native HOLD. One coherent genuine2D whole-background paving/stair surface repaint is required.','reference_background':ref(dest),'base':ref(base),'all_three_lower_links_receipt':ref(receiptpath),'lower_rgba_parts':parts,'final_36_state_index':ref(indexpath),'all36_source_role_and_master_pins':pins,'outside_lower_rgba_union_unchanged':True,'all36_body_and_structural_foot_clearance_verified':True,'peer_reference_rgba_equal':ref(peer),'script':ref(Path(__file__)),'geometry_to_preserve':'Exact36buildinglayers/poses, publicconnections, court topology, terraceheights, real stair footprints/endpoints, sky/coast/roads/crests; no new body poses or disconnected tile patches.','art_accepted':False,'physical_admission_selected':False,'canonical_written':False,'stage_built':False,'native_verified':False,'release_accepted':False};(OUT/'REFERENCE-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'reference':ref(dest),'record':ref(OUT/'REFERENCE-v1.json'),'lower_links':parts,'state_index':ref(indexpath),'rgba_equal_peer':sha(dest)==sha(peer),'status':'UNSELECTED; user visual rejection HOLD'}))
if __name__=='__main__':main()
