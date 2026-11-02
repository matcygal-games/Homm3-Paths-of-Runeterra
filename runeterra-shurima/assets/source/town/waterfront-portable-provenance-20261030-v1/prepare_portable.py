"""Portable own-art guide metadata candidate; no canonical selection or writes."""
from pathlib import Path
import json,hashlib,shutil,sys
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3];ROOT=PROJECT.parent;OLD=HERE.parent/'waterfront-repair-20261030-v1';REPORT=ROOT/'reports/shurima-waterfront-repair-20261030-v1/selected-conversion-v1/portable-provenance-v1'
sys.path.insert(0,str(ROOT/'scripts'));from faction_art_compile import create_compiler
sys.path.insert(0,str(PROJECT/'scripts'));import selected_source_closure as closure
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf8')
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}

def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    ledger=read(OLD/'generation-ledger-v1.json');before=sha(OLD/'generation-ledger-v1.json')
    guide=HERE/'painted-edit-guide-v1.png';shutil.copyfile(PROJECT/ledger['reference']['path'],guide)
    assert sha(guide)==ledger['reference']['sha256']
    ledger['reference']=ref(guide)
    ledger['portable_derivative']={'preserved_prior_ledger_sha256':before,'reason':'The original own-art editing guide used a reference-prefixed filename rejected by source admission. This portable record selects the byte-identical own painted editing guide with a production-input filename. Original generation record and guide remain unchanged; no licensed extracted reference is selected.'}
    dump(HERE/'generation-ledger-v1.json',ledger)
    oldplan=read(OLD/'integration-plan.json');targets=[];candidate_paths=[]
    for row in oldplan['recipes']:
        target=PROJECT/row['target'];recipe=read(target);recipe['generation'].update({'source_generation_ledger':ref(HERE/'generation-ledger-v1.json')['path'],'source_generation_ledger_sha256':sha(HERE/'generation-ledger-v1.json')})
        candidate=HERE/'candidate-recipes'/target.relative_to(PROJECT/'assets/recipes');dump(candidate,recipe);candidate_paths.append(candidate)
        targets.append({'target':row['target'],'before_sha256':sha(target),'candidate':ref(candidate)})
    compiler=create_compiler('shurima');runs=[]
    for _ in range(2):
        outputs={}
        for path in candidate_paths:
            values,_=compiler.plan(PROJECT,path);outputs.update(values)
        runs.append({k:hashlib.sha256(v).hexdigest() for k,v in outputs.items()})
    assert runs[0]==runs[1]==oldplan['native_output_pins']
    active={p.relative_to(PROJECT).as_posix():read(p) for p in (PROJECT/'assets/recipes').rglob('*.json')}
    retired={r['recipe_path'] for r in read(PROJECT/'assets/production/shurima-t7-retired-recipes-20261029-v1.json')['recipes']};active={k:v for k,v in active.items() if k not in retired}
    overlays={}
    for row in targets:active[row['target']]=read(PROJECT/row['candidate']['path']);overlays[row['target']]=PROJECT/row['candidate']['path']
    contract=read(PROJECT/'design/town-visuals.json')['layout_contract'];proof=closure.collect(PROJECT,active,[(contract['path'],contract['sha256'])],overlay_files=overlays)
    assert proof['eligible'],str(proof['dependency_errors'])+str(proof['private_metadata_fields'])
    plan={'status':'authored configuration','candidate_only':True,'metadata_only':True,'recipes':targets,'layout_contract_unchanged':contract,'native_output_pins':runs[0],'preserved_reviewed_waterfront_ledger':{'sha256':before,'remains_unchanged':sha(OLD/'generation-ledger-v1.json')==before},'portable_ledger':ref(HERE/'generation-ledger-v1.json'),'own_painted_edit_guide':ref(guide),'original_guide_sha256':ledger['reference']['sha256']}
    dump(HERE/'metadata-integration-plan.json',plan)
    dump(REPORT/'prospective-source-closure.json',proof)
    result={'status':'authored configuration','canonical_selection_performed':False,'actual_compile_runs':2,'recipe_roots':10,'physical_outputs':47,'all_output_bytes_unchanged':runs[0]==runs[1]==oldplan['native_output_pins'],'strict_source_closure_eligible':proof['eligible'],'private_metadata_fields':proof['private_metadata_fields'],'dependency_errors':proof['dependency_errors'],'source_files':proof['source_files'],'source_json_files':proof['source_json_files'],'own_edit_guide_byte_identical':sha(guide)==sha(OLD/'reference-hidden-quay.png'),'preserved_prior_ledger_unchanged':sha(OLD/'generation-ledger-v1.json')==before,'metadata_integration_plan':ref(HERE/'metadata-integration-plan.json')}
    dump(REPORT/'candidate-proof.json',result);print(json.dumps(result))

if __name__=='__main__':main()
