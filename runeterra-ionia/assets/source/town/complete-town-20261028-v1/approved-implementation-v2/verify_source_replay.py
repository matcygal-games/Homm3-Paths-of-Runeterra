"""Convert copied editable town inputs in a fresh isolated workspace, no stage."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys,argparse,re
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-ionia')
WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v2'
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_pipeline as fp
import faction_production as production
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',default='source-replay-v2');args=parser.parse_args()
 if not re.fullmatch(r'source-replay-v[1-9][0-9]*',args.label):raise ValueError('Safe unique replay label required')
 target=REPORT/args.label;target.mkdir(exist_ok=False);workspace=target/'workspace';workspace.mkdir();project=workspace/'runeterra-ionia';project.mkdir()
 fixture=HERE/'physical-baseline/fixture-final';collected=production._current_town_layout_source_entries(fp.Pipeline(fixture,'runeterra-ionia','ionia'),{})
 repaired={r['native']['path']for r in read(HERE/'painted-repairs-provenance.json')['records']}
 omitted=[];copied=[]
 for member,data in collected.items():
  local=member.removeprefix('runeterra-ionia/')
  if('/physical-baseline/'in member or'/prepared/'in member or local in repaired or local.endswith(('/frame-index.json','/hidden-bed-incorporation.json','/rear-underlap-incorporation.json','/art-source-inputs.json'))or local.endswith('-incorporation-mask.png')):
   omitted.append(member);continue
  out=workspace/member;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data);copied.append(member)
 def copy(source,destination):destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 copy(PROJECT/'content/factions.json',project/'content/factions.json')
 # Original recipe bytes are guard inputs, not converted/cached sprite inputs.
 for path in sorted((PROJECT/'assets/recipes/town').glob('*.json')):copy(path,project/'assets/recipes/town'/path.name)
 # The five retained map producers supply their genuine source/overlay bitmaps.
 map_inputs=set()
 def visit(v):
  if isinstance(v,dict):
   for k,x in v.items():
    if k in('source','overlay_source','painted_master')and isinstance(x,str)and x.startswith('assets/source/'):map_inputs.add(x)
    visit(x)
  elif isinstance(v,list):
   for x in v:visit(x)
 for path in sorted((PROJECT/'assets/recipes/town').glob('map_*.json.json')):visit(read(path))
 for name in map_inputs:copy(PROJECT/name,project/name)
 for name in ('faction_art_compile.py','faction_sdk_profile.py'):copy(WORKSPACE/'scripts'/name,workspace/'scripts'/name)
 library=WORKSPACE/'vcmi-develop/vcmi-develop/config/buildingsLibrary.json';library_sha=sha(library);copy(library,workspace/'vcmi-develop/vcmi-develop/config/buildingsLibrary.json')
 own=project/HERE.relative_to(PROJECT)
 if(own/'prepared').exists()or(project/'assets/generated').exists():raise ValueError('Replay must start without prepared or generated town products')
 commands=[]
 for script in ('convert_repairs.py','assemble.py','compile_candidates.py'):
  result=subprocess.run([sys.executable,'-B',str(own/script)],cwd=workspace,capture_output=True,text=True);commands.append({'script':script,'exit_code':result.returncode,'stdout':result.stdout.strip(),'stderr':result.stderr.strip()})
  if result.returncode:raise ValueError('Actual copied-source replay failed: '+script+' '+result.stderr)
 expected=read(REPORT/'compiler-receipt.json')['outputs'];actual=read(project/'build/reports/complete-town-20261028-v1/approved-implementation-v2/compiler-receipt.json')['outputs']
 native_expected={p.relative_to(HERE/'prepared').as_posix():sha(p)for p in(HERE/'prepared').rglob('*.png')};native_actual={p.relative_to(own/'prepared').as_posix():sha(p)for p in(own/'prepared').rglob('*.png')}
 receipt={'status':'authored configuration','scope':'Actual town-only source conversion replay in a fresh copied workspace. This is not a full-mod package, game installation or native execution.','actual_collector_member_count':len(collected),'copied_raw_members':copied,'intentionally_omitted_derived_members':omitted,'started_without_prepared_or_generated_products':True,'genuine_map_input_count':len(map_inputs),'public_native_ID_library_copied_sha256':library_sha,'public_native_ID_original_unchanged':sha(library)==library_sha,'commands':commands,'all_prepared_PNGs_reproduced_exactly':native_expected==native_actual,'prepared_PNG_count':len(native_actual),'all_compiled_output_hashes_reproduced_exactly':expected==actual,'compiled_output_count':len(actual),'approved_full_PNG_sha256':sha(project/'build/reports/complete-town-20261028-v1/approved-implementation-v2/compiled-approved-full.png'),'canonical_or_stage_writes':False,'native_execution':False,'release_accepted':False}
 (target/'receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:receipt[k]for k in('all_prepared_PNGs_reproduced_exactly','prepared_PNG_count','all_compiled_output_hashes_reproduced_exactly','compiled_output_count','approved_full_PNG_sha256')}));return 0 if native_expected==native_actual and expected==actual else 2
if __name__=='__main__':raise SystemExit(main())
