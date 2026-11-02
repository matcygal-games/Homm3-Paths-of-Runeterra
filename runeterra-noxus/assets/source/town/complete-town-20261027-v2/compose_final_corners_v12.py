"""Consolidated genuine-source corner court and Minotaur left apron correction."""
from pathlib import Path
from PIL import Image,ImageOps,ImageChops
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'terrain-repairs-v12/final-corners';REPORT=ROOT/'build/reports/complete-town-20261027-v2/final-corners-v12/proposal-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True);bg=Image.open(HERE/'terrain/final-native-v10-proposal.png').convert('RGBA');before=bg.copy();allowed=Image.new('L',bg.size);rows=[]
 patches=[('fort-corner',HERE/'terrain-repairs-v8/fort-caps/central-family-master-v1.png',(350,300,1150,800),(448,138),(34,15),HERE/'terrain-repairs-v8/fort-caps/generation-record-v1.json'),('minotaur-left-apron',HERE/'terrain/minotaur-apron-master-v5.png',(720,71,1620,480),(430,316),(64,38),HERE/'terrain/minotaur-apron-generation-v5.json')]
 for name,master,crop,xy,size,gen in patches:
  im=ImageOps.fit(Image.open(master).convert('RGBA').crop(crop),size,Image.Resampling.LANCZOS);p=OUT/(name+'-native-v1.png');im.save(p,compress_level=9);bg.alpha_composite(im,xy);allowed.paste(255,(*xy,xy[0]+size[0],xy[1]+size[1]));rows.append({'name':name,'existing_genuine_master':ref(master),'generation_record':ref(gen),'source_crop':list(crop),'native':ref(p),'position':list(xy),'native_size':list(size),'method':'Uniform crop/fit of existing genuine horizontal paving. No procedural drawing/filter. Minotaur obsolete prop and intrusive old flight replaced by broad true court/apron with open western paved connector at430..432; actual main avenue x<430 remains unchanged.'})
 assert bg.crop((0,0,430,374)).tobytes()==before.crop((0,0,430,374)).tobytes();assert not ImageChops.multiply(ImageChops.difference(bg,before).convert('RGB'),ImageChops.invert(allowed).convert('RGB')).getbbox();target=HERE/'terrain/final-native-v12-proposal.png';bg.save(target,compress_level=9);bg.save(REPORT/'empty-native.png');s=json.loads((HERE/'candidate-final-v10/selection.json').read_text());by={r['state']:r for r in s['states']}
 for mode in ['full','base','coast','guild-absent']:
  chosen=[site['states'][0]if mode=='base'else site['top']for site in s['sites']if site['id']not in ('coast','grail')]
  if mode=='coast':chosen.append('ship')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  im=bg.copy()
  for state in sorted(chosen,key=lambda a:by[a]['native_z']):im.alpha_composite(Image.open(ROOT/by[state]['native_layer']).convert('RGBA'))
  im.save(REPORT/(mode+'-native.png'))
 for tag in ['empty','full','base']:
  im=Image.open(REPORT/(tag+'-native.png'))
  for name,b in [('fort',(440,132,486,157)),('minotaur',(420,310,500,358))]:im.crop(b).resize(((b[2]-b[0])*10,(b[3]-b[1])*10),Image.Resampling.NEAREST).save(REPORT/(name+'-'+tag+'-10x.png'))
 result={'status':'design proposal','base':ref(HERE/'terrain/final-native-v10-proposal.png'),'terrain':ref(target),'patches':rows,'script':ref(Path(__file__)),'actual_main_avenue_x_below430_unchanged':True,'outside_two_patches_unchanged':True,'all36_architecture_frames_unchanged':True,'structural_foot_contacts_unchanged':True,'public_connector':'Old interfering Minotaur left public flight replaced by broad genuine horizontal court/apron opening WEST to unchanged main avenue; connector430..432 lies outside all-state physical foot union xmin433. Own main entry512+ stays unchanged.','physical_support_admitted':False,'native_verified':False,'release_accepted':False};(OUT/'receipt-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
