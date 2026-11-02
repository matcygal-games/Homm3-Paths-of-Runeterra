"""Source-only Freljord whole-painting extraction. Never stages or publishes.

All creative pixels come from saved imagegen paintings. Polygon masks, exact
composition, binary geometry, and uniform icon reduction are deterministic.
"""
from pathlib import Path
import argparse, copy, hashlib, json, shutil, sys
from collections import deque
from PIL import Image, ImageChops as C, ImageDraw, ImageFilter

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/complete-town-20261027-v2/derivation-finish-v1'
SIZE=(800,374)
PREFIX='Content/Sprites/runeterra/freljord/'
BASE='assets/source/town/complete-town-20261027-v2/derivation-v1/'

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def ref(p):return {'path':Path(p).relative_to(PROJECT).as_posix(),'sha256':digest(p)}
def save(p,im):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);im.save(p);return ref(p)
def blank():return Image.new('L',SIZE)
def poly(points):
    out=blank();ImageDraw.Draw(out).polygon([tuple(q) for q in points],fill=255);return out
def line(points,width=3):
    out=blank();ImageDraw.Draw(out).line([tuple(q) for q in points],fill=255,width=width);return out
def union(items):
    out=blank()
    for item in items:out=C.lighter(out,item)
    return out
def image(name):return Image.open(HERE/name).convert('RGBA')

# Whole visible frontal bearing profile, not a tiny selected support pixel.
# Back/side contacts hidden in the full town are shown in saved reveal paintings.
CONTACTS={
'dwelling-tier-7':[[54,96],[65,103],[83,105],[101,102],[110,94]],
'civic-hall':[[259,137],[274,141],[294,142],[314,143],[329,143],[344,144],[362,143],[383,143],[402,144],[421,142],[439,135],[449,126]],
'fortifications':[[509,119],[526,128],[551,135],[573,135],[592,136],[610,143],[629,142],[644,137],[657,132],[680,131],[701,126],[718,118]],
'mage-guild':[[419,165],[434,170],[454,171],[475,172],[495,173],[515,172],[535,169],[550,163]],
'dwelling-tier-3':[[18,169],[32,174],[49,177],[67,178],[86,177],[103,173],[110,169]],
'anivia-shrine':[[320,203],[329,210],[342,214],[356,217],[374,213],[386,207]],
'true-ice-quarry':[[700,195],[711,201],[722,207],[739,213],[753,213],[770,215],[785,211],[794,204]],
'dwelling-tier-4':[[534,202],[545,208],[552,211],[562,216],[573,217],[583,213],[588,208],[607,205],[626,201],[638,195]],
'dwelling-tier-5':[[398,230],[407,237],[425,240],[442,240],[460,242],[479,242],[498,241],[515,236],[522,227]],
'tavern-hall':[[144,237],[151,245],[165,249],[182,251],[200,254],[219,256],[241,256],[261,255],[282,251],[300,245],[305,237]],
'thunder-temple':[[10,258],[20,265],[34,270],[52,274],[74,277],[94,277],[116,274],[133,267],[145,258]],
'forge':[[570,243],[580,252],[588,254],[598,249],[615,248],[634,251],[654,251],[678,250],[698,248],[712,241]],
'market':[[320,273],[334,280],[351,285],[368,289],[386,292],[405,294],[423,293],[441,292],[458,286],[472,276]],
'dwelling-tier-2':[[122,311],[131,320],[147,326],[163,331],[182,334],[201,339],[221,339],[239,342],[257,341],[276,339],[293,333],[303,323]],
'dwelling-tier-6':[[597,301],[605,309],[622,315],[639,320],[659,323],[681,326],[704,328],[726,326],[750,325],[770,322],[786,315],[791,307]],
'dwelling-tier-1':[[416,322],[434,328],[453,333],[474,336],[495,340],[516,343],[537,347],[558,349],[578,349],[596,345],[607,336]],
'coast':[[711,357],[724,361],[739,365],[754,367],[773,366],[787,362]],
'grail':[[282,280],[289,285],[301,288],[314,286],[324,281]]}

