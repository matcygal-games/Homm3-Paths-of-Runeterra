"""Prepare pixel-bound physical masks from separately authored observations.

All artwork is already painted. Binary masks are technical annotations only;
the level terrain and public stairs are authored independently of building alpha.
Conflicts are reported, never silently erased from support/path masks.
"""
from pathlib import Path
import hashlib
import json
from itertools import combinations
from PIL import Image, ImageDraw, ImageChops

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
SIZE=(800,374)


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')


def ref(path):return {'path':path.relative_to(PROJECT).as_posix(),'sha256':digest(path)}


def mask(polygons):
    image=Image.new('L',SIZE);draw=ImageDraw.Draw(image)
    for poly in polygons:draw.polygon([tuple(p) for p in poly],fill=255)
    return image


def line(points,width=3):
    image=Image.new('L',SIZE);ImageDraw.Draw(image).line([tuple(p) for p in points],fill=255,width=width,joint='curve')
    return image


def save(image,name):
    p=HERE/'physical-v4'/name;p.parent.mkdir(parents=True,exist_ok=True);image.convert('RGBA').save(p)
    return ref(p)


def pixels(image):return image.histogram()[255]


def main():
    guide=json.loads((HERE/'site-plan-v1.json').read_text())['sites']
    physical=json.loads((HERE/'physical-annotations-v4.json').read_text())
    # The mountain landmass is not external water. Sky remains outside land;
    # separate authored level-support surfaces constrain every real footing.
    land=mask([[[0,74],[180,74],[210,106],[270,96],[315,80],[418,91],[596,75],[800,80],[800,373],[0,373]]])
    support=mask(physical['level_support_polygons']);stairs=mask(physical['public_stair_polygons']);water=Image.new('L',SIZE)
    paths=Image.new('L',SIZE)
    for points in physical['road_centerlines']:paths=ImageChops.lighter(paths,line(points,width=2))
    contract={'canvas':[800,374],'alpha_threshold':8,'geometry_mode':'silhouette-v2','native_topology':'targon-dryland-annexes-v1',
              'ordinary_land_sites':16,'optional_coastal_sites':0,
              'independent_annexes':{'solariTemple':'guild','lunariShrine':'lunari','reliquary':'civic'},
              'background':ref(HERE/'background-selected-native-v9.png'),'land_mask':save(land,'land.png'),'sites':[],'frames':{},
              'silhouette_plan':{'version':2,'support_mask':save(support,'level-support.png'),'stairs_mask':save(stairs,'public-stairs.png'),
                  'water_mask':save(water,'external-water.png'),'paths_mask':save(paths,'paths.png'),'states':{},'overlaps':[],
                  'foundation_occlusions':[], 'complete_scene_states':[],'complete_scene':ref(HERE/'native-v4/fully-built.png')}}
    frames={};bodies={};unions={};state_site={};observations={};problems=[]
    for site,record in guide.items():
        union=Image.new('L',SIZE)
        for state in record['keys']:
            p=HERE/'native-v4'/(state+'.png');image=Image.open(p).convert('RGBA')
            frames[state]=image;contract['frames'][state]=ref(p)
            alpha=image.getchannel('A').point(lambda p:255 if p>=8 else 0);body=image.getchannel('A').point(lambda p:255 if p>=128 else 0)
            bodies[state]=body;state_site[state]=site;union=ImageChops.lighter(union,alpha)
            observed=physical['states'][state];point=observed['entrance'];bounds=alpha.getbbox()
            foundation=ImageChops.multiply(mask([observed['foundation']]),body)
            # The actual door/open-frontage includes its complete front steps,
            # through the lowest selected root pixel, rather than a fake point.
            door=mask([[[point[0]-6,point[1]-4],[point[0]+6,point[1]-4],[point[0]+6,bounds[3]-1],[point[0]-6,bounds[3]-1]]])
            approach=line(observed['approach'],width=2)
            observations[state]=(foundation,door,approach)
            contract['silhouette_plan']['states'][state]={'access_kind':'open-site' if site in ('ibex','stellacorns','marketplace','grail') else 'door',
                'entrance':point,'body_mask':save(body,'states/'+state+'-body.png'),'foundation_mask':save(foundation,'states/'+state+'-foundation.png'),
                'door_mask':save(door,'states/'+state+'-door.png'),'approach_mask':save(approach,'states/'+state+'-approach.png')}
            for label,bad in [('foundation-outside-level-support',ImageChops.subtract(foundation,support)),('foundation-on-public-stair',ImageChops.multiply(foundation,stairs)),
                              ('own-approach-through-body',ImageChops.multiply(approach,ImageChops.subtract(body,door))),('global-path-through-body',ImageChops.multiply(paths,ImageChops.subtract(body,door)))]:
                if bad.getbbox():problems.append({'kind':label,'state':state,'bounds':list(bad.getbbox()),'pixels':pixels(bad)})
        unions[site]=union;bounds=union.getbbox();top=record['top']
        entry={'id':site,'states':record['keys'],'box':[bounds[0],bounds[1],bounds[2]-bounds[0],bounds[3]-bounds[1]],'depth':record['z'],
               'entrance':physical['states'][top]['entrance'],'silhouette_mask':save(union,'sites/'+site+'-silhouette.png')}
        if 'annex_of' in record:entry['annex_of']=record['annex_of']
        contract['sites'].append(entry)
        if site!='grail':contract['silhouette_plan']['complete_scene_states'].append(top)
    for a,b in combinations(guide,2):
        intersection=ImageChops.multiply(unions[a],unions[b])
        if intersection.getbbox():
            behind,front=(a,b) if guide[a]['z']<guide[b]['z'] else (b,a)
            reason='Actual bounded roof/wall projection at native painted depth; complete foundations and every doorway/approach remain separately verified and exposed.'
            contract['silhouette_plan']['overlaps'].append({'behind':behind,'front':front,'reason':reason,'mask':save(intersection,'overlaps/'+behind+'--'+front+'.png')})
    for state,(foundation,door,approach) in observations.items():
        for other,body in bodies.items():
            if state_site[state]==state_site[other]:continue
            tests=[('approach-obscured',ImageChops.multiply(approach,body))]
            if guide[state_site[other]]['z']>guide[state_site[state]]['z']:
                tests.extend([('door-obscured',ImageChops.multiply(door,body)),('foundation-obscured',ImageChops.multiply(foundation,body))])
            for label,bad in tests:
                if bad.getbbox():problems.append({'kind':label,'state':state,'other':other,'bounds':list(bad.getbbox()),'pixels':pixels(bad)})
    for label,bad in [('support-on-stairs',ImageChops.multiply(support,stairs)),('support-outside-land',ImageChops.subtract(support,land)),('paths-outside-land',ImageChops.subtract(paths,land))]:
        if bad.getbbox():problems.append({'kind':label,'bounds':list(bad.getbbox()),'pixels':pixels(bad)})
    contract['silhouette_plan']['complete_scene_states'].sort(key=lambda state:guide[state_site[state]]['z'])
    write(HERE/'layout-acceptance-contract-v4.json',contract)
    content=json.loads((PROJECT/'content/factions.json').read_text(encoding='utf-8'))
    for state,row in content['targon']['town']['structures'].items():row.update(x=0,y=0,z=guide[state_site[state]]['z'])
    write(HERE/'proposed/content/factions.json',content)
    design={'status':'authored configuration','visual_approval_granted':False,'canvas':[800,374],'layout_geometry_mode':'silhouette-v2',
            'layout_contract':ref(HERE/'layout-acceptance-contract-v4.json'),'native_topology':'targon-dryland-annexes-v1',
            'ordinary_land_sites':16,'optional_coastal_sites':0,'independent_annexes':contract['independent_annexes'],
            'source_composition':ref(HERE/'complete-selected-native-v1.png'),'selected_native_composition':ref(HERE/'native-v4/fully-built.png'),
            'identity':'Main public Solari/Rakkor stone mountain community; physically separate violet Lunari dwelling and prayer frontage. Native35 states preserved; no invented coast.'}
    write(HERE/'proposed/design/town-visuals.json',design)
    write(HERE/'physical-preflight-v4.json',{'status':'authored configuration','problem_count':len(problems),'problems':problems,
          'state_count':len(frames),'site_count':len(unions),'foundation_occlusion_waivers':0,
          'overlap_pairs':[(r['behind'],r['front']) for r in contract['silhouette_plan']['overlaps']]})
    print(json.dumps({'state_count':len(frames),'site_count':len(unions),'problem_count':len(problems),'problems':problems}))


if __name__=='__main__':main()
