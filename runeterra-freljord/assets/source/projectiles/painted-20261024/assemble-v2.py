"""Convert two genuine painted masters to native angle frames; no artwork synthesis."""
from pathlib import Path
import hashlib
import io
import json
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'scripts'))
from faction_art_compile import create_compiler


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    report = ROOT / 'build/reports/roster-revision-20261024-v1/projectiles-v2-matched-seer'
    report.mkdir(parents=True, exist_ok=True)
    requests = json.loads((SOURCE / 'requests-v2.json').read_text())['requests']
    compiler = create_compiler('freljord')
    receipts = []
    board = Image.new('RGBA', (240, 96), (70, 65, 58, 255))
    for row, (name, bounds, extent) in enumerate((
        ('seerRitual', (213, 566, 1044, 737), (18, 6)),
        ('rimewakeCall', (349, 417, 1173, 630), (30, 12)),
    )):
        master = SOURCE / ('seerRitual-splinter-master-v2.png' if name == 'seerRitual' else name + '-master.png')
        image = Image.open(master).convert('RGBA')
        # One fixed crop preserves the complete visible missile while excluding
        # alpha<16 distant generator haze. Every orientation shares this crop.
        actor = image.crop(bounds)
        actor.thumbnail(extent, Image.Resampling.LANCZOS)
        horizontal = Image.new('RGBA', (48, 48))
        horizontal.alpha_composite(actor, ((48-actor.width)//2, (48-actor.height)//2))
        frames = []
        for index, angle in enumerate((90, 45, 0, -45, -90)):
            frame = horizontal.rotate(angle, resample=Image.Resampling.BICUBIC)
            path = SOURCE / (name + '-direction-' + str(index) + '.png')
            frame.save(path)
            board.alpha_composite(frame, (index*48, row*48))
            frames.append({'source': path.relative_to(ROOT).as_posix(), 'source_sha256': digest(path), 'source_canvas': [48, 48]})
        req = next(req for req in requests if req['unit'] == name)
        recipe = {
            'recipe_type': 'vcmi_animation', 'output_path': 'Content/Sprites/runeterra/freljord/projectiles/' + name + '.json',
            'role': 'projectile-animation', 'canvas': [48,48], 'pivot': {'x':24,'y':24},
            'groups': [{'group':0,'frames':frames}], 'generateOverlay':0,'generateShadow':0,
            'production_status':'painted-master-complete-unapproved','visual_approval_granted':False,
            'credits':{'author':'Project-directed OpenAI built-in imagegen; technical conversion by Codex','license':'not reviewed','redistribution':'unresolved; release prohibited'},
            'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','prompt':req['prompt'],
                'painted_master':master.relative_to(ROOT).as_posix(),'painted_master_sha256':digest(master),
                'conversion':{'method':'Fixed crop of own painted projectile, uniform downsample and centered angle rotations','crop':list(bounds),'visible_extent':list(extent),'frame_angles':[90,45,0,-45,-90],'animation_in_time':False},
                'damage_semantics':'Project ritual fiction; native physical single-target hit. No spell-school, area, freeze or free summons.','native_visual_review':'pending','release_accepted':False}
        }
        path = ROOT / ('assets/recipes/projectiles/painted-20261024/' + name + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n')
        first, receipt = compiler.plan(ROOT,path)
        second, _ = compiler.plan(ROOT,path)
        assert first == second and len(first)==6
        for output, raw in first.items():
            target=report/'compiled'/output;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        receipts.append({'unit':name,'repeat_byte_equal':True,'expanded_files':len(first),'receipt':receipt})
    board.save(report/'directions-native-1x.png')
    (report/'strict-conversion.json').write_text(json.dumps(receipts,indent=2)+'\n')
    print('Two projectile recipes: 12 real shared-compiler outputs, repeat byte-equal; native review pending')


if __name__ == '__main__':
    run()