# Exterior step/frontage anchors and painted-lane destinations. The full stair
# corridor is part of doorway access; approaches begin outside actual bodies.
ACCESS={
'dwelling-tier-7':[[77,94],[98,104],[115,116],[134,130]],
'civic-hall':[[335,130],[335,146],[335,157]],
'fortifications':[[615,131],[615,147],[626,151]],
'mage-guild':[[485,171],[485,185],[493,186]],
'dwelling-tier-3':[[54,160],[54,180],[64,187]],
'anivia-shrine':[[355,210],[355,220],[355,227]],
'true-ice-quarry':[[756,206],[756,219],[747,230]],
'dwelling-tier-4':[[571,207],[570,220],[564,227]],
'dwelling-tier-5':[[456,231],[456,246],[470,251]],
'tavern-hall':[[215,240],[215,260],[221,268]],
'thunder-temple':[[81,260],[81,281],[95,288]],
'forge':[[611,242],[597,257],[580,264]],
'market':[[394,281],[394,298],[382,307]],
'dwelling-tier-2':[[238,327],[238,346],[249,353]],
'dwelling-tier-6':[[619,308],[633,325],[648,336]],
'dwelling-tier-1':[[418,318],[411,318],[402,315]],
'coast':[[714,353],[708,355],[693,351]],
'grail':[[305,281],[305,291],[312,296]]}

# Per-state silhouettes follow the same stable base. Lower roof profiles are
# traced from the saved complete lower-stage paintings, never raster-warped.
ROOFS={
'villageHall':[[260,100],[275,94],[288,84],[300,72],[314,59],[329,44],[340,43],[353,51],[365,60],[382,70],[394,81],[406,87],[426,91],[442,99],[449,110]],
'townHall':[[263,92],[276,83],[289,72],[303,56],[316,42],[331,31],[342,36],[352,48],[370,59],[386,67],[400,77],[416,80],[431,85],[446,96],[451,109]],
'cityHall':[[258,98],[274,89],[290,77],[304,62],[320,50],[333,44],[345,49],[360,59],[376,68],[396,77],[415,87],[434,93],[450,105]],
'fort':[[502,92],[514,89],[525,76],[536,66],[547,71],[557,81],[578,85],[589,78],[603,66],[614,60],[626,64],[640,80],[659,84],[680,80],[690,68],[701,63],[713,74],[722,91]],
'citadel':[[502,82],[516,76],[528,62],[540,56],[551,63],[560,75],[581,78],[591,66],[604,54],[616,49],[628,58],[643,71],[663,76],[681,67],[694,53],[706,60],[717,73],[723,91]],
'mageGuild1':[[414,148],[429,140],[444,135],[460,126],[474,114],[485,111],[499,122],[512,131],[529,137],[545,144],[557,150]],
'mageGuild2':[[414,148],[429,139],[444,133],[460,122],[477,109],[487,104],[499,116],[514,128],[531,136],[548,144],[558,150]],
'mageGuild3':[[414,148],[430,138],[447,128],[463,114],[479,102],[488,100],[501,115],[518,129],[535,138],[551,145],[558,151]],
}

def source_for(state,site):
    if state=='grail':return 'grail-town-native.png'
    if state=='ship':return 'ship-town-native.png'
    if state=='shipyard':return 'coast-town-native.png'
    if state in ('townHall','mageGuild2'):return 'town-stage-native.png'
    if state in ('cityHall','citadel','mageGuild3'):return 'city-stage-native.png'
    if state in ('villageHall','fort','mageGuild1','tavern','blacksmith') or state.startswith('dwellingLvl'):
        return 'base-repair-native.png' if state in ('dwellingLvl1','dwellingLvl3','dwellingLvl7') and (HERE/'base-repair-native.png').is_file() else 'base-town-native.png'
    return '../complete-master-v2-native.png'

