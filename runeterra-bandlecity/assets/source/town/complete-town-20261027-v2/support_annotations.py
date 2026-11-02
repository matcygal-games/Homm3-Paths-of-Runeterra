"""Actual full-column foundation controls for the reviewed complete town.

Masks annotate observed terrain surfaces only; no finished artwork is drawn.
Source-pixel support is separate from native construction and human acceptance.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageChops, ImageDraw

HERE=Path(__file__).resolve().parent
SIZE=(800,374)
REAR=('guild','hall','fortification','dwelling7')
STAIRS={
 'tree_path_connection':[[126,77],[154,74],[153,91],[144,104],[124,104]],
 'hall_front_connection':[[213,129],[242,129],[243,153],[211,154]],
 'eastern_civic_connection':[[585,128],[611,128],[614,154],[584,154]],
 'western_near_connection':[[120,254],[147,254],[145,280],[113,283]],
 'central_near_connection':[[318,256],[343,256],[348,289],[315,291]],
}
CLIFFS={
 'western_civic_bank_face':[[0,125],[197,127],[195,158],[0,159]],
 'central_civic_bank_face':[[246,132],[579,132],[579,162],[246,159]],
 'eastern_civic_bank_face':[[619,148],[799,148],[799,174],[619,167]],
}
LANDINGS={
 'guild':[[8,82],[124,82],[124,123],[8,123]],
 'hall':[[145,89],[315,89],[315,127],[145,127]],
 'fortification':[[320,90],[536,90],[536,131],[320,131]],
 'dwelling7':[[645,105],[799,105],[799,151],[645,151]],
}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def polygon_mask(polygons):
    image=Image.new('L',SIZE)
    draw=ImageDraw.Draw(image)
    for points in polygons.values():draw.polygon([tuple(p) for p in points],fill=255)
    return image

def contact_profile(layer):
    """Include every actual occupied root/base/shadow column in the low band.

    Alpha8 retains faint source shadow/root edges; using a 24%-height lower
    band is deliberately conservative and includes intentional front steps.
    It is not a centrepoint, square plot or last-toe heuristic.
    """
    mask=layer.getchannel('A').point(lambda value:255 if value>=8 else 0)
    box=mask.getbbox()
    if not box:raise ValueError('Empty full painted building')
    band=max(8,round((box[3]-box[1])*.24))
    mask.paste(0,(0,0,SIZE[0],max(0,box[3]-band)))
    return mask

def profile_errors(profile, stairs, cliffs, landing=None):
    errors=[]
    if ImageChops.multiply(profile,stairs).getbbox():errors.append('foundation/root/shadow profile intersects observed terrain stair treads')
    if ImageChops.multiply(profile,cliffs).getbbox():errors.append('foundation/root/shadow profile intersects observed vertical civic bank face')
    if landing is not None and ImageChops.subtract(profile,landing).getbbox():errors.append('full rear foundation profile leaves its observed broad level landing')
    return errors

def prepare(design,layers):
    directory=HERE/'support';directory.mkdir(parents=True,exist_ok=True)
    stairs=polygon_mask(STAIRS);cliffs=polygon_mask(CLIFFS)
    stairs.save(directory/'terrain-stair-exclusion.png');cliffs.save(directory/'terrain-cliff-exclusion.png')
    masks={}
    for name,polygon in LANDINGS.items():
        mask=polygon_mask({name:polygon})
        mask=ImageChops.subtract(mask,ImageChops.lighter(stairs,cliffs))
        mask.save(directory/('level-landing-'+name+'.png'));masks[name]=mask
    rows=[];files=[Path(__file__),directory/'terrain-stair-exclusion.png',directory/'terrain-cliff-exclusion.png',
                 *[directory/('level-landing-'+name+'.png') for name in LANDINGS]]
    for site in design['sites']:
        if site['id'] in {'coast','grailOrnament'}:continue
        for state in site['states']:
            profile=contact_profile(layers[state]);path=directory/'profiles'/(state+'.png');path.parent.mkdir(parents=True,exist_ok=True);profile.save(path)
            errors=profile_errors(profile,stairs,cliffs,masks.get(site['id']))
            columns=[]
            for x in range(SIZE[0]):
                strip=profile.crop((x,0,x+1,SIZE[1]));box=strip.getbbox()
                if box:
                    unsupported=0 if site['id'] not in masks else sum(ImageChops.subtract(strip,masks[site['id']].crop((x,0,x+1,SIZE[1]))).histogram()[128:])
                    columns.append({'x':x,'low_y':box[1],'high_y':box[3]-1,'occupied_profile_pixels':sum(strip.histogram()[128:]),'unsupported_level_pixels':unsupported})
            rows.append({'site':site['id'],'state':state,'profile':path.relative_to(HERE).as_posix(),'sha256':sha(path),
                         'profile_pixels':sum(profile.histogram()[128:]),'occupied_columns':columns,'errors':errors})
            files.append(path)
    report={'status':'authored configuration','complete_town_first':True,'rear_level_landings':LANDINGS,
            'observed_terrain_stair_polygons':STAIRS,'observed_vertical_bank_polygons':CLIFFS,
            'source_complete_town_master':'complete-design/native.png','source_complete_town_sha256':sha(HERE/'complete-design/native.png'),
            'derived_background':'background/native.png','derived_background_sha256':sha(HERE/'background/native.png'),
            'profile_method':'Actual alpha>=8 lower24percent-of-building-height profile, every occupied root/base/shadow column, union checked per individual state; no rectangle-only or centerpoint support claim.',
            'intentional_entrance_steps':'Architecture-owned entrance steps remain part of painted building profiles. External terrain steps begin below/between their level landings.',
            'states':rows,'ok':all(not row['errors'] for row in rows),'native_verified':False,'release_accepted':False}
    path=directory/'foundation-annotations.json';path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');files.append(path)
    complete=Image.open(HERE/'complete-design/native.png').convert('RGBA')
    overlay=Image.new('RGBA',SIZE)
    for mask,color in [(stairs,(255,75,75,145)),(cliffs,(220,70,220,100))]:
        colored=Image.new('RGBA',SIZE,color);colored.putalpha(mask.point(lambda v:round(v*color[3]/255)));overlay.alpha_composite(colored)
    for mask in masks.values():
        colored=Image.new('RGBA',SIZE,(60,255,90,75));colored.putalpha(mask.point(lambda v:round(v*75/255)));overlay.alpha_composite(colored)
    complete.alpha_composite(overlay);complete.save(directory/'complete-town-support-annotation.png');files.append(directory/'complete-town-support-annotation.png')
    return report,files
