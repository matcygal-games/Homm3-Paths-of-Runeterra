"""Portable raw-generation ledger; default tool save locations remain private."""
from pathlib import Path
from PIL import Image
import json,hashlib
S=Path(__file__).resolve().parent;P=S.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'source':p.relative_to(P).as_posix(),'source_sha256':sha(p)}
rows=[]
for p in sorted(S.rglob('*-raw.png')):
 if p.parent.name in ('native','resources'):continue
 prompt=p.with_name(p.name.replace('-raw.png','-prompt.txt'))
 if not prompt.exists():raise RuntimeError('Missing exact generation prompt '+str(p))
 im=Image.open(p);bad=p.parent.name=='awakenedSunforged' and p.name in ('melee-prepare-v1-raw.png','melee-up-v1-raw.png','melee-down-v1-raw.png','turn-back-v1-raw.png')
 inputs=[]
 if p.parent.name=='duneVeteran':
  stem=p.stem.removesuffix('-raw');target=P/'assets/source/creatures/painted-v2/ruinRunner'/(stem+'.png');armor=P/'assets/source/creatures/painted-v2/duneVeteran/armour-detail-reference-v1.png';inputs=[dict(pin(target),role='exact genuine2D action target'),dict(pin(armor),role='upgrade equipment detail only')]
 elif p.parent.name=='awakenedSunforged':
  stem=p.stem.removesuffix('-raw').replace('-v2','-v1');target=P/'assets/source/creatures/painted-v2/sunforgedColossus'/(stem+'.png');armor=P/'assets/source/creatures/painted-v2/awakenedSunforged/standing-v2.png';inputs=[dict(pin(target),role='genuine2D action target'),dict(pin(armor),role='upgrade equipment identity only')]
 elif p.name=='sunforgedColossus-turn-front-v1-raw.png':inputs=[dict(pin(S/'awakenedSunforged/turn-front-v1-raw.png'),role='exact frontal turn action target'),dict(pin(P/'assets/source/creatures/painted-v2/sunforgedColossus/standing-candidate-v1.png'),role='base equipment identity only')]
 elif p.name=='heraldry-cloth-raw.png':inputs=[dict(pin(P/'assets/source/regional-crests-20261025-v1/creatures/t1-pilot-v2/desertNomad/painted-cloth-provider-v2.png'),role='genuine prior painted textile style reference')]
 rows.append({'output':pin(p),'prompt':pin(prompt),'provider':'OpenAI built-in imagegen','model':'not exposed by tool','raw_provider_bytes_preserved':True,'canvas':list(im.size),'mode':im.mode,'embedded_metadata_keys':sorted(im.info),'input_images':inputs,'selected':not bad,'limitation':('Wrong-aspect first draft preserved, or rear-turn exploration not used by the native frontal boundary' if bad else 'Authored source; native visual/motion and external acceptance separate')})
result={'status':'authored configuration','actual_builtin_generation_calls':len(rows),'selected_call_outputs':sum(r['selected'] for r in rows),'no_3d_inputs':True,'official_private_shape_reference':{'url':'https://universe.leagueoflegends.com/images/shurima_crest_icon.png','sha256':'4a49e2bdfa9d4ebf411585d6877239edb0425aa14db9e67af4e6390b29c2c365','source_pixels_not_redistributed':True},'original_private_native_style_control_sha256':sha(P.parent/'runeterra-demacia/references/sheets/creature-battle-00.png'),'records':rows,'visual_approval_granted':False,'native_execution':False}
(S/'generation-ledger-v1.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'calls':len(rows),'selected':result['selected_call_outputs'],'ledger_sha256':sha(S/'generation-ledger-v1.json')}))
