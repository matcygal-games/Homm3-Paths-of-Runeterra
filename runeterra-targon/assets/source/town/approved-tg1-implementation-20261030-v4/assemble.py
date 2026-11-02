"""TG1 candidate extraction from immutable genuine 2D construction paintings.

Creates only this versioned source candidate and its uniquely named report.
No canonical recipe/content/manifest/generated/stage or native-game writes.
Architecture pixels are copied from the corresponding genuine painting; this
script creates technical masks, compositing, outlines and proportional icons.
"""
from collections import defaultdict
import hashlib
import io
import json
from pathlib import Path
import sys

from PIL import Image, ImageChops, ImageDraw, ImageOps

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
WORKSPACE = PROJECT.parent
PRIOR = HERE.parent/'approved-tg1-20261029-v1'
REPORT = WORKSPACE/'reports/targon-tg1-implementation-20261030-v4'
APPROVED = '964d3345bba9265ece58638d20de4ef15f6217ccde633ea0402b707f351aa669'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def encoded(value):
    return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()


def write(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=raw:
        raise ValueError('Versioned candidate changed; preserve and use a new revision: '+str(path))
    if not path.exists():
        with path.open('xb') as stream:
            stream.write(raw)


def dump(path,value):
    write(path,encoded(value))


def png(image):
    out=io.BytesIO()
    image.save(out,format='PNG',compress_level=9,optimize=False)
    return out.getvalue()


def save(path,image):
    write(path,png(image))


def image(path):
    with Image.open(path) as opened:
        opened.load()
        return opened.convert('RGBA')


def mask(points):
    if len(points)<3 or any(len(p)!=2 or any(type(v)is not int for v in p)
                            or not 0<=p[0]<800 or not 0<=p[1]<374 for p in points):
        raise ValueError('Explicit native source-pixel polygon required')
    out=Image.new('L',(800,374))
    ImageDraw.Draw(out).polygon([tuple(p)for p in points],fill=255)
    return out


def ref(path):
    return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}


