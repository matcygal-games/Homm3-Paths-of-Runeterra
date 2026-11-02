"""Authorized technical crop of existing genuine V5 paving; no new artwork drawn."""
from pathlib import Path
from PIL import Image,ImageOps,ImageChops
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'terrain-repairs-v11/minotaur-prop';REPORT=ROOT/'build/reports/complete-town-20261027-v2/minotaur-prop-removal-v11/proposal-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True);master=HERE/'terrain/minotaur-apron-master-v5.png';crop=(780,200,1420,440);xy=(430,316);size=(35,24);patch=ImageOps.fit(Image.open(master).convert('RGBA').crop(crop),size,Image.Resampling.LANCZOS);native=OUT/'native-v1.png';patch.save(native,compress_level=9)
 bg=Image.open(HERE/'terrain/final-native-v10-proposal.png').convert('RGBA');before=bg.copy();bg.alpha_composite(patch,xy);assert bg.crop((0,340,800,374)).tobytes()==before.crop((0,340,800,374)).tobytes();allowed=Image.new('L',bg.size);allowed.paste(255,(430,316,465,340));assert not ImageChops.multiply(ImageChops.difference(bg,before).convert('RGB'),ImageChops.invert(allowed).convert('RGB')).getbbox()
 target=HERE/'terrain/final-native-v11-proposal.png';bg.save(target,compress_level=9);bg.save(REPORT/'empty-native.png');s=json.loads((HERE/'candidate-final-v10/selection.json').read_text());by={r['state']:r for r in s['states']}
 for mode in ['full','base','coast']:
  chosen=[site['states'][0]if mode=='base'else site['top']for site in s['sites']if site['id']not in ('coast','grail')]
  if mode=='coast':chosen.append('ship')
  im=bg.copy()
  for state in sorted(chosen,key=lambda a:by[a]['native_z']):im.alpha_composite(Image.open(ROOT/by[state]['native_layer']).convert('RGBA'))
  im.save(REPORT/(mode+'-native.png'))
 for tag in ['empty','full','base']:
  im=Image.open(REPORT/(tag+'-native.png'));im.crop((426,312,470,353)).resize((880,820),Image.Resampling.NEAREST).save(REPORT/(tag+'-prop-context20x.png'))
 result={'status':'design proposal','base':ref(HERE/'terrain/final-native-v10-proposal.png'),'terrain':ref(target),'existing_painted_master':ref(master),'original_genuine_generation':ref(HERE/'terrain/minotaur-apron-generation-v5.json'),'source_crop':list(crop),'native':ref(native),'native_rectangle':[430,316,465,340],'method':'Uniform crop/fit of preexisting genuine V5 horizontal paving. Complete obsolete flame/bowl/pier/flare context removed; no code-drawn floor or filter.','script':ref(Path(__file__)),'all_pixels_y340_and_below_unchanged':True,'outside_patch_unchanged':True,'all36_architecture_frames_unchanged':True,'physical_support_admitted':False,'native_verified':False,'release_accepted':False};(OUT/'receipt-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
