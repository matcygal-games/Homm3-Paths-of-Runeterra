"""Only confirmed Silo/Arena structural caps and obsolete Rift brazier removal."""
from pathlib import Path
from PIL import Image,ImageOps,ImageChops
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'terrain-repairs-v13/three-caps';REPORT=ROOT/'build/reports/complete-town-20261027-v2/final-three-caps-v13/proposal-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True);bg=Image.open(HERE/'terrain/final-native-v12-proposal.png').convert('RGBA');before=bg.copy();allowed=Image.new('L',bg.size);rows=[]
 patches=[('silo-right',HERE/'terrain-repairs-v9/landing-connectors/silo-master-v1.png',(850,450,1200,750),(748,242),(25,18),HERE/'terrain-repairs-v9/landing-connectors/generation-record-v1.json'),('arena-right',HERE/'terrain-repairs-v10/arena-caps/front-master-v1.png',(1000,180,1600,400),(320,220),(14,9),HERE/'terrain-repairs-v10/arena-caps/generation-record-v1.json'),('rift-obsolete-brazier',HERE/'terrain/minotaur-apron-master-v5.png',(650,170,1750,470),(420,268),(21,30),HERE/'terrain/minotaur-apron-generation-v5.json')]
 for name,master,crop,xy,size,gen in patches:
  im=ImageOps.fit(Image.open(master).convert('RGBA').crop(crop),size,Image.Resampling.LANCZOS);p=OUT/(name+'-native-v1.png');im.save(p,compress_level=9);bg.alpha_composite(im,xy);allowed.paste(255,(*xy,xy[0]+size[0],xy[1]+size[1]));rows.append({'name':name,'existing_genuine_master':ref(master),'generation_record':ref(gen),'source_crop':list(crop),'native':ref(p),'position':list(xy),'native_size':list(size),'method':'Uniform crop/fit of existing genuine horizontal paving; no code-drawn floor/filter, body or root omission.'})
 assert bg.crop((773,0,800,374)).tobytes()==before.crop((773,0,800,374)).tobytes();assert bg.crop((299,188,335,220)).tobytes()==before.crop((299,188,335,220)).tobytes();assert bg.crop((0,255,420,306)).tobytes()==before.crop((0,255,420,306)).tobytes();assert not ImageChops.multiply(ImageChops.difference(bg,before).convert('RGB'),ImageChops.invert(allowed).convert('RGB')).getbbox();target=HERE/'terrain/final-native-v13-proposal.png';bg.save(target,compress_level=9);bg.save(REPORT/'empty-native.png');index=json.loads((HERE/'native-transforms-v13/states.json').read_text());by={r['state']:r for r in index['states']};s=json.loads((HERE/'candidate-final-v12/selection.json').read_text())
 for mode in ['full','base','coast','guild-absent']:
  chosen=[site['states'][0]if mode=='base'else site['top']for site in s['sites']if site['id']not in ('coast','grail')]
  if mode=='coast':chosen.append('ship')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  im=bg.copy()
  for state in sorted(chosen,key=lambda a:by[a]['native_z']):im.alpha_composite(Image.open(ROOT/by[state]['frame']['path']).convert('RGBA'))
  im.save(REPORT/(mode+'-native.png'))
 for tag in ['empty','full','base']:
  im=Image.open(REPORT/(tag+'-native.png'))
  for name,b in [('silo',(744,236,784,268)),('arena',(313,216,346,235)),('rift',(410,264,445,307))]:im.crop(b).resize(((b[2]-b[0])*12,(b[3]-b[1])*12),Image.Resampling.NEAREST).save(REPORT/(name+'-'+tag+'-12x.png'))
 result={'status':'design proposal','base':ref(HERE/'terrain/final-native-v12-proposal.png'),'terrain':ref(target),'patches':rows,'script':ref(Path(__file__)),'state_index':ref(HERE/'native-transforms-v13/states.json'),'outside_three_patches_unchanged':True,'coast_x773_and_beyond_unchanged':True,'arena_public_flight_rectangle_unchanged':[299,188,335,220],'rift_left_flight_x_below420_unchanged':True,'structural_contacts_not_trimmed':True,'physical_support_admitted':False,'native_verified':False,'release_accepted':False};(OUT/'receipt-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
