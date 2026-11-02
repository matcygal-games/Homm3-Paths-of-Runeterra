"""Strict T2/T3 source-only battle delivery. No manifest, conversion or staging.

Only complete genuine painted cohorts with independently hash-bound native pixel
findings can replace the four missing battle recipes. All acceptance stays false.
"""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, shutil
from PIL import Image

PROJECT=Path(__file__).resolve().parents[1]
UNITS=('chemRavager','mutantBerserker','chemtechConstruct','reinforcedConstruct')
BASE={0:6,1:4,2:1,3:4,4:4,5:6,7:4,8:4,11:6,12:6,13:6,22:1}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def safe(value):
 if not isinstance(value,str) or '\\' in value or ':' in value:raise ValueError('Only project-relative POSIX evidence paths allowed')
 parts=PurePosixPath(value).parts
 if not parts or PurePosixPath(value).is_absolute() or any(p in ('.','..') or p.endswith((' ','.')) for p in parts):raise ValueError('Unsafe evidence path')
 path=(PROJECT/Path(*parts)).resolve()
 if not path.is_relative_to(PROJECT):raise ValueError('Evidence escapes project')
 return path
def pinned(record):
 if not isinstance(record,dict) or not {'path','sha256'}<=set(record):raise ValueError('Missing evidence pin')
 path=safe(record['path']);expected=record['sha256']
 if not isinstance(expected,str) or len(expected)!=64 or sha(path)!=expected:raise ValueError('Changed pinned evidence: '+str(record['path']))
 return path
def pin(path):return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}
def protected_aux():
 return {f'{unit}-{kind}.json':sha(PROJECT/f'assets/recipes/creatures/{unit}-{kind}.json')
         for unit in UNITS for kind in ('map','large','small','attackLeft','attackRight')}

def validate(unit,version,review_path):
 if unit not in UNITS or version not in (5,6):raise ValueError('Unowned unit or unsupported version')
 folder=f'assets/source/creatures/{unit}/painted-battle-v{version}'
 cohort_path=safe(folder+f'/battle-cohort-v{version}.json')
 c=json.loads(cohort_path.read_text(encoding='utf-8'))
 expected_counts={**BASE,**({14:8,15:8,16:8} if unit in UNITS[2:] else {})}
 if c.get('unit')!=unit or c.get('canvas')!=[450,400] or c.get('pivot')!=[197,266] or c.get('art_accepted') is not False or c.get('visual_approval_granted') is not False:raise ValueError('Exact native source-only contract required')
 if set(c.get('groups',{}))!={str(g) for g in expected_counts}:raise ValueError('Missing or extra required groups')
 frames=[]
 for g,fs in c['groups'].items():
  if len(fs)!=expected_counts[int(g)]:raise ValueError('Wrong frame count for group '+g)
  for i,f in enumerate(fs):
   if not f['source'].startswith(folder+'/native-candidate/'):raise ValueError('Cross-unit or non-native frame source')
   path=pinned({'path':f['source'],'sha256':f['sha256']})
   with Image.open(path) as im:
    if im.mode!='RGBA' or im.size!=(450,400):raise ValueError('Wrong native canvas or alpha mode')
    alpha=im.getchannel('A');bounds=alpha.point(lambda p:255 if p>=128 else 0).getbbox()
    if not bounds or bounds[0]<=0 or bounds[1]<=0 or bounds[2]>=450 or bounds[3]>=400:raise ValueError('Empty or clipped opaque native body')
    if any(alpha.getpixel(p) for p in ((0,0),(449,0),(0,399),(449,399))):raise ValueError('Nontransparent native canvas corners')
   frames.append({'group':int(g),'frame':i,'source':f['source'],'sha256':f['sha256']})
 if len({f['sha256'] for f in frames})!=len(frames)-1 or c['groups']['5'][-1]['sha256']!=c['groups']['22'][0]['sha256']:raise ValueError('Repeated filler or wrong intentional corpse')
 pinned(c['contact_sheet']);pinned(c['producer']);pinned(c['atlas_selector'])
 for master in c['masters']:
  p=pinned(master['master']);meta_path=p.with_name('generation.json')
  meta=json.loads(meta_path.read_text(encoding='utf-8'))
  if meta.get('provider')!='OpenAI built-in image_gen' or meta.get('image_generation_used') is not True or meta.get('master')!=master['master'] or not isinstance(meta.get('prompt'),str) or not meta['prompt'].strip():raise ValueError('Missing genuine prompt/provider/master binding')
  for source in meta.get('inputs',[]):
   path=Path(source['path'])
   if not path.is_absolute() or sha(path)!=source['sha256']:raise ValueError('Changed generation input')
 if review_path is None:raise ValueError('Explicit independent review required')
 rp=Path(review_path)
 if not rp.is_absolute():rp=safe(rp.as_posix())
 rp=rp.resolve()
 if not rp.is_relative_to(PROJECT):raise ValueError('Review must live inside project')
 r=json.loads(rp.read_text(encoding='utf-8'))
 if r.get('unit')!=unit or r.get('cohort')!=pin(cohort_path) or r.get('comparison')!=c['contact_sheet'] or r.get('frames')!=frames:raise ValueError('Independent review must bind this exact complete cohort, board and ordered frames')
 reviewer=r.get('reviewer')
 if not isinstance(reviewer,str) or not reviewer.strip() or 'zaun_creatures_a' in reviewer:raise ValueError('Named independent reviewer required')
 if r.get('source_ready') is not True or r.get('visual_approval_granted') is not False or r.get('final_art_acceptance') is not False:raise ValueError('Source-only readiness without final approval required')
 findings=r.get('findings')
 if not isinstance(findings,list) or not findings or any(not ((isinstance(f,str) and f.strip()) or (isinstance(f,dict) and isinstance(f.get('detail'),str) and f['detail'].strip() and isinstance(f.get('severity'),str) and f['severity'].strip())) for f in findings):raise ValueError('Actual concrete independent pixel findings required')
 return c,r,rp,frames

