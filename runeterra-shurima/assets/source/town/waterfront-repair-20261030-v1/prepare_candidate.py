"""Isolated waterfront recipe/geometry proof; never selects or stages outputs."""
from assemble_candidate import *
import copy, shutil, tempfile
sys.path.insert(0,str(WORKSPACE/'scripts'))
from faction_art_compile import create_compiler
import faction_town_layout
sys.path.insert(0,str(OLD))
import build_candidate as baseline

def read(p):return json.loads(p.read_text(encoding='utf8'))
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def line(points,width=1):return baseline.line(points,width)
def merge(items):return union(*items)

def main():
    prompt='Edit this painted 2D Heroes of Might and Magic III town waterfront crop. Remove the entire constructed dock/quay projecting into the water: all masonry deck, wooden posts/pilings, railings, mooring ropes, boat remnants, their shadows and reflections. Replace only that projecting structure and the water below it with one continuous natural turquoise-blue river surface with irregular small painted ripples. Restore a natural rocky shoreline where the dock began. Keep the existing land, palm foliage, stone retaining walls and upper town architecture unchanged. Preserve the original oblique perspective, hand-painted native game texture, lighting and palette. No rectangular water patches, no floating posts or straight rope remnants, no new structures, no boat. This is an empty unbuilt waterfront.'
    (HERE/'empty-water-prompt-v1.txt').write_text(prompt+'\n',encoding='utf8')
    dump(HERE/'generation-ledger-v1.json',{'status':'authored configuration','tool':'built-in image_gen.imagegen','provider':'OpenAI','model':'Not exposed by tool','workflow':'image-based-painted-2d','derived_from_blender':False,'prompt':ref(HERE/'empty-water-prompt-v1.txt'),'reference':ref(HERE/'reference-hidden-quay.png'),'raw':ref(HERE/'empty-water-painted-raw-v1.png'),'native':ref(HERE/'empty-water-painted-native-v1.png'),'reference_conversion':'Native crop (600,275,800,374), enlarged six times by deterministic conversion for editing; entire generated crop reduced uniformly by Lanczos to200x99.','composition':'assemble_candidate.py bounded gradient-domain composition; no new artwork made by raster geometry.','preserved_parent_ledger':ref(PROJECT/'assets/source/town/approved-sh1-portable-provenance-20261030-v1/generation-ledger-v1.json'),'producer':ref(HERE/'assemble_candidate.py')})
    ledger=ref(HERE/'generation-ledger-v1.json')
    contract=read(OLD/'layout-acceptance-contract-v2.json');plan=contract['silhouette_plan']
    contract['background']=ref(HERE/'background-candidate.png')
    save(HERE/'full-candidate.png',Image.open(REPORT/'full-candidate.png'))
    plan['complete_scene']=ref(HERE/'full-candidate.png')
    coast=next(s for s in contract['sites'] if s['id']=='coast')
    coast['entrance']=[638,323]
    coast_mask=Image.open(HERE/'ship-body.png').convert('L');save(HERE/'geometry/coast-silhouette.png',coast_mask)
    coast['silhouette_mask']=ref(HERE/'geometry/coast-silhouette.png');b=coast_mask.getbbox();coast['box']=[b[0],b[1],b[2]-b[0],b[3]-b[1]]
    for state in ['shipyard','ship']:
        frame=Image.open(HERE/(state+'-candidate.png')).convert('RGBA');body=frame.getchannel('A')
        save(HERE/'geometry'/(state+'-body.png'),body)
        foundation=Image.new('L',SIZE);draw=ImageDraw.Draw(foundation)
        b=body.getbbox()
        for x in range(b[0],b[2]):
            ys=[y for y in range(328,b[3]) if body.getpixel((x,y))]
            if ys:draw.line((x,max(328,max(ys)-1),x,max(ys)),fill=255)
        door=line([(638,320),(638,325)],1)
        approach=line([(632,323),(637,323)],1)
        row=plan['states'][state];row['entrance']=[638,323]
        for suffix,im in [('foundation',foundation),('door',door),('approach',approach)]:
            save(HERE/'geometry'/(state+'-'+suffix+'.png'),im);row[suffix+'_mask']=ref(HERE/'geometry'/(state+'-'+suffix+'.png'))
        row['body_mask']=ref(HERE/'geometry'/(state+'-body.png'))
        marine=ImageChops.multiply(foundation,Image.open(OLD/'geometry/water.png').convert('L'))
        save(HERE/'geometry'/(state+'-marine.png'),marine);row['marine_support_mask']=ref(HERE/'geometry'/(state+'-marine.png'))
        contract['frames'][state]=ref(HERE/(state+'-candidate.png'))
        area=Image.new('RGBA',SIZE);area.putalpha(body);save(HERE/'derived'/(state+'_area.png'),area)
        border=Image.new('RGBA',SIZE,(245,210,85,0));border.putalpha(ImageChops.subtract(body.filter(ImageFilter.MaxFilter(3)),body));save(HERE/'derived'/(state+'_border.png'),border)
        save(HERE/'derived'/(state+'_campaign.png'),baseline.icon(frame,(58,64)))
        save(HERE/'construction'/(state+'.png'),baseline.icon(frame,(150,70)))
    # One newly owned nearshore piling contact (638,331) is on the original
    # rocky land bank. The old tip-only coast landing did not annotate it.
    support=Image.open(OLD/'geometry/support.png').convert('L');support.putpixel((638,331),255)
    save(HERE/'geometry/support.png',support);plan['support_mask']=ref(HERE/'geometry/support.png')
    tavern_approach=line([(666,312),(665,313),(657,313),(647,313),(637,317),(632,323)],2)
    save(HERE/'geometry/tavern-approach.png',tavern_approach);plan['states']['tavern']['approach_mask']=ref(HERE/'geometry/tavern-approach.png')
    streets=copy.deepcopy(baseline.STREET_LINES[:-1]);streets[5][-1]=(632,323)
    approaches=[line(points,1) for sid,(_,points) in baseline.ACCESS.items() if sid not in ['archers','coast','tavern']]
    approaches += [line([(226,284),(227,294),(234,302)],1),line([(666,312),(665,313),(657,313),(647,313),(637,317),(632,323)],1),line([(632,323),(637,323)],1)]
    paths=merge([line(p) for p in streets]+approaches)
    save(HERE/'geometry/paths.png',paths);plan['paths_mask']=ref(HERE/'geometry/paths.png')
    for overlap in plan['overlaps']:
        if overlap['front']=='coast':
            rear=next(s for s in contract['sites'] if s['id']==overlap['behind'])
            hit=ImageChops.multiply(Image.open(PROJECT/rear['silhouette_mask']['path']).convert('L'),coast_mask)
            save(HERE/'geometry/tavern-behind-coast.png',hit);overlap['mask']=ref(HERE/'geometry/tavern-behind-coast.png')
    for row in plan['foundation_occlusions']:
        if row['front']=='coast':
            hidden=ImageChops.multiply(Image.open(OLD/'geometry/tavern-foundation.png').convert('L'),coast_mask)
            save(HERE/'geometry/tavern-root-behind-coast.png',hidden);row['mask']=ref(HERE/'geometry/tavern-root-behind-coast.png')
            case=read(PROJECT/row['source_case']['path']);case.update({'hidden_pixels':hidden.histogram()[255],'hidden_bounds':list(hidden.getbbox()),'mask_sha256':row['mask']['sha256']})
            dump(HERE/'physical-cases/tavern-coast.json',case);row['source_case']=ref(HERE/'physical-cases/tavern-coast.json')
            absent=Image.open(HERE/'background-candidate.png').convert('RGBA');town=read(PROJECT/'content/factions.json')['shurima']['town']
            for state in sorted(plan['complete_scene_states'],key=lambda s:town['structures'][s]['z']):
                if state not in ['ship','shipyard']:absent.alpha_composite(Image.open(PROJECT/contract['frames'][state]['path']).convert('RGBA'))
            save(HERE/'physical-cases/tavern-without-coast.png',absent)
            overlay=Image.open(HERE/'full-candidate.png').convert('RGBA');mark=Image.new('RGBA',SIZE,(255,0,80,0));mark.putalpha(hidden.point(lambda p:220 if p else 0));overlay.alpha_composite(mark);save(HERE/'physical-cases/tavern-coast-overlay.png',overlay)
            row['evidence']={'complete_scene':ref(HERE/'full-candidate.png'),'front_absent_scene':ref(HERE/'physical-cases/tavern-without-coast.png'),'intersection_overlay':ref(HERE/'physical-cases/tavern-coast-overlay.png')}
    dump(HERE/'layout-contract-candidate.json',contract)
    recipes=[];canonical=[]
    recipe_paths=[PROJECT/'assets/recipes/town/background.png.json',PROJECT/'assets/recipes/ui/town-surfaces-v1/buildingIcons.json']
    recipe_paths += [PROJECT/'assets/recipes/town/painted-resume-v6'/(state+'-'+suffix+'.json') for state in ['shipyard','ship'] for suffix in ['animation','area','border','campaign']]
    for path in recipe_paths:
        r=read(path);r['generation'].update({'source_generation_ledger':ledger['path'],'source_generation_ledger_sha256':ledger['sha256'],'prompt':'Bounded painted empty waterfront repair and complete coastal ownership; exact prompt, sources and deterministic composition in generation-ledger-v1.json.'})
        if r['role']=='town-background':source=HERE/'background-candidate.png';r.update({'source':ref(source)['path'],'source_sha256':sha(source)})
        elif r['role']=='town-construction-icons':
            for entry in r['frames']:
                if entry['building'] in ['shipyard','ship']:
                    source=HERE/'construction'/(entry['building']+'.png');entry.update({'source':ref(source)['path'],'source_sha256':sha(source)})
        elif r['recipe_type']=='vcmi_animation':
            state=path.name.split('-')[0];source=HERE/(state+'-candidate.png');r['groups'][0]['frames'][0].update({'source':ref(source)['path'],'sha256':sha(source)})
        else:
            state,suffix=path.stem.split('-');source=HERE/'derived'/(state+'_'+suffix+'.png');r.update({'source':ref(source)['path'],'source_sha256':sha(source)})
        target=HERE/'candidate-recipes'/path.relative_to(PROJECT/'assets/recipes');dump(target,r);recipes.append(target);canonical.append({'target':path.relative_to(PROJECT).as_posix(),'before_sha256':sha(path),'candidate':ref(target)})
    compiler=create_compiler('shurima');runs=[];payload={}
    for run in range(2):
        values={}
        for recipe in recipes:
            outputs,_=compiler.plan(PROJECT,recipe);values.update(outputs)
        runs.append({k:hashlib.sha256(v).hexdigest() for k,v in values.items()});payload=values
    assert runs[0]==runs[1]
    for name,data in payload.items():
        target=REPORT/'native-candidate'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    dump(HERE/'integration-plan.json',{'status':'authored configuration','candidate_only':True,'recipes':canonical,'design_patch':{'layout_contract':ref(HERE/'layout-contract-candidate.json')},'native_output_pins':runs[0]})
    with tempfile.TemporaryDirectory(prefix='waterfront-proof-',dir=REPORT) as tmp:
        project=Path(tmp)
        shutil.copytree(PROJECT/'assets/source/town',project/'assets/source/town')
        shutil.copytree(PROJECT/'assets/generated',project/'assets/generated')
        shutil.copytree(REPORT/'native-candidate',project/'assets/generated',dirs_exist_ok=True)
        design=read(PROJECT/'design/town-visuals.json');design['layout_contract']=ref(HERE/'layout-contract-candidate.json');dump(project/'design/town-visuals.json',design)
        faction=read(PROJECT/'content/factions.json');dump(project/'content/factions.json',faction)
        errors,deps=faction_town_layout.inspect(project,{'factions':faction},'shurima')
    result={'status':'authored configuration','candidate_only':True,'actual_compile_runs':2,'deterministic':runs[0]==runs[1],'recipes':len(recipes),'physical_outputs':len(payload),'strict_native_layout_errors':errors,'declared_layout_dependencies':len(deps),'canonical_recipe_inputs_unchanged':all(sha(PROJECT/r['target'])==r['before_sha256'] for r in canonical),'ship_includes_whole_dock':ImageChops.subtract(Image.open(HERE/'shipyard-body.png'),Image.open(HERE/'ship-body.png')).getbbox() is None}
    dump(REPORT/'candidate-proof.json',result);print(json.dumps(result))

if __name__=='__main__':main()
