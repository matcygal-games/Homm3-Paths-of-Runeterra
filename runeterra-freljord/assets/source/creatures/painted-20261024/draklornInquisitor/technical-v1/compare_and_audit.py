"""Read selected sources/consumer evidence; compose native1x review and seal report."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib, json, importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('packet',HERE/'assemble_packet.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
R=p.REPORT; W=p.WORKSPACE; S=p.SOURCE
def pin(path):
 return {'path':path.relative_to(W).as_posix(),'sha256':p.sha(path)}
def alpha_bounds(im):return im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
def place(board,path,xy,mirror=False):
 im=Image.open(path).convert('RGBA')
 if mirror:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 board.paste(im,xy,im)
def fixed_battle_board(entries,name):
 # All use the SAME native crop, never fit any pose's alpha bounds.
 board=Image.new('RGB',(600,len(entries)*170),(68,67,62));d=ImageDraw.Draw(board)
 for row,(label,path) in enumerate(entries):
  im=Image.open(path).convert('RGBA')
  for facing in range(2):
   actor=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if facing else im
   tile=actor.crop((75,145,375,295));x=facing*300;y=row*170+20
   board.paste(tile,(x,y),tile);d.text((x+4,row*170+3),label+(' L' if facing else ' R'),fill='white')
 board.save(R/'private'/name)
 return pin(R/'private'/name)

def main():
 original=W/'runeterra-demacia/references/frames'
 refs=[original/'csword/g02-f000.png',original/'csword/g05-f005.png',original/'cpkman/g02-f000.png',original/'avwpike/g00-f000.png',original/'avwattak/g00-f000.png']
 attendant=p.PROJECT/'build/reports/painted-draklorn-actions-20261024-v1/draklornAttendant-standing-native-v1.png'
 boards=[]
 boards.append(fixed_battle_board([('Original swordsman',refs[0]),('Original pikeman',refs[2]),('Attendant selected standing',attendant),('Inquisitor selected standing',p.native('standing'))],'native1x-original-pair.png'))
 old=[]
 for key in ['death-fall-v1','death-rest-v1']:
  body,_=p.converted(p.master(key),source_anchor=(780,p.GROUND[key]));im,_=p.shadowed(body,266)
  dest=R/'private'/(key+'-old-native.png');im.save(dest);old.append(dest)
 boards.append(fixed_battle_board([('Standing anatomy authority',p.native('standing')),('Unselected old straight fall',old[0]),('Selected bent-knee fall v3',p.native('death-fall-v3')),('Unselected old straight rest',old[1]),('Selected folded rest v4',p.native('death-rest-v4')),('Original swordsman final corpse',refs[1])],'native1x-death-anatomy-comparison.png'))
 resources=S/'technical-v1/resources-v2'
 entries=[('Original Pike64',refs[3]),('Original attack64',refs[4]),('Map64 root48,60',resources/'map.png'),('Attack right64',resources/'attackRight.png'),('Attack left64',resources/'attackLeft.png'),('Portrait58x64',resources/'large.png'),('Portrait32x32',resources/'small.png')]
 board=Image.new('RGB',(len(entries)*160,112),(68,67,62));d=ImageDraw.Draw(board)
 for i,(label,path) in enumerate(entries):
  x=i*160;im=Image.open(path).convert('RGBA');board.paste(im,(x+40,30),im);d.text((x+2,5),label,fill='white')
  if im.size==(64,64):
   # Actual 32px tile split and same-frame root; overlay only technical review.
   d.rectangle((x+40,30,x+103,93),outline=(120,120,120));d.line((x+72,30,x+72,93),fill=(100,100,100));d.line((x+40,62,x+103,62),fill=(100,100,100))
   if i in (2,3,4):d.point((x+88,90),fill=(255,220,0))
 board.save(R/'private/native1x-resources-original-tileproof.png');boards.append(pin(R/'private/native1x-resources-original-tileproof.png'))
 # Root reflection proof must test actual Pillow pixel semantics, not algebra alone.
 impulse=Image.new('L',(64,64));impulse.putpixel((48,60),255)
 discrete=impulse.transform((64,64),Image.Transform.AFFINE,(-1,0,97,0,1,0),Image.Resampling.NEAREST)
 assert discrete.getbbox()==(48,60,49,61)
 bad=impulse.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 assert bad.getbbox()==(15,60,16,61)
 reflected=Image.open(resources/'attackRight.png').transform((64,64),Image.Transform.AFFINE,(-1,0,97,0,1,0),Image.Resampling.NEAREST)
 assert reflected.tobytes()==Image.open(resources/'attackLeft.png').tobytes()
 bounds=[]
 for key in sorted({k for seq in p.GROUPS.values() for k in seq}):
  path=S/'technical-v1/native/body'/f'{key}.png';im=Image.open(path);box=alpha_bounds(im)
  assert im.size==(450,400) and box and box[0]>0 and box[1]>0 and box[2]<450 and box[3]<400
  bounds.append(dict(pose=key,body_opaque_bounds=box,source_ground_y=p.GROUND.get(key,1000),native_root=[193,266],fixed_scale=.100))
 adv=[]
 for name in ('map','attackRight','attackLeft'):
  im=Image.open(resources/(name+'-body.png'));box=alpha_bounds(im)
  assert im.size==(64,64) and box and box[0]>0 and box[1]>0 and box[2]<64 and box[3]<64
  adv.append(dict(resource=name,body_opaque_bounds=box,canvas=[64,64],root=[48,60],common_scale=.046))
 # Store playback as exact existing native-frame assembly; no interpolated/warped action.
 frames=[]
 for key in p.GROUPS[0]:
  board=Image.new('RGB',(500,200),(68,67,62))
  for face in (0,1):
   im=Image.open(p.native(key));im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if face else im
   tile=im.crop((80,120,330,310));board.paste(tile,(face*250,0),tile)
  frames.append(board)
 frames[0].save(R/'private/native1x-gait-assembly.gif',save_all=True,append_images=frames[1:],duration=150,loop=0)
 consumers=[W/'vcmi-develop/vcmi-develop/client/battle/CreatureAnimation.cpp',W/'vcmi-develop/vcmi-develop/client/battle/BattleAnimationClasses.cpp',W/'vcmi-develop/vcmi-develop/client/mapView/MapRenderer.cpp',W/'scripts/freljord_asset_manifest.py',W/'scripts/faction_art_compile.py']
 compile_record=json.loads((R/'strict-repeat-compile-v1.json').read_text())
 outputs=[];recipes=[]
 for item in compile_record['recipes']:
  assert item['two_plan_runs_identical']
  rp=p.PROJECT/item['recipe'];assert p.sha(rp)==item['receipt']['recipe_sha256'];recipes.append(pin(rp))
  for name,digest in item['outputs'].items():
   path=R/'compiled'/name;assert p.sha(path)==digest;outputs.append(pin(path))
 assert len(recipes)==6 and len(outputs)==55 and len(p.GROUPS[2])==1 and len(p.GROUPS[1])==9
 gait=[
  ('walk-contact-a-v1','Near plated/large-chevron shin leads and contacts; far narrow boot trails.'),
  ('walk-down-a-v1','Near flat boot bears weight; far trailing boot lifts behind.'),
  ('walk-pass-a-v1','Near support rolls toward toe; far knee/boot passes forward in air.'),
  ('walk-contact-b-v1','Far narrow boot leads and contacts; near large-chevron plated shin trails.'),
  ('walk-down-b-v1','Far flat boot bears weight; near plated boot lifts behind.'),
  ('walk-pass-b-v1','Far support rolls toward toe; near plated knee/boot crosses foreground in air.')]
 anatomy=dict(method='Manual landmark projection at exact .100 scale, not opacity fitting; measurements are perspective-dependent and do not prove native motion.',
  standing=dict(helmet_tip_y=182,boot_sole_y=1006,vertical_anatomical_projection_native=82.4),
  unselected_rest_v1=dict(boot_to_helmet_projection_source_approx=[94,1200],native_projection_approx=110.6),
  selected_rest_v4=dict(boot_to_helmet_projection_source_approx=[320,1165],native_projection_approx=84.5,pose='Both knees folded; body side-curl and gathered robe; sourcebodyground750.'),
  selected_fall_v3=dict(boot_to_helmet_projection_source_approx=[200,1075],native_projection_approx=87.5,pose='Bent legs, torso/forearm dropping right; sourceknee/robecontact810.'),
  repairs='Actual built-in painted edits; old straight poses and failed v2/v3 rest candidates preserved. No per-pose scaling; all use .100 and translation-only registration to nativey266.',
  coordinator_source_review='Coordinator viewed repaired native1x-death, considered folded anatomy sufficient for source integration; final artistic/native motion approval remains separate.')
 audit=dict(status='authored configuration',required_contract_weakened=False,selected_battle_pose_count=len(bounds),battle_frame_count=sum(map(len,p.GROUPS.values())),
  body_bounds=bounds,adventure=adv,adventure_reflection=dict(actual_pillow_inverse_coefficient=97,root_impulse_after=[48,60],wholeframe_flip_wrong_root=[15,60],actual_attack_pixels_match=True),
  gait_support_order=[dict(pose=k,visible_support_observation=o) for k,o in gait],gait_evidence='Distinct visible shin/boot, knee and cloth articulation inspected in actual raw masters and native1x-gait board; previewGIF is source assembly only, native motion remains pending.',
  anatomy=anatomy,reference_pins=[pin(x) for x in refs]+[pin(attendant)],consumer_pins=[pin(x) for x in consumers],
  comparisons=boards+[pin(R/('private/native1x-'+n+'.png')) for n in ['gait','idle-guard-turn','death','melee']],
  actual_shared_compiler_recipe_count=len(recipes),actual_checksum_verified_outputs=len(outputs),all_body_and_map_canvas_edges_clear=True,
  active_selection_changed=False,stage_changed=False,native_runtime_verified=False,visual_approval_granted=False)
 p.dump(R/'native-source-audit-v1.json',audit)
 handoff=dict(status='authored configuration',unit='draklornInquisitor',writes_stopped_after_seal=True,standing_master=pin(p.master('standing')),
  report_only_canonical_recipes=recipes,compiled_outputs=outputs,repeat_compile=pin(R/'strict-repeat-compile-v1.json'),
  action_contract=pin(R/'native-action-contract-v1.json'),source_audit=pin(R/'native-source-audit-v1.json'),
  conversion_provenance=pin(S/'technical-v1/fixed-conversion-v1.json'),generation_provenance=pin(S/'technical-v1/generation-provenance-v1.json'),
  technical_scripts=[pin(HERE/'assemble_packet.py'),pin(Path(__file__))],
  all_preserved_raw_action_masters=[pin(x) for x in sorted((S/'actions-v1').glob('*.png'))],
  all_prompts=[pin(x) for x in sorted((S/'prompts-v1').glob('*.json'))],standing_alternatives_preserved=[pin(x) for x in sorted(S.glob('standing-v*.png'))],
  selected_battle_pose_keys=sorted({k for seq in p.GROUPS.values() for k in seq}),groups={str(g):seq for g,seq in p.GROUPS.items()},
  battle_canvas=[450,400],battle_root=[193,266],battle_common_scale=.100,adventure_canvas=[64,64],adventure_root=[48,60],adventure_common_scale=.046,
  visual_approval_granted=False,native_runtime_verified=False,release_accepted=False,active_or_stage_writes=False,
  pending=['Coordinator selection and production integration','Native moving/idle/melee/death/turn timing at both facings','Final artistic and rights/release acceptance'],
  notes=['Living ordinary melee screening/Defend unit; no cast or shooting groups authored.','Group2 one staticstanding, group1 nine heldticks at10FPS; sixframe meleecontactzeroindex3.','All originals, failed candidates and existing standing requests preserved.','Private reference images and generated-tool storage paths remain in private report inputs/receipts.'])
 p.dump(R/'coordinator-handoff-final-v1.json',handoff)
 print(json.dumps(dict(recipes=len(recipes),outputs=len(outputs),raw_action_masters=len(handoff['all_preserved_raw_action_masters']),handoff_sha256=p.sha(R/'coordinator-handoff-final-v1.json'))))
if __name__=='__main__':main()