def deliver(unit,version,review_path):
 before=protected_aux();c,r,rp,frames=validate(unit,version,review_path)
 path=PROJECT/f'assets/recipes/creatures/{unit}-battle.json'
 recipe=json.loads(path.read_text(encoding='utf-8'))
 if recipe.get('production_status')=='delivered':raise ValueError('Refuse implicit replacement of delivered battle')
 if {str(g['group']) for g in recipe['groups']}!=set(c['groups']):raise ValueError('Canonical group contract changed')
 for g in recipe['groups']:
  real=c['groups'][str(g['group'])]
  if len(g['frames'])!=len(real):raise ValueError('Canonical frame count changed')
  g['frames']=[{'source':f['source'],'sha256':f['sha256'],'source_sha256':f['sha256']}for f in real]
 review_dir=PROJECT/f'assets/reviews/creatures/{unit}-battle-source-v{version}-20261021'
 stable_review=review_dir/'independent-source-review.json';review_dir.mkdir(parents=True,exist_ok=True)
 if stable_review.exists() and sha(stable_review)!=sha(rp):raise ValueError('Preserve prior independent review')
 shutil.copy2(rp,stable_review)
 historical=review_dir/'blocked-recipe-before-selection.json'
 if historical.exists() and sha(historical)!=sha(path):raise ValueError('Historical recipe already differs')
 shutil.copy2(path,historical)
 cohort_path=PROJECT/f'assets/source/creatures/{unit}/painted-battle-v{version}/battle-cohort-v{version}.json'
 record={**pin(stable_review),'source_ready':True,'reviewer':r['reviewer'],'visual_approval_granted':False,'final_art_acceptance':False}
 masters=[]
 for m in c['masters']:
  p=safe(m['master']['path']);metadata=p.with_name('generation.json')
  masters.append({**m['master'],'generation':pin(metadata),'camera':{key:m[key]for key in ('scale','reference_anchor','fixed_stride','reference_basis','native_registration_target','animation_pivot')}})
 first=masters[0]
 recipe.update({'source':cohort_path.relative_to(PROJECT).as_posix(),'source_sha256':sha(cohort_path),
  'production_status':'delivered','status':'built-unreviewed','visual_approval_granted':False,'source_review':record,
  'credits':{'author':'OpenAI built-in image_gen; project-directed genuine paintings and technical extraction','license':None,'redistribution':'unresolved; release prohibited'},
  'generation':{'provider':'OpenAI built-in image_gen','model':None,'model_note':'Not exposed by the built-in tool','image_generation_used':True,'painted_master':first['path'],'painted_master_sha256':first['sha256'],'painted_masters':masters,'route':'Genuine independently painted action cohorts; alpha-preserving technical extraction and one camera per atlas only','prompt':'Exact prompts and real tool hints in each pinned generation.json'},
  'delivery':{'status':'authored configuration; built-unreviewed source delivery only','cohort':cohort_path.relative_to(PROJECT).as_posix(),'cohort_sha256':sha(cohort_path),'source_review':record,'visual_approval_granted':False,'sources':[{'path':f['source'],'sha256':f['sha256']}for f in frames]}})
 if protected_aux()!=before:raise ValueError('Frozen auxiliary recipes changed during preparation')
 write(path,recipe)
 if protected_aux()!=before:raise ValueError('Frozen auxiliary recipes changed during delivery')
 result={'unit':unit,'status':'authored configuration; built-unreviewed','frame_count':len(frames),'recipe':pin(path),'cohort':pin(cohort_path),'independent_source_review':pin(stable_review),'visual_approval_granted':False,'final_art_acceptance':False,'protected_twenty_auxiliary_recipes_unchanged':True}
 write(review_dir/'delivery.json',result)
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('unit',choices=UNITS);p.add_argument('--version',type=int,choices=(5,6),required=True);p.add_argument('--source-review',type=Path,required=True);p.add_argument('--deliver',action='store_true');a=p.parse_args()
 if a.deliver:print(json.dumps(deliver(a.unit,a.version,a.source_review),indent=2))
 else:
  c,r,rp,frames=validate(a.unit,a.version,a.source_review);print(json.dumps({'unit':a.unit,'valid_independent_source_review':True,'frames':len(frames),'recipes_changed':False}))
