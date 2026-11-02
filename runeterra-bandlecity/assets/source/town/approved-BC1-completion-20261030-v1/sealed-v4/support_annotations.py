"""BC1 observed painted terraces, steps and full source support profiles."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent
SIZE=(800,374)
REAR=('guild','hall','fortification','dwelling7')
STAIRS={
 'western_bridge_descent':[[135,98],[158,98],[166,123],[135,123]],
 'hall_front_steps':[[384,119],[417,119],[417,147],[383,147]],
 'central_lower_descent':[[405,204],[438,204],[440,246],[414,246]],
 'western_lower_descent':[[139,198],[172,198],[174,222],[142,222]],
 'foreground_descent':[[293,229],[322,229],[325,266],[295,266]],
 'eastern_steps':[[750,279],[776,279],[775,319],[750,319]],
}
CLIFFS={
 'civic_bridge_elevation':[[217,101],[282,101],[282,123],[217,123]],
 'western_mid_bank':[[0,194],[130,194],[132,222],[0,222]],
 'central_mid_bank':[[181,206],[397,206],[398,230],[181,230]],
 'eastern_mid_bank':[[549,227],[735,227],[737,243],[549,243]],
}
LANDINGS={
 'guild':[[146,62],[241,62],[243,96],[160,101],[146,97]],
 'fortification':[[230,55],[296,55],[296,100],[230,100]],
 'hall':[[303,84],[479,84],[479,119],[303,119]],
 'dwelling7':[[587,110],[723,110],[723,146],[587,146]],
}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def polygon_mask(polygons):
 image=Image.new('L',SIZE);draw=ImageDraw.Draw(image)
 for points in polygons.values():draw.polygon(points,fill=255)
 return image
def contact_profile(layer):
 mask=layer.getchannel('A').point(lambda a:255 if a>=8 else 0);box=mask.getbbox()
 if not box:raise ValueError('Empty full painted building')
 band=max(8,round((box[3]-box[1])*.24));mask.paste(0,(0,0,800,max(0,box[3]-band)))
 return mask
def profile_errors(profile,stairs,cliffs,landing=None):
 errors=[]
 if ImageChops.multiply(profile,stairs).getbbox():errors.append('foundation/root profile intersects observed terrain stair treads')
 if ImageChops.multiply(profile,cliffs).getbbox():errors.append('foundation/root profile intersects observed vertical civic bank face')
 if landing is not None and ImageChops.subtract(profile,landing).getbbox():errors.append('full rear foundation profile leaves observed level landing')
 return errors
def prepare(design,layers):
 directory=HERE/'support';directory.mkdir(parents=True,exist_ok=True)
 stairs=polygon_mask(STAIRS);cliffs=polygon_mask(CLIFFS)
 stairs.save(directory/'terrain-stair-exclusion.png');cliffs.save(directory/'terrain-cliff-exclusion.png')
 masks={};files=[Path(__file__),directory/'terrain-stair-exclusion.png',directory/'terrain-cliff-exclusion.png']
 for name,points in LANDINGS.items():
  mask=ImageChops.subtract(polygon_mask({name:points}),ImageChops.lighter(stairs,cliffs));path=directory/('level-landing-'+name+'.png');mask.save(path);masks[name]=mask;files.append(path)
 rows=[]
 for site in design['sites']:
  if site['id'] in ('coast','grailOrnament'):continue
  for state in site['states']:
   profile=contact_profile(layers[state]);path=directory/'profiles'/(state+'.png');path.parent.mkdir(parents=True,exist_ok=True);profile.save(path);files.append(path)
   errors=profile_errors(profile,stairs,cliffs,masks.get(site['id']));columns=[]
   for x in range(800):
    strip=profile.crop((x,0,x+1,374));box=strip.getbbox()
    if box:
     unsupported=0 if site['id'] not in masks else ImageChops.subtract(strip,masks[site['id']].crop((x,0,x+1,374))).histogram()[255]
     columns.append({'x':x,'low_y':box[1],'high_y':box[3]-1,'occupied_profile_pixels':strip.histogram()[255],'unsupported_level_pixels':unsupported})
   rows.append({'site':site['id'],'state':state,'profile':path.relative_to(HERE).as_posix(),'sha256':sha(path),'profile_pixels':profile.histogram()[255],'occupied_columns':columns,'errors':errors})
 record={'status':'authored configuration','complete_town_first':True,'states':rows,'ok':not any(r['errors'] for r in rows),
   'observed_terrain_stair_polygons':STAIRS,'observed_vertical_bank_polygons':CLIFFS,'rear_level_landings':LANDINGS,
   'scope':'Source-pixel support only; native drawing/clicks and user visual acceptance separate.'}
 target=directory/'foundation-annotations.json';target.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');files.append(target)
 return record,files
