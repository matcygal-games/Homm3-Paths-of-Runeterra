"""ONE globally registered master preview; no local texture crops or acceptance."""
from pathlib import Path
from PIL import Image,ImageOps
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;TOWN=HERE.parent;ROOT=TOWN.parents[3];W=ROOT.parent;REPORT=ROOT/'build/reports/complete-town-20261027-v2/coherent-paving-repaint-v1/raw-whole-preview-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 REPORT.mkdir(parents=True,exist_ok=True);master=HERE/'whole-scene-master-v1.png'
 if not master.exists():shutil.copyfile('C:/Users/matcy/.codex/generated_images/01a17e29-054b-7131-8ed8-60292e75b6e1/exec-2440fd30-cf2b-44e3-8931-a8c9321904e9.png',master)
 raw=Image.open(master).convert('RGBA');bg=ImageOps.fit(raw,(800,374),Image.Resampling.LANCZOS,centering=(.5,.5));native=HERE/'raw-whole-native-v1.png';bg.save(native,compress_level=9);bg.save(REPORT/'empty-native.png');indexpath=TOWN/'native-transforms-v14/states.json';index=json.loads(indexpath.read_text());rows={r['state']:r for r in index['states']};s=json.loads((TOWN/'candidate-final-v14/selection.json').read_text());originals=json.loads((ROOT/'build/reports/complete-town-20261027-v2/final-v3/original-control-provenance.json').read_text())['sources']
 for p,pin in originals.items():assert sha(W/p)==pin
 for r in index['states']:
  assert sha(ROOT/r['frame']['path'])==r['frame']['sha256'];assert sha(ROOT/r['painted_master']['path'])==r['painted_master']['sha256']
 for mode in ['full','base','early','coast','grail','guild-absent']:
  chosen=[site['states'][0]if mode=='base'else site['top']for site in s['sites']if site['id']not in ('coast','grail')]
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  if mode=='coast':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  im=bg.copy()
  for state in sorted(chosen,key=lambda a:rows[a]['native_z']):im.alpha_composite(Image.open(ROOT/rows[state]['frame']['path']).convert('RGBA'))
  im.save(REPORT/(mode+'-native.png'),compress_level=9)
 result={'status':'design proposal','selection':'UNSELECTED RAW WHOLE-PAINT PREVIEW ONLY. Immutable background surface mask not applied; geometry/visual review pending; user-rejection hold remains.','master':ref(master),'master_size':list(raw.size),'global_native':ref(native),'registration':'ONE ImageOps.fit of entire master to800x374 with LANCZOS and center(.5,.5). No independently resized region or texture patch.','source_index':ref(indexpath),'all36_raw_master_and_frame_pins_unchanged':True,'all18_protected_original_inputs_unchanged':True,'generation':ref(HERE/'generation-record-v1.json'),'script':ref(Path(__file__)),'protected_mask_applied':False,'art_selected':False,'canonical_written':False,'stage_built':False,'native_verified':False,'release_accepted':False};(HERE/'RAW-PREVIEW-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
