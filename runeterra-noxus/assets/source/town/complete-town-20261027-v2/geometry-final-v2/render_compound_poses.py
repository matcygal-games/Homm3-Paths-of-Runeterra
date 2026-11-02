"""Compound unchanged-source translations for coordinator/source-owner review."""
from pathlib import Path
from PIL import Image, ImageChops
import hashlib,json,argparse
HERE=Path(__file__).resolve().parent
TOWN=HERE.parent
ROOT=HERE.parents[4]
def load(path):return json.loads(path.read_text(encoding='utf8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',default='compound-pose-proposal-v1');parser.add_argument('--lower-scales',action='store_true');parser.add_argument('--hall-fit',action='store_true');parser.add_argument('--lower-ground',action='store_true');args=parser.parse_args()
    if not args.attempt.replace('-','').isalnum():raise ValueError('Simple attempt name required')
    REPORT=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2'/args.attempt
    REPORT.mkdir(parents=True,exist_ok=False)
    selection=load(TOWN/'candidate-final-v5/selection.json')
    rows={row['state']:row for row in selection['states']}
    sites={site['id']:site for site in selection['sites']}
    entries={row['state']:row for row in load(TOWN/'entry-spans-v2/entries.json')['states']}
    transforms={'dwellingRose':[9,0],'dwellingLegion':[11,-10],'grandMarket':[11,-19]}
    scales={}
    if args.lower_scales:
        transforms.update(foundry=[0,-22],dwellingCrimson=[-10,-21]);scales.update(foundry=0.85,dwellingCrimson=0.88)
    if args.hall_fit:
        transforms.update(trifarianHall=[8,-1]);scales.update(trifarianHall=0.90)
    original={state:Image.open(ROOT/row['native_layer']).convert('RGBA')for state,row in rows.items()}
    layers={};roots={};doors={};before_roots={}
    def move(image,offset):
        result=Image.new(image.mode,image.size)
        result.paste(image,tuple(offset))
        return result
    def alpha(image,threshold):return image.getchannel('A').point(lambda value:255 if value>=threshold else 0)
    def union(images):
        result=Image.new('L',(800,374))
        for image in images:result=ImageChops.lighter(result,image)
        return result
    family_boxes={sid:union([alpha(original[state],8)for state in site['states']]).getbbox()for sid,site in sites.items()}
    def rescale(image,sid):
        if sid not in scales:return image
        box=family_boxes[sid];scale=scales[sid];pivot=((box[0]+box[2])/2,box[3]);size=(round((box[2]-box[0])*scale),round((box[3]-box[1])*scale));origin=(round(pivot[0]+(box[0]-pivot[0])*scale),round(pivot[1]+(box[1]-pivot[1])*scale));result=Image.new(image.mode,image.size);result.paste(image.crop(box).resize(size,Image.Resampling.LANCZOS if image.mode=='RGBA'else Image.Resampling.NEAREST),origin);return result
    for state,row in rows.items():
        if sha(ROOT/row['native_layer'])!=row['native_layer_sha256']:raise ValueError('Frozen source changed '+state)
        offset=transforms.get(row['site'],[0,0])
        layers[state]=move(rescale(original[state],row['site']),offset)
        before_roots[state]=Image.open(TOWN/'physical-v10'/state/'foundation.png').convert('L')
        roots[state]=move(rescale(before_roots[state],row['site']),offset)
        doors[state]=move(rescale(Image.open(ROOT/entries[state]['mask']['path']).convert('L'),row['site']),offset)
    backgrounds={'original':Image.open(ROOT/selection['terrain']['native']).convert('RGBA'),'approved-upper':Image.open(TOWN/'terrain-repairs-v6/upper-left-proposal/terrain-recomposed-v5.png').convert('RGBA')}
    background=backgrounds['approved-upper'].copy();full=None
    if args.lower_ground:
        lower=Image.open(TOWN/'terrain-repairs-v6/lower-proposal/terrain-proposal-v1.png').convert('RGBA')
        for box in ((0,310,235,374),(590,321,800,374)):background.paste(lower.crop(box),box[:2])
    background.save(REPORT/'review-background.png')
    for mode in ('full','base'):
        chosen=[site['states'][0]if mode=='base'else site['top']for site in selection['sites']if site['id']not in ('coast','grail')]
        for label,frames in [('before',original),('after',layers)]:
            scene=background.copy()
            for state in sorted(chosen,key=lambda state:rows[state]['native_z']):scene.alpha_composite(frames[state])
            scene.save(REPORT/(mode+'-'+label+'.png'))
            if mode=='full'and label=='after':full=scene
    body={sid:union([alpha(layers[state],128)for state in site['states']])for sid,site in sites.items()}
    old_body={sid:union([alpha(original[state],128)for state in site['states']])for sid,site in sites.items()}
    root={sid:union([roots[state]for state in site['states']])for sid,site in sites.items()}
    old_root={sid:union([before_roots[state]for state in site['states']])for sid,site in sites.items()}
    conflicts=[]
    for rear,r in rows.items():
        for front,f in rows.items():
            if r['site']==f['site']or r['native_z']>=f['native_z']:continue
            hit=ImageChops.multiply(doors[rear],alpha(layers[front],128))
            if hit.getbbox():conflicts.append({'rear':rear,'front':front,'entry_pixels':hit.histogram()[255],'bbox':hit.getbbox()})
    pairs=[]
    for sid,rear in sites.items():
        for fid,front in sites.items():
            if rear['native_z']>=front['native_z']:continue
            hit=ImageChops.multiply(root[sid],body[fid])
            old=ImageChops.multiply(old_root[sid],old_body[fid])
            if not hit.getbbox():continue
            row={'behind':sid,'front':fid,'pixels':hit.histogram()[255],'bbox':hit.getbbox(),'new_pair':old.getbbox()is None,'previous_pixels':old.histogram()[255]}
            pairs.append(row)
            if row['new_pair']:
                folder=REPORT/'new-root-cases'/(sid+'--'+fid)
                folder.mkdir(parents=True)
                hit.save(folder/'intersection.png')
                absent=background.copy()
                for site in sorted(selection['sites'],key=lambda site:site['native_z']):
                    if site['id']not in ('coast','grail',fid):absent.alpha_composite(layers[site['top']])
                absent.save(folder/'front-absent.png');full.save(folder/'full.png')
                overlay=full.copy();tint=Image.new('RGBA',full.size,(0,255,255,0));tint.putalpha(hit);overlay.alpha_composite(tint);overlay.save(folder/'intersection-overlay.png')
                bb=hit.getbbox();crop=(max(0,bb[0]-10),max(0,bb[1]-10),min(800,bb[2]+10),min(374,bb[3]+10));overlay.crop(crop).resize(((crop[2]-crop[0])*8,(crop[3]-crop[1])*8),Image.Resampling.NEAREST).save(folder/'intersection8x.png')
    support=Image.open(ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2/pose-fits-v2/fixed-actual-level-support.png').convert('L')
    from PIL import ImageDraw
    ImageDraw.Draw(support).rectangle((710,150,724,158),fill=255)
    if args.lower_ground:support=ImageChops.lighter(support,Image.open(HERE/'proposal-lower-v1/independently-traced-new-level-floors.png').convert('L'))
    positives=[]
    for sid in dict.fromkeys(('dwellingLegion','grandMarket',*scales,*(['gildedCup','foundry']if args.lower_ground else []))):
        gap=ImageChops.subtract(root[sid],support)
        source_union=union([alpha(layers[state],8)for state in sites[sid]['states']]);positives.append({'site':sid,'root_union_pixels':root[sid].histogram()[255],'unsupported_pixels':gap.histogram()[255],'bbox':root[sid].getbbox(),'transformed_root_pixels_outside_actual_source_alpha8':ImageChops.subtract(root[sid],source_union).histogram()[255]})
    result={'status':'design proposal','transforms':transforms,'scales':scales,'source_selection_sha256':sha(TOWN/'candidate-final-v5/selection.json'),'renderer_sha256':sha(Path(__file__)),'source_art_parts_preserved':True,'source_resize_method':'Whole common-family canvas crop, uniform ratio rounded to native dimensions, RGBA LANCZOS; roots/entries transformed together at NEAREST. Actual scaled root tracing still required.','compound_entry_conflicts':conflicts,'supported_families_on_fixed_floor':positives,'root_projection_pairs':pairs,'new_root_projection_pairs':[row for row in pairs if row['new_pair']],'actual_approach_routes_verified':False,'whole_town_support_verified':False,'stage_selected':False,'native_executed':False,'release_accepted':False}
    (REPORT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
