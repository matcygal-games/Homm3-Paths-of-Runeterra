"""Check real TG1 candidate silhouettes using the unchanged shared consumer.

Each run is hash-named and immutable. A failed trace remains evidence, never
silently widened support or an acceptance gate override. No generated content.
"""
from collections import deque
import importlib.util,json,sys
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3];WORKSPACE=PROJECT.parent
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_town_layout as layout
spec=importlib.util.spec_from_file_location('tg1_ownership',HERE.parent/'approved-tg1-implementation-20261030-v5/finish_sources.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
REPORT=WORKSPACE/'reports/targon-tg1-implementation-20261030-v18'

def blank():return Image.new('L',(800,374))
def polygon(points):
    out=blank();ImageDraw.Draw(out).polygon([tuple(p)for p in points],fill=255);return out
def lines(paths,width=3):
    out=blank();draw=ImageDraw.Draw(out)
    for points in paths:draw.line([tuple(p)for p in points],fill=255,width=width)
    return out
def binary(run,name,mask):
    path=run/(name+'.png');core.save(path,mask.convert('RGB'));return core.ref(path)
def inter(a,b):return ImageChops.multiply(a,b)
def stats(mask):return {'pixels':mask.histogram()[255],'bounds':mask.getbbox()}

def main():
    annotations=core.read(HERE/'physical_annotations.json');index=core.read(HERE/'candidate-frames.json')
    fingerprint=core.sha(HERE/'physical_annotations.json')[:16]+'-'+core.sha(Path(__file__))[:12]
    run=HERE/'physical-runs'/fingerprint
    plan=core.read(core.ORIGINAL/'site-plan-v1.json')
    images={s:core.image(PROJECT/r['frame']['path'])for s,r in index['states'].items()}
    bodies={s:i.getchannel('A').point(lambda p:255 if p>=128 else 0)for s,i in images.items()}
    land=polygon(annotations['land_outline']);support=blank()
    for points in annotations['level_terraces']:support=ImageChops.lighter(support,polygon(points))
    stairs=blank()
    for points in annotations['stairs']:stairs=ImageChops.lighter(stairs,polygon(points))
    support=ImageChops.subtract(inter(support,land),stairs)
    water=blank();paths=lines(annotations['routes'])
    sites=[];unions={};physical={};overlaps=[];diagnostics=[]
    for site in plan['sites']:
        key=site['id'];annotation=annotations['sites'][key];union=blank()
        for state in site['states']:union=ImageChops.lighter(union,bodies[state])
        unions[key]=union;box=union.getbbox();x,y,x2,y2=box
        row={'id':key,'box':[x,y,x2-x,y2-y],'depth':site['z'],'entrance':annotation['entrance'],
          'states':site['states'],'silhouette_mask':binary(run,'silhouette-'+key,union)}
        if key in ('solariTemple','lunariShrine','reliquary'):row['annex_of']={'solariTemple':'guild','lunariShrine':'lunari','reliquary':'civic'}[key]
        sites.append(row)
        for state in site['states']:
            actual={**annotation,**annotations.get('state_overrides',{}).get(state,{})}
            body=bodies[state];foundation=inter(lines(actual['contacts'],2),body)
            door=polygon(actual['frontage'])
            # A shared frontage annotation is bounded by its genuine state's
            # frame, not silently projected beyond a shorter painted base.
            bb=body.getbbox();inside=blank();ImageDraw.Draw(inside).rectangle((bb[0],bb[1],bb[2]-1,bb[3]-1),fill=255)
            door=inter(door,inside);approach=lines([actual['approach']],3)
            physical[state]={'access_kind':'open-site'if key in ('ibex','marketplace','grail','sunhawks')else'door',
              'entrance':actual['entrance'],'body_mask':binary(run,state+'-body',body),
              'foundation_mask':binary(run,state+'-foundation',foundation),'door_mask':binary(run,state+'-door',door),
              'approach_mask':binary(run,state+'-approach',approach)}
            for label,mask in [('path-through-solid',inter(paths,ImageChops.subtract(body,door))),
              ('unsupported-contact',ImageChops.subtract(foundation,support)),
              ('approach-through-own-solid',inter(approach,ImageChops.subtract(body,door)))]:
                if mask.getbbox():diagnostics.append({'state':state,'kind':label,**stats(mask)})
    for n,a in enumerate(sites):
        for b in sites[n+1:]:
            mask=inter(unions[a['id']],unions[b['id']])
            if not mask.getbbox():continue
            behind,front=(a,b)if a['depth']<b['depth']else(b,a)
            overlaps.append({'behind':behind['id'],'front':front['id'],
              'mask':binary(run,'overlap-'+behind['id']+'--'+front['id'],mask),
              'reason':annotations['depth_cases'][behind['id']+'/'+front['id']]})
            if a['depth']==b['depth']:diagnostics.append({'kind':'same-depth-overlap','sites':[a['id'],b['id']],**stats(mask)})
    content=core.read(HERE/'factions-candidate.json');town=content['targon']['town']
    projection=annotations['foundation_projection_case'];behind,front=projection['behind'],projection['front']
    rear=blank();foreground=blank()
    for state in next(s['states']for s in sites if s['id']==behind):
        rear=ImageChops.lighter(rear,core.image(PROJECT/physical[state]['foundation_mask']['path']).convert('L'))
    for state in next(s['states']for s in sites if s['id']==front):foreground=ImageChops.lighter(foreground,bodies[state])
    hidden=inter(rear,foreground);hidden_ref=binary(run,'supported-terrace-root-projection',hidden)
    depths={s['id']:s['depth']for s in sites}
    case={**projection,'kind':'supported-terrace-projection','behind_depth':depths[behind],'front_depth':depths[front],
      'hidden_pixels':hidden.histogram()[255],'hidden_bounds':list(hidden.getbbox()),'mask_sha256':hidden_ref['sha256']}
    core.dump(run/'supported-terrace-source-case.json',case)
    complete=core.image(HERE/'fully-built.png');absent=core.image(HERE/'background-native.png')
    for state in index['complete_scene_states']:
        if index['states'][state]['site']!=front:absent.alpha_composite(images[state])
    core.save(run/'stable-absent-temple-visible.png',absent)
    root_view=complete.copy();highlight=Image.new('RGBA',(800,374),(255,25,80,0));highlight.putalpha(hidden);root_view.alpha_composite(highlight)
    core.save(run/'supported-root-intersection.png',root_view)
    foundation_cases=[{'behind':behind,'front':front,'reason':projection['reason'],'mask':hidden_ref,
      'source_case':core.ref(run/'supported-terrace-source-case.json'),'evidence':{
       'complete_scene':core.ref(HERE/'fully-built.png'),'front_absent_scene':core.ref(run/'stable-absent-temple-visible.png'),
       'intersection_overlay':core.ref(run/'supported-root-intersection.png')}}]
    contract={'canvas':[800,374],'alpha_threshold':8,'geometry_mode':'silhouette-v2',
      'native_topology':'targon-dryland-annexes-v1','ordinary_land_sites':16,'optional_coastal_sites':0,
      'independent_annexes':{'solariTemple':'guild','lunariShrine':'lunari','reliquary':'civic'},
      'background':index['background'],'frames':{s:r['frame']for s,r in index['states'].items()},
      'land_mask':binary(run,'land',land),'sites':sites,
      'silhouette_plan':{'version':2,'support_mask':binary(run,'level-support',support),'stairs_mask':binary(run,'stairs',stairs),
        'water_mask':binary(run,'external-water',water),'paths_mask':binary(run,'paved-route-centrelines',paths),
        'states':physical,'overlaps':overlaps,'foundation_occlusions':foundation_cases,
        'complete_scene_states':index['complete_scene_states'],'complete_scene':core.ref(HERE/'fully-built.png')}}
    core.dump(run/'layout-contract-candidate.json',contract)
    error=None
    try:
        layout._validate_site_topology(contract,sites,'targon',town)
        layout._inspect_silhouettes(PROJECT,contract,sites,images,town,land,set())
    except(ValueError,KeyError,OSError)as caught:error=str(caught)
    report={'status':'authored configuration','candidate_only':True,'actual_shared_physical_consumer_pass':error is None,
      'shared_consumer_sha256':core.sha(WORKSPACE/'scripts/faction_town_layout.py'),
      'annotations':core.ref(HERE/'physical_annotations.json'),'producer':core.ref(Path(__file__)),
      'contract':core.ref(run/'layout-contract-candidate.json'),'first_consumer_error':error,
      'diagnostics':diagnostics,'all_state_intersections':[{k:v for k,v in r.items()if k!='reason'}for r in overlaps],
      'native_execution':False,'visual_approval':False,'release_accepted':False}
    core.dump(run/'result.json',report)
    overlay=core.image(HERE/'fully-built.png')
    def tint(mask,color):
        im=Image.new('RGBA',(800,374),(*color,0));im.putalpha(mask.point(lambda p:180 if p else 0));overlay.alpha_composite(im)
    tint(stairs,(240,70,190));tint(paths,(40,245,60))
    for state,row in physical.items():
        tint(core.image(PROJECT/row['foundation_mask']['path']).convert('L'),(60,155,255))
    core.save(run/'physical-overlay.png',overlay)
    print(json.dumps({'run':str(run.relative_to(PROJECT)),'consumer_error':error,'diagnostics':diagnostics,'overlaps':len(overlaps)}))

if __name__=='__main__':main()
