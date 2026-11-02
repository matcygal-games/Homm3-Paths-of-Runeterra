"""Read-only inventory and proposed complete-scene design; no publication writes."""
from pathlib import Path
import hashlib,json

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    content=json.loads((PROJECT/'content/factions.json').read_text(encoding='utf-8'))
    town=content['bilgewater']['town']
    visual=json.loads((PROJECT/'design/town-visuals.json').read_text(encoding='utf-8'))
    states={key:{'name':spec['name'],'upgrades':spec.get('upgrades'),
                 'original_structure':town['structures'][key]}
            for key,spec in town['buildings'].items()}
    files=[PROJECT/'content/factions.json',PROJECT/'design/town-visuals.json',
           *sorted((PROJECT/'assets/recipes/town').glob('*.json'))]
    inventory={'status':'design proposal','request_date':'2026-10-28',
      'request':'Rebuild complete coherent Bilgewater town first, then derive playable layers; actual full silhouettes, doors, roads, support and intentional shoreline determine layout.',
      'quotes':[
        'Design the town as one immersive place before splitting functional layers.',
        'Use the native 800 x 374 scene.',
        'Reserve the largest valid replacement-state envelope at each site, clear supported door approaches, connecting roads and explicit water/shore boundaries.',
        'The terrain plate must not contain completed functional architecture.'],
      'preservation':'All old authored inputs remain unchanged. No creature, hero, economy, service or construction prerequisite change. Root alone integrates/builds/publishes.',
      'ordinary_land_sites':16,'optional_coastal_sites':1,'small_grail_sites':1,
      'actual_building_state_count':len(states),'actual_states':states,
      'source_control_sha256':{str(p.relative_to(PROJECT)).replace('\\','/'):sha(p) for p in files},
      'original_site_state_families':visual['sites'],
      'complete_scene_program':{
        'rear':['Harbor bastion','Captains civic council palace','Tide Archive','Cliffwing roost'],
        'middle':['Leviathan basin','Treasure Vault','Buhru priest temple','Shellshot battery','Fleet Captains Hall'],
        'lower_middle':['Corsair Deck','Sea Dog quarters','Slaughter Docks'],
        'foreground':['Black Market','Shipwright Forge','Trading Market','Tavern'],
        'coast':'Single optional supported slipway and compact moored boat, with ship replacing shipyard as dock-plus-boat composite.',
        'grail':'Tiny separate civic ledge beacon ornament.',
        'public_access':'A curved wide central street joins civic doorway to foreground, with dry supported branch lanes, stairs and landings to every site; no stairs under building roots.',
        'material':'Tarred repurposed ship timber, rough ancient Buhru serpent stone, patched sails, brass/copper, limited ivory/red/navy/turquoise, warm amber lights and teal bay.',
        'water':'Distant right bay and lower-right coastal pocket only. Ordinary plots are dry rock/stone or visibly braced supported timber; no accidental levitating or submerged building bases.',
        'silhouettes':'Complete native painted master reviewed first. Actual full contours/roofs/poles/shadows and maximum family envelope traced afterward, never rectangles accepted as click masks.'},
      'derivation':'After complete master source-composition review, genuine imagegen empty-scene and state variants preserve camera/light/site roots; deterministic alpha segmentation/crop/mask/icon conversion only. Existing generic raster/animation recipe consumers retained; new explicit silhouette-v2 contract proposed.',
      'source_art_acceptance':False,'native_verified':False,'release_accepted':False}
    (HERE/'whole-town-plan-v1.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
    (REPORT/'inventory-v1.json').write_text(json.dumps({'state_count':len(states),'ordinary_sites':len(visual['sites']),
      'whole_plan':'assets/source/town/complete-town-20261028-v1/whole-town-plan-v1.json',
      'whole_plan_sha256':sha(HERE/'whole-town-plan-v1.json'),
      'canonical_inputs_unchanged':all(sha(PROJECT/name)==pin for name,pin in inventory['source_control_sha256'].items())},indent=2)+'\n')
    print(json.dumps({'state_count':len(states),'ordinary_sites':len(visual['sites']),'plan_sha256':sha(HERE/'whole-town-plan-v1.json')}))

if __name__=='__main__':main()
