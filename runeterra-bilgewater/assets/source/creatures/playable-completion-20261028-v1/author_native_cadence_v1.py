"""Author explicit whole-painted-key holds for inspected native animation ticks.

This creates new proposal configs. It never invents in-between poses, changes
creative pixels, mutates canonical content or overwrites prior evidence.
"""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(source,version):
    source=source.resolve();cfg=json.loads(source.read_text());cfg['version']=version
    operations={
      0:(6,[0,0,1,2,3,3,4,5]),
      1:(2,[0,1,1,1,0]),3:(3,[0,0,1,1,2]),4:(2,[0,0,0,1,1]),5:(4,[0,0,1,1,2,2,3,3]),
      7:(4,[0,1,2,3,3]),8:(4,[0,0,1,2,3]),
      11:(4,[0,0,1,1,2,2,3,3]),12:(4,[0,0,1,1,2,2,3,3]),13:(4,[0,0,1,1,2,2,3,3]),
      14:(6,[0,1,2,3,4,4,5,5]),15:(6,[0,1,2,3,4,4,5,5]),16:(6,[0,1,2,3,4,4,5,5]),
      30:(6,[0,1,2,2,3,3,4,5]),31:(6,[0,1,2,2,3,3,4,5]),32:(6,[0,1,2,2,3,3,4,5])}
    timeline=[]
    for name,keys in list(cfg['groups'].items()):
        group=int(name)
        if group in operations:
            expected,indices=operations[group]
            if len(keys)!=expected:raise ValueError('Inspect new source key count before timeline expansion: '+name)
            cfg['groups'][name]=[keys[i]for i in indices]
            timeline.append({'group':group,'original_genuine_key_sequence':keys,'timeline_source_key_indices':indices,'native_ticks':len(indices),'unique_painted_keys':len(set(keys))})
    cfg['timeline_contract']={'status':'authored configuration','description':'Existing native8-tick melee/walk/death/shoot/cast and5-tick response/turn cadence, with explicit holds of genuine painted keys. Repeated timeline images are deliberate holds, never claimed as extra painted poses.','native_base_fps':10,'battle_speed_factor':'Selected native engine setting; actual quantization and visual rhythm need runtime observation','source_consumer':'vcmi-develop/vcmi-develop/client/battle/CreatureAnimation.cpp','source_consumer_sha256':sha(PROJECT.parent/'vcmi-develop/vcmi-develop/client/battle/CreatureAnimation.cpp'),'climax_consumer':'vcmi-develop/vcmi-develop/client/battle/BattleAnimationClasses.cpp','climax_consumer_sha256':sha(PROJECT.parent/'vcmi-develop/vcmi-develop/client/battle/BattleAnimationClasses.cpp'),'shooter_release_source_index':3,'native_shooter_attackClimaxFrame':4,'eight_tick_cast_release_source_index':4,'groups':timeline,'native_execution':False}
    cfg.setdefault('generation_reference_inputs',[]).extend([{'path':source.relative_to(PROJECT).as_posix(),'sha256':sha(source),'use':'Preserved source key selection before timeline expansion'},{'path':Path(__file__).relative_to(PROJECT).as_posix(),'sha256':sha(Path(__file__)),'use':'Explicit deterministic whole-painted-key timeline authoring'}])
    dest=source.with_name(f'assembly-config-v{version}.json');data=(json.dumps(cfg,sort_keys=True,indent=2)+'\n').encode()
    if dest.exists()and dest.read_bytes()!=data:raise ValueError('Preserve previous authored timeline; version correction')
    if not dest.exists():dest.write_bytes(data)
    print(dest.relative_to(PROJECT).as_posix())
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--version',type=int,required=True);a=p.parse_args();main(a.source,a.version)