def make():
    REPORT.mkdir(parents=True,exist_ok=True)
    plan=read(HERE/'silhouette-plan.json');sites=copy.deepcopy(plan['sites'])
    # The legacy study label is retained as file history; active subject is Vigil.
    for s in sites:
        if s['id']=='thunder-temple':s['subject']='Frostguard Vigil, not an invented new service'
        if s['id']=='dwelling-tier-1':s['door']=[418,318]
    sites += [dict(id='coast',states=['shipyard','ship'],full_state='shipyard',z=373,door=[714,353],polygon=[[712,334],[719,329],[727,332],[734,338],[737,347],[753,351],[770,351],[787,348],[794,352],[794,362],[784,367],[770,370],[751,371],[733,367],[716,363],[705,359],[705,350]],intentional_water=True),
              dict(id='grail',states=['grail'],full_state='grail',z=310,door=[305,281],polygon=[[294,230],[303,225],[313,229],[318,237],[317,253],[321,267],[327,272],[326,281],[314,287],[302,290],[289,286],[280,282],[280,274],[289,268],[290,251],[289,240]])]
    content=read(PROJECT/'content/factions.json');town=content['freljord']['town']
    assert sum(len(s['states']) for s in sites)==len(town['buildings'])==36
    assert digest(HERE.parent/'complete-master-v2-native.png')=='a7aab0298946fedb137c621b546a192a63e3d80d49da526921d71c0ab3ff0486'
    assert digest(HERE.parent/'complete-master-v2.png')=='24a9af507f02392ea5fca4fe61bf3a3a50643a6b8ebc14bf7f5bf5ac0846ec9a'
    assert digest(HERE/'coast-town-native.png')=='004ac3ea75e15fd10f28b6f6b3bf387312683b5b51fe504f0285ddf7e9e35ef1'
    root=HERE/'candidate';root.mkdir(exist_ok=True)
    masks=root/'physical';frames={};bodies={};foundations={};doors={};approaches={};silhouettes={};provenance={};recipes={}
    water=poly([[739,354],[752,351],[771,351],[786,348],[799,349],[799,373],[713,373],[721,367],[733,366]])
    # Land includes the dock's snowy shore but never the painted external fjord.
    # Native dry terrain contour. Sky/mountains/tree canopy above the village
    # are not walkable land. The upper-left roost is a separate snowy rock shelf
    # joined to the village by its actual descending access ledge.
    terrain=poly([[0,110],[109,110],[132,118],[173,113],[230,105],[300,107],[395,107],[510,112],[585,112],[670,110],[720,110],[780,150],[799,165],[799,373],[0,373]])
    shelf=poly([[46,55],[55,39],[70,40],[95,52],[108,69],[112,97],[125,113],[137,128],[116,137],[98,114],[48,107]])
    land=C.subtract(C.lighter(terrain,shelf),water)
    stairs=blank()
    for pts in [[[315,127],[355,127],[355,139],[315,139]],[[606,124],[628,124],[633,138],[603,138]],[[197,240],[225,240],[228,250],[193,250]],[[67,253],[91,253],[94,269],[63,269]],[[558,203],[582,203],[584,214],[552,214]]]:stairs=C.lighter(stairs,poly(pts))
    allpaint={}
    for site in sites:
        smasks=[]
        scale=.88 if site['id'] in ('dwelling-tier-1','dwelling-tier-6') else 1.
        anchor=(695,330) if site['id']=='dwelling-tier-6' else (532,351)
        def mapped(q):return [round(anchor[0]+(q[0]-anchor[0])*scale),round(anchor[1]+(q[1]-anchor[1])*scale)]
        if scale!=1:
            site['door']=mapped(site['door'])
        for state in site['states']:
            src=source_for(state,site);paint=image(src);points=site['polygon']
            if site['id']=='mage-guild':
                # Prior study included the foreground bushes/retaining snow
                # below the actual archive stair foot. These are landscape.
                points=points[:20]+[[555,160],[550,165],[536,171],[518,174],[495,175],[475,174],[454,173],[436,172],[421,168],[416,160],[417,155],[411,148]]
            if site['id']=='dwelling-tier-4':
                points=points[:29]+[[542,209],[533,205],[529,196],[529,190]]
            if state in ROOFS:
                # Roof profile + original frontal/base chain from right to left.
                low=[q for q in points if q[1]>= (120 if site['id'] in ('civic-hall','fortifications') else 165)]
                # Preserve clockwise lower edge, explicit rather than convex hull.
                if site['id']=='civic-hall':low=[[451,127],[437,140],[419,145],[393,146],[361,145],[328,145],[293,145],[267,144],[258,139],[257,124]]
                elif site['id']=='fortifications':low=[[722,117],[699,130],[681,133],[654,134],[642,141],[629,144],[610,146],[592,139],[572,137],[553,138],[531,132],[516,128],[506,118]]
                else:low=[[555,160],[550,165],[536,171],[518,174],[495,175],[475,174],[454,173],[436,172],[421,168],[416,160],[417,155]]
                points=ROOFS[state]+low
            mask=poly(points)
            if state=='ship':
                mask=C.lighter(mask,poly([[753,347],[759,344],[764,345],[770,349],[782,349],[793,343],[796,346],[794,356],[786,362],[774,365],[762,363],[755,358]]))
            # Reconstructed hidden rear surfaces are used ONLY where foreground
            # source silhouettes project over the actual rear body.
            if site['id'] in ('civic-hall','fortifications','mage-guild','dwelling-tier-4') and src.startswith('../'):
                reveal=image('reveal-rear-native.png')
                foreground=union(poly(s['polygon']) for s in sites if s['z']>site['z'] and s['id'] not in ('coast','grail'))
                paint.paste(reveal,(0,0),C.multiply(mask,foreground))
            layer=paint.copy();layer.putalpha(mask)
            if scale!=1:
                # Permitted whole-family UNIFORM scale about its unchanged dry
                # frontal bearing root. No part motion, pose or painted repair.
                layer=layer.transform(SIZE,Image.Transform.AFFINE,(1/scale,0,anchor[0]-anchor[0]/scale,0,1/scale,anchor[1]-anchor[1]/scale),Image.Resampling.BICUBIC)
                mask=layer.getchannel('A').point(lambda p:255 if p>=128 else 0)
                layer.putalpha(mask)
                points=[mapped(q) for q in points]
            folder=root/'states'/state
            frames[state]=save(folder/'layer.png',layer)
            bodies[state]=mask;smasks.append(mask);allpaint[state]=layer
            provenance[state]={'source':ref(HERE/src),'silhouette_polygon':points,'source_native_scale':[800,374],'uniform_scale':scale,'fixed_scale_root':list(anchor) if scale!=1 else None,'method':'Whole painted source clipped at manually traced architectural silhouette; optional whole-family uniform scale. No part warps or recoloring.'}
            town['structures'][state]['x']=town['structures'][state]['y']=0;town['structures'][state]['z']=site['z']
            profile=C.multiply(line([mapped(q) for q in CONTACTS[site['id']]] if scale!=1 else CONTACTS[site['id']],3),mask)
            if state=='ship':profile=C.lighter(profile,C.multiply(line([[757,357],[764,362],[776,363],[786,360],[792,354]],3),mask))
            # Actual terrace bearing excludes external stair treads. The full
            # bearing chain is preserved on both sides of every doorway.
            profile=C.subtract(profile,stairs)
            foundations[state]=profile
            access=[mapped(q) for q in ACCESS[site['id']]] if scale!=1 else ACCESS[site['id']]
            site['access_points']=access
            door=C.multiply(line(access[:2],7),mask)
            doors[state]=door
            approaches[state]=line(access,3)
            # Door mask is the complete exterior stair/frontage corridor; own
            # body at its junction is a legitimate doorway, never a new road.
            doors[state]=C.lighter(door,C.multiply(approaches[state],mask))
        silhouettes[site['id']]=union(smasks)
    # Connect approaches to an actual lane network with cardinal free-space
    # routing. Waypoints constrain this to the painted packed-snow street areas.
    allbody=union(bodies.values());alldoor=union(doors.values())
    forbidden=C.subtract(allbody,alldoor)
    walkable=C.subtract(land,forbidden)
    def route(start,end):
        q=deque([tuple(start)]);prev={tuple(start):None};target=tuple(end)
        while q:
            x,y=q.popleft()
            if (x,y)==target:
                out=[];cur=target
                while cur is not None:out.append(cur);cur=prev[cur]
                return out[::-1]
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if 0<=nx<800 and 0<=ny<374 and (nx,ny) not in prev and walkable.getpixel((nx,ny)):
                    prev[(nx,ny)]=(x,y);q.append((nx,ny))
        raise ValueError('No actual ground connection '+str((start,end))+' visited='+str(len(prev))+' start_land='+str(walkable.getpixel(tuple(start)))+' target_land='+str(walkable.getpixel(tuple(end))))
    paths=blank();hub=(330,310)
    # Separate short approach from connected global paths; all access retains
    # actual all-state body avoidance. Do not erase bad annotation intersections.
    for site in sites:
        ap=site['access_points'];routepts=route(ap[-1],hub)
        paths=C.lighter(paths,line(routepts,1))
        for state in site['states']:
            approaches[state]=C.subtract(approaches[state],C.subtract(bodies[state],doors[state]))
    # Only the bounded level bearing pads around full traced contact chains
    # are annotated as support; sky, mountains and sheer cliff faces are not.
    support=C.subtract(C.multiply(union(foundations.values()).filter(ImageFilter.MaxFilter(13)),land),stairs)
    physical={}
    for site in sites:
        for state in site['states']:
            folder=masks/state
            rec={'access_kind':'moored-vessel' if state=='ship' else 'open-site' if state in ('marketplace','resourceSilo','special2','grail','dwellingLvl1','dwellingUpLvl1') else 'door',
                 'foundation_mask':save(folder/'foundation.png',foundations[state]),'door_mask':save(folder/'door.png',doors[state]),'approach_mask':save(folder/'approach.png',approaches[state]),'body_mask':save(folder/'body.png',bodies[state])}
            if site['id']=='coast':
                marine=C.multiply(foundations[state],water)
                if marine.getbbox():rec.update(marine_support_mask=save(folder/'marine.png',marine),marine_support_kind='moored-hull' if state=='ship' else 'deck-and-pilings')
            physical[state]=rec
            alpha=bodies[state]
            area=Image.new('RGBA',SIZE,(255,255,255,0));area.putalpha(alpha)
            border=Image.new('RGBA',SIZE,(255,220,90,0));border.putalpha(C.subtract(alpha.filter(ImageFilter.MaxFilter(3)),alpha))
            folder=root/'states'/state
            save(folder/'area.png',area);save(folder/'border.png',border)
            box=alpha.getbbox();icon=Image.new('RGBA',(150,70));crop=allpaint[state].crop(box);crop.thumbnail((142,64),Image.Resampling.LANCZOS);icon.alpha_composite(crop,((150-crop.width)//2,68-crop.height));save(folder/'icon.png',icon)
    bg=image('empty-coast-native.png');bgref=save(root/'background.png',bg)
    selected=sorted((s['full_state'] for s in sites if s['id']!='grail'),key=lambda s:town['structures'][s]['z'])
    def scene(states):
        out=bg.copy()
        for st in sorted(states,key=lambda s:town['structures'][s]['z']):out=Image.alpha_composite(out,allpaint[st])
        return out
    complete=scene(selected);complete_ref=save(root/'complete-native.png',complete)
    for label,states in [('empty',[]),('early',['villageHall','fort','tavern','dwellingLvl1']),('base',[s['states'][0] for s in sites if s['id'] not in ('coast','grail')]),('upgraded',[s['full_state'] for s in sites if s['id'] not in ('coast','grail')]),('grail',selected+['grail']),('coastal-ship',[s for s in selected if s!='shipyard']+['ship'])]:save(root/(label+'-native.png'),scene(states))
    rows=[];rootrows=[]
    for i,a in enumerate(sites):
        for b in sites[i+1:]:
            back,front=sorted((a,b),key=lambda s:s['z']);pair=back['id']+'--'+front['id'];inter=C.multiply(silhouettes[back['id']],silhouettes[front['id']])
            if not inter.getbbox():continue
            reason='The '+front['id']+' foreground roof/body projects in front of the '+back['id']+' upper terrace at the painted oblique camera; their entrances use separate snow lanes.'
            overlap_ref=save(masks/'overlaps'/(pair+'.png'),inter)
            rows.append(dict(behind=back['id'],front=front['id'],reason=reason,mask=overlap_ref))
            hidden=C.multiply(union(foundations[s] for s in back['states']),union(bodies[s] for s in front['states']))
            if hidden.getbbox():
                hr=save(masks/'root-projections'/(pair+'.png'),hidden)
                case={'kind':'supported-terrace-projection','behind':back['id'],'front':front['id'],'behind_depth':back['z'],'front_depth':front['z'],'rear_level':'Upper packed-snow bearing terrace of '+back['id'],'front_level':'Separate lower packed-snow bearing terrace of '+front['id'],'reason':reason,'hidden_pixels':hidden.histogram()[255],'hidden_bounds':list(hidden.getbbox()),'mask_sha256':hr['sha256'],'review_status':'Source candidate; coordinator pixel review required.'}
                cp=masks/'root-projections'/(pair+'.json');write(cp,case)
                # Optional Grail is absent from the default complete-state list.
                # Every case must nevertheless SHOW its exact front occluder,
                # and remove that same front from the corresponding comparison.
                case_states=selected.copy()
                if front['full_state'] not in case_states:case_states.append(front['full_state'])
                case_complete=scene(case_states)
                case_ref=complete_ref if case_states==selected else save(masks/'root-projections'/(pair+'-complete.png'),case_complete)
                overlay=case_complete.copy();red=Image.new('RGBA',SIZE,(255,0,100,190));overlay=Image.composite(red,overlay,hidden)
                rootrows.append(dict(behind=back['id'],front=front['id'],reason=reason,mask=hr,source_case=ref(cp),evidence={'complete_scene':case_ref,'front_absent_scene':save(masks/'root-projections'/(pair+'-front-absent.png'),scene([s for s in case_states if s not in front['states']])),'intersection_overlay':save(masks/'root-projections'/(pair+'-overlay.png'),overlay)}))
    outsites=[]
    for s in sites:
        box=silhouettes[s['id']].getbbox();outsites.append({'id':s['id'],'states':s['states'],'box':[box[0],box[1],box[2]-box[0],box[3]-box[1]],'entrance':s['door'],'depth':s['z'],'silhouette_mask':save(masks/(s['id']+'-silhouette.png'),silhouettes[s['id']]),**({'intentional_water':True} if s['id']=='coast' else {})})
    contract={'canvas':[800,374],'alpha_threshold':8,'geometry_mode':'silhouette-v2','ordinary_land_sites':16,'background':bgref,'land_mask':save(masks/'land.png',land),'frames':frames,'sites':outsites,'silhouette_plan':{'version':2,'support_mask':save(masks/'level-support.png',support),'stairs_mask':save(masks/'stairs.png',stairs),'water_mask':save(masks/'water.png',water),'paths_mask':save(masks/'paths.png',paths),'states':physical,'overlaps':rows,'foundation_occlusions':rootrows,'complete_scene':complete_ref,'complete_scene_states':selected}}
    write(root/'layout-contract.json',contract)
    write(root/'town-visuals.json',{'status':'authored configuration','visual_approval_granted':False,'layout_geometry_mode':'silhouette-v2','layout_contract':ref(root/'layout-contract.json'),'geometry_helper':{'path':'scripts/faction_town_layout.py','sha256':digest(WORKSPACE/'scripts/faction_town_layout.py')}})
    flavor=read(HERE/'flavor-deltas.json')
    assert digest(PROJECT/'content/factions.json')==flavor['baseline_factions_sha256']
    for delta in flavor['deltas']:
        parent=content
        for key in delta['pointer'][:-1]:parent=parent[key]
        key=delta['pointer'][-1]
        assert parent[key]==delta['old']
        parent[key]=delta['new']
    write(root/'factions.candidate.json',content);write(root/'state-provenance.json',provenance)
    common={'production_status':'delivered','status':'authored configuration','visual_approval_granted':False,'credits':{'author':'Built-in OpenAI imagegen saved painted masters; project deterministic extraction','license':None,'redistribution':'unresolved; release prohibited'},'inputs':[ref(Path(__file__)),ref(HERE/'silhouette-plan.json')]+[ref(p) for p in sorted(HERE.glob('*')) if p.is_file() and p.suffix in ('.png','.txt','.json') and not any(x in p.name for x in ('inspection','study','debug','review'))],'generation':{'image_generation_used':True,'method':'Saved whole-town painted2D sources, manually traced silhouettes, deterministic exact native crop/composition. No Blender or alternative3D. Poro family uniform0.88 scale about532,351 fixed ground root, all states and physical annotations together.'}}
    common['inputs'] += [ref(HERE.parent/name) for name in ('complete-master-v2.png','complete-master-v2-native.png','prompt-v2.txt','generation-v2.json')]
    common['generation']['whole_family_transforms']=[{'site':'dwelling-tier-1','uniform_scale':.88,'fixed_ground_root':[532,351],'scope':'Both base/upgrade whole native bodies, silhouettes, front bearing contacts, yard gate and access together'},{'site':'dwelling-tier-6','uniform_scale':.88,'fixed_ground_root':[695,330],'scope':'Both base/upgrade whole native bodies, silhouettes, front bearing contacts, door and access together'}]
    def raster(name,source,size):return {**copy.deepcopy(common),'recipe_type':'raster','source':ref(source)['path'],'source_sha256':digest(source),'source_canvas':size,'size':size,'canvas':size,'require_alpha':True,'output_path':PREFIX+name}
    recipes['town/background.json']=raster('town/background.png',root/'background.png',[800,374])
    icons=[];icondeps=[]
    ids={q['building']:q['frame'] for q in read(PROJECT/'assets/recipes/town/buildingIcons.json')['frames']}
    for state in sorted(frames):
        folder=root/'states'/state
        recipes['town/structures/'+state+'-animation.json']={**copy.deepcopy(common),'recipe_type':'vcmi_animation','canvas':[800,374],'pivot':{'x':0,'y':0},'output_path':PREFIX+'town/structures/'+state+'.json','groups':[{'group':0,'generateShadow':0,'generateOverlay':0,'frames':[{'source':frames[state]['path'],'source_sha256':frames[state]['sha256']}]}]}
        for role in ('area','border'):recipes['town/structures/'+state+'-'+role+'.json']=raster('town/structures/'+state+'_'+role+'.png',folder/(role+'.png'),[800,374])
        iconname='town/icons/'+state+'.json';ir=raster('town/icons/buildings/'+state+'.png',folder/'icon.png',[150,70]);recipes[iconname]=ir
        if state in ids:
            ip=root/'recipes'/iconname;write(ip,ir);dep='assets/recipes/'+iconname;icondeps.append(dep)
            icons.append({'building':state,'frame':ids[state],'source':'assets/generated/'+ir['output_path'],'sha256':digest(folder/'icon.png'),'generated_by':dep,'producer_sha256':digest(ip)})
    recipes['town/buildingIcons.json']={**copy.deepcopy(common),'recipe_type':'indexed_animation','canvas':[150,70],'output_path':PREFIX+'town/buildingIcons.json','depends_on':sorted(icondeps),'frames':icons}
    for name,recipe in recipes.items():write(root/'recipes'/name,recipe)
    write(root/'candidate-summary.json',{'status':'authored configuration','ordinary_land_sites':16,'states':36,'recipe_count':len(recipes),'full_master':ref(HERE.parent/'complete-master-v2-native.png'),'approved_coast':ref(HERE/'coast-town-native.png'),'helper_sha256':digest(WORKSPACE/'scripts/faction_town_layout.py'),'native_verified':False,'release_accepted':False,'foundation_projection_cases':len(rootrows)})
    print('Authored source candidate:',root)

if __name__=='__main__':make()
