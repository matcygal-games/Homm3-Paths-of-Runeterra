"""Exact project-owned prompts for remaining genuine Dragonguard actions."""
from pathlib import Path
import json

PROJECT = Path(__file__).resolve().parents[3]
PILOTS = json.loads((PROJECT / 'assets/source/creatures/dragonguard-family-generation-inputs-v1.json').read_text())
ACTIONS = {
 1: 'Exactly FOUR actual FIDGET phases,2columns x2rows,row-major. Keep both hands gripping one shaft while he briefly checks/shifts its diagonal carry angle, then returns ready. Preserve the guide actual subtle head/arm/shaft motion; not four unrelated idle designs or random texture changes.',
 3: 'Exactly FOUR actual HIT/RECOIL phases,2columns x2rows,row-major: ready, upper body recoils from a blow with actual shoulders/head/shaft moving back, settle, return ready. Both hands retain the same polearm; no blood splash, lost weapon, extra attack, flying limb or idle substitution.',
 4: 'Exactly FOUR actual DEFEND/BRACE phases,2columns x2rows,row-major: ready, lower centre of gravity and brace with the long shaft butt near the floor, hold the real protected two-handed stance, return ready. Preserve actual knees/hips/hand/shaft positions. This is anti-charge polearm infantry, no shield, forcefield, magic circle or attack swing.',
 5: 'Exactly SIX real DEATH phases,3columns x2rows,row-major: standing ready, wounded stagger, legs buckle/crouch with lowered weapon, whole body falls forward, nearly-prone landing, final clearly DEAD prone grounded corpse. Preserve true full body/leg orientation from the guide. Final body and both legs lie down naturally, helmet stays on, polearm lies flat along the floor beside the corpse. All corpse, boots, blade and butt entirely inside its own cell; no last standing idle or repeated fall. No gore or detached body parts.',
 7: 'Exactly FOUR actual TURN-TOWARD-VIEWER phases,2columns x2rows,row-major. Preserve actual gradual full-body yaw from initial three-quarter facing right toward front, including pelvis/boots/shoulders/helmet and rigid polearm foreshortening. Both hands stay at their proper grips. Not four side-on idles or a repeated body with a different head.',
 8: 'Exactly FOUR actual TURN-BACK phases,2columns x2rows,row-major. Preserve actual gradual full-body yaw from front back to the default right-facing three-quarter battle stance, including pelvis/boots/shoulders/helmet and polearm foreshortening. Both hands stay at their proper grips. No extra weapon or faux walking action.',
 11: 'Exactly SIX actual UPPER-DIRECTION single POLEARM THRUST phases,3columns x2rows,row-major:0diagonal ready,1draw back,2load and aim upper/right,3ONE genuine forward/upward thrust reaching maximum extension and impact in the FOURTH cell(zero-based3),4recover,5return ready. Preserve actual guide projection and elevated target direction; both real hands on ONE rigid shaft, actual arm/torso/leg articulation. No overhead axe chop, spinning pole, projectile, magic or duplicate idle.',
 13: 'Exactly SIX actual LOWER-DIRECTION single POLEARM THRUST phases,3columns x2rows,row-major:0diagonal ready,1draw back,2load,3ONE genuine downward/right thrust reaching maximum extension toward a lower adjacent target in FOURTH cell(zero-based3),4recover,5return ready. Preserve actual guide projection and clearly lowered blade at impact; both real hands on ONE rigid shaft with actual arm/torso/leg articulation. No overhead axe chop, spinning pole, projectile, magic or duplicate idle.',
}
jobs = []
for unit in ('dragonguard', 'veteranDragonguard'):
    pilot = next(item for item in PILOTS if item['unit'] == unit and item['group'] == 2)
    identity = pilot['prompt'].split('IDENTITY: ')[1].split('\nWeapon geometry:')[0]
    folder = PROJECT / 'assets/source/creatures' / unit / 'dragonguard-rig-v3'
    for group, action in ACTIONS.items():
        transform = json.loads((folder / f'raw-action-g{group:02}-padding-transform-v1.json').read_text())
        columns, rows = transform['layout']
        refs = [transform['output'], (folder / 'paint-action-g02-atlas-v1.png').relative_to(PROJECT).as_posix(),
            f'assets/source/creatures/{unit}/master-v1.png',
            'references/prototypes/dragonguard-family-v3/castle-grounded-polearm-native-style-v1.png',
            'references/riot/heraldry/demacia-official-region-icon.png']
        prompt = f'''Use case: style-transfer / identity-preserve.
Asset: OWN original HeroesIII-compatible transparent painted creature animation SOURCE atlas, {unit} g{group:02}.
Inputs: IMAGE1 is the ACTUAL EDIT TARGET, genuine articulated volumetric 3D action poses with executed420px-in512px common padding. IMAGE2 is the FIRST ALREADY-PAINTED SAME FAMILY miniature: lock its anatomy, equipment identity, full refined polearm, matte materials and palette. IMAGE3 is OUR OWN full character/equipment master. IMAGE4 contains private ORIGINAL CASTLE sprites for MATERIAL/LIGHT/PERSPECTIVE STYLE ONLY, do not copy their men, outfits, silhouettes, poleheads or pixels. IMAGE5 is official Demacia crest SHAPE reference only.
Primary request: paint the SAME MAN from IMAGE2/3 into EVERY actual articulated action pose of IMAGE1. Preserve exact pose count and row-major order, fixed orthographic right-facing three-quarter battle camera, upper-left warm light and transparent gutters. Output {columns*512}x{rows*512} RGBA; exactly{columns}equal columns by{rows}equal rows, one FULL figure per cell. Keep complete helmet, boots, cape, polearm blade and long butt within its cell. Do not zoom/recenter individual poses, merge cells, add figures or crop weapons.
ACTION: {action}
IDENTITY: {identity}
Weapon: ONE long rigid petricite polearm from IMAGE2/3 with BOTH real gauntleted hands at proper separated positions on ONE unbroken shaft. Coherent shaft length and refined head shape across the action, no extra hand, separated handle, detached blade, floating tip or neighboring cell leak. Replace only the primitive guide blade with the genuine finished master weapon, preserve actual action/shaft axis and whole physical figure.
Heraldry: visible broad navy chest/tabard carries pale-gold official Demacia shape from IMAGE5: one tallest broad upright central blade/leaf with tapering downward stem and paired descending feathered wings. Same location and shape, naturally occluded in turned/prone poses. No flower/trident/invented emblem.
Style: original1999HeroesIII richly painted/prerendered compact adult miniature; textured but restrained worn steel/pale petricite, matte navy cloth, readable chain/leather, subtle gold, dark underside. Natural sturdy anatomy and shoulder/neck/hand joints, not mechanical blocks or random noisy spots. Eventual native human height80px(base)/84px(veteran), no modern splashart, anime, glossy3D, giant mobile-game proportions or arbitrary pixel filter.
Background: GENUINELY TRANSPARENT alpha throughout, clean cutout edges. No visible backdrop, colored halo, floor plane, shadows baked into surrounding empty canvas, labels, grid, border, checkerboard painting, text, extra figures or watermark. This is unapproved source action finishing, not native/release acceptance. Preserve genuine motion; never replace complete actions with copied idle or random texture jitter.'''
        prompt_path = folder / f'paint-action-g{group:02}-atlas-v1-executed-prompt.txt'
        if prompt_path.exists() and prompt_path.read_text(encoding='utf-8') != prompt:
            raise ValueError(f'Preserve previous executed prompt: {prompt_path}')
        prompt_path.write_text(prompt, encoding='utf-8')
        jobs.append({'unit': unit, 'group': group, 'folder': folder.relative_to(PROJECT).as_posix(), 'layout': [columns, rows],
            'refs': refs, 'prompt': prompt, 'promptPath': prompt_path.relative_to(PROJECT).as_posix(),
            'atlas_metadata': (folder / f'raw-action-g{group:02}-padding-transform-v1.json').relative_to(PROJECT).as_posix()})
(PROJECT / 'assets/source/creatures/dragonguard-family-remaining-generation-inputs-v1.json').write_text(json.dumps(jobs, indent=2) + '\n', encoding='utf-8')
print(f'Prepared{len(jobs)} distinct genuine action finishing prompts; not executed by this script.')
