"""Versioned current-SDK adapter; preserve all selected painted source bytes.

V1's legacy converter packet remains immutable history. This emits only the206
actual native town recipes in the configured Targon production compiler grammar.
"""
from pathlib import Path
import importlib.util
import hashlib
import json

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
SOURCE=HERE.relative_to(PROJECT).as_posix()


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    spec=importlib.util.spec_from_file_location('preserved_town_v1_derivatives',HERE/'derive_resources.py')
    legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    legacy.main()
    inventory=json.loads((HERE/'derived-source-inventory-v1.json').read_text())
    schema=json.loads((HERE/'native-resource-schema-v1.json').read_text())['recipes']
    ledger=HERE/'source-generation-ledger-v2.json'
    recipes={}
    for relative,baseline in sorted(schema.items()):
        old=HERE/'proposed/recipes'/relative;recipe=json.loads(old.read_text());role=recipe.get('role','town-background');name=Path(relative).stem
        recipe['production_status']='derived-technical-mask-complete' if role in ('town-structure-area','town-structure-border') else 'painted-master-complete-unapproved'
        if recipe['recipe_type']=='raster':recipe['fit']='exact'
        generation=recipe['generation'];generation['source_generation_ledger']=SOURCE+'/source-generation-ledger-v2.json'
        generation.pop('source_generation_ledger_sha256',None)
        if ledger.is_file():generation['source_generation_ledger_sha256']=sha(ledger)
        state=name.removesuffix('_area').removesuffix('_border').removesuffix('_campaign')
        master=HERE/'states'/state/'master-v1-raw.png'
        if master.is_file():
            prompt=(master.parent/'prompt-v1.txt').read_text(encoding='utf-8')
        elif role=='town-adventure':
            master=HERE/'ancillary'/name/('master-v2-raw.png' if name=='village' else 'master-v1-raw.png')
            prompt=(master.parent/('prompt-v2.txt' if name=='village' else 'prompt-v1.txt')).read_text(encoding='utf-8')
        elif role=='puzzle-piece':
            master=HERE/'ancillary/puzzle/master-v1-raw.png';prompt=(master.parent/'prompt-v1.txt').read_text(encoding='utf-8')
        elif role=='town-interface':
            master=HERE/'ancillary'/('guild-window' if name=='guildWindow' else 'creature-background')/'master-v1-raw.png';prompt=(master.parent/'prompt-v1.txt').read_text(encoding='utf-8')
        elif role=='town-state-icon':
            label='castle' if name.startswith('fort') else 'village';master=HERE/'ancillary'/label/('master-v2-raw.png' if label=='village' else 'master-v1-raw.png');prompt=(master.parent/('prompt-v2.txt' if label=='village' else 'prompt-v1.txt')).read_text(encoding='utf-8')
        elif role=='town-background':
            master=HERE/'terrain-repair-v9/upper-raw.png';prompt=(master.parent/'upper-prompt.txt').read_text(encoding='utf-8')
        else:
            master=HERE/'complete-crest-edit-v1-raw.png';prompt=(HERE/'complete-crest-edit-v1-prompt.txt').read_text(encoding='utf-8')
        generation['painted_master']=master.relative_to(PROJECT).as_posix();generation['painted_master_sha256']=sha(master);generation['prompt']=prompt
        if recipe['recipe_type']=='indexed_animation':
            recipe.pop('depends_on',None)
            recipe['pivot']={'x':0,'y':0,'basis':'Native construction atlas150x70; frames retain actual BuildingID gaps.'}
            recipe['frames']=[{'building':row['building'],'frame':row['frame'],
                              'source':inventory[row['building']+'_construction']['path'],
                              'source_sha256':inventory[row['building']+'_construction']['sha256'],
                              'source_canvas':[150,70]} for row in baseline['frames']]
        path=HERE/'proposed-configured-v2/recipes'/relative;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n');recipes[relative]=sha(path)
    if len(recipes)!=206:raise ValueError('Configured town must cover its actual206 logical native resources exactly')
    (HERE/'configured-recipe-index-v2.json').write_text(json.dumps({'status':'authored configuration','actual_native_recipe_count':206,'canonical_recipes':recipes,'legacy_auxiliary_construction_producers_selected':False},sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'configured_native_recipes':len(recipes),'legacy_generated_index_dependencies':0}))


if __name__=='__main__':main()
