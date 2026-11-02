"""Prepare and execute the existing town compiler, never a canonical build.

The root coordinator owns adoption. This produces an exact 155-recipe payload,
preserving 13 untouched adventure-town/icon producers, and privately materializes
the actual compiler's bytes for source/physical review. It does not stage a mod.
"""
from pathlib import Path
import argparse,copy,hashlib,json,sys
from PIL import Image
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
BASE=HERE.parent.parent
WORKSPACE=PROJECT.parent
sys.path.insert(0,str(WORKSPACE/'scripts'))
from faction_art_compile import create_compiler

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def save(p,value):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cohort',required=True);parser.add_argument('--cohort-sha256',required=True);parser.add_argument('--out',default='compiler-source-finish-v1');args=parser.parse_args()
    index_path=PROJECT/args.cohort
    if sha(index_path)!=args.cohort_sha256:raise ValueError('Unreviewed cohort index drift')
    index=json.loads(index_path.read_text());states=index['states']
    if len(states)!=35:raise ValueError('Need the exact35-state town cohort')
    original=json.loads((PROJECT/'content/factions.json').read_text())
    if set(states)!=set(original['bilgewater']['town']['buildings']):raise ValueError('State identity differs from actual content')
    out=HERE/args.out;out.mkdir(exist_ok=False);recipes=out/'recipes';recipes.mkdir()
    sources=[]
    for key,entry in states.items():
        for field in ('frame','area','border','campaign','construction'):
            source=PROJECT/entry[field]
            if sha(source)!=entry[field+'_sha256']:raise ValueError('Cohort source changed: '+key+'/'+field)
            sources.append({'path':entry[field],'sha256':sha(source)})
    bg_source=PROJECT/index['background']
    if sha(bg_source)!=index['background_sha256']:raise ValueError('Background changed')
    bg=out/'background-RGBA.png';Image.open(bg_source).convert('RGBA').save(bg)
    if Image.open(bg).convert('RGBA').tobytes()!=Image.open(bg_source).convert('RGBA').tobytes():raise ValueError('Background RGB conversion drift')
    generation={'image_generation_used':False,'method':'Technical crop/matte/whole-variant registration and native PNG conversion of genuinely painted complete-town/state/underlap sources; no 3D or code artwork.',
      'cohort_index':rel(index_path),'cohort_index_sha256':sha(index_path),'complete_scene_source':'assets/source/town/complete-town-20261028-v1/complete-town-native-v3.png',
      'complete_scene_source_sha256':sha(BASE/'complete-town-native-v3.png')}
    generation['hidden_support_source_closure']={'path':rel(HERE.parent/'hidden-support-source-closure-v4.json'),'sha256':sha(HERE.parent/'hidden-support-source-closure-v4.json')}
    generation['lower_roost_registration']={'path':rel(HERE/'lower-roost-registration-v1/registration-inputs.json'),'sha256':sha(HERE/'lower-roost-registration-v1/registration-inputs.json')}
    generation['current_structural_source_refinement']={'path':rel(HERE/'structural-source-finish-v1/source-refinement-receipt.json'),'sha256':sha(HERE/'structural-source-finish-v1/source-refinement-receipt.json')}
    generation['current_painted_floor_sources']={'path':rel(HERE/'localized-ground-selection-v3/selection-receipt.json'),'sha256':sha(HERE/'localized-ground-selection-v3/selection-receipt.json')}
    generation['source_scenery_ownership']={'path':rel(HERE/'ownership-separation-v5/plan.json'),'sha256':sha(HERE/'ownership-separation-v5/plan.json')}
    generation['source_ownership_receipt']={'path':rel(HERE/'ownership-separation-v5/separation-receipt.json'),'sha256':sha(HERE/'ownership-separation-v5/separation-receipt.json')}
    generation['source_ownership_assembler']={'path':rel(HERE/'assemble_ownership_separation_v5.py'),'sha256':sha(HERE/'assemble_ownership_separation_v5.py')}
    generation['converter_helper']={'path':rel(Path(__file__).resolve()),'sha256':sha(Path(__file__).resolve())}
    originals=sorted((PROJECT/'assets/recipes/town').glob('*.json'))
    if len(originals)!=155:raise ValueError('Actual selected town recipe inventory changed; re-audit before continuing')
    changed=[];unchanged=[];payload=[]
    for path in originals:
        before=json.loads(path.read_text());value=copy.deepcopy(before);name=path.name
        if name.startswith('structures_'):
            key=name[len('structures_'):].split('.')[0]
            if key.endswith(('_area','_border','_campaign')):
                state,kind=key.rsplit('_',1);field=kind
                source=states[state][field]
                value['source']=source;value['source_sha256']=states[state][field+'_sha256']
                value['source_canvas']=list(Image.open(PROJECT/source).size)
            else:
                state=key;entry=states[state]
                value['groups']=[{'group':0,'frames':[{'source':entry['frame'],'source_sha256':entry['frame_sha256'],'sha256':entry['frame_sha256'],'source_canvas':[800,374]}]}]
                value['pivot']={'x':0,'y':0}
            value['generation']=copy.deepcopy(generation)
        elif name=='background.png.json':
            value.update({'source':rel(bg),'source_sha256':sha(bg),'source_canvas':[800,374],'fit':'exact','generation':copy.deepcopy(generation)})
        elif name=='buildingIcons.json.json':
            for descriptor in value['frames']:
                entry=states[descriptor['building']]
                descriptor['source']=entry['construction'];descriptor['source_sha256']=entry['construction_sha256'];descriptor['source_canvas']=[150,70]
            value['generation']=copy.deepcopy(generation)
        else:
            unchanged.append(name)
        if value!=before:changed.append(name)
        destination=recipes/name
        if value==before:destination.write_bytes(path.read_bytes())
        else:save(destination,value)
        payload.append({'target':'assets/recipes/town/'+name,'before_sha256':sha(path),'candidate':rel(destination),'sha256':sha(destination),'changed':value!=before})
    candidate_content=copy.deepcopy(original)
    for state,entry in states.items():
        candidate_content['bilgewater']['town']['structures'][state]['z']=entry['z']
    for state in states:
        baseline=copy.deepcopy(original['bilgewater']['town']['structures'][state]);current=copy.deepcopy(candidate_content['bilgewater']['town']['structures'][state])
        baseline.pop('z');current.pop('z')
        if baseline!=current:raise ValueError('Unexpected authored structure-field change')
    save(out/'content/factions.json',candidate_content)
    compiler=create_compiler('bilgewater');outputs={};receipts=[]
    for path in sorted(recipes.glob('*.json')):
        data,receipt=compiler.plan(PROJECT,path)
        for name,value in data.items():
            if name in outputs:raise ValueError('Duplicate actual compiler output: '+name)
            outputs[name]=value
        receipts.append(receipt)
    # A second actual configured pass, with exact required logical membership.
    import faction_pipeline as fp
    pipeline=fp.Pipeline(PROJECT,'runeterra-bilgewater','bilgewater')
    current_content=pipeline.content();current_content['factions']=candidate_content
    required=fp.required_outputs(current_content,pipeline)
    compiler_two=create_compiler('bilgewater');second={};logical=[]
    for recipe_path in sorted(recipes.glob('*.json')):
        recipe_value=json.loads(recipe_path.read_text());logical_name=recipe_value.get('output_path')
        if logical_name not in required:raise ValueError('Auxiliary or nonrequired logical town producer: '+str(logical_name))
        logical.append(logical_name)
        data_two,receipt_two=compiler_two.plan(PROJECT,recipe_path)
        for name,data in data_two.items():
            if name in second:raise ValueError('Second-pass duplicate output')
            second[name]=data
    if len(set(logical))!=155 or set(second)!=set(outputs)or any(second[n]!=outputs[n]for n in outputs):
        raise ValueError('Configured strict town passes differ')
    save(out/'configured-two-pass.json',{'status':'authored configuration','configured_factory':'faction_art_compile.create_compiler(bilgewater)','logical_required_members':len(logical),'actual_registered_required_count':len(required),'physical_products_each_pass':len(outputs),'exact_output_bytes_equal':True,'auxiliary_logical_producers':False,'passes':2,'shared_compiler_sha256':sha(WORKSPACE/'scripts/faction_art_compile.py'),'pipeline_sha256':sha(WORKSPACE/'scripts/faction_pipeline.py'),'native_or_release_acceptance':False})
    outputpins=[]
    for name,data in sorted(outputs.items()):
        destination=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1'/args.out/'compiled'/name
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
        outputpins.append({'path':name,'sha256':hashlib.sha256(data).hexdigest()})
    report={'status':'authored configuration','scope':'Actual existing155 town-only recipes and declared source frames, not full-mod production/stage freshness or game acceptance.',
        'cohort_index':rel(index_path),'cohort_index_sha256':sha(index_path),'recipe_count':len(receipts),'changed_recipe_count':len(changed),'unchanged_recipe_count':len(unchanged),
        'changed_recipes':changed,'unchanged_recipes':unchanged,'actual_output_count':len(outputs),'outputs':outputpins,'recipes':payload,
        'candidate_content':rel(out/'content/factions.json'),'candidate_content_sha256':sha(out/'content/factions.json'),
        'content_change_scope':'Only35 drawing z fields; all gameplay/economy/identity/building-library relationships remain unchanged.',
        'background_source':index['background'],'background_source_sha256':index['background_sha256'],'RGBA_source':rel(bg),'RGBA_source_sha256':sha(bg),'RGBA_decoded_pixels_equal':True,
        'physical_layout_status':'Pending separate exact-cohort contract/public-consumer/negative verification.', 'native_verified':False,'release_accepted':False}
    save(out/'compiler-receipts.json',receipts);save(out/'payload-and-compiler.json',report)
    print(json.dumps({'recipes':len(receipts),'changed':len(changed),'unchanged':len(unchanged),'actual_outputs':len(outputs),'receipt':rel(out/'payload-and-compiler.json')}))
if __name__=='__main__':main()
