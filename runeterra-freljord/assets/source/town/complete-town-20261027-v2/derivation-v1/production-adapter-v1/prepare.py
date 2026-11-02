"""Bounded adapter for the ACTUAL CLI compiler; no canonical writes.

Preserves all reviewed state/area/border/card sources and the selected physical
contract. Removes only the obsolete unconfigured standalone card producers;
the actual indexed compiler owns its own36 physical card-frame outputs.
"""
from pathlib import Path
import copy,hashlib,json,sys
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[5];WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/complete-town-20261027-v2/production-adapter-v1'
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_art_compile
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    compiler=faction_art_compile.create_compiler('freljord')
    prior=read(HERE.parent/'integration-v2/plan.json')
    # Require the coordinator's exact integrated packet; no earlier source can
    # silently replace the currently selected canonical recipes.
    before={r['destination']:r['after_sha256']for r in prior['changes']}
    for name,expected in before.items():assert sha(PROJECT/name)==expected,'Integrated source drift: '+name
    actions=[];planned={};townprefix='Content/Sprites/runeterra/freljord/town/'
    sourcepins={}
    for path in sorted((PROJECT/'assets/recipes/town').rglob('*.json')):
        name=path.relative_to(PROJECT).as_posix()
        if name not in before:continue
        old=read(path)
        if name.startswith('assets/recipes/town/icons/'):
            actions.append({'operation':'delete','destination':name,'before_sha256':sha(path),'reason':'Unconfigured standalone construction-card producer; actual indexed compiler now consumes its reviewed source directly.'})
            continue
        value=copy.deepcopy(old)
        role='derived-technical-mask-complete'if name.endswith(('-area.json','-border.json'))else'painted-master-complete-unapproved'
        value['production_status']=role
        value['generation']={'image_generation_used':False,'method':'Deterministic technical assembly from the preserved built-in imagegen painted whole-town derivatives and traced source layers; this recipe makes no new artwork. No pixel, alpha, pose, physical contact or native placement change.','painted_source_provenance':copy.deepcopy(old['generation']),'technical_adapter':ref(Path(__file__))}
        value['inputs'].append(ref(Path(__file__)))
        if value['recipe_type']=='raster':value['fit']='exact'
        if value['recipe_type']=='indexed_animation':
            value.pop('depends_on',None)
            for frame in value['frames']:
                building=frame['building'];source=HERE.parent/'candidate/states'/building/'icon.png'
                frame.clear();frame.update(building=building,frame=compiler.indexed_building_ids(PROJECT)[building],source=source.relative_to(PROJECT).as_posix(),source_sha256=sha(source),sha256=sha(source),source_canvas=[150,70])
                sourcepins[source.relative_to(PROJECT).as_posix()]=sha(source)
        dest=HERE/'recipes'/Path(name).relative_to('assets/recipes');write(dest,value)
        outputs,record=compiler.plan(PROJECT,dest)
        planned[name]={'recipe_sha256':sha(dest),'outputs':{n:hashlib.sha256(raw).hexdigest()for n,raw in outputs.items()},'dimensions':record['dimensions']}
        actions.append({'operation':'replace','source':dest.relative_to(PROJECT).as_posix(),'destination':name,'before_sha256':sha(path),'after_sha256':sha(dest)})
    assert len(planned)==110 and sum(a['operation']=='delete'for a in actions)==36
    manifest=read(PROJECT/'assets/manifest.json');original=copy.deepcopy(manifest)
    for entry in manifest['assets']:
        recipe=entry.get('source',{}).get('recipe_path')
        if recipe not in planned:continue
        record=planned[recipe];output=entry['output_path'];expected=record['outputs'][output]
        assert entry.get('status')!='accepted' or entry['sha256']==expected,'Accepted asset mismatch'
        entry['sha256']=expected;entry['dimensions']=record['dimensions'];entry['dimensions_basis']='measured from the built output'
        entry['source'].update(editable_path='assets/generated/'+output,recipe=recipe,recipe_path=recipe,recipe_present=True,recipe_sha256=record['recipe_sha256'])
        entry['dependencies']=[recipe]
        if entry.get('status')!='accepted':entry.update(status='built-unreviewed',native_visual_review='pending')
    write(HERE/'manifest.candidate.json',manifest)
    actions.append({'operation':'replace','source':(HERE/'manifest.candidate.json').relative_to(PROJECT).as_posix(),'destination':'assets/manifest.json','before_sha256':sha(PROJECT/'assets/manifest.json'),'after_sha256':sha(HERE/'manifest.candidate.json')})
    bodypins={s:record['sha256']for s,record in read(HERE.parent/'candidate/layout-contract.json')['frames'].items()}
    write(HERE/'proposal.json',{'status':'authored configuration','canonical_applied':False,'native_verified':False,'release_accepted':False,'actions':actions,'recipe_count':110,'removed_unconfigured_icon_recipes':36,'body_source_pins':bodypins,'reviewed_icon_source_pins':sourcepins,'physical_contract':ref(HERE.parent/'candidate/layout-contract.json'),'expected_actual_compiler_plans':planned,'manifest_entries':len(manifest['assets']),'manifest_changed_entries':sum(a!=b for a,b in zip(original['assets'],manifest['assets']))})
    print(json.dumps({'recipes':len(planned),'guarded_actions':len(actions),'manifest_before':sha(PROJECT/'assets/manifest.json'),'manifest_candidate':sha(HERE/'manifest.candidate.json'),'body_pixels_changed':False},indent=2))
if __name__=='__main__':main()
