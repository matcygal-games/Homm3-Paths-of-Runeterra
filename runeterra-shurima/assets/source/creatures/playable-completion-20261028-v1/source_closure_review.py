"""Read the actual shared source predicate and bound this candidate's dependencies."""
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
import importlib.util,json
import assemble_packets as common
S=common.SOURCE;P=common.PROJECT;R=common.REPORT/'heraldry-v1'
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def main():
 guard=module(P/'scripts/source_export_guard.py','candidate_source_guard');consumer=guard.api(P.parent);pipeline=SimpleNamespace(root=P,mod_id='runeterra-shurima',faction='shurima')
 paths=set();recipes=sorted((S/'recipe-payload-heraldry-v1').rglob('*.json'));metadata=[]
 for recipe in recipes:
  paths.add(common.rel(recipe));value=json.loads(recipe.read_text());metadata.extend({'file':common.rel(recipe),'finding':row} for row in guard.fields(value))
  def walk(v):
   if isinstance(v,dict):
    for x in v.values():walk(x)
   elif isinstance(v,list):
    for x in v:walk(x)
   elif isinstance(v,str) and v.startswith('assets/source/'):paths.add(v)
  walk(value)
 rows=[];errors=[];png_count=0;native_exception=[]
 for name in sorted(paths):
  path=P/name;allowed=consumer.source_payload_allowed(pipeline,name);exact_native=not allowed and consumer._source_payload_allowed(pipeline,name,selected_native=True)
  if not path.is_file():errors.append(name+': missing dependency');continue
  guard.direct(path,P.parent)
  row={'path':name,'sha256':common.sha(path),'actual_shared_source_predicate_allowed':allowed,'exact_own_native_exception_required_after_canonical_selection':exact_native}
  if not allowed and not exact_native:errors.append(name+': actual collector predicate excludes dependency')
  if exact_native:native_exception.append(name)
  if path.suffix=='.json':metadata.extend({'file':name,'finding':finding} for finding in guard.fields(json.loads(path.read_text(encoding='utf-8-sig'))))
  if path.suffix=='.png':
   with Image.open(path) as im:
    png_count+=1;row['embedded_metadata_keys']=sorted(im.info)
    for key,value in im.info.items():metadata.extend({'file':name,'metadata_key':key,'finding':finding} for finding in guard.fields(value))
  reason=guard.three_d_reason(path,name)
  if reason:errors.append(name+': '+reason)
  rows.append(row)
 result={'status':'authored configuration','recipes':len(recipes),'candidate_dependency_files':len(rows),'png_metadata_inspected':png_count,'errors':errors,'metadata_findings':metadata,'dependencies':rows,'actual_shared_collector_helper':{'workspace_path':'scripts/faction_production.py','sha256':common.sha(P.parent/'scripts/faction_production.py')},'actual_regional_guard':common.descriptor(P/'scripts/source_export_guard.py'),'exact_native_vN_exception_dependencies':native_exception,'whole_canonical_source_archive_executed':False,'scope':'Actual candidate dependency pins, direct regular files, real shared payload predicate, exact own-native admission class, JSON/PNG metadata and obvious3D header refusal. Coordinator must still execute the complete current source collector after guarded canonical integration.','native_execution':False,'release_accepted':False}
 common.put(R/'source-closure-review-v1.json',result)
 print(json.dumps({'recipes':len(recipes),'dependencies':len(rows),'png_metadata_inspected':png_count,'errors':errors,'metadata_findings':metadata,'exact_native_exception_dependencies':len(native_exception)}))
 if errors or metadata:raise SystemExit(2)
if __name__=='__main__':main()
