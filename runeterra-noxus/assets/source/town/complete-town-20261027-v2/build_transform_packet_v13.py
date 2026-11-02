"""Root-reviewed Hound/Market whole-source access corrections; V12 preserved."""
from pathlib import Path
from copy import deepcopy
from PIL import Image,ImageOps,ImageChops,ImageFilter
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'native-transforms-v13';DELTAS={'dwellingLvl2':(-1,-7),'dwellingUpLvl2':(-1,-7),'marketplace':(3,0)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def move(im,xy):out=Image.new(im.mode,im.size);out.paste(im,xy);return out
def main():
 old=HERE/'native-transforms-v12/states.json';index=deepcopy(json.loads(old.read_text()))
 for r in index['states']:
  if r['state']not in DELTAS:continue
  state=r['state'];xy=DELTAS[state];folder=OUT/state;source=ROOT/r['frame']['path'];original=Image.open(source).convert('RGBA');im=move(original,xy);assert original.getchannel('A').histogram()==im.getchannel('A').histogram();save(folder/'layer.png',im)
  for key,name in [('foundation_mask','foundation'),('body_mask','body'),('silhouette_mask','silhouette'),('semantic_zone_mask','semantic-zone'),('door_mask','entry'),('own_treads_mask','own-treads')]:
   before=Image.open(ROOT/r[key]['path']).convert('L');after=move(before,xy);assert before.histogram()==after.histogram();p=folder/(name+'.png');save(p,after);r[key]=ref(p)
  solid=im.getchannel('A').point(lambda a:255 if a>=128 else 0);assert solid.tobytes()==Image.open(ROOT/r['body_mask']['path']).convert('L').tobytes();area=Image.new('RGBA',(800,374),(255,255,255,0));area.putalpha(solid);save(folder/'area.png',area);border=Image.new('RGBA',(800,374),(255,230,100,0));border.putalpha(ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(5)),solid));save(folder/'border.png',border);bb=im.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox();icon=Image.new('RGBA',(150,70));small=ImageOps.contain(im.crop(bb),(146,66),Image.Resampling.LANCZOS);icon.alpha_composite(small,((150-small.width)//2,68-small.height));save(folder/'construction.png',icon)
  prior=r['transform'];r.update(frame=ref(folder/'layer.png'),alpha8_bbox=list(bb),source_before=ref(source),entrance=[r['entrance'][0]+xy[0],r['entrance'][1]+xy[1]],native_z=r['native_z']+xy[1],construction=ref(folder/'construction.png'),transform={'kind':'whole-native-translation','delta':list(xy),'prior_transform':prior,'purpose':'Root-reviewed actual private/public access clearance on unchanged genuine support planes; complete family/source/contact/entry move together.'})
  assert Image.open(ROOT/r['foundation_mask']['path']).histogram()[255]==r['actual_foundation_pixels']
 index['base_state_index']=ref(old);index['script']=ref(Path(__file__));dest=OUT/'states.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(index,indent=2)+'\n');print(json.dumps({'index':ref(dest),'whole_states_moved':3,'all_source_alpha_histograms_preserved':True,'all_full_contacts_preserved':True}))
if __name__=='__main__':main()
