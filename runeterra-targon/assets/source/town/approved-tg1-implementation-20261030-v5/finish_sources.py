"""Complete TG1 source ownership behind foreground buildings; candidate only.

The approved full view is invariant. Genuine painted hidden faces are admitted
only under the exact opaque full-state foreground pixel budget. Minor ground
projection intersections retain visible ownership rather than cloning another
functional building. No canonical content/recipe/manifest/generated/stage writes.
"""
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys

from PIL import Image,ImageChops,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
WORKSPACE=PROJECT.parent
ANCESTOR=HERE.parent/'approved-tg1-implementation-20261030-v4'
ORIGINAL=HERE.parent/'approved-tg1-20261029-v1'
HIDDEN=ANCESTOR/'hidden-paint-v1'
REPORT=WORKSPACE/'reports/targon-tg1-implementation-20261030-v5'
APPROVED_SHA='964d3345bba9265ece58638d20de4ef15f6217ccde633ea0402b707f351aa669'
PAINTED_PAIRS={('civic','reliquary'),('guild','solariTemple'),('silo','marketplace'),
               ('tavern','monastery'),('solariTemple','stellacorns')}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_bytes())
def encoded(value):return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def image(path):
    with Image.open(path)as opened:
        opened.load();return opened.convert('RGBA')
