"""Bind ordinary immutable new painted-role contracts, never old live recipes."""
from pathlib import Path
import argparse,json,sys
S=Path(__file__).resolve().parent;P=S.parents[3];sys.path.insert(0,str(S))
from pose_tools import sha,enc,put,rel

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--recipes',default='assets/candidates/ionia-revision20261025-kashuri-v1/recipes');args=ap.parse_args()
    output=(P/args.recipes).resolve();assert output.is_relative_to(P.resolve())
    roles=json.loads((S/'role-contracts-v1.json').read_text());data=json.loads((S/'native-production-v1.json').read_text());selection=[]
    names=['generation-v1.json','native-production-v1.json','native-assembly-contract-v1.json','role-contracts-v1.json','assemble_native_v1.py','assemble_base_gait.py','prepare_gait_reference.py','prepare_reference_inputs_v1.py','pose_tools.py','painted_components.py','release-mouth-registration-v2.json']
    dependencies=[{'source':rel(S/n),'source_sha256':sha(S/n)} for n in names]
    credits={'author':'Original genuine painted2D subjects/actions: OpenAI built-in imagegen; deterministic native assembly: project tools','license':'not reviewed','redistribution':'unresolved; release prohibited'}
    for unit in roles['units']:
        info=data['units'][unit];counts={str(g):sum(r['group']==g for r in info['frames']) for g in sorted({r['group']for r in info['frames']})};assert counts==roles['battle_groups']
        generation={'provider':'OpenAI built-in imagegen','image_generation_used':True,'model':'not exposed by built-in tool','status':'authored configuration','painted_master':rel(S/unit/'identity-v2.png'),'painted_master_sha256':sha(S/unit/'identity-v2.png'),'technical_method':'Whole genuine painted2D action ownership, fixed native contact, uniform camera scale, deterministic projection and own scene portrait composition; no3D or body warp','current_dependencies':dependencies,'native_playback':'not_run','release_accepted':False}
        common={'unit':unit,'production_status':'delivered','status':'built-unreviewed','visual_approval_granted':False,'acceptance':'authored configuration; independent source review, native playback, external human art and redistribution acceptance pending','credits':credits,'generation':generation,'technical_scope':'Deterministic compilation of complete own painted sources; delivered is compiler availability, not release acceptance'}
        for role in roles['ordinary_roles']:
            recipe={**common}
            if role in ['battle','map','projectile']:
                if role=='battle':canvas=[450,400];pivot={'x':197,'y':266};records=info['frames'];groups=[]
                elif role=='map':canvas=[96,64];pivot={'x':80,'y':60};records=info['map_frames'];groups=[]
                else:canvas=[40,40];pivot={'x':20,'y':20};records=data['projectile']['frames'];groups=[]
                if role=='battle':
                    for g in sorted({r['group']for r in records}):groups.append({'group':g,'frames':[{k:r[k]for k in ['source','source_sha256','source_canvas']} for r in records if r['group']==g]})
                else:groups=[{'group':0,'frames':[{k:r[k]for k in ['source','source_sha256','source_canvas','projection_contract']if k in r}for r in records]}]
                recipe.update(recipe_type='vcmi_animation',canvas=canvas,pivot=pivot,groups=groups,generateShadow=2 if role=='map' else 0 if role=='projectile' else 1,generateOverlay=0 if role=='projectile' else 1)
                if role=='projectile':recipe.update(physical_projectile=True,trajectory_angles=roles['projectile_angles'])
            else:
                r=next(r for r in info['portraits']+info['attacks']if r['role']==role);size=[58,64]if role=='large' else[32,32]if role=='small' else[96,64]
                recipe.update(recipe_type='raster',source=r['source'],source_sha256=r['source_sha256'],source_canvas=size,size=size,fit='stretch',require_alpha=role.startswith('attack'))
                if 'projection_contract'in r:recipe['projection_contract']=r['projection_contract']
            recipe['output_path']=f'Content/Sprites/runeterra/ionia/projectiles/{unit}.json'if role=='projectile'else f'Content/Sprites/runeterra/ionia/creatures/{unit}/{role}.'+('json'if role in ['battle','map']else'png')
            p=output/f'{unit}-{role}.json';put(p,enc(recipe));selection.append({'unit':unit,'role':role,'candidate':p.relative_to(P).as_posix(),'candidate_sha256':sha(p),'canonical_target':f'assets/recipes/creatures/{unit}-{role}.json','output_path':recipe['output_path']})
    put(S/'selection-v1.json',enc({'status':'authored configuration','recipes':selection,'no_live_selection':True,'runtime_verified':False,'release_accepted':False}));print('Bound',len(selection),'ordinary candidate recipes')

if __name__=='__main__':main()
