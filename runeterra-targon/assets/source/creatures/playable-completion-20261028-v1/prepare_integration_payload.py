"""Create guarded per-entry integration payloads; never modify current selections."""
from __future__ import annotations
import copy,hashlib,json,shutil,sys
from pathlib import Path
from assemble_humanoids import HERE,PROJECT,ROOT,REPORT,dump,sha

def encoded(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def value_sha(value):return hashlib.sha256(encoded(value)).hexdigest()

def main():
    sys.path.insert(0,str(ROOT/'scripts'))
    from faction_art_compile import create_compiler
    compiler=create_compiler('targon')
    current=json.loads((PROJECT/'assets/manifest.json').read_text());by_output={a['output_path']:a for a in current['assets']}
    patches=[]
    for kind in ['humanoids','animals']:patches+=json.loads((HERE/('proposed-manifest-'+kind+'.json')).read_text())['assets']
    # Tower icons are creature appearance: the exact base Archer head/upperbody
    # painting on its own regional backdrop, not any old tower/model render.
    tower_checks=[]
    for name,size,source_name in [('towerLarge',[58,64],'large'),('towerSmall',[32,32],'small')]:
        original=HERE/'proposed-recipes/mountainArcher'/(source_name+'.json')
        recipe=json.loads(original.read_text());recipe.update({'configured_shooter':'mountainArcher','role':'siege-tower-portrait',
                    'output_path':'Content/Sprites/runeterra/targon/siege/'+name+'.png','canvas':size})
        path=HERE/'proposed-recipes/siegeTower'/(name+'.json');dump(path,recipe)
        a,r=compiler.plan(PROJECT,path);b,_=compiler.plan(PROJECT,path);assert a==b
        for output,raw in a.items():
            target=REPORT/'compiled'/output;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        patches.append({'output_path':recipe['output_path'],'dimensions':size,'sha256':hashlib.sha256(a[recipe['output_path']]).hexdigest(),
                    'source':{'editable_path':'assets/generated/'+recipe['output_path'],'recipe_path':path.relative_to(PROJECT).as_posix(),
                              'recipe':path.relative_to(PROJECT).as_posix(),'recipe_present':True,'recipe_sha256':sha(path)},
                    'dependencies':[path.relative_to(PROJECT).as_posix()],'status':'built-unreviewed','native_visual_review':'pending'})
        tower_checks.append({'output_path':recipe['output_path'],'dimensions':size,'double_replay_identical':True,
                              'source_identity':'mountainArcher','source_sha256':recipe['source_sha256']})
    replacements=[];history=HERE/'integration-history';history.mkdir(exist_ok=True)
    for patch in patches:
        output=patch['output_path'];old=by_output[output];path=HERE/patch['source']['recipe_path'].split('playable-completion-20261028-v1/',1)[1]
        raw=path.read_bytes();recipe=json.loads(raw)
        canonical=old['source']['recipe_path']
        payload=HERE/'canonical-recipe-payloads'/canonical;payload.parent.mkdir(parents=True,exist_ok=True);payload.write_bytes(raw)
        snapshot=history/'canonical-recipes'/canonical;snapshot.parent.mkdir(parents=True,exist_ok=True);snapshot.write_bytes((PROJECT/canonical).read_bytes())
        new=copy.deepcopy(old);new.update({k:v for k,v in patch.items() if k not in ['role','unit']})
        new['role']=old['role']
        new['source'].update({'recipe_path':canonical,'recipe':canonical,'recipe_sha256':hashlib.sha256(raw).hexdigest()})
        new['dependencies']=[canonical]
        for key in ['identity_review','user_rejected','visual_approval_granted']:new.pop(key,None)
        if recipe['recipe_type']=='vcmi_animation':new['required_groups']={str(g['group']):len(g['frames']) for g in recipe['groups']}
        replacements.append({'id':old['id'],'output_path':output,'expected_entry_sha256':value_sha(old),
                 'expected_output_sha256':old['sha256'],'expected_canonical_recipe_sha256':sha(PROJECT/canonical),
                 'canonical_recipe_path':canonical,'recipe_payload':payload.relative_to(PROJECT).as_posix(),
                 'replacement_entry':new})
    selected_ids={r['id'] for r in replacements}
    unaffected={a['id']:value_sha(a) for a in current['assets'] if a['id'] not in selected_ids}
    dump(HERE/'integration-manifest-entry-patch.json',{'status':'authored configuration','schema':1,
          'operation':'Guard each selected entry, replace only these88 IDs; merge into then-current manifest, never overwrite complete manifest',
          'replacements':replacements,'unaffected_entry_sha256':unaffected,'canonical_manifest_modified':False})
    # Guarded current-production ledger replacement; original files remain
    # untouched and the complete old records are preserved as explicit history.
    units=json.loads((PROJECT/'content/creatures.json').read_text());production=[];selections={}
    for kind,ids,producer_name in [('animal',[u for u in units if (HERE/'animals'/u).is_dir()],'assemble_animals.py'),
                                  ('humanoid',[u for u in units if (HERE/'humanoids'/u).is_dir()],'assemble_humanoids.py')]:
        target='assets/production/'+kind+'-art.json';oldpath=PROJECT/target;snapshot=history/(kind+'-art.before.json');shutil.copy2(oldpath,snapshot)
        records={}
        for unit in ids:
            unitroot=HERE/('animals' if kind=='animal' else 'humanoids')/unit;ledger=unitroot/'source-generation-ledger.json'
            record={'source_generation_ledger':ledger.relative_to(PROJECT).as_posix(),'source_generation_ledger_sha256':sha(ledger),
                    'assembly':(unitroot/'assembly.json').relative_to(PROJECT).as_posix(),'assembly_sha256':sha(unitroot/'assembly.json'),
                    'canonical_recipes':{r['canonical_recipe_path']:r['replacement_entry']['source']['recipe_sha256'] for r in replacements if r['replacement_entry'].get('unit')==unit or r['output_path'].endswith('/projectiles/'+unit+'.json') or (unit=='mountainArcher' and '/siege/tower' in r['output_path'])}}
            records[unit]=record;selections[unit]=record
        replacement={'status':'authored configuration','workflow':'image-based-painted-2d','required_for_production':True,
                 'producer':(HERE/producer_name).relative_to(PROJECT).as_posix(),'producer_sha256':sha(HERE/producer_name),
                 'units':records,'selected_recipe_binding':'Canonical recipe payloads in this guarded integration packet; original genuinely painted masters/frame closure pinned per unit',
                 'historical_provenance':{'required_for_production':False,'source':snapshot.relative_to(PROJECT).as_posix(),'sha256':sha(snapshot),
                      'reason':'Old creature geometry selection is retired; preserved raw records are history, never executed or required by current painted production'},
                 'art_acceptance':False,'native_execution':False}
        payload=HERE/'production-ledger-payloads'/Path(target).name;dump(payload,replacement)
        production.append({'target':target,'expected_sha256':sha(oldpath),'replacement_payload':payload.relative_to(PROJECT).as_posix(),'replacement_sha256':sha(payload),
                           'preserved_history':snapshot.relative_to(PROJECT).as_posix(),'preserved_history_sha256':sha(snapshot)})
    old_export=PROJECT/'assets/production/source-export.json';old=json.loads(old_export.read_text());snapshot=history/'source-export.before.json';shutil.copy2(old_export,snapshot)
    def creature_scene(name):return name.startswith(('assets/source/animals/','assets/source/creatures/'))
    retired={k:v for k,v in old['editable_scenes'].items() if creature_scene(k)}
    retired_producers={k:v for k,v in old.get('scene_producers',{}).items() if k in retired}
    dump(HERE/'integration-production-ledger-patch.json',{'status':'authored configuration','schema':1,'ledger_replacements':production,
        'source_export_patch':{'target':'assets/production/source-export.json','operation':'Remove only guarded selected creature scene declarations/producers and set painted_creature_sources; preserve every town/siege/hero declaration',
             'remove_editable_scenes':retired,'remove_scene_producers':retired_producers,
             'set_painted_creature_sources':selections,'unaffected_editable_scenes':{k:v for k,v in old['editable_scenes'].items() if k not in retired},
             'preserved_history':snapshot.relative_to(PROJECT).as_posix(),'preserved_history_sha256':sha(snapshot)},
        'canonical_files_modified':False})
    # Dry-run guards prove preservation using the real current manifest bytes.
    merged=copy.deepcopy(current);lookup={r['id']:r for r in replacements}
    for i,entry in enumerate(merged['assets']):
        if entry['id'] in lookup:
            r=lookup[entry['id']];assert value_sha(entry)==r['expected_entry_sha256'];merged['assets'][i]=r['replacement_entry']
    assert {a['id']:value_sha(a) for a in merged['assets'] if a['id'] not in lookup}==unaffected
    new_export=copy.deepcopy(old)
    for k,v in retired.items():assert new_export['editable_scenes'].pop(k)==v
    for k,v in retired_producers.items():assert new_export['scene_producers'].pop(k)==v
    assert new_export['editable_scenes']=={k:v for k,v in old['editable_scenes'].items() if k not in retired}
    dump(REPORT/'guarded-integration-payload-verification.json',{'status':'authored configuration','ok':True,
       'manifest_replacements':len(replacements),'unchanged_entries':len(unaffected),'unaffected_entries_byte_identical':True,
       'retired_selected_creature_scenes':len(retired),'remaining_town_siege_scenes_unchanged':len(new_export['editable_scenes']),
       'tower_appearance':tower_checks,'canonical_files_modified':False,'native_execution':False})
    print(json.dumps({'manifest_replacements':len(replacements),'unaffected_entries':len(unaffected),'retired_creature_scenes':len(retired),'tower_appearances':tower_checks},indent=2))
if __name__=='__main__':main()
