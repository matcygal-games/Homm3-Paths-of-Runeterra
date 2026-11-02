"""Coherent bounded genuine painted Hound/Silo landings and public flights."""
from pathlib import Path
from PIL import Image,ImageOps,ImageChops
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'terrain-repairs-v9/landing-connectors';REPORT=ROOT/'build/reports/complete-town-20261027-v2/landing-connectors-v9/proposal-v1'
MASTERS={'hound':'exec-4369a13c-f7bb-4e5c-a53e-8c9a486a5d76.png','silo':'exec-57007c44-b3c8-42b8-8e3d-13ebd20650d1.png'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
 for n,f in MASTERS.items():
  p=OUT/(n+'-master-v1.png')
  if not p.exists():shutil.copyfile(Path('C:/Users/matcy/.codex/generated_images/01a17e29-054b-7131-8ed8-60292e75b6e1')/f,p)
 bg=Image.open(HERE/'terrain/final-native-v8-proposal.png').convert('RGBA');before=bg.copy();allowed=Image.new('L',bg.size);rows=[]
 patches=[('hound',(500,0,1800,500),(86,204),(115,36),'landing'),('hound',(40,150,450,540),(74,208),(12,27),'public-flight'),('silo',(850,450,1200,750),(658,240),(53,29),'landing'),('silo',(430,310,760,770),(640,236),(18,27),'public-flight')]
 for name,crop,xy,size,kind in patches:
  master=OUT/(name+'-master-v1.png');im=ImageOps.fit(Image.open(master).convert('RGBA').crop(crop),size,Image.Resampling.LANCZOS);p=OUT/(name+'-'+kind+'-native-v1.png');im.save(p,compress_level=9);bg.alpha_composite(im,xy);allowed.paste(255,(*xy,xy[0]+size[0],xy[1]+size[1]));rows.append({'site':name,'kind':kind,'master':ref(master),'crop':list(crop),'native':ref(p),'position':list(xy),'size':list(size),'method':'Uniform crop/fit of genuine painted courtyard or public stair component; all architecture and contacts remain unchanged.'})
 target=HERE/'terrain/final-native-v9-proposal.png';bg.save(target,compress_level=9);bg.save(REPORT/'empty-native.png');s=json.loads((HERE/'candidate-final-v7/selection.json').read_text());by={r['state']:r for r in s['states']}
 for mode in ['full','base','coast','guild-absent']:
  chosen=[site['states'][0]if mode=='base'else site['top']for site in s['sites']if site['id']not in ('coast','grail')]
  if mode=='coast':chosen.append('ship')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  im=bg.copy()
  for state in sorted(chosen,key=lambda a:by[a]['native_z']):im.alpha_composite(Image.open(ROOT/by[state]['native_layer']).convert('RGBA'))
  im.save(REPORT/(mode+'-native.png'))
 for tag in ['empty','full','base']:
  im=Image.open(REPORT/(tag+'-native.png'))
  for name,b in [('hound',(70,198,205,248)),('silo',(630,230,785,277))]:im.crop(b).resize(((b[2]-b[0])*8,(b[3]-b[1])*8),Image.Resampling.NEAREST).save(REPORT/(name+'-'+tag+'-8x.png'))
 diff=ImageChops.difference(bg,before).convert('RGB');assert not ImageChops.multiply(diff,ImageChops.invert(allowed).convert('RGB')).getbbox();assert bg.crop((407,316,590,365)).tobytes()==before.crop((407,316,590,365)).tobytes()
 result={'status':'design proposal','base':ref(HERE/'terrain/final-native-v8-proposal.png'),'terrain':ref(target),'patches':rows,'script':ref(Path(__file__)),'outside_patches_unchanged':True,'all36_architecture_frames_unchanged':True,'v5_minotaur_apron_unchanged':True,'physical_support_admitted':False,'native_verified':False,'release_accepted':False};(OUT/'receipt-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
