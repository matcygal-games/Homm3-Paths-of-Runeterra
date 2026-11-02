"""Reproducible metadata closure and exact24-resource candidate packet.

No canonical/selected/generated/stage writes. No creative bitmap operations.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
from assemble import HERE,PROJECT,WORKSPACE,REPORT,sha,put,record,encoded
from verify import unit_test
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_art_compile,source_export_guard

VERSIONS={'cliffwing':4,'stormwing':3,'shoreLeviathan':1,'elderShoreLeviathan':1}

def strings(value,key):
    if isinstance(value,dict):
        for k,v in value.items():
            if k==key and isinstance(v,str):yield v
            yield from strings(v,key)
    elif isinstance(value,list):
        for v in value:yield from strings(v,key)

def main():
    compiler=faction_art_compile.create_compiler('bilgewater');products={};allrecipes=[];bindings={};sources=set();tests=[];replays=[]
    policy_spec=importlib.util.spec_from_file_location('_read_only_painted_recipe_gate',HERE/'painted_source_policy.py');policy=importlib.util.module_from_spec(policy_spec);policy_spec.loader.exec_module(policy)
    for unit,version in VERSIONS.items():
        src=HERE/f'proposed-recipes-v{version}'/unit;recipefiles=sorted(src.glob('*.json'))
        if len(recipefiles)!=6:raise ValueError('Finish actual six unit roles before packaging '+unit)
        input_recipes=[json.loads(p.read_text())for p in recipefiles];files={};origins=[]
        for recipe in input_recipes:
            for pin in recipe['generation']['production_inputs']:files[pin['path']]=pin['sha256']
            prior_ledger=recipe['generation']['provenance'];files[prior_ledger]=sha(PROJECT/prior_ledger)
            for name in strings(recipe,'source'):
                if name.startswith('assets/source/'):
                    p=PROJECT/name;files[name]=sha(p)
        for p in [Path(__file__),HERE/'assemble.py',HERE/'annotate_sources.py',HERE/'verify.py',HERE/'painted_source_policy.py']:files[p.relative_to(PROJECT).as_posix()]=sha(p)
        for name,pin in files.items():
            if name.endswith('-raw.png'):
                origins.append({'kind':'image-generation','path':name,'sha256':pin,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool'})
        ledger=HERE/unit/'selected-source-generation-v2.json'
        record(ledger,{'schema_version':1,'status':'authored configuration','unit':unit,'workflow':'image-based-painted-2d','derived_from_blender':False,'user_rejected':False,'assembly_operations':['fixed-canvas','root-placement','alpha-cleanup','frame-assembly','png-conversion'],'origins':sorted(origins,key=lambda x:x['path']),'files_sha256':dict(sorted(files.items())),'actual_assembly_config':(HERE/unit/f'assembly-config-v{version}.json').relative_to(PROJECT).as_posix(),'native_execution':False,'art_acceptance':False,'rights':'unresolved; release prohibited'})
        sources.update(PROJECT/n for n in files);sources.add(ledger);selected=[]
        for old in input_recipes:
            recipe=copy.deepcopy(old);g=recipe['generation'];g['workflow']='image-based-painted-2d';g['derived_from_blender']=False;g['source_generation_ledger']=ledger.relative_to(PROJECT).as_posix();g['source_generation_ledger_sha256']=sha(ledger)
            role=Path(recipe['output_path']).stem;target=HERE/'final-proposed-recipes-v2'/unit/(role+'.json');record(target,recipe)
            errors=policy.recipe_errors(PROJECT,recipe,set())
            if errors:raise ValueError('Actual painted source policy rejected '+unit+': '+'; '.join(errors))
            selected.append(target);sources.add(target);allrecipes.append(target)
        first=None;unitproducts=None
        for replay in (1,2):
            current={};receipt=[]
            for recipe in selected:
                outputs,r=compiler.plan(PROJECT,recipe);receipt.append(r)
                for name,data in outputs.items():
                    if name in current:raise ValueError('Duplicate produced resource '+name)
                    current[name]=data
            hashes={n:hashlib.sha256(b).hexdigest()for n,b in current.items()}
            if first is not None and hashes!=first:raise ValueError('Actual converter replay diverged')
            first=hashes;unitproducts=current
            replays.append({'unit':unit,'pass':replay,'physical_outputs':len(hashes),'files_sha256':hashes,'receipts':receipt})
        tests.append(unit_test(unit,version,unitproducts))
        for name,data in unitproducts.items():
            if name in products:raise ValueError('Cross-unit duplicate product '+name)
            products[name]=data;put(REPORT/'final-compiled'/name,data)
        bindings[unit]={'source_generation_ledger':ledger.relative_to(PROJECT).as_posix(),'source_generation_ledger_sha256':sha(ledger),'assembly_config':(HERE/unit/f'assembly-config-v{version}.json').relative_to(PROJECT).as_posix(),'proposed_recipes':{p.relative_to(PROJECT).as_posix():sha(p)for p in selected}}
    assert len(allrecipes)==24 and len(products)==324
    exported={PROJECT.name+'/'+p.relative_to(PROJECT).as_posix():p.read_bytes()for p in sorted(sources)}
    metadata=source_export_guard.check(PROJECT,files=exported);record(REPORT/'actual-source-export-metadata-admission.json',metadata)
    if not metadata['source_export_eligible']:raise ValueError('Actual privacy/PNG metadata guard rejected candidate')
    record(REPORT/'actual-consumer-and-mutation-tests.json',{'status':'authored configuration','ok':True,'unit_results':tests,'mutations_rejected':sum(len(r['mutations'])for r in tests),'native_crop_contract':__import__('verify').preview.native_crop_contract(WORKSPACE),'source_policy_consumer':'Unmodified read-only creature_art_policy.recipe_errors actual explicit closure checks','native_game_executed':False,'art_acceptance':False})
    record(REPORT/'actual-two-pass-conversion.json',{'status':'authored configuration','deterministic':True,'recipes':24,'actual_unique_physical_outputs':len(products),'passes':replays,'native_execution':False,'art_acceptance':False})
    record(REPORT/'actual-closed-output-inventory.json',{'status':'authored configuration','files':len(products),'bytes':sum(map(len,products.values())),'files_sha256':{n:hashlib.sha256(b).hexdigest()for n,b in sorted(products.items())},'cached_unselected_outputs_included':False,'native_execution':False})
    current=json.loads((PROJECT/'assets/manifest.json').read_text());changes=[]
    for p in allrecipes:
        recipe=json.loads(p.read_text());e=next(e for e in current['assets']if e['output_path']==recipe['output_path']);oldpath=e['source']['recipe']
        changes.append({'id':e['id'],'output_path':e['output_path'],'role':e['role'],'expected_entry_sha256':hashlib.sha256(encoded(e)).hexdigest(),'expected_current_recipe_path':oldpath,'expected_current_recipe_sha256':sha(PROJECT/oldpath),'proposed_recipe':p.relative_to(PROJECT).as_posix(),'proposed_recipe_sha256':sha(p),'compiled_sha256':hashlib.sha256(products[e['output_path']]).hexdigest(),'dimensions':recipe.get('canvas',recipe.get('size')),'required_groups':{str(g['group']):len(g['frames'])for g in recipe.get('groups',[])}})
    record(HERE/'integration-proposal-v1.json',{'status':'authored configuration','selected':False,'canonical_modified':False,'operation':'Main Bilgewater owner/root only: merge these24 guarded role proposals into then-current complete14-creature packet; never replace whole manifest.','changes':changes,'source_bindings':bindings,'unchanged_content_graphics_fields':True,'actual_battle_root':[218,266],'actual_map_root':[76,60],'actual_encounter_root':[44,60],'graphics_field_changes_required':False,'native_execution':False,'release_accepted':False})
    record(HERE/'selected-source-inventory-v1.json',{'status':'authored configuration','files':len(sources),'files_sha256':{p.relative_to(PROJECT).as_posix():sha(p)for p in sorted(sources)},'excluded_private_original_reference_pixels':True,'excluded_old_3d_sources':True,'excluded_unselected_bad_compact_candidates':True})
    delivery={'status':'authored configuration','units':list(VERSIONS),'selected_candidate_versions':VERSIONS,'logical_recipes':24,'actual_compiled_files':324,'candidate_source_root':HERE.relative_to(WORKSPACE).as_posix(),'compiled_root':(REPORT/'final-compiled').relative_to(WORKSPACE).as_posix(),'integration_proposal':(HERE/'integration-proposal-v1.json').relative_to(WORKSPACE).as_posix(),'integration_proposal_sha256':sha(HERE/'integration-proposal-v1.json'),'evidence_pins':{p.relative_to(WORKSPACE).as_posix():sha(p)for p in [REPORT/'actual-consumer-and-mutation-tests.json',REPORT/'actual-two-pass-conversion.json',REPORT/'actual-closed-output-inventory.json',REPORT/'actual-source-export-metadata-admission.json',HERE/'selected-source-inventory-v1.json']},'no_gameplay_town_hero_or_canonical_changes':True,'native_game_executed':False,'release_accepted':False,'limitations':['Native shadow/ground compositing, fast playback and battle transitions remain to be observed in a fresh coordinator-owned stage.','Correct region crest is physically painted; tiny native readability and independent art/upgrade acceptance remain pending.','Bird holding/fidget uses genuine folded-wing nearfrontal poses; leviathan holding uses genuine four-grounded-paw front poses with tail behind. Full broad locomotion/attacks keep original physical scale.','Rights and full release acceptance remain separate; this is a candidate production packet, not final Bilgewater review.']}
    record(REPORT/'DELIVERY.json',delivery)
    links=''.join(f'<li><a href="{u}/candidate-v{v}/index.html">{u} all native source actions and GIFs</a></li>'for u,v in VERSIONS.items())
    put(REPORT/'index.html',('<!doctype html><meta charset="utf-8"><title>Bilgewater flying and leviathan painted candidates</title><style>body{background:#272924;color:#eee;font:16px system-ui;max-width:1200px;margin:auto}a{color:#c9d9ec}</style><h1>Bilgewater — four painted creature candidates</h1><p>Authored configuration.24 proposed logical resources,324 exact compiled products. The locked BL2 town and all other creature/hero/gameplay sources remain untouched. Source/GIF evidence is not native game acceptance.</p><ul>'+links+'</ul><p><a href="DELIVERY.json">Pinned handoff</a> · <a href="actual-consumer-and-mutation-tests.json">Actual consumer and mutation tests</a> · <a href="actual-two-pass-conversion.json">Two-pass converter</a> · <a href="actual-source-export-metadata-admission.json">Source and PNG metadata admission</a></p>').encode())
    print(json.dumps(delivery,indent=2))

if __name__=='__main__':main()