def write(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists()and path.read_bytes()!=raw:raise ValueError('Preserve versioned candidate: '+str(path))
    if not path.exists():
        with path.open('xb')as stream:stream.write(raw)
def png(im):
    stream=io.BytesIO();im.save(stream,format='PNG',compress_level=9,optimize=False);return stream.getvalue()
def save(path,im):write(path,png(im))
def dump(path,value):write(path,encoded(value))
def ref(path):return {'path':Path(path).relative_to(PROJECT).as_posix(),'sha256':sha(path)}
def icon(im,size):
    box=im.getchannel('A').getbbox()
    if box is None:raise ValueError('Empty architecture frame')
    piece=im.crop(box);piece.thumbnail((size[0]-4,size[1]-4),Image.Resampling.LANCZOS)
    result=Image.new('RGBA',size);result.alpha_composite(piece,((size[0]-piece.width)//2,size[1]-piece.height-2));return result


def visible_states(buildings,built):
    """CCastleBuildings refresh: retain furthest BUILT member of each family.

    The actual CBuilding.upgrade parent comes from JSON `upgrades`. Annexes have
    no upgrade parent and remain independent. This is a source-side consumer
    model, not execution of native C++ rendering.
    """
    built=set(built)
    if not built<=set(buildings):raise ValueError('Unknown native building')
    hidden=set()
    for state in built:
        seen={state};parent=buildings[state].get('upgrades')
        while parent:
            if parent in seen or parent not in buildings:raise ValueError('Invalid native upgrade lineage')
            seen.add(parent);hidden.add(parent);parent=buildings[parent].get('upgrades')
    return built-hidden


def compile_candidate(index):
    sys.path.insert(0,str(WORKSPACE/'scripts'))
    from faction_art_compile import create_compiler
    compiler=create_compiler('targon');prefix='Content/Sprites/runeterra/targon/town/'
    recipes={}
    base_generation={'image_generation_used':True,'workflow':'image-based-painted-2d','derived_from_blender':False,
        'provider':'OpenAI built-in image_gen','model':'Not exposed','prompt':'Approved TG1 and genuine construction-stage paintings; exact original RGB contour extraction, bounded genuine hidden-face completion. No 3D. See project-relative source ownership ledger.',
        'painted_master':(ORIGINAL/'approved-full-raw.png').relative_to(PROJECT).as_posix(),
        'painted_master_sha256':sha(ORIGINAL/'approved-full-raw.png')}
    common={'production_status':'painted-master-complete-unapproved','visual_approval_granted':False,
            'generation':base_generation,'credits':{'author':'Project-directed original painted2D; OpenAI image_gen, technical native assembly',
            'license':None,'redistribution':'Unresolved; no release acceptance'}}
    def raster(path,output,role):
        im=image(path);return {**deepcopy(common),'recipe_type':'raster','output_path':prefix+output,'role':role,
          'canvas':list(im.size),'source_canvas':list(im.size),'source':path.relative_to(PROJECT).as_posix(),
          'source_sha256':sha(path),'fit':'exact'}
    recipes['background']=raster(HERE/'background-native.png','background.png','town-background')
    for state,row in sorted(index['states'].items()):
        recipes[state]={**deepcopy(common),'recipe_type':'vcmi_animation','output_path':prefix+'structures/'+state+'.json',
          'role':'town-structure-animation','canvas':[800,374],'pivot':{'x':0,'y':0,'basis':'Complete native TG1 registration; no frame fitting'},
          'generateShadow':0,'generateOverlay':0,'groups':[{'group':0,'frames':[{'source':row['frame']['path'],
           'sha256':row['frame']['sha256'],'source_canvas':[800,374]}]}]}
        for suffix in ('area','border','campaign'):
            recipes[state+'_'+suffix]=raster(HERE/'derived'/(state+'_'+suffix+'.png'),'structures/'+state+'_'+suffix+'.png','town-structure-'+suffix)
    ids=compiler.indexed_building_ids(PROJECT)
    recipes['buildingIcons']={**deepcopy(common),'recipe_type':'indexed_animation','output_path':prefix+'buildingIcons.json',
      'role':'town-construction-icons','canvas':[150,70],'pivot':{'x':0,'y':0,'basis':'Actual native BuildingID mapping; gaps preserved'},
      'frames':[{'building':state,'frame':frame,'source':(HERE/'construction'/(state+'.png')).relative_to(PROJECT).as_posix(),
        'source_sha256':sha(HERE/'construction'/(state+'.png')),'source_canvas':[150,70]}for state,frame in sorted(ids.items(),key=lambda row:row[1])]}
    paths=[]
    for name,recipe in recipes.items():
        path=HERE/'candidate-recipes'/(name+'.json');dump(path,recipe);paths.append(path)
    first={};passes=[]
    for ordinal in range(2):
        outputs={}
        for path in paths:
            actual,_=compiler.plan(PROJECT,path)
            if set(actual)&set(outputs):raise ValueError('Conflicting actual native producers')
            outputs.update(actual)
        pins={n:hashlib.sha256(raw).hexdigest()for n,raw in sorted(outputs.items())};passes.append(pins)
        if ordinal==0:first=outputs
    if passes[0]!=passes[1]:raise ValueError('Actual native converter is nondeterministic')
    catalog={'status':'authored configuration','candidate_only':True,'native_verified':False,'release_accepted':False,
             'actual_converter_passes':2,'recipes':[{'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p),'output_path':read(p)['output_path']}for p in paths],
             'native_output_pins':passes[0],'native_output_count':len(first),'recipe_count':len(paths),
             'compiler_sha256':sha(WORKSPACE/'scripts/faction_art_compile.py')}
    dump(HERE/'candidate-selection.json',catalog)
    return catalog


def main():
    if sha(ORIGINAL/'approved-full-native.png')!=APPROVED_SHA:raise ValueError('Approved TG1 changed')
    index=read(ANCESTOR/'candidate-frames.json');plan=read(ORIGINAL/'site-plan-v1.json')
    states=deepcopy(index['states']);layers={s:image(PROJECT/r['frame']['path'])for s,r in states.items()}
    complete=index['complete_scene_states'];full_by_site={states[s]['site']:s for s in complete}
    site_by_id={s['id']:s for s in plan['sites']};pairs=[]
    for behind in plan['sites']:
        for front in plan['sites']:
            if front['z']<=behind['z']:continue
            front_mask=layers[full_by_site[front['id']]].getchannel('A')
            any_overlap=False
            for state in behind['states']:
                layer=layers[state];budget=ImageChops.multiply(layer.getchannel('A'),front_mask)
                if budget.getbbox()is None:continue
                any_overlap=True;pair=(behind['id'],front['id']);kind='visible-ground-projection-cut'
                if pair in PAINTED_PAIRS:
                    tag=states[state]['source_tag']
                    paint='temple-front-native.png'if behind['id']=='solariTemple'else(tag+'-rear-native.png')
                    source=HIDDEN/paint;hidden=image(source)
                    # Exact generated RGB is restricted to the exact opaque
                    # foreground coverage. The original rear alpha is retained.
                    before_alpha=layer.getchannel('A');layer.paste(hidden,(0,0),budget);layer.putalpha(before_alpha)
                    kind='genuine-painted-hidden-face'
                else:
                    layer.putalpha(ImageChops.subtract(layer.getchannel('A'),budget));source=None
                path=HERE/'ownership'/(state+'--'+front['id']+'.png');save(path,budget)
                pairs.append({'behind_state':state,'behind_site':behind['id'],'front_site':front['id'],
                  'front_complete_state':full_by_site[front['id']],'kind':kind,'mask':ref(path),
                  'pixels':budget.histogram()[255],'bounds':list(budget.getbbox()),
                  'painted_source':ref(source)if source else None})
    background=image(PROJECT/index['background']['path']);replay=background.copy()
    for state in complete:replay.alpha_composite(layers[state])
    approved=image(ORIGINAL/'approved-full-native.png')
    if replay.tobytes()!=approved.tobytes():raise ValueError('Hidden-face ownership changed approved full view')
    save(HERE/'background-native.png',background);save(HERE/'fully-built.png',replay)
    for state,layer in layers.items():
        frame=HERE/'frames'/(state+'.png');save(frame,layer)
        body=layer.getchannel('A');bodypath=HERE/'masks'/(state+'-body.png');save(bodypath,body)
        area=Image.new('RGBA',(800,374));area.putalpha(body);save(HERE/'derived'/(state+'_area.png'),area)
        border=Image.new('RGBA',(800,374),(245,210,85,0));border.putalpha(ImageChops.subtract(body.filter(ImageFilter.MaxFilter(3)),body))
        save(HERE/'derived'/(state+'_border.png'),border);save(HERE/'derived'/(state+'_campaign.png'),icon(layer,(58,64)))
        save(HERE/'construction'/(state+'.png'),icon(layer,(150,70)))
        states[state].update(frame=ref(frame),body=ref(bodypath),bbox=list(body.getbbox()))
        for suffix in ('area','border','campaign'):states[state][suffix]=ref(HERE/'derived'/(state+'_'+suffix+'.png'))
        states[state]['construction']=ref(HERE/'construction'/(state+'.png'))
    content=read(PROJECT/'content/factions.json');town=content['targon']['town']
    for state,patch in index['native_structure_patch'].items():town['structures'][state].update(patch)
    if set(visible_states(town['buildings'],town['buildings']))!=set(complete):raise ValueError('Complete scene differs from actual native family replacement')
    dump(HERE/'factions-candidate.json',content)
    result={**index,'background':ref(HERE/'background-native.png'),'states':states,'hidden_face_ownership':pairs,
            'approved_full_RGBA_changes':0,'native_family_visible_complete_states':complete,'source_ancestor':ref(ANCESTOR/'candidate-frames.json'),
            'remaining_depth_intersections':'Recompute actual all-state intersections for the physical contract; ancestral list is not an approval.',
            'scope':'Candidate source ownership and real converter replay only; physical/source art and native acceptance remain separate.'}
    dump(HERE/'candidate-frames.json',result)
    catalog=compile_candidate(result)
    REPORT.mkdir(parents=True,exist_ok=True)
    parts=['<!doctype html><meta charset="utf-8"><title>Targon TG1 ownership</title><style>body{background:#222;color:#eee;font:17px Georgia;max-width:1200px;margin:auto}img{max-width:100%}</style>',
           '<h1>Targon TG1 source ownership candidate</h1><p>Authored configuration. Exact approved full view retained. Genuine hidden-face sources are bounded by opaque foreground masks. Physical/native review remains pending.</p>']
    relative='../../'+HERE.relative_to(WORKSPACE).as_posix()
    for name,title in [('background-native.png','Empty source plate'),('fully-built.png','Exact approved fully built')]:parts.append('<h2>'+title+'</h2><img width="800" height="374" src="'+relative+'/'+name+'">')
    for site in plan['sites']:
        canvas=Image.new('RGB',(400,160*len(site['states'])),(28,31,30));draw=ImageDraw.Draw(canvas)
        for n,state in enumerate(site['states']):
            im=layers[state];bg=Image.new('RGBA',im.size,(57,59,61,255));bg.alpha_composite(im);crop=bg.crop(im.getchannel('A').getbbox());crop.thumbnail((390,130),Image.Resampling.NEAREST)
            canvas.paste(crop.convert('RGB'),((400-crop.width)//2,n*160+24));draw.text((5,n*160+5),state,fill='white')
        name=site['id']+'-states.png';save(REPORT/name,canvas);parts.append('<h2>'+site['id']+'</h2><img src="'+name+'">')
    write(REPORT/'index.html',('\n'.join(parts)+'\n').encode())
    print(json.dumps({'states':len(states),'painted_hidden_face_records':sum(p['kind']=='genuine-painted-hidden-face'for p in pairs),
                      'ownership_records':len(pairs),'full_RGBA_changes':0,'converter_passes':2,'recipes':catalog['recipe_count'],'outputs':catalog['native_output_count']}))


if __name__=='__main__':main()
