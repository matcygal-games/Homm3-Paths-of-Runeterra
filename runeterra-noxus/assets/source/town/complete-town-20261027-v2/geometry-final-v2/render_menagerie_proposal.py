"""Render only review proposals for a whole-family source translation."""
from pathlib import Path
from PIL import Image, ImageChops
import argparse, hashlib, json
HERE = Path(__file__).resolve().parent
TOWN = HERE.parent
ROOT = HERE.parents[4]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text(encoding='utf8'))
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dx', type=int, required=True)
    parser.add_argument('--dy', type=int, default=0)
    parser.add_argument('--attempt', required=True)
    args = parser.parse_args()
    if not args.attempt.replace('-', '').isalnum(): raise ValueError('Simple attempt name required')
    report = ROOT / 'build/reports/complete-town-20261027-v2/geometry-final-v2' / args.attempt
    report.mkdir(parents=True, exist_ok=False)
    selection = load(TOWN/'candidate-final-v5/selection.json')
    rows = {row['state']:row for row in selection['states']}
    sites = {site['id']:site for site in selection['sites']}
    entries = {row['state']:row for row in load(TOWN/'entry-spans-v2/entries.json')['states']}
    layers = {state:Image.open(ROOT/row['native_layer']).convert('RGBA') for state,row in rows.items()}
    for state,row in rows.items():
        if sha(ROOT/row['native_layer']) != row['native_layer_sha256']: raise ValueError('Frozen frame changed '+state)
    def shift(image):
        result = Image.new(image.mode,image.size)
        result.paste(image,(args.dx,args.dy))
        return result
    def alpha(image, threshold): return image.getchannel('A').point(lambda value:255 if value>=threshold else 0)
    def union(images):
        result = Image.new('L',(800,374))
        for image in images: result=ImageChops.lighter(result,image)
        return result
    moved = dict(layers)
    for state in sites['dwellingRose']['states']: moved[state]=shift(layers[state])
    background_path=TOWN/'terrain-repairs-v6/upper-left-proposal/terrain-recomposed-v5.png'
    background=Image.open(background_path).convert('RGBA')
    scenes={}
    for mode in ('full','base'):
        chosen=[site['states'][0] if mode=='base' else site['top'] for site in selection['sites'] if site['id'] not in ('coast','grail')]
        for suffix,frames in [('before',layers),('after',moved)]:
            scene=background.copy()
            for state in sorted(chosen,key=lambda key:rows[key]['native_z']):scene.alpha_composite(frames[state])
            scene.save(report/(mode+'-'+suffix+'.png'))
            scenes[mode+'-'+suffix]=scene
        scenes[mode+'-after'].crop((410,115,710,210)).resize((1200,380),Image.Resampling.NEAREST).save(report/(mode+'-castle-menagerie-barracks4x.png'))
    rear_roots=union([Image.open(TOWN/'physical-v10'/state/'foundation.png').convert('L') for state in sites['dwellingLegion']['states']])
    front_body=union([alpha(moved[state],128) for state in sites['dwellingRose']['states']])
    hidden=ImageChops.multiply(rear_roots,front_body)
    hidden.save(report/'new-legion-root-intersection.png')
    without_front=background.copy()
    for site in sorted(selection['sites'],key=lambda site:site['native_z']):
        if site['id'] not in ('coast','grail','dwellingRose'):without_front.alpha_composite(moved[site['top']])
    without_front.save(report/'new-legion-root-front-absent.png')
    overlay=scenes['full-after'].copy()
    tint=Image.new('RGBA',overlay.size,(0,255,255,0));tint.putalpha(hidden);overlay.alpha_composite(tint)
    overlay.save(report/'new-legion-root-overlay.png')
    overlay.crop((575,135,610,180)).resize((350,450),Image.Resampling.NEAREST).save(report/'new-legion-root-overlay10x.png')
    door=Image.open(ROOT/entries['castle']['mask']['path']).convert('L')
    mask8=union([alpha(moved[state],8) for state in sites['dwellingRose']['states']])
    case={'status':'design proposal','whole_family_offset':[args.dx,args.dy],'source_selection_sha256':sha(TOWN/'candidate-final-v5/selection.json'),'background_sha256':sha(background_path),'renderer_sha256':sha(Path(__file__)),'castle_entry_vs_shifted_family_alpha128':ImageChops.multiply(door,front_body).histogram()[255],'castle_entry_vs_shifted_family_alpha8':ImageChops.multiply(door,mask8).histogram()[255],'new_legion_root_pair':{'pixels':hidden.histogram()[255],'bbox':hidden.getbbox()},'source_art_modified':False,'stage_published':False,'final_level_support':'Requires genuine floor repair and independent trace of final merged terrain.','full_town_admitted':False}
    (report/'receipt.json').write_text(json.dumps(case,indent=2)+'\n')
    print(json.dumps(case))
if __name__=='__main__':main()
