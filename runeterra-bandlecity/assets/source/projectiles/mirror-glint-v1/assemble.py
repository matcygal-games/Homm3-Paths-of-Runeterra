"""Technical five-angle assembly of an original transparent painted missile.

One symmetric whole-source camera preserves the original alpha and centers the
opaque shard; no procedural painting, alpha keying or per-angle fitting.
"""
from pathlib import Path
import hashlib
import json
import math
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    master = HERE / 'master.png'
    with Image.open(master) as opened:
        image = opened.convert('RGBA')
    alpha = image.getchannel('A')
    body = alpha.point(lambda a: 255 if a >= 128 else 0).getbbox()
    whole = alpha.getbbox()
    if not body or not whole or alpha.getextrema()[0] != 0:
        raise ValueError('Intact transparent painted master required')
    cx, cy = (body[0]+body[2])/2, (body[1]+body[3])/2
    radius = math.ceil(max(cx-whole[0], whole[2]-cx, cy-whole[1], whole[3]-cy)) + 2
    crop = [round(cx-radius), round(cy-radius), round(cx+radius), round(cy+radius)]
    # Padding is transparent outside the source. All nonzero source alpha stays.
    reduced = image.crop(crop).resize((34,34), Image.Resampling.LANCZOS)
    base = Image.new('RGBA', (48,48))
    base.alpha_composite(reduced, (7,7))
    receipt = json.loads((HERE/'generation.json').read_text(encoding='utf8'))
    receipt.update({'painted_master':master.relative_to(ROOT).as_posix(),
                    'painted_master_sha256':SHA(master), 'source_canvas':list(image.size),
                    'source_crop':crop, 'body_bbox_alpha128':list(body),
                    'conversion':'Whole-source symmetric fixed camera, alpha-preserving downsample and static angle rotation',
                    'projectile_feature_pixel':[24,24]})
    (HERE/'generation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    frames=[]
    for i, angle in enumerate((90,45,0,-45,-90)):
        frame=base.rotate(angle,resample=Image.Resampling.BICUBIC,expand=False,center=(24,24))
        target=HERE/f'direction-{i:02}.png';frame.save(target,compress_level=9)
        frames.append({'source':target.relative_to(ROOT).as_posix(), 'source_sha256':SHA(target),
                       'source_canvas':[48,48], 'frame':i})
    for unit in ('mirrorMage','mirrorArchmage'):
        recipe={'recipe_type':'vcmi_animation','role':'projectile-animation',
                'canvas':[48,48],'pivot':{'x':24,'y':24},'generateOverlay':0,'generateShadow':0,
                'production_status':'painted-master-complete-unapproved','visual_approval_granted':False,
                'generation':receipt,'groups':[{'group':0,'frames':frames}],
                'output_path':f'Content/Sprites/runeterra/bandlecity/projectiles/{unit}.json'}
        path=ROOT/f'assets/recipes/projectiles/{unit}.json';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(recipe,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'recipes':2,'angles':5,'master_sha256':SHA(master),'accepted':False}))


if __name__ == '__main__':
    main()
