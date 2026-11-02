"""Seal actual CLI writer results; leaves prior source proposal reproducible."""
from pathlib import Path
import copy,hashlib,json,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[5];WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/complete-town-20261027-v2/production-adapter-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def main():
    proof=REPORT/'actual-cli-001';project=proof/'workspace/runeterra-freljord'
    execution=read(proof/'EXECUTION.json');assets=read(proof/'assets-validation.json');proposal=read(HERE/'proposal.json')
    assert execution['commands'][0]['exit_code']==0 and assets['ok'] and not assets['errors']
    assert assets['conversion']['compiled_count']==assets['conversion']['selected_count']==355
    current=read(PROJECT/'assets/manifest.json');actual=read(project/'assets/manifest.json')
    old={v['output_path']:v for v in current['assets']};new={v['output_path']:v for v in actual['assets']}
    changed=[name for name in old if old[name]!=new[name]]
    assert len(changed)==110 and all('/town/'in name for name in changed)
    assert {k:v for k,v in current.items()if k!='assets'}=={k:v for k,v in actual.items()if k!='assets'}
    manifest=HERE/'manifest.cli-verified.json';shutil.copyfile(project/'assets/manifest.json',manifest)
    actions=copy.deepcopy(proposal['actions']);actions[-1].update(source=manifest.relative_to(PROJECT).as_posix(),after_sha256=sha(manifest))
    outputs={};source_checks={}
    recipes=set(proposal['expected_actual_compiler_plans'])
    for row in assets['conversion']['results']:
        if row.get('recipe')not in recipes:continue
        for record in row['outputs']:
            name=record['output_path'];path=project/'assets/generated'/name
            assert sha(path)==record['sha256']
            outputs[name]={'sha256':sha(path),'dimensions':record.get('dimensions')}
            if path.suffix=='.png':
                source=project/record['source'];before=Image.open(source).convert('RGBA');after=Image.open(path).convert('RGBA')
                assert before.size==after.size and before.tobytes()==after.tobytes(),'Reviewed source pixel change: '+name
                outputs[name]['decoded_rgba_sha256']=hashlib.sha256(after.tobytes()).hexdigest()
                source_checks[name]={'source':record['source'],'source_sha256':sha(source),'decoded_equal':True}
    assert len(outputs)==182
    contract=read(HERE.parent/'candidate/layout-contract.json')
    for state,reference in contract['frames'].items():
        name='Content/Sprites/runeterra/freljord/town/structures/'+state+'-frames/g00-f000.png'
        assert outputs[name]['sha256']==reference['sha256'],'Actual body bytes changed: '+state
    write(REPORT/'town-output-pins-v1.json',outputs);write(REPORT/'reviewed-pixel-equality-v1.json',source_checks)
    code={name:sha(WORKSPACE/'scripts'/name)for name in ('runeterra.py','faction_pipeline.py','faction_production.py','faction_art_compile.py','faction_town_layout.py')}
    for name,digest in code.items():assert sha(proof/'workspace/scripts'/name)==digest,'CLI copy code differs'
    pins={a['source']:sha(PROJECT/a['source'])for a in actions if a.get('source')}
    pins.update({(HERE/'prepare.py').relative_to(PROJECT).as_posix():sha(HERE/'prepare.py'),(HERE/'reproduce.py').relative_to(PROJECT).as_posix():sha(HERE/'reproduce.py')})
    packet={'status':'authored configuration','canonical_applied_by_worker':False,'actions':actions,'source_pins':pins,'reviewed_physical_contract':proposal['physical_contract'],'body_source_pins':proposal['body_source_pins'],'actual_cli_execution':{'path':str((proof/'EXECUTION.json').relative_to(PROJECT)),'sha256':sha(proof/'EXECUTION.json')},'actual_cli_code_sha256':code,'actual_cli_assets':{'exit_code':0,'selected_recipes':355,'compiled_recipes':355,'required_fresh_outputs':355,'physical_files':assets['inventory']['physical_files'],'cold_town_cache':True},'town_output_pins':{'path':str((REPORT/'town-output-pins-v1.json').relative_to(PROJECT)),'sha256':sha(REPORT/'town-output-pins-v1.json'),'outputs':len(outputs)},'reviewed_decoded_pngs_unchanged':len(source_checks),'manifest_changed_entries':len(changed),'manifest_non_town_entries_unchanged':True,'known_source_validation_requirement':'Apply separately owned regional rules adapter; baseline actual CLI validation identified exactly36legacy depth errors and zero other errors.','applier_sha256':sha(HERE/'apply.py'),'native_verified':False,'release_accepted':False}
    write(HERE/'packet.json',packet)
    print(json.dumps({'packet_sha256':sha(HERE/'packet.json'),'guarded_actions':len(actions),'manifest_cli_sha256':sha(manifest),'native_body_pngs_byte_identical':len(contract['frames']),'decoded_pngs_identical':len(source_checks),'town_output_map_sha256':sha(REPORT/'town-output-pins-v1.json')},indent=2))
if __name__=='__main__':main()
