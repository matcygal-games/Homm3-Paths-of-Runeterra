"""Finish truthful scoped-repair metadata without rewriting selected-v1 history."""
from pathlib import Path
import copy,hashlib,json
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
OLD=PROJECT/'assets/source/town/approved-BC1-completion-20261030-v1/sealed-v5'
PREVIOUS=HERE/'selected-v1';OUT=HERE/'selected-v2'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(PROJECT).as_posix()
def write(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=raw:raise ValueError('Source already differs: '+str(p))
 if not p.exists():p.write_bytes(raw)
def save(p,value):write(p,(json.dumps(value,indent=2,sort_keys=True)+'\n').encode())
def main():
 design=read(PROJECT/'design/town-visuals.json');selection=read(PREVIOUS/'selection.json')
 if design['selected_sources']['path']!=rel(PREVIOUS/'selection.json'):raise ValueError('Selection moved concurrently')
 files={PROJECT/p for p in selection['files']};files.add(Path(__file__))
 for p in PREVIOUS.rglob('*'):
  if not p.is_file() or p.name=='selection.json' or p.is_relative_to(PREVIOUS/'recipes'):continue
  target=OUT/p.relative_to(PREVIOUS);write(target,p.read_bytes());files.add(target)
 baseline={key:{'path':rel(OLD/path),'sha256':sha(OLD/path)} for key,path in (
   ('checkpoint','complete-design/review-checkpoint.json'),('native','complete-design/native.png'),
   ('master','complete-design/master.png'),('extracted_provider','background/extracted-provider-master-v1.png'),
   ('generation','background/generation.json'))}
 checkpoint={'workflow':'bounded_local_repair','source_pixel_review_before_extraction':False,
  'reason':'This pass repairs one inherited site and bridgehead; it is not a newly generated complete-town-first extraction.',
  'complete_native_sha256':sha(OUT/'complete-design/native.png'),'inherited_whole_town':baseline,
  'local_revision':selection['local_revision'],'status':'authored configuration','native_acceptance':False}
 generation={'workflow':'bounded_local_repair','image_generation_used':True,'provider':'OpenAI built-in imagegen',
  'baseline_complete_design_sha256':baseline['native']['sha256'],
  'selected_complete_after_repair_sha256':sha(OUT/'complete-design/native.png'),
  'actual_requests':{'path':rel(HERE/'imagegen-exact-requests-v1.json'),'sha256':sha(HERE/'imagegen-exact-requests-v1.json')},
  'source_generation_ledger':{'path':rel(HERE/'generation-ledger-v3.json'),'sha256':sha(HERE/'generation-ledger-v3.json')},
  'scope':'Two painted edits; exact pixels preserved outside local background ROI and old/new gate silhouettes. No new whole-town approval claimed.'}
 save(OUT/'complete-design/review-checkpoint.json',checkpoint);save(OUT/'background/generation.json',generation)
 files.update([OUT/'complete-design/review-checkpoint.json',OUT/'background/generation.json'])
 selection.update(files={rel(p):sha(p) for p in sorted(files)},revision='BC1-library-bulwark-repair-20261030-v2')
 save(OUT/'selection.json',selection)
 design['selected_sources'].update(path=rel(OUT/'selection.json'),sha256=sha(OUT/'selection.json'))
 (PROJECT/'design/town-visuals.json').write_text(json.dumps(design,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'selected':design['selected_sources'],'files':len(files)}))
if __name__=='__main__':main()
