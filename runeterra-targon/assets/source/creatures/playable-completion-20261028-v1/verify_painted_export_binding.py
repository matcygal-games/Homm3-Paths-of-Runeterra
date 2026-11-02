"""Execute the proposed production/source-export boundary in a copied fixture."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,shutil,sys
from pathlib import Path
from assemble_humanoids import HERE,PROJECT,ROOT,REPORT,dump,sha

def main():
    workspace=REPORT/'portable-replay-v2';project=workspace/'runeterra-targon'
    if not project.is_dir():raise RuntimeError('Final copied-source replay must finish first')
    patch=json.loads((HERE/'integration-production-ledger-patch.json').read_text())
    for p in (HERE/'canonical-recipe-payloads').rglob('*.json'):
        target=project/p.relative_to(HERE/'canonical-recipe-payloads');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    for row in patch['ledger_replacements']:
        target=project/row['target'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PROJECT/row['replacement_payload'],target)
    export={'schema':1,'editable_scenes':{},'scene_producers':{},'painted_creature_sources':patch['source_export_patch']['set_painted_creature_sources']}
    export_path=project/'assets/production/source-export.json';dump(export_path,export)
    shutil.copy2(HERE/'production-ledger-payloads/source_dependencies.py',project/'scripts/source_dependencies.py')
    shutil.copy2(ROOT/'scripts/faction_source_prerequisites.py',workspace/'scripts/faction_source_prerequisites.py')
    sys.path.insert(0,str(workspace/'scripts'))
    spec=importlib.util.spec_from_file_location('_targon_painted_export_candidate',project/'scripts/source_dependencies.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    selected=module.selected_scene_exports(project,workspace)
    assert not any(name.casefold().endswith('.blend') for name in selected)
    assert len(export['painted_creature_sources'])==14
    mutations=[]
    def rejects(label,mutated):
        dump(export_path,mutated)
        try:module.selected_scene_exports(project,workspace)
        except Exception as exc:mutations.append({'mutation':label,'rejected':True,'reason':str(exc).replace(str(workspace),'<copied-workspace>')})
        else:raise AssertionError('Invalid source export accepted: '+label)
        finally:dump(export_path,export)
    changed=copy.deepcopy(export);changed['painted_creature_sources']['mountainArcher']['source_generation_ledger_sha256']='0'*64
    rejects('Changed painted source ledger pin',changed)
    changed=copy.deepcopy(export);changed['painted_creature_sources'].pop('stellacorn')
    rejects('Missing actual registered creature variant',changed)
    changed=copy.deepcopy(export);record=changed['painted_creature_sources']['mountainArcher'];key=next(iter(record['canonical_recipes']));record['canonical_recipes'][key]='0'*64
    rejects('Changed canonical selected creature recipe pin',changed)
    active=project/'assets/production/invalid-active-geometry-control.json'
    dump(active,{'status':'authored configuration','editable_scene':{'source':'assets/source/retired/control.blend','sha256':'0'*64}})
    try:
        try:module.selected_scene_exports(project,workspace)
        except Exception as exc:mutations.append({'mutation':'Reintroduced active unselected geometry dependency','rejected':True,'reason':str(exc).replace(str(workspace),'<copied-workspace>')})
        else:raise AssertionError('Active unselected geometry was accepted')
    finally:
        # A preserved history record must genuinely remain nonproduction.
        dump(active,{'required_for_production':False,'editable_scene':{'source':'assets/source/retired/control.blend','sha256':'0'*64}})
    after=module.selected_scene_exports(project,workspace);assert after.keys()==selected.keys()
    receipt={'status':'authored configuration','ok':True,'selected_painted_variants':14,'exported_current_files':len(selected),
        'canonical_recipes':len(list((project/'assets/recipes').rglob('*.json'))),'no_selected_creature_geometry_files':True,
        'historical_nonproduction_geometry_ignored':True,'actual_consumer':'Proposed bounded scripts/source_dependencies.py:selected_scene_exports in copied fixture',
        'scope':'Owned creature source selection only. Unrelated town/siege scene declarations are excluded from this fixture; the real patch preserves them and makes no full-town export acceptance claim.',
        'mutations':mutations,'native_execution':False,'canonical_workspace_modified':False}
    dump(REPORT/'painted-production-binding-consumer-tests.json',receipt)
    pins={p.relative_to(workspace).as_posix():sha(p) for p in workspace.rglob('*') if p.is_file()}
    dump(REPORT/'portable-source-inventory-with-export-consumer.json',{'status':'authored configuration','files_sha256':pins,'files':len(pins),
          'bytes':sum(p.stat().st_size for p in workspace.rglob('*') if p.is_file()),'original_game_pixels_included':False,'native_execution':False})
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
