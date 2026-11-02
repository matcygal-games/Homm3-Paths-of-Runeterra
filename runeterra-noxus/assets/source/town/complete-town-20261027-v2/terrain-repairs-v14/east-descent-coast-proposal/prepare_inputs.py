"""Pin current source and produce reference crops; never paint final artwork."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent;TOWN=HERE.parents[1];ROOT=TOWN.parents[3]
REPORT=ROOT/'build/reports/complete-town-20261027-v2/east-descent-coast-proposal'
GUIDE=TOWN/'geometry-final-v2/east-descent-source-guide-v13b'
BOX=(654,160,711,215)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def main():
 HERE.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
 guide=load(GUIDE/'index.json');bgp=ROOT/guide['background']['path'];assert sha(bgp)==guide['background']['sha256']
 s=load(ROOT/guide['source_index']['path']);assert sha(ROOT/guide['source_index']['path'])==guide['source_index']['sha256']
 for r in s['states']:
  if r['state']=='resourceSilo':r['frame']=guide['approved_source_pose_superseding_index_silo']['frame']
 pins={'background':ref(bgp),'source_guide':ref(GUIDE/'index.json'),'source_index':guide['source_index'],'approved_silo_override':guide['approved_source_pose_superseding_index_silo'],'states':s['states'],'exclusions':{n:ref(GUIDE/n)for n in('all36-actual-body128-EXCLUSION.png','all36-full-structural-contact-EXCLUSION.png','all36-source-alpha8-including-shadow.png')}}
 for r in s['states']:
  assert sha(ROOT/r['frame']['path'])==r['frame']['sha256'];assert sha(ROOT/r['painted_master']['path'])==r['painted_master']['sha256']
 (HERE/'input-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
 bg=Image.open(bgp).convert('RGBA');save(HERE/'descent-target-v1.png',bg.crop(BOX));save(HERE/'descent-target-native8x-v1.png',bg.crop(BOX).resize((456,440),Image.Resampling.NEAREST))
 body=Image.open(GUIDE/'all36-actual-body128-EXCLUSION.png').convert('L');roots=Image.open(GUIDE/'all36-full-structural-contact-EXCLUSION.png').convert('L');ex=ImageChops.lighter(body,roots)
 annotated=bg.copy();annotated.paste((255,0,90,255),(0,0,800,374),ex)
 d=ImageDraw.Draw(annotated);d.line([(666,166),(669,180),(680,190),(689,198),(692,210)],fill=(0,255,200),width=2)
 save(HERE/'descent-source-guide-v1.png',annotated.crop(BOX).resize((456,440),Image.Resampling.NEAREST))
 selection=load(TOWN/'candidate-final-v5/selection.json');rows={r['state']:r for r in s['states']}
 for mode in('empty','base','full','coast'):
  im=bg.copy();chosen=[] if mode=='empty'else[site['states'][0]if mode=='base'else site['top']for site in selection['sites']if site['id']not in('coast','grail')]
  if mode=='coast':chosen.append('ship')
  for state in sorted(chosen,key=lambda k:rows[k]['native_z']):im.alpha_composite(Image.open(ROOT/rows[state]['frame']['path']).convert('RGBA'))
  save(REPORT/f'before-{mode}-native.png',im)
  if mode=='full':save(HERE/'descent-architecture-context-v1.png',im.crop((620,125,735,240)).resize((460,460),Image.Resampling.NEAREST))
 print(json.dumps({'source_guide':pins['source_guide'],'background':pins['background'],'states':len(s['states'])}))
if __name__=='__main__':main()
