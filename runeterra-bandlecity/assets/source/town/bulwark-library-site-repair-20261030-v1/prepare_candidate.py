"""Prepare reviewable recipes and a read-only compiler plan; never select or stage."""
from pathlib import Path
import copy, hashlib, json, sys
import numpy as np
from PIL import Image

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ROOT=PROJECT.parent
OUT=SOURCE/'candidate-v4'
STATE=SOURCE/'states-v3'
REPORT=ROOT/'reports/bandle-bulwark-site-repair-20261030-v1'
sys.path.insert(0,str(ROOT/'scripts'))
from faction_art_compile import create_compiler

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rel(path): return Path(path).relative_to(PROJECT).as_posix()
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    if path.exists() and path.read_bytes()!=raw: raise RuntimeError('Immutable candidate differs: '+str(path))
    if not path.exists(): path.write_bytes(raw)
def load(path): return json.loads(Path(path).read_text())
def pin(path): return {'path':rel(path),'sha256':sha(path)}

def main():
    derivation=load(STATE/'derivation.json')
    ledger={'status':'authored configuration','visual_approval_granted':False,'release_accepted':False,
      'reason':'User rejected the library-to-Bulwark bridgehead and unupgraded fort placement after BC1 selection.',
      'provider':'OpenAI built-in imagegen','model':'not exposed by tool','no_3d':True,
      'painted_inputs':[
        {**pin(SOURCE/'background-provider-v1.png'),'role':'local ground repaint',
         'prompt_summary':'Repair only the small mossy bridgehead/courtyard between Glade Library and the gate, making a connected walkable stone route. Preserve other approved town details. Exact old pixels restored outside the bounded ROI by technical composition.',
         'references':[pin(PROJECT/'assets/source/town/approved-BC1-completion-20261030-v1/background-v7.png')]},
        {**pin(SOURCE/'castle-provider-v1.png'),'role':'independent final fortification',
         'prompt_summary':'A complete isolated Bandle City twin gatehouse with stone and timber towers, teal roofs, golden lamps, leaf/spiral crest banners and centered entrance, coherent with the painted HoMM3 town. Transparent outside the full building; no scenery or bridge.'},
        {**pin(PROJECT/'assets/source/town/approved-BC1-completion-20261030-v1/civic-states-v1.png'),
         'role':'preserved prior painted fort and citadel, uniform scale and threshold registration only'}],
      'producer':pin(SOURCE/'derive-v3.py'),'derivation':pin(STATE/'derivation.json'),
      'scope':{'background_roi':derivation['roi'],'common_gate_door':derivation['door'],
        'library_layers_changed':False,'dwelling_layers_changed':False,'sixteen_land_plots_preserved':True,
        'optional_coastal_site_preserved':True,'one_site_per_creature_tier_preserved':True}}
    save(SOURCE/'generation-ledger-v3.json',ledger)
    generation={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by tool',
      'prompt':'Scoped painted Bandle bridgehead and independent final gate; see pinned generation ledger for descriptions and provenance.',
      'method':'Painted 2D master, bounded native scenery composite, uniform scaled doorway registration and alpha-derived masks; no 3D.',
      'source_generation_ledger':rel(SOURCE/'generation-ledger-v3.json'),
      'source_generation_ledger_sha256':sha(SOURCE/'generation-ledger-v3.json'),
      'technical_producer':rel(SOURCE/'derive-v3.py'),'technical_producer_sha256':sha(SOURCE/'derive-v3.py')}
    recipes=[];before={};mapping=[]
    names=['background.json','buildingIcons.json']+[f'structures/{k}-{role}.json' for k in ('fort','citadel','castle') for role in ('animation','area','border','campaign')]
    for name in names:
        path=PROJECT/'assets/recipes/town'/name
        current=load(path);before[rel(path)]=sha(path)
        save(OUT/'before/recipes'/name,current)
        recipe=copy.deepcopy(current)
        recipe['generation']=copy.deepcopy(generation)
        painted=SOURCE/'background-provider-v1.png' if name=='background.json' else SOURCE/'castle-provider-v1.png'
        if name.startswith(('structures/fort-','structures/citadel-')):
            painted=PROJECT/'assets/source/town/approved-BC1-completion-20261030-v1/civic-states-v1.png'
        recipe['generation'].update(painted_master=rel(painted),painted_master_sha256=sha(painted))
        recipe['visual_approval_granted']=False
        recipe['acceptance']='Scoped user-requested bridgehead repair; authored configuration, native visual/gameplay and rights acceptance pending.'
        recipe['status']='authored configuration'
        if name=='buildingIcons.json':
            for frame in recipe['frames']:
                if frame['building'] in ('fort','citadel','castle'):
                    p=STATE/frame['building']/'hall.png';frame.update(source=rel(p),source_sha256=sha(p))
            # Keep unrelated card producer provenance explicit; only three indexed frames change.
            recipe['generation']['painted_source_provenance']=current['generation']
        elif name=='background.json':
            p=STATE/'background.png';recipe.update(source=rel(p),source_sha256=sha(p))
        else:
            key,role=Path(name).stem.rsplit('-',1)
            p=STATE/key/('layer.png' if role=='animation' else role+'.png')
            if role=='animation':
                recipe['groups'][0]['frames'][0].update(source=rel(p),source_sha256=sha(p))
                recipe['generation']['conversion']={'method':'Full-canvas layer at origin; common doorway (270,75), native depth 80.','native_z':80,'composition_rectangle':[239,11,58,67]}
            else: recipe.update(source=rel(p),source_sha256=sha(p))
        candidate=OUT/'recipes'/name;save(candidate,recipe);recipes.append(candidate)
        mapping.append({'canonical':rel(path),'before_sha256':sha(path),'candidate':rel(candidate),'candidate_sha256':sha(candidate)})
    factions=load(PROJECT/'content/factions.json');town=factions['bandlecity']['town']
    save(OUT/'before/factions.json',factions)
    config_changes=[{'path':['bandlecity','town','structures',key,'z'],'before':town['structures'][key]['z'],'after':80} for key in ('fort','citadel','castle')]
    design=load(PROJECT/'design/town-visuals.json');save(OUT/'before/town-visuals.json',design)
    site=next(x for x in design['sites'] if x['id']=='fortification') if 'sites' in design else None
    # Describe exact field replacements rather than overwrite the concurrently edited design.
    design_change={'site_id':'fortification','native_z':80,'center':[268,44],
      'composition_rectangle':[239,11,58,67],'common_door':[270,75],
      'selected_state_art':{}}
    for key,row in derivation['states'].items():
        a=np.array(Image.open(STATE/key/'area.png').getchannel('A'))
        source=SOURCE/'castle-provider-v1.png' if key=='castle' else PROJECT/'assets/source/town/approved-BC1-completion-20261030-v1/civic-states-v1.png'
        design_change['selected_state_art'][key]={'native_layer':rel(STATE/key/'layer.png'),
          'native_layer_sha256':sha(STATE/key/'layer.png'),'master':rel(source),'master_sha256':sha(source),
          'source_crop_xyxy':row['sheet_box'],'click_bbox':list(Image.fromarray(a).getbbox()),
          'click_pixels':int(np.count_nonzero(a)),'native_z':80,'fit_size':row['size'],'common_door':[270,75],
          'composition_rectangle':[239,11,58,67],'visual_approval_granted':False,'site':'fortification','state':key}
    save(OUT/'integration-plan.json',{'status':'authored configuration','selected':False,'recipes':mapping,
      'config_source_before_sha256':sha(PROJECT/'content/factions.json'),'config_field_changes':config_changes,
      'design_source_before_sha256':sha(PROJECT/'design/town-visuals.json'),'design_site_replacement_fields':design_change,
      'instructions':'Coordinator must merge only these fields, update its sealed recipe selections/manifest, regenerate outputs with existing pipeline, and run fresh source checks. No direct profile patch. Keep prior BC1 selected source intact as history.'})
    compiler=create_compiler('bandlecity');results=[];outputs={}
    for p in recipes:
        blobs,receipt=compiler.plan(PROJECT,p)
        results.append(receipt)
        outputs.update({k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()})
    save(REPORT/'compiler-plan-v3.json',{'ok':True,'recipe_count':len(results),'planned_output_count':len(outputs),'results':results,'outputs':outputs,'outputs_written':False})
    save(OUT/'canonical-before-hashes.json',before)
    print(json.dumps({'ok':True,'candidate_recipes':len(results),'planned_outputs':len(outputs),'canonical_or_generated_outputs_written':False}))

if __name__=='__main__':main()
