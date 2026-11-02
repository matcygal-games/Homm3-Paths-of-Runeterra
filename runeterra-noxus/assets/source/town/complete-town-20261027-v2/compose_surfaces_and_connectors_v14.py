"""Genuine projected caps/retaining faces plus exact reviewed public connector RGBA."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageChops
import json,hashlib,shutil,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'terrain-repairs-v14/surface-integration';REPORT=ROOT/'build/reports/complete-town-20261027-v2/surface-integration-v14/proposal-v1'
FILES={'silo':'exec-afbdb540-c6c0-4b99-ae93-e2a2d8375a7d.png','rift':'exec-2827ecb9-63fc-4e1e-9fb2-a57358c29a0a.png'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True);bg=Image.open(HERE/'terrain/final-native-v13b-proposal.png').convert('RGBA');before=bg.copy();allowed=Image.new('L',bg.size);parts=[]
 for name,filename in FILES.items():
  master=OUT/(name+'-master-v1.png')
  if not master.exists():shutil.copyfile(Path('C:/Users/matcy/.codex/generated_images/01a17e29-054b-7131-8ed8-60292e75b6e1')/filename,master)
  xy,size=((736,232),(43,38))if name=='silo'else((414,262),(32,47));im=ImageOps.fit(Image.open(master).convert('RGBA'),size,Image.Resampling.LANCZOS);mask=Image.new('L',size,255)
  if name=='rift':mask=Image.new('L',size);ImageDraw.Draw(mask).rectangle((6,5,26,36),fill=255)
  im.putalpha(mask);native=OUT/(name+'-native-v1.png');im.save(native,compress_level=9);bg.alpha_composite(im,xy);allowed.paste(mask,xy);parts.append({'kind':'genuine-painted-surface-edit','master':ref(master),'native':ref(native),'position':list(xy),'size':list(size),'method':'Uniform whole-context fit of genuine horizontal-top/projected-edge/vertical-retaining-face painting; Rift alpha restricts edit to420267441299, preserving actual left flight.'})
 index=json.loads((HERE/'native-transforms-v14/states.json').read_text());public=HERE/'terrain-repairs-v13/mainavenue-east-connector-proposal'
 for name,xy,size,pin in [('east',(414,168),(31,18),'f487197f34691527675c9aed13d4eba30feffc83b4a7c10871fa6a39b9c340b3'),('west',(0,130),(10,25),'4b2549e97167678f02439981b52ffd9b1743bd7a647804bf4b5a9dc1de6a37ce')]:
  p=public/(name+'-native-v2.png');assert sha(p)==pin;im=Image.open(p).convert('RGBA');assert im.size==size;mask=Image.new('L',(800,374));mask.paste(im.getchannel('A').point(lambda a:255 if a else 0),xy)
  for r in index['states']:
   body=Image.open(ROOT/r['frame']['path']).convert('RGBA').getchannel('A').point(lambda a:255 if a>=128 else 0);assert not ImageChops.multiply(body,mask).getbbox(),(name,r['state']);foundation=Image.open(ROOT/r['foundation_mask']['path']).convert('L');assert not ImageChops.multiply(foundation,mask).getbbox(),(name,r['state'],'foundation')
  bg.alpha_composite(im,xy);allowed=ImageChops.lighter(allowed,mask);parts.append({'kind':'reviewed-public-flight-and-landing','native':ref(p),'position':list(xy),'size':list(size),'alpha_preserved_exact':True,'all36_current_bodies_and_foundations_clear':True})
 assert bg.crop((779,0,800,374)).tobytes()==before.crop((779,0,800,374)).tobytes();assert bg.crop((299,188,335,220)).tobytes()==before.crop((299,188,335,220)).tobytes();assert bg.crop((400,255,420,306)).tobytes()==before.crop((400,255,420,306)).tobytes();assert not ImageChops.multiply(ImageChops.difference(bg,before).convert('RGB'),ImageChops.invert(allowed.point(lambda v:255 if v else 0)).convert('RGB')).getbbox();target=HERE/'terrain/final-native-v14-proposal.png';bg.save(target,compress_level=9);bg.save(REPORT/'empty-native.png');by={r['state']:r for r in index['states']};sites=json.loads((HERE/'candidate-final-v12/selection.json').read_text())['sites']
 for mode in ['full','base','coast','guild-absent','early']:
  chosen=[site['states'][0]if mode=='base'else site['top']for site in sites if site['id']not in ('coast','grail')]
  if mode=='coast':chosen.append('ship')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  im=bg.copy()
  for state in sorted(chosen,key=lambda a:by[a]['native_z']):im.alpha_composite(Image.open(ROOT/by[state]['frame']['path']).convert('RGBA'))
  im.save(REPORT/(mode+'-native.png'))
 for tag in ['empty','full','base']:
  im=Image.open(REPORT/(tag+'-native.png'))
  for name,b in [('silo',(736,232,779,270)),('rift',(414,262,446,309)),('east',(406,160,453,193)),('west',(0,123,20,160))]:im.crop(b).resize(((b[2]-b[0])*12,(b[3]-b[1])*12),Image.Resampling.NEAREST).save(REPORT/(name+'-'+tag+'-12x.png'))
 result={'status':'design proposal','base':ref(HERE/'terrain/final-native-v13b-proposal.png'),'terrain':ref(target),'parts':parts,'script':ref(Path(__file__)),'actual_pose_index':ref(HERE/'native-transforms-v14/states.json'),'outside_edit_union_unchanged':True,'protected_coast_x779_plus_unchanged':True,'arena_public_flight_rectangle_unchanged':[299,188,335,220],'rift_left_actual_flight_x_below420_unchanged':True,'physical_support_admitted':False,'native_verified':False,'release_accepted':False};(OUT/'receipt-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
