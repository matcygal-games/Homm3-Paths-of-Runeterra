"""Independent exact Tavern timber/stair ownership correction, preserving wood."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
OUT=HERE/'ownership-separation-v5'
OUT.mkdir(exist_ok=False)
prior=HERE/'ownership-separation-v4/plan.json';plan=json.loads(prior.read_text())
row=plan['states']['tavern']
row['retain_polygons']=[[[604,222],[640,222],[640,291],[604,291]],[[531,244],[550,244],[550,260],[531,260]]]
row.setdefault('permanent_ground_polygons',[]).append([[531,261],[539,260],[549,264],[550,271],[531,271]])
row['structural_contact_regions']=[[[607,265],[615,265],[615,292],[607,292]],[[629,262],[640,262],[640,287],[629,287]],[[531,244],[550,244],[550,260],[531,260]]]
row['bearing_seam']=[[515,254],[531,259],[548,261],[569,270],[595,274]]
row['source_interpretation']='Retain all real warm timber facade/toe through its observed native259/260 seam, and the complete right lower annex/entry with independently retained pillars. The pale/grey masonry spur around532–549/262–270 is the actual permanent public stair-head/parapet continuous with the descending city stair; it is not a detached timber column or a fake door. The upper diagonal edge of the lower annex is not a ground sole: its complete actual lower bearing components remain separate.'
plan['independent_tavern_material_correction']={'reviewer':'/root/ionia_creature_delivery','evidence':'independent-bilgewater-ownership-v1/tavern-retained-stairhead-grid10x.png','real_timber_above259_260_preserved':True,'right_annex_entrance_preserved':True,'masonry_stair_not_relabelled_as_door':True,'terrain_mask_read':False,'ancestor':{'path':prior.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(prior.read_bytes()).hexdigest()}}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
print('Frozen independently observed real wood/public stair correction')
