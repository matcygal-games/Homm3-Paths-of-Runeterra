"""Bounded whole-family pose proposals on independently traced fixed floors.
No art, canonical placement, annotation or stage is changed.
"""
from pathlib import Path
from PIL import Image, ImageChops
import argparse, hashlib, json
import numpy as np
HERE = Path(__file__).resolve().parent
TOWN = HERE.parent
ROOT = HERE.parents[4]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text(encoding='utf8'))
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--attempt',required=True)
    parser.add_argument('--entries',default='entry-spans-v2')
    parser.add_argument('--scales',default='1')
    parser.add_argument('--radius',type=int,default=40)
    parser.add_argument('--sites',default='dwellingLegion,gildedCup,foundry,grandMarket,dwellingCrimson')
    parser.add_argument('--forbid-root-pairs',default='')
    parser.add_argument('--fixed-poses')
    args=parser.parse_args()
    forbidden_pairs={tuple(value.split(':'))for value in args.forbid_root_pairs.split(',')if value}
    if not args.attempt.replace('-','').isalnum():raise ValueError('Simple attempt name required')
    report=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2'/args.attempt
    report.mkdir(parents=True,exist_ok=False)
    selection=load(TOWN/'candidate-final-v5/selection.json')
    rows={row['state']:row for row in selection['states']}
    sites={site['id']:site for site in selection['sites']}
    entries={row['state']:row for row in load(TOWN/args.entries/'entries.json')['states']}
    def blank():return Image.new('L',(800,374))
    def union(images):
        result=blank()
        for image in images:result=ImageChops.lighter(result,image)
        return result
    def alpha(image,threshold):return image.getchannel('A').point(lambda value:255 if value>=threshold else 0)
    def move(image,dx,dy):
        result=Image.new(image.mode,image.size)
        result.paste(image,(dx,dy))
        return result
    layers={state:Image.open(ROOT/row['native_layer']).convert('RGBA') for state,row in rows.items()}
    state_roots={state:Image.open(TOWN/'physical-v10'/state/'foundation.png').convert('L') for state in rows}
    state_doors={state:Image.open(ROOT/entries[state]['mask']['path']).convert('L') for state in rows}
    for state,row in rows.items():
        if sha(ROOT/row['native_layer'])!=row['native_layer_sha256']:raise ValueError('Frozen frame changed '+state)
    # Proposed whole-family poses, independently reviewed separately.
    fixed_poses={'dwellingRose':[9,0]}
    if args.fixed_poses:
        path=(HERE/args.fixed_poses).resolve()
        if not path.is_relative_to(HERE):raise ValueError('Fixed pose proposal must remain in owned source tree')
        fixed_poses=load(path)
    for sid,offset in fixed_poses.items():
        for state in sites[sid]['states']:
            layers[state]=move(layers[state],*offset)
            state_roots[state]=move(state_roots[state],*offset)
            state_doors[state]=move(state_doors[state],*offset)
    def pack(image):return (np.asarray(image)>0,image.getbbox())
    def overlap(moved,other,dx=0,dy=0):
        array,box=moved;other_array,other_box=other
        left,top=max(box[0]+dx,other_box[0],0),max(box[1]+dy,other_box[1],0)
        right,bottom=min(box[2]+dx,other_box[2],800),min(box[3]+dy,other_box[3],374)
        if left>=right or top>=bottom:return 0
        return int(np.count_nonzero(array[top-dy:bottom-dy,left-dx:right-dx]&other_array[top:bottom,left:right]))
    body_images={sid:union([alpha(layers[state],128)for state in site['states']])for sid,site in sites.items()}
    root_images={sid:union([state_roots[state]for state in site['states']])for sid,site in sites.items()}
    door_images={sid:union([state_doors[state]for state in site['states']])for sid,site in sites.items()}
    silhouette_images={sid:union([alpha(layers[state],8)for state in site['states']])for sid,site in sites.items()}
    bodies={sid:pack(image)for sid,image in body_images.items()}
    roots={sid:pack(image)for sid,image in root_images.items()}
    doors={sid:pack(image)for sid,image in door_images.items()}
    support=Image.open(HERE/'support.png').convert('L')
    support=ImageChops.lighter(support,Image.open(HERE/'proposal-upper-v5/independently-traced-level-floor.png').convert('L'))
    # Independent source-pixel reviewer classified this native stone-cap strip.
    cap=blank()
    from PIL import ImageDraw
    ImageDraw.Draw(cap).polygon([(439,336),(449,337),(461,341),(474,344),(486,346),(486,349),(474,348),(461,345),(449,342),(439,339)],fill=255)
    ImageDraw.Draw(cap).rectangle((710,150,724,158),fill=255)
    support=ImageChops.lighter(support,cap)
    support.save(report/'fixed-actual-level-support.png')
    support_array=np.asarray(support)>0
    baseline_pairs=set()
    for rear,rsite in sites.items():
        for front,fsite in sites.items():
            if rsite['native_z']<fsite['native_z'] and overlap(roots[rear],bodies[front]):baseline_pairs.add((rear,front))
    targets=args.sites.split(',')
    print('Actual source site IDs: '+str(list(sites)))
    # Canonical regional site IDs, never invented gameplay identifiers.
    targets=[sid for sid in targets if sid in sites]
    scales=[float(value)for value in args.scales.split(',')]
    results=[]
    offsets=sorted([(dx,dy)for dx in range(-args.radius,args.radius+1)for dy in range(-args.radius,args.radius+1)],key=lambda point:(point[0]**2+point[1]**2,abs(point[0])+abs(point[1]),abs(point[1]),point[0],point[1]))
    for target in targets:
        target_results=[]
        original_box=silhouette_images[target].getbbox()
        pivot=((original_box[0]+original_box[2])/2,original_box[3])
        for scale in scales:
            if scale < 1 and any(row['supported_and_entry_clear_count'] for row in target_results):break
            width=round((original_box[2]-original_box[0])*scale)
            height=round((original_box[3]-original_box[1])*scale)
            origin=(round(pivot[0]+(original_box[0]-pivot[0])*scale),round(pivot[1]+(original_box[1]-pivot[1])*scale))
            def transformed(image):
                result=blank()
                resized=image.crop(original_box).resize((width,height),Image.Resampling.NEAREST)
                result.paste(resized,origin)
                return result
            root_image=transformed(root_images[target]);door_image=transformed(door_images[target]);scaled_sources=[]
            for state in sites[target]['states']:
                native=Image.new('RGBA',(800,374));native.paste(layers[state].crop(original_box).resize((width,height),Image.Resampling.LANCZOS),origin);scaled_sources.append(native)
            body_image=union([alpha(native,128)for native in scaled_sources]);silhouette=union([alpha(native,8)for native in scaled_sources])
            moved_root,moved_body,moved_door=map(pack,(root_image,body_image,door_image))
            ys,xs=np.nonzero(np.asarray(root_image)>0)
            box=silhouette.getbbox()
            supported_count=0;entry_clear=[];blocked=[]
            for dx,dy in offsets:
                if not(0<=box[0]+dx<box[2]+dx<=800 and 0<=box[1]+dy<box[3]+dy<=374):continue
                if not support_array[ys+dy,xs+dx].all():continue
                supported_count+=1
                conflicts=[];pairs=[]
                for sid,site in sites.items():
                    if sid==target:continue
                    if site['native_z']<sites[target]['native_z']:
                        count=overlap(moved_body,doors[sid],dx,dy)
                        if count:conflicts.append({'rear':sid,'front':target,'entry_pixels':count})
                        count=overlap(moved_body,roots[sid],dx,dy)
                        if count:pairs.append({'behind':sid,'front':target,'pixels':count})
                    elif site['native_z']>sites[target]['native_z']:
                        count=overlap(moved_door,bodies[sid],dx,dy)
                        if count:conflicts.append({'rear':target,'front':sid,'entry_pixels':count})
                        count=overlap(moved_root,bodies[sid],dx,dy)
                        if count:pairs.append({'behind':target,'front':sid,'pixels':count})
                if conflicts:
                    if len(blocked)<5:blocked.append({'scale':scale,'dx':dx,'dy':dy,'distance_squared':dx*dx+dy*dy,'entry_conflicts':conflicts})
                    continue
                if any((row['behind'],row['front'])in forbidden_pairs for row in pairs):continue
                new_pairs=[row for row in pairs if(row['behind'],row['front'])not in baseline_pairs]
                entry_clear.append({'scale':scale,'pivot':list(pivot),'resized_full_family_canvas_rectangle':[origin[0]+dx,origin[1]+dy,width,height],'dx':dx,'dy':dy,'distance_squared':dx*dx+dy*dy,'all_root_pixels_supported':True,'root_pixels':len(xs),'all_target_entry_conflicts':[],'root_projection_pairs':pairs,'new_root_projection_pairs':new_pairs})
            target_results.append({'scale':scale,'fully_supported_candidate_count':supported_count,'supported_and_entry_clear_count':len(entry_clear),'closest_supported_and_entry_clear':entry_clear[:10],'closest_without_new_root_pairs':[row for row in entry_clear if not row['new_root_projection_pairs']][:5],'closest_supported_but_entry_blocked':blocked})
        record={'site':target,'states':sites[target]['states'],'scales':target_results}
        results.append(record)
        print(json.dumps({'site':target,'results':[{'scale':row['scale'],'support':row['fully_supported_candidate_count'],'entry_clear':row['supported_and_entry_clear_count'],'best':row['closest_supported_and_entry_clear'][:1]}for row in target_results]}),flush=True)
    result={'status':'design proposal','selection_sha256':sha(TOWN/'candidate-final-v5/selection.json'),'entries_sha256':sha(TOWN/args.entries/'entries.json'),'fixed_support_sha256':sha(report/'fixed-actual-level-support.png'),'background_context':'CurrentV5 with approved upper-left proposalV5; independent bounded cap classification added. Menagerie whole-family+9 proposed and fixed as another source body.','bounded_translation_radius':args.radius,'scales':scales,'results':results,'scaled_source_method':'Actual common-family RGBA crop resized with LANCZOS; body/silhouette derive from its actual alpha128/alpha8. Roots/entry annotations transform together at nearest sampling.','limitations':['These exact conservative true-floor interiors can leave feasible boundary solutions unclassified; absence is bounded search result, not external blocker.','Actual scaled physical root trace requires source-owner conversion and independent review.','All approaches and full city composition remain to be verified; no source selection, stage or native acceptance.','New root projections require actual separately supported-level source review.']}
    result['forbidden_root_pairs']=[list(pair)for pair in sorted(forbidden_pairs)]
    result['fixed_whole_family_poses']=fixed_poses
    (report/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
