"""Last demonstrated Arena contact bands; preserve complete east public flight."""
from pathlib import Path
from PIL import Image,ImageOps,ImageChops,ImageDraw
import json,hashlib,shutil,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'terrain-repairs-v10/arena-caps';REPORT=ROOT/'build/reports/complete-town-20261027-v2/arena-caps-v10/proposal-v1'
FILES={'left':'exec-49faacca-2dc9-4a2b-804a-9eb922731449.png','front':'exec-94e11245-704b-4062-8192-ff77a76eb7ea.png'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
 for n,f in FILES.items():
  p=OUT/(n+'-master-v1.png')
  if not p.exists():shutil.copyfile(Path('C:/Users/matcy/.codex/generated_images/01a17e29-054b-7131-8ed8-60292e75b6e1')/f,p)
 bg=Image.open(HERE/'terrain/final-native-v9-proposal.png').convert('RGBA');before=bg.copy();allowed=Image.new('L',bg.size);rows=[]
 for name in ['left','front']:
  p=OUT/(name+'-master-v1.png');im=Image.open(p).convert('RGBA')
  if name=='left':crop=(0,460,im.width,im.height);xy=(184,194);size=(30,24);im=ImageOps.fit(im.crop(crop),size,Image.Resampling.LANCZOS);mask=Image.new('L',size,255)
  else:
   rgb=np.array(im.convert('RGB'));valid=(rgb.max(axis=2)>24).sum(axis=1)>im.width*.2;ys=np.where(valid)[0];crop=(0,int(ys.min()),im.width,int(ys.max()+1));xy=(230,219);size=(116,23);im=ImageOps.fit(im.crop(crop),size,Image.Resampling.LANCZOS);mask=Image.new('L',size);ImageDraw.Draw(mask).rectangle((0,0,89,22),fill=255);ImageDraw.Draw(mask).rectangle((69,0,104,0),fill=0)
  im.putalpha(mask);native=OUT/(name+'-native-v1.png');im.save(native,compress_level=9);bg.alpha_composite(im,xy);allowed.paste(mask,xy);rows.append({'master':ref(p),'source_crop':list(crop),'native':ref(native),'position':list(xy),'native_size':list(size),'method':'Uniform crop/fit of genuine painted level paving/cap. Front composition restricted to proven band west of320; protected east publicflight pixels unchanged.'})
 assert bg.crop((299,188,335,220)).tobytes()==before.crop((299,188,335,220)).tobytes()
 assert not ImageChops.multiply(ImageChops.difference(bg,before).convert('RGB'),ImageChops.invert(allowed).convert('RGB')).getbbox()
 target=HERE/'terrain/final-native-v10-proposal.png';bg.save(target,compress_level=9);bg.save(REPORT/'empty-native.png');s=json.loads((HERE/'candidate-final-v9/selection.json').read_text());by={r['state']:r for r in s['states']}
 for mode in ['full','base','coast','guild-absent']:
  chosen=[site['states'][0]if mode=='base'else site['top']for site in s['sites']if site['id']not in ('coast','grail')]
  if mode=='coast':chosen.append('ship')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  im=bg.copy()
  for state in sorted(chosen,key=lambda a:by[a]['native_z']):im.alpha_composite(Image.open(ROOT/by[state]['native_layer']).convert('RGBA'))
  im.save(REPORT/(mode+'-native.png'))
 for tag in ['empty','full','base']:
  im=Image.open(REPORT/(tag+'-native.png'))
  for name,b in [('left',(184,194,214,218)),('front',(230,219,346,242))]:im.crop(b).resize(((b[2]-b[0])*10,(b[3]-b[1])*10),Image.Resampling.NEAREST).save(REPORT/(name+'-'+tag+'-10x.png'))
 result={'status':'design proposal','base':ref(HERE/'terrain/final-native-v9-proposal.png'),'terrain':ref(target),'patches':rows,'script':ref(Path(__file__)),'outside_patches_unchanged':True,'east_public_flight_rectangle_preserved':[299,188,335,220],'all36_architecture_frames_unchanged':True,'physical_support_admitted':False,'native_verified':False,'release_accepted':False};(OUT/'receipt-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
