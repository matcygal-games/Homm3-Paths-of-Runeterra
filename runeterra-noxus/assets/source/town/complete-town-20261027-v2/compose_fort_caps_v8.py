"""Reproduce bounded genuine painted support caps; never alters architecture."""
from pathlib import Path
from PIL import Image,ImageOps,ImageChops
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'terrain-repairs-v8/fort-caps';REPORT=ROOT/'build/reports/complete-town-20261027-v2/fort-support-repair-v8/proposal-v1'
MASTERS={'left-family':'exec-b6581018-fc57-458e-b85d-a794067cc18f.png','central-family':'exec-00dc9cb5-1487-419c-9132-a86b80f3cdcf.png','east-family':'exec-ee49f255-ec8b-4cb0-b217-6f1157ff1425.png'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
 for n,f in MASTERS.items():
  p=OUT/(n+'-master-v1.png')
  if not p.exists():shutil.copyfile(Path('C:/Users/matcy/.codex/generated_images/01a17e29-054b-7131-8ed8-60292e75b6e1')/f,p)
 bg=Image.open(HERE/'terrain/final-native-v6.png').convert('RGBA');before=bg.copy();allowed=Image.new('L',bg.size);rows=[]
 patches=[('left-family',(80,0,800,650),(195,105),(77,28)),('central-family',None,(390,128),(36,25)),('east-family',(750,120,1320,515),(525,106),(141,47)),('east-family',(1430,275,1810,440),(644,133),(26,15))]
 for i,(name,crop,xy,size) in enumerate(patches):
  master=OUT/(name+'-master-v1.png');im=Image.open(master).convert('RGBA')
  if crop:im=im.crop(crop)
  patch=ImageOps.fit(im,size,Image.Resampling.LANCZOS);p=OUT/(name+'-native-'+str(i)+'.png');patch.save(p,compress_level=9);bg.alpha_composite(patch,xy);allowed.paste(255,(*xy,xy[0]+size[0],xy[1]+size[1]));rows.append({'master':ref(master),'crop':list(crop)if crop else None,'native':ref(p),'position':list(xy),'size':list(size),'method':'Uniform fit/crop of genuine painted horizontal cap, plus entire genuine painted public-stair component; no procedural architecture or contact-mask acceptance.'})
 p=HERE/'terrain/final-native-v8-proposal.png';bg.save(p,compress_level=9);bg.save(REPORT/'empty-native.png');s=json.loads((HERE/'candidate-final-v7/selection.json').read_text());by={x['state']:x for x in s['states']}
 for mode in ['full','base','coast','guild-absent']:
  chosen=[site['states'][0]if mode=='base'else site['top']for site in s['sites']if site['id']not in ('coast','grail')]
  if mode=='coast':chosen.append('ship')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  im=bg.copy()
  for state in sorted(chosen,key=lambda a:by[a]['native_z']):im.alpha_composite(Image.open(ROOT/by[state]['native_layer']).convert('RGBA'))
  im.save(REPORT/(mode+'-native.png'))
 for tag in ['empty','full','base','guild-absent']:
  im=Image.open(REPORT/(tag+'-native.png'))
  for name,b in [('left',(195,105,272,133)),('central',(390,128,426,153)),('east',(525,106,670,153))]:im.crop(b).resize(((b[2]-b[0])*10,(b[3]-b[1])*10),Image.Resampling.NEAREST).save(REPORT/(name+'-'+tag+'-10x.png'))
 diff=ImageChops.difference(bg,before).convert('RGB');outside=ImageChops.multiply(diff,ImageChops.invert(allowed).convert('RGB'));assert not outside.getbbox();assert bg.crop((407,316,590,365)).tobytes()==before.crop((407,316,590,365)).tobytes()
 receipt={'status':'design proposal','base':ref(HERE/'terrain/final-native-v6.png'),'terrain':ref(p),'patches':rows,'script':ref(Path(__file__)),'outside_patches_unchanged':True,'all36_architecture_frames_unchanged':True,'v5_minotaur_apron_unchanged':True,'physical_support_admitted':False,'native_verified':False,'release_accepted':False};(OUT/'receipt-v1.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
