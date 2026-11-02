"""Bounded genuine painted terrain crops, preserving all architecture and V5 apron."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageChops
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'terrain-repairs-v6';REPORT=ROOT/'build/reports/complete-town-20261027-v2/terrain-repairs-v6/merged-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 REPORT.mkdir(parents=True,exist_ok=True);m=OUT/'menagerie-proposal';m.mkdir(parents=True,exist_ok=True)
 master=m/'painted-master-v2.png'
 if not master.exists():shutil.copyfile('C:/Users/matcy/.codex/generated_images/01a17e29-054b-7131-8ed8-60292e75b6e1/exec-996db486-8e62-4697-b7ef-6ebf5c2a2925.png',master)
 # Broad uninterrupted painted paving crop, rather than retaining-wall pixels.
 crop=(0,320,2169,665);native=ImageOps.fit(Image.open(master).convert('RGBA').crop(crop),(181,51),Image.Resampling.LANCZOS)
 mask=Image.new('L',(181,51));ImageDraw.Draw(mask).polygon([(40,8),(174,8),(174,45),(38,45),(14,24),(14,13)],fill=255);native.putalpha(mask);native.save(m/'patch-native-v2.png',compress_level=9);mask.save(m/'composition-mask-v2.png',compress_level=9)
 bg=Image.open(HERE/'terrain/final-native-v5.png').convert('RGBA');before=bg.copy();patches=[(OUT/'upper-left-proposal/patch-native-v5.png',(0,104)),(OUT/'lower-proposal/tavern-patch-rgba-v1.png',(0,310)),(OUT/'lower-proposal/foundry-patch-rgba-v1.png',(590,321)),(OUT/'crimson-proposal/patch-native-v1.png',(236,302)),(m/'patch-native-v2.png',(425,156))]
 allowed=Image.new('L',bg.size)
 for p,xy in patches:
  im=Image.open(p).convert('RGBA');bg.alpha_composite(im,xy);allowed.paste(ImageChops.lighter(allowed.crop((xy[0],xy[1],xy[0]+im.width,xy[1]+im.height)),im.getchannel('A')),xy)
 dest=HERE/'terrain/final-native-v6.png';bg.save(dest,compress_level=9)
 states=json.loads((HERE/'native-transforms-v6/states.json').read_text())['states'];by={}
 for r in states:by.setdefault(r['site'],[]).append(r)
 def compose(up):
  scene=bg.copy();rows=[v[-1] if up else v[0] for site,v in by.items() if site not in ('grail','coast') and not site.lower().startswith(('ship','dock'))]
  for r in sorted(rows,key=lambda a:a['native_z']):scene.alpha_composite(Image.open(ROOT/r['frame']['path']).convert('RGBA'))
  return scene
 bg.save(REPORT/'empty-native.png');base=compose(False);full=compose(True);base.save(REPORT/'base-native.png');full.save(REPORT/'full-native.png')
 for name,box in [('menagerie',(425,156,606,207)),('crimson',(236,302,398,346)),('upper',(0,104,398,178)),('lower',(0,310,800,374))]:
  for tag,im in [('empty',bg),('base',base),('full',full)]:im.crop(box).resize(((box[2]-box[0])*6,(box[3]-box[1])*6),Image.Resampling.NEAREST).save(REPORT/(name+'-'+tag+'-6x.png'))
 diff=ImageChops.difference(bg,before);outside=ImageChops.multiply(diff.getchannel('R'),ImageChops.invert(allowed.point(lambda v:255 if v else 0)));assert not outside.getbbox();assert bg.crop((407,316,590,365)).tobytes()==before.crop((407,316,590,365)).tobytes()
 receipt={'status':'authored configuration','base':ref(HERE/'terrain/final-native-v5.png'),'terrain':ref(dest),'patches':[{'source':ref(p),'position':list(xy)}for p,xy in patches],'menagerie_source_crop':list(crop),'menagerie_master':ref(master),'transformed_states':ref(HERE/'native-transforms-v6/states.json'),'outside_patches_unchanged':True,'v5_minotaur_apron_unchanged':True,'native_verified':False,'release_accepted':False}
 (OUT/'merge-receipt-v1.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()

