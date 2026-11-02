"""Bind and replay actual source-ownership bytes without a stage or game launch.

The existing never-executed fixture-v6 is explicitly reused as a mutable owned
working directory. Historical executed fixtures are not altered. This replay
is expected to expose strict physical HOLDs; no failing baseline is a control.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,importlib.util
from PIL import Image,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
WORKSPACE=PROJECT.parent
REPORTS=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1'
OUT=HERE/'ownership-replay-inputs-v1'
OUT.mkdir(exist_ok=False)
RUN=REPORTS/'ownership-replay-execution-v1'
RUN.mkdir(parents=True,exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
index_path=HERE/'ownership-separation-v3/states.json';index=read(index_path)
annotation_path=HERE/'ownership-contact-roles-v1/annotations.json';annotation=read(annotation_path)
annotation['terrain']={role:ref(HERE/'public-source-ground-v1'/(role+'.png'))for role in ('land','support','stairs','water')}
annotation['terrain']['paths']=ref(HERE/'public-routes-study-v1/main-component.png')
# Only actual remaining all-state source intersections are bound. Public-only
# overlaps retired by scenery separation are not invented back into the plan.
sil={}
for key,row in index['states'].items():
 im=Image.open(PROJECT/row['frame']).getchannel('A').point(lambda v:255 if v>=8 else 0)
 site=row['site'];sil[site]=ImageChops.lighter(sil.get(site,Image.new('L',(800,374))),im)
old={(r['behind'],r['front']):r for r in annotation['overlaps']}
depth={r['site']:r['z']for r in index['states'].values()}
overlaps=[];retired=[];new=[]
sites=list(sil)
for i,a in enumerate(sites):
 for b in sites[i+1:]:
  pair=(a,b)if depth[a]<depth[b]else(b,a)
  if ImageChops.multiply(sil[a],sil[b]).getbbox():
   r=old.get(pair,{'behind':pair[0],'front':pair[1],'reason':'Actual source-pinned oblique all-state architecture silhouette intersection; this bounded declaration does not waive actual feet, entrance, approach, ground support or native depth checks.'})
   overlaps.append(r)
   if pair not in old:new.append(list(pair))
for pair in old:
 if not ImageChops.multiply(sil[pair[0]],sil[pair[1]]).getbbox():retired.append(list(pair))
annotation['overlaps']=overlaps
annotation['foundation_occlusions']=[]
annotation['physical_replay_scope']='Strict unchanged public consumer with all35 actual compiled states and exact full BL2 pixels. Main source street component is intentionally not falsely connected over source cliffs or projected bodies. A failing positive baseline is never reported as a meaningful negative control.'
refs={}
def add(p):
 p=p.resolve()
 if p.is_relative_to(PROJECT.resolve()) and p.is_file():refs[p.relative_to(PROJECT.resolve()).as_posix()]=sha(p)
closure=read(HERE.parent/'hidden-support-source-closure-v4.json')
for r in closure['editable_sources']:add(PROJECT/r['path'])
for p in [index_path,annotation_path,HERE/'ownership-separation-v3/plan.json',HERE/'ownership-separation-v3/separation-receipt.json',HERE/'ownership-contact-roles-v1/role-receipt.json',HERE/'public-source-ground-v1/terrain-plan.json',HERE/'public-routes-study-v1/study.json',Path(__file__),HERE/'plan_source_separation_v3.py',HERE/'assemble_ownership_separation_v3.py',HERE/'trace_ownership_contact_roles_v1.py',HERE/'trace_public_source_ground_v1.py',HERE/'study_public_routes_v1.py',HERE/'compile_ownership_candidate_v1.py']:add(p)
for row in index['states'].values():
 for field,pin in row.items():
  if field.endswith('_sha256') and isinstance(row.get(field[:-7]),str):add(PROJECT/row[field[:-7]])
for folder in ('ownership-contact-roles-v1','ownership-separation-v3'):
 for p in (HERE/folder).rglob('*.png'):add(p)
annotation['selected_editable_sources']=[{'path':p,'sha256':pin}for p,pin in sorted(refs.items())]
write(OUT/'annotations.json',annotation)
write(OUT/'source-ownership-overlap-delta.json',{'retired_public_scenery_only_pairs':retired,'new_actual_pairs':new,'actual_pairs':[[r['behind'],r['front']]for r in overlaps],'no_access_or_footing_waiver':True})
commands=[]
def run(script,*args):
 cmd=[sys.executable,'-B',str(HERE/script),*map(str,args)];result=subprocess.run(cmd,cwd=WORKSPACE,capture_output=True,text=True)
 (RUN/(script+'.stdout.txt')).write_text(result.stdout);(RUN/(script+'.stderr.txt')).write_text(result.stderr)
 commands.append({'command':cmd,'exit_code':result.returncode});write(RUN/'commands.json',commands)
 if result.returncode:raise RuntimeError(result.stderr or result.stdout)
 print(result.stdout)
run('bind_contract.py','--index',ref(index_path)['path'],'--index-sha256',sha(index_path),'--annotations',OUT/'annotations.json','--out-name','contract-ownership-v1')
# Reuse the explicitly mutable, previously unexecuted working fixture only.
preparer=(HERE/'prepare_fixture.py').read_text()
preparer=preparer.replace("fixture=REPORT/args.out_name/'runeterra-bilgewater';fixture.mkdir(parents=True,exist_ok=False)","fixture=REPORT/'fixture-v6'/'runeterra-bilgewater';fixture.mkdir(parents=True,exist_ok=True)")
preparer=preparer.replace("'public_consumer_run':False", "'working_fixture_reused':True,'historical_executed_fixture_modified':False,'public_consumer_run':False")
helper=HERE/'reuse_working_fixture_v1.py'
if helper.exists():raise ValueError('Reproducible helper already exists')
helper.write_text(preparer)
payload=HERE/'compiler-ownership-v1/payload-and-compiler.json';receipts=HERE/'compiler-ownership-v1/compiler-receipts.json';contract=HERE/'contract-ownership-v1/layout-contract.json'
run(helper.name,'--payload',ref(payload)['path'],'--payload-sha256',sha(payload),'--compiler-receipts',ref(receipts)['path'],'--compiler-receipts-sha256',sha(receipts),'--compiled-root',REPORTS/'compiler-ownership-v1/compiled','--contract',ref(contract)['path'],'--contract-sha256',sha(contract),'--out-name','working-ownership-v1')
print(json.dumps({'contract':ref(contract),'working_fixture':str(REPORTS/'fixture-v6/runeterra-bilgewater'),'flat_authoring_refs':len(refs),'baseline_pass_claimed':False}))
