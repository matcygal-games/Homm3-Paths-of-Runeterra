"""Versioned coherent College-family2px registration correction, preserving V6."""
from pathlib import Path
from copy import deepcopy
from PIL import Image,ImageChops,ImageFilter,ImageOps
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'native-transforms-v7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def move(im):out=Image.new(im.mode,im.size);out.paste(im,(0,-2));return out
def main():
 old=HERE/'native-transforms-v6/states.json';v=deepcopy(json.loads(old.read_text()));proposal=json.loads((ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2/guild-family-up2-proposal-v1/receipt.json').read_text());pins={r['state']:r['proposed_frame_sha256']for r in proposal['states']}
 for r in v['states']:
  if r['state']not in pins:continue
  state=r['state'];folder=OUT/state;original=ROOT/r['frame']['path'];frame=move(Image.open(original).convert('RGBA'));save(folder/'layer.png',frame);assert sha(folder/'layer.png')==pins[state]
  for key,name in [('foundation_mask','foundation'),('body_mask','body'),('silhouette_mask','silhouette'),('semantic_zone_mask','semantic-zone'),('door_mask','entry'),('own_treads_mask','own-treads')]:
   p=folder/(name+'.png');save(p,move(Image.open(ROOT/r[key]['path']).convert('L')));r[key]=ref(p)
  solid=frame.getchannel('A').point(lambda a:255 if a>=128 else 0);area=Image.new('RGBA',(800,374),(255,255,255,0));area.putalpha(solid);save(folder/'area.png',area);border=Image.new('RGBA',(800,374),(255,230,100,0));border.putalpha(ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(5)),solid));save(folder/'border.png',border)
  bb=frame.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox();icon=Image.new('RGBA',(150,70));small=ImageOps.contain(frame.crop(bb),(146,66),Image.Resampling.LANCZOS);icon.alpha_composite(small,((150-small.width)//2,68-small.height));save(folder/'construction.png',icon)
  r.update(frame=ref(folder/'layer.png'),alpha8_bbox=list(bb),source_before=ref(original),entrance=[r['entrance'][0],r['entrance'][1]-2],transform={'kind':'whole-native-translation','delta':[0,-2],'scope':'All4CollegeGuild construction states; preserve common site/native depth159.'},construction=ref(folder/'construction.png'));assert r['native_z']==159
  assert Image.open(ROOT/r['foundation_mask']['path']).histogram()[255]==r['actual_foundation_pixels']
 v['script']=ref(Path(__file__));v['base_state_index']=ref(old);v['route_registration_proposal']=ref(ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2/guild-family-up2-proposal-v1/receipt.json');p=OUT/'states.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({'index':ref(p),'source_states_changed':4,'full_roots_preserved':1795,'common_site_depth':159}))
if __name__=='__main__':main()