def icon(layer,size):
    bbox=layer.getchannel('A').getbbox()
    if not bbox:
        raise ValueError('Empty selected building source')
    body=layer.crop(bbox)
    body.thumbnail((size[0]-4,size[1]-4),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',size)
    out.alpha_composite(body,((size[0]-body.width)//2,size[1]-body.height-2))
    return out


def assemble():
    if sha(PRIOR/'approved-full-native.png')!=APPROVED:
        raise ValueError('Approved TG1 full painting changed')
    annotations=read(HERE/'contours.json')
    prior=read(PRIOR/'candidate-frames.json')
    site_plan=read(PRIOR/'site-plan-v1.json')
    if set(annotations['sites'])!={s['id']for s in site_plan['sites']}:
        raise ValueError('All twenty actual physical forms must remain accounted for')
    content=read(PROJECT/'content/factions.json')
    town=content['targon']['town']
    if set(prior['states'])!=set(town['buildings']) or len(prior['states'])!=35:
        raise ValueError('All thirty-five actual native functions are required')
    paintings={'approved':image(PRIOR/'approved-full-native.png')}
    paintings.update({tag:image(PRIOR/(tag+'-states-native.png'))for tag in ('early','middle','late')})
    states={};layers={};unions={};full_union=Image.new('L',(800,374));complete=[]
    patch={};source_pins={}
    for name in ['approved-full-native.png','empty-recovery-native.png','candidate-frames.json','site-plan-v1.json',
                 'early-states-native.png','middle-states-native.png','late-states-native.png','generation-ledger.json']:
        source_pins[(PRIOR/name).relative_to(PROJECT).as_posix()]=sha(PRIOR/name)
    source_pins[Path(__file__).relative_to(PROJECT).as_posix()]=sha(Path(__file__))
    source_pins[(HERE/'contours.json').relative_to(PROJECT).as_posix()]=sha(HERE/'contours.json')
    for site in site_plan['sites']:
        key=site['id'];annotation=annotations['sites'][key]
        unions[key]=Image.new('L',(800,374))
        selected=site['states'][-1]
        complete.append(selected)
        for state in site['states']:
            record=prior['states'][state]
            points=annotations['state_outlines'].get(state,annotation['outline'])
            from PIL import ImageFilter
            body=mask(points).filter(ImageFilter.MaxFilter(9))
            if state==site['states'][-1]:
                split={'sunhawks':94,'guild':129,'fortifications':133,'lunari':232,'grail':252}.get(key)
                if split:
                    upper=mask(site['whole_form_polygon']).filter(ImageFilter.MaxFilter(11))
                    ImageDraw.Draw(upper).rectangle((0,split+1,799,373),fill=0)
                    body=ImageChops.lighter(body,upper)
                for addition in annotations.get('approved_additions',{}).get(key,[]):
                    body=ImageChops.lighter(body,mask(addition))
            tag=record['source_tag']
            layer=Image.new('RGBA',(800,374));layer.paste(paintings[tag],(0,0),body)
            frame=HERE/'frames'/(state+'.png');save(frame,layer)
            bodypath=HERE/'masks'/(state+'-body.png');save(bodypath,body)
            area=Image.new('RGBA',(800,374),(0,0,0,0));area.putalpha(body)
            area_path=HERE/'derived'/(state+'_area.png');save(area_path,area)
            from PIL import ImageFilter
            border=Image.new('RGBA',(800,374),(245,210,85,0))
            border.putalpha(ImageChops.subtract(body.filter(ImageFilter.MaxFilter(3)),body))
            border_path=HERE/'derived'/(state+'_border.png');save(border_path,border)
            campaign=HERE/'derived'/(state+'_campaign.png');save(campaign,icon(layer,(58,64)))
            construction=HERE/'construction'/(state+'.png');save(construction,icon(layer,(150,70)))
            states[state]={'site':key,'source_tag':tag,'painting':ref(PRIOR/('approved-full-native.png'if tag=='approved'else tag+'-states-native.png')),
                           'frame':ref(frame),'body':ref(bodypath),'area':ref(area_path),'border':ref(border_path),
                           'campaign':ref(campaign),'construction':ref(construction),'bbox':list(body.getbbox()),
                           'entrance':annotation['door'],'z':site['z'],'architecture_alpha_values':[0,255]}
            layers[state]=layer
            unions[key]=ImageChops.lighter(unions[key],body)
            patch[state]={'x':0,'y':0,'z':site['z']}
        full_union=ImageChops.lighter(full_union,layers[selected].getchannel('A'))
    # Only pixels that are completely covered by approved full architecture may
    # differ in the absence painting. All other approved pixels stay unchanged.
    full=paintings['approved']
    background=Image.composite(image(PRIOR/'empty-recovery-native.png'),full,full_union)
    save(HERE/'background-native.png',background)
    save(HERE/'approved-architecture-budget.png',full_union)
    complete.sort(key=lambda key:(patch[key]['z'],key))
    replay=background.copy()
    for state in complete:
        replay.alpha_composite(layers[state])
    if replay.tobytes()!=full.tobytes():
        raise ValueError('Approved TG1 full scene changed')
    save(HERE/'fully-built.png',replay)
    earliest=background.copy()
    for site in sorted(site_plan['sites'],key=lambda s:(s['z'],s['id'])):
        earliest.alpha_composite(layers[site['states'][0]])
    save(HERE/'earliest-all-sites.png',earliest)
    overlaps=[]
    for i,a in enumerate(site_plan['sites']):
        for b in site_plan['sites'][i+1:]:
            intersection=ImageChops.multiply(unions[a['id']],unions[b['id']])
            if intersection.getbbox():
                path=HERE/'masks/overlaps'/(a['id']+'--'+b['id']+'.png');save(path,intersection)
                overlaps.append({'site_a':a['id'],'site_b':b['id'],'mask':ref(path),
                                 'pixels':sum(v>0 for v in intersection.tobytes()),'bbox':list(intersection.getbbox())})
    frontage=[]
    for a in site_plan['sites']:
        x,y=annotations['sites'][a['id']]['door']
        for b in site_plan['sites']:
            if a is not b and b['z']>=a['z']and unions[b['id']].getpixel((x,y)):
                frontage.append({'rear':a['id'],'front':b['id'],'point':[x,y]})
    index={'status':'authored configuration','candidate_only':True,'native_verified':False,'release_accepted':False,
           'approved_full':ref(PRIOR/'approved-full-native.png'),'approved_full_RGBA_changes':0,
           'background':ref(HERE/'background-native.png'),'complete_scene_states':complete,'states':states,
           'native_structure_patch':patch,'source_pins':source_pins,'remaining_depth_intersections':overlaps,
           'obscured_frontage_points':frontage,
           'scope':'Exact approved architecture pixels and genuine lower paintings; technical manually traced alpha masks. Physical source interpretation and native acceptance remain separate.'}
    dump(HERE/'candidate-frames.json',index)
    REPORT.mkdir(parents=True,exist_ok=True)
    parts=['<!doctype html><meta charset="utf-8"><title>Targon TG1 source implementation</title>',
           '<style>body{background:#222;color:#eee;font:17px Georgia;max-width:1200px;margin:24px auto}img{max-width:100%}a{color:#edc}</style>',
           '<h1>Approved TG1 source candidate</h1><p>Authored configuration; no active recipe, stage or game changes. Approved full pixels preserved. Physical/native review remains separate.</p>']
    relative='../../'+HERE.relative_to(WORKSPACE).as_posix()
    for name,label in [('background-native.png','Empty recovered plate'),('earliest-all-sites.png','Every earliest state'),('fully-built.png','Approved fully built TG1, exact pixels')]:
        parts.append('<h2>'+label+'</h2><img width="800" height="374" src="'+relative+'/'+name+'">')
    for site in site_plan['sites']:
        sheet=Image.new('RGB',(400,160*len(site['states'])),(28,31,30));draw=ImageDraw.Draw(sheet)
        for n,state in enumerate(site['states']):
            f=layers[state];box=f.getchannel('A').getbbox();bg=Image.new('RGBA',f.size,(53,56,58,255));bg.alpha_composite(f)
            view=bg.crop(box).convert('RGB');view.thumbnail((390,132),Image.Resampling.NEAREST)
            sheet.paste(view,((400-view.width)//2,n*160+24));draw.text((7,n*160+5),state,fill='white')
        name=site['id']+'-states.png';save(REPORT/name,sheet)
        parts.append('<h2>'+site['id']+'</h2><img src="'+name+'">')
    write(REPORT/'index.html',('\n'.join(parts)+'\n').encode())
    print(json.dumps({'states':len(states),'physical_forms':len(site_plan['sites']),
                      'approved_full_RGBA_changes':0,'all_state_overlap_pairs':len(overlaps),'frontage_alerts':frontage}))
    return index


if __name__=='__main__':
    assemble()
