"""Execute actual town-producer reproducibility and approved-pixel controls.

This deliberately does not stand in for the pending public physical contract.
No canonical source, old artifact or shared helper is written.
"""
from pathlib import Path
import json,hashlib,sys,copy,io
from PIL import Image,ImageChops,ImageOps,ImageDraw
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/source-verification-v2'
sys.path.insert(0,str(WORKSPACE/'scripts'))
from faction_art_compile import create_compiler

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def rgba(p):return Image.open(p).convert('RGBA')
def rgbdiff(a,b):
 d=ImageChops.difference(a.convert('RGB'),b.convert('RGB'))
 return ImageChops.lighter(ImageChops.lighter(*d.split()[:2]),d.split()[2]).point(lambda p:255 if p else 0)

def main():
 REPORT.mkdir(parents=True,exist_ok=False)
 compiler=create_compiler('bilgewater');payload=load(HERE/'town-compiler-approved-v3/payload-and-compiler.json')
 index=load(HERE/'states-hidden-support-v3.json');approval=load(HERE/'approved-selection-source-v1.json');selection=load(HERE/'hidden-support-selection-v3.json')
 checks=[]
 def check(name,condition,detail=None):
  checks.append({'name':name,'passed':bool(condition),'detail':detail})
  if not condition:raise ValueError('Source verification failed: '+name)
 for key,row in index['states'].items():
  for role in ['frame','area','border','campaign','construction']:
   check('selected-'+key+'-'+role,sha(PROJECT/row[role])==row[role+'_sha256'])
 check('exact35',len(index['states'])==35)
 check('16ordinary-plus-coast-Grail',len({v['site'] for v in index['states'].values()})==18)
 old=load(HERE.parent/'derived-v2/states.json')
 check('35released-frame-dictionaries-preserved',old['states']==index['states'])
 budget=Image.open(HERE/'approved-full-opaque-budget.png').convert('L')
 baseline=rgba(PROJECT/old['background']);bg=rgba(PROJECT/index['background'])
 approved=rgba(PROJECT/approval['approved_full']['path'])
 check('background-pin',sha(PROJECT/index['background'])==index['background_sha256'])
 changed=rgbdiff(baseline,bg)
 check('no-recovered-background-pixel-outside-approved-opaque-budget',not ImageChops.multiply(changed,ImageChops.invert(budget)).getbbox())
 current=baseline.convert('RGB')
 metadata={}
 for site,row in selection['support_recoveries'].items():
  for role in ['genuine_master','native_crop','prompt','actual_selected_mask']:
   check('hidden-'+site+'-'+role+'-pin',sha(PROJECT/row[role]['path'])==row[role]['sha256'])
  master=PROJECT/row['genuine_master']['path'];metadata[site]=dict(Image.open(master).info)
  check('genuine-'+site+'-no-embedded-text-metadata',not metadata[site])
  box=row['native_context'];size=(box[2]-box[0],box[3]-box[1])
  native=ImageOps.fit(Image.open(master).convert('RGB'),size,method=Image.Resampling.LANCZOS)
  check('hidden-'+site+'-native-fit-reproduces',native.tobytes()==Image.open(PROJECT/row['native_crop']['path']).convert('RGB').tobytes())
  proposal=baseline.convert('RGB');delta=row['whole_painted_crop_registration'];proposal.paste(native,(box[0]+delta[0],box[1]+delta[1]))
  region=Image.new('L',(800,374));ImageDraw.Draw(region).polygon([tuple(p) for p in row['planned_support_polygon']],fill=255)
  mask=ImageChops.multiply(region,budget)
  check('hidden-'+site+'-mask-exact-budget-intersection',mask.tobytes()==Image.open(PROJECT/row['actual_selected_mask']['path']).convert('L').tobytes())
  current=Image.composite(proposal,current,mask)
 check('new-hidden-background-replayed-exactly',current.tobytes()==bg.convert('RGB').tobytes())
 scene=bg.copy()
 for key in index['full_scene_states']:scene.alpha_composite(rgba(PROJECT/index['states'][key]['frame']))
 check('approved-full-pixels-exact',not rgbdiff(scene,approved).getbbox())
 stream=io.BytesIO();scene.convert('RGB').save(stream,format='PNG')
 check('approved-full-file-encoding-exact',hashlib.sha256(stream.getvalue()).hexdigest()==approval['approved_full']['sha256'])
 outputpins={r['path']:r['sha256'] for r in payload['outputs']};replayed={}
 for row in payload['recipes']:
  recipe=PROJECT/row['candidate'];check('actual-recipe-pin-'+recipe.name,sha(recipe)==row['sha256'])
  data,receipt=compiler.plan(PROJECT,recipe)
  for name,value in data.items():
   check('actual-compiler-replay-'+name,hashlib.sha256(value).hexdigest()==outputpins[name])
   observed=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/town-compiler-approved-v3/compiled'/name
   check('materialized-output-'+name,observed.read_bytes()==value)
   replayed[name]=value
 check('exact235outputs',len(replayed)==235 and set(replayed)==set(outputpins))
 # These are source/compiler/pixel negative controls. They are explicitly not
 # the separately required physical source-displacement controls.
 negatives=[]
 visible=ImageChops.invert(budget);point=next((x,y) for y in range(374) for x in range(800) if visible.getpixel((x,y)))
 corrupted=bg.copy();pixel=list(corrupted.getpixel(point));pixel[0]=(pixel[0]+30)%256;corrupted.putpixel(point,tuple(pixel))
 damaged=corrupted.copy()
 for key in index['full_scene_states']:damaged.alpha_composite(rgba(PROJECT/index['states'][key]['frame']))
 negatives.append({'name':'visible-empty-terrain-pixel-change','actual_probe_point':list(point),'rejected_by_exact_approved_composition':bool(rgbdiff(damaged,approved).getbbox())})
 control=copy.deepcopy(load(HERE/'town-compiler-approved-v3/recipes/structures_castle.json.json'))
 control['groups'][0]['frames'][0]['source_sha256']='0'*64
 cp=REPORT/'negative-stale-source.json';cp.write_text(json.dumps(control,indent=2)+'\n')
 try:compiler.plan(PROJECT,cp)
 except Exception as exc:negatives.append({'name':'actual-compiler-stale-frame-source-pin','rejected':True,'exception_type':type(exc).__name__,'diagnostic':str(exc)})
 else:negatives.append({'name':'actual-compiler-stale-frame-source-pin','rejected':False})
 check('visible-pixel-negative-rejects',negatives[0]['rejected_by_exact_approved_composition'])
 check('actual-compiler-source-negative-rejects',negatives[1]['rejected'])
 result={'status':'authored configuration','scope':'Executed actual155-recipe compiler replay,235output byte equality,35cohort integrity,genuine-source masked recovery and exact approved full pixel preservation. No physical or native acceptance.',
  'helper':ref(Path(__file__).resolve()),'payload':ref(HERE/'town-compiler-approved-v3/payload-and-compiler.json'),
  'source_closure':ref(HERE/'hidden-support-source-closure-v2.json'),'approved_full_sha256':approval['approved_full']['sha256'],
  'checks_executed':len(checks),'checks_passed':sum(x['passed'] for x in checks),'checks':checks,'negative_controls':negatives,
  'genuine_master_png_metadata':metadata,'public_physical_consumer_passed':False,'physical_displacement_negatives_executed':False,'native_verified':False,'release_accepted':False}
 (REPORT/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'checks':len(checks),'passed':sum(x['passed'] for x in checks),'source_negative_controls':len(negatives),'report':str(REPORT/'result.json')}))

if __name__=='__main__':main()
