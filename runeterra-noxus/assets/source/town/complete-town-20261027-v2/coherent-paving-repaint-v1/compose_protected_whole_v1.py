"""One global painted master, root-approved complete surface mask, exact immutable pixels."""
from pathlib import Path
from PIL import Image,ImageOps
import json,hashlib,shutil,numpy as np
HERE=Path(__file__).resolve().parent;TOWN=HERE.parent;ROOT=TOWN.parents[3];REPORT=ROOT/'build/reports/complete-town-20261027-v2/coherent-paving-repaint-v1/protected-whole-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 REPORT.mkdir(parents=True,exist_ok=True);control=TOWN/'geometry-final-v2/coherent-paving-guide-v1/paint-controls/revised-v3/SURFACE-CONTROL.json';assert sha(control)=='842e361f9d192c16a0a2f606cbb26e24f27deeae8b052dbd7dd55a6c8d492ea7';c=json.loads(control.read_text());masksource=ROOT/c['paintable_mask']['path'];assert sha(masksource)==c['paintable_mask']['sha256']=='901d8e52bd7365badd1049bce5cd1522167f64b80b7c9747a9629a1c9103c23a';maskpath=HERE/'surface-mask-v1.png';shutil.copyfile(masksource,maskpath);mask=Image.open(maskpath).convert('L');m=np.array(mask);assert set(np.unique(m))<={0,255};assert int((m>0).sum())==186878
 basepath=HERE/'input-scene/native-structural-base.png';assert sha(basepath)=='a6734272452581492165564f67a59b8785f862e66ce421e918e2503bc15b6ed2';base=Image.open(basepath).convert('RGBA');master=HERE/'whole-scene-master-v1.png';assert sha(master)=='c16bf0a74f93d040de2a467226a37474e73d258d9cd1d8c5844e22d1dbdeed4c';paint=ImageOps.fit(Image.open(master).convert('RGBA'),(800,374),Image.Resampling.LANCZOS,centering=(.5,.5));assert paint.tobytes()==Image.open(HERE/'raw-whole-native-v1.png').convert('RGBA').tobytes();out=Image.composite(paint,base,mask);a=np.array(base);b=np.array(out);assert np.array_equal(a[m==0],b[m==0]);dest=HERE/'surface-painted-native-v1.png';out.save(dest,compress_level=9);out.save(REPORT/'empty-native.png');base.save(REPORT/'before-empty-native.png');indexpath=TOWN/'native-transforms-v14/states.json';assert sha(indexpath)=='e5101798a4336583495f9fbcb04ad780e54cca81275677b94e191ac69f233023';index=json.loads(indexpath.read_text());by={r['state']:r for r in index['states']};sites=json.loads((TOWN/'candidate-final-v14/selection.json').read_text())['sites'];pins={}
 for r in index['states']:
  for key in ['frame','painted_master']:
   p=ROOT/r[key]['path'];assert sha(p)==r[key]['sha256'];pins[r[key]['path']]=sha(p)
 for mode in ['full','base','early','coast','grail','guild-absent']:
  chosen=[site['states'][0]if mode=='base'else site['top']for site in sites if site['id']not in ('coast','grail')]
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  if mode=='coast':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  im=out.copy();old=base.copy()
  for state in sorted(chosen,key=lambda s:by[s]['native_z']):
   layer=Image.open(ROOT/by[state]['frame']['path']).convert('RGBA');im.alpha_composite(layer);old.alpha_composite(layer)
  im.save(REPORT/(mode+'-native.png'),compress_level=9);old.save(REPORT/('before-'+mode+'-native.png'),compress_level=9);board=Image.new('RGBA',(1600,374));board.alpha_composite(old);board.alpha_composite(im,(800,0));board.save(REPORT/(mode+'-before-left-after-right-native.png'),compress_level=9)
 board=Image.new('RGBA',(1600,374));board.alpha_composite(base);board.alpha_composite(out,(800,0));board.save(REPORT/'empty-before-left-after-right-native.png',compress_level=9)
 result={'status':'design proposal','selection':'UNSELECTED first protected whole-master composite. Root visual review, fresh support/entry/routes and meaningful negatives/cold source closure remain required. No admission or staging.','native_surface':ref(dest),'whole_master':ref(master),'master_size':[1836,857],'owned_structural_input':ref(basepath),'surface_mask':ref(maskpath),'surface_control_revision_id':'COHERENT_PAVING_SURFACE_V3','surface_control_sha256':sha(control),'global_registration':'ONE global ImageOps.fit whole1836x857master to800x374,LANCZOS,center(.5,.5); no independently scaled region, filter or code-drawn artwork.','editable_pixels':int((m>0).sum()),'changed_pixels':int(np.any(a!=b,axis=2).sum()),'changed_outside_surface_mask':0,'all_immutable_background_pixels_exact':True,'all36_raw_master_and_frame_pins_unchanged':pins,'state_index':ref(indexpath),'generation':ref(HERE/'generation-record-v2.json'),'script':ref(Path(__file__)),'canonical_written':False,'stage_built':False,'native_verified':False,'release_accepted':False};(HERE/'surface-assembly-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['native_surface','whole_master','surface_mask','editable_pixels','changed_pixels','changed_outside_surface_mask','global_registration']}))
if __name__=='__main__':main()
