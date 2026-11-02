"""Source-only whole-master slicing and genuine painted state reconstruction.

Actual master RGB is retained wherever architecture is visible. Imagegen family
paintings supply lower construction states and occluded-face completion only.
No active recipes/content/manifests/stage/native writes are performed here.
"""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,shutil,sys
import numpy as np
from PIL import Image,ImageChops,ImageDraw,ImageFilter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];REPORT=ROOT/'build/reports/complete-town-20261027-v2'
spec=importlib.util.spec_from_file_location('zaun_complete_contours',HERE/'visible_contours.py');contours=importlib.util.module_from_spec(spec);spec.loader.exec_module(contours)
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT.parent/'scripts'))
import zaun_coastal_state_v1 as coast
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def binary(alpha,t=8):return alpha.point(lambda a:255 if a>=t else 0)
def population(im):return im.histogram()[255]

def components(binary_array):
 """Four-connected run-length components; masks only, never new artwork."""
 parents=[0];runs=[];previous=[]
 def find(a):
  while parents[a]!=a:parents[a]=parents[parents[a]];a=parents[a]
  return a
 def union(a,b):
  a,b=find(a),find(b)
  if a!=b:parents[max(a,b)]=min(a,b)
 for y,row in enumerate(binary_array):
  edges=np.flatnonzero(np.diff(np.r_[False,row,False]));current=[];cursor=0
  for x0,x1 in zip(edges[::2],edges[1::2]):
   x0,x1=int(x0),int(x1)
   while cursor<len(previous) and previous[cursor][1]<=x0:cursor+=1
   overlaps=[];j=cursor
   while j<len(previous) and previous[j][0]<x1:
    overlaps.append(previous[j][2]);j+=1
   if overlaps:
    label=overlaps[0]
    for other in overlaps[1:]:union(label,other)
   else:label=len(parents);parents.append(label)
   current.append((x0,x1,label));runs.append((y,x0,x1,label))
  previous=current
 stats={}
 for y,x0,x1,label in runs:
  label=find(label);s=stats.setdefault(label,{'area':0,'bbox':[x0,y,x1,y+1]});s['area']+=x1-x0;b=s['bbox'];s['bbox']=[min(b[0],x0),min(b[1],y),max(b[2],x1),max(b[3],y+1)]
 return runs,stats,find

def painted_family(family):
 path=HERE/'families'/family['id']/'provider-atlas-v1.png'
 if not path.is_file():return None
 im=Image.open(path).convert('RGBA');arr=np.array(im.getchannel('A'));runs,stats,find=components(arr>=128);n=len(family['states'])
 chosen=sorted(stats,key=lambda k:stats[k]['area'],reverse=True)[:n]
 if len(chosen)!=n:raise ValueError('Missing genuine family objects: '+family['id'])
 if n in (3,4):
  ordered=sorted(chosen,key=lambda k:(stats[k]['bbox'][1]+stats[k]['bbox'][3])/2);ordered=sorted(ordered[:2],key=lambda k:stats[k]['bbox'][0])+sorted(ordered[2:],key=lambda k:stats[k]['bbox'][0])
 else:ordered=sorted(chosen,key=lambda k:stats[k]['bbox'][0])
 result=[]
 for index,label in enumerate(ordered):
  mask=Image.new('L',im.size);draw=ImageDraw.Draw(mask)
  for y,x0,x1,k in runs:
   if find(k)==label:draw.line((x0,y,x1-1,y),fill=255)
  # Preserve genuine edge AA/contact pixels close to the actual object; remove
  # distant transparent-provider RGB haze and other atlas objects, never bodies.
  domain=mask.filter(ImageFilter.MaxFilter(7));alpha=ImageChops.multiply(im.getchannel('A'),domain);isolated=im.copy();isolated.putalpha(alpha);bb=binary(alpha).getbbox()
  if bb is None:raise ValueError('Empty genuine state')
  crop=isolated.crop(bb);folder=HERE/'families'/family['id']/'isolated';save(folder/(family['states'][index]+'.png'),crop)
  result.append({'state':family['states'][index],'source':rel(folder/(family['states'][index]+'.png')),'source_sha256':sha(folder/(family['states'][index]+'.png')),'raw_atlas':rel(path),'raw_atlas_sha256':sha(path),'object_bbox':bb,'structural_component_area':stats[label]['area'],'image':crop})
 return result

def polygon_mask(points):
 im=Image.new('L',(800,374));ImageDraw.Draw(im).polygon(points,fill=255);return im

def body_annotation(name):
 mask=polygon_mask(contours.CONTOURS[name]);limit=contours.GROUND_LIMITS.get(name)
 if limit:
  keep=polygon_mask([(limit[0][0],0),(limit[-1][0],0),*reversed(limit)]);mask=ImageChops.multiply(mask,keep)
 return mask

def register_proxy(crop,target_bbox,scale):
 """One family scale; whole-building projected root placement, no part warp."""
 w,h=max(1,round(crop.width*scale)),max(1,round(crop.height*scale));paint=crop.resize((w,h),Image.Resampling.LANCZOS);alpha=paint.getchannel('A');core=binary(alpha,248).filter(ImageFilter.MinFilter(3));alpha.paste(255,(0,0),core);paint.putalpha(alpha)
 x=round((target_bbox[0]+target_bbox[2]-w)/2);y=target_bbox[3]-h
 out=Image.new('RGBA',(800,374));out.alpha_composite(paint,(x,y));return out,{'uniform_family_scale':scale,'native_offset':[x,y],'native_size':[w,h]}

def derive():
 specs=read(HERE/'family-specs.json');families=specs['families'];master_path=HERE/'complete-design/native-v2.png';master=Image.open(master_path).convert('RGBA')
 if sha(master_path)!='14d5942fe3d7d157f29d13e086352c14c0c9cde63424b496a0ef26c3f52dee86':raise ValueError('Reviewed complete town changed')
 masks={f['id']:body_annotation(f['id']) for f in families};proxy={};family_rows={}
 for f in families:
  name=f['id'];cohort=painted_family(f);family_rows[name]=cohort
  if cohort:
   bb=masks[name].getbbox();scale=min((bb[2]-bb[0])/max(r['image'].width for r in cohort),(bb[3]-bb[1])/max(r['image'].height for r in cohort))
   for row in cohort:
    proxy[row['state']],registration=register_proxy(row['image'],bb,scale);row['registration']=registration
   if name=='shipyard':
    dock=cohort[0]['image'];proxy['shipyard'],registration=register_proxy(dock,(690,280,778,325),min(88/dock.width,45/dock.height));cohort[0]['registration']=registration
  print('Prepared genuine family '+name,flush=True)
 layers={};records=[];visible_masks={};whole_union=Image.new('L',(800,374));occlusions=[]
 for f in families:
  name=f['id'];own=masks[name];whole_union=ImageChops.lighter(whole_union,own);higher=Image.new('L',(800,374));relations=[]
  for other,mask in masks.items():
   if contours.DEPTHS[other]<=contours.DEPTHS[name]:continue
   overlap=ImageChops.multiply(own,mask)
   if overlap.getbbox():higher=ImageChops.lighter(higher,mask);relations.append({'front':other,'pixels':population(overlap)});occlusions.append({'behind':name,'front':other,'pixels':population(overlap)})
  visible=ImageChops.subtract(own,higher);visible_masks[name]=visible;hidden=ImageChops.subtract(own,visible);save(HERE/'master-masks'/(name+'-visible.png'),visible);save(HERE/'master-masks'/(name+'-complete-contour.png'),own);save(HERE/'master-masks'/(name+'-occluded.png'),hidden)
  developed=f['states'][-1]
  # New west-block painting also supplies genuine occluded edge completion of
  # its adjacent boiler plant; no old V1 source or synthetic painted fill.
  reconstruction=proxy.get(developed)
  if name=='shimmerFactory' and reconstruction is None:
   raw=family_rows.get('dwellingThug')
   if raw:
    pic=raw[-1]['image'];plant=pic.crop((0,0,max(1,round(pic.width*.32)),pic.height));bb=own.getbbox();reconstruction,_=register_proxy(plant,bb,min((bb[2]-bb[0])/plant.width,(bb[3]-bb[1])/plant.height))
  if hidden.getbbox() and reconstruction is None:raise ValueError('Genuine unseen-face completion missing: '+name+' '+str(relations))
  full=Image.new('RGBA',(800,374))
  if reconstruction is not None:
   completion=reconstruction.copy();completion.putalpha(ImageChops.multiply(completion.getchannel('A'),hidden));full.alpha_composite(completion)
  actual=master.copy();actual.putalpha(visible);full.alpha_composite(actual)
  if name=='shipyard':
   # Native ship replaces shipyard: retain the genuine painted boarding pier
   # behind the actual master-cut hull, never water-coloured opaque padding.
   moored=proxy['shipyard'].copy();moored.alpha_composite(full);full=moored
  for state in f['states']:
   if state==developed:layer=full.copy();route='Actual reviewed whole-master visible RGB cut, with genuine painted completion only where another selected institution occludes it.'
   else:
    if state not in proxy:raise ValueError('Missing genuine lower construction painting: '+state)
    layer=proxy[state].copy();route='Genuine painted lower construction state from this exact reviewed whole-town architectural family, one uniform family scale.'
    if state=='dwellingLvl2':
     # Align the smaller workshop's actual right-side loading frontage with the
     # same exposed east street as its developed parent, beyond market canopies.
     aligned=Image.new('RGBA',(800,374));aligned.alpha_composite(layer,(15,0));layer=aligned
   # Shared city-front surfaces remain fixed scenery. The visible architectural
   # plane ends at its traced permanent court/parapet boundary in every state.
   if name in contours.GROUND_LIMITS:
    g=contours.GROUND_LIMITS[name];clip=polygon_mask([(0,0),(799,0),(799,g[-1][1]),*reversed(g),(0,g[0][1])]);layer.putalpha(ImageChops.multiply(layer.getchannel('A'),clip))
   layers[state]=layer;folder=HERE/'structures'/state
   for kind,picture in coast.surfaces(layer).items():save(folder/(kind+'.png'),picture)
   record={'state':state,'site':name,'native_layer':rel(folder/'layer.png'),'native_layer_sha256':sha(folder/'layer.png'),'native_z':contours.DEPTHS[name],'actual_alpha8_bbox':binary(layer.getchannel('A')).getbbox(),'actual_alpha128_bbox':binary(layer.getchannel('A'),128).getbbox(),'route':route,'whole_master':rel(master_path),'whole_master_sha256':sha(master_path),'visible_master_mask':rel(HERE/'master-masks'/(name+'-visible.png')),'visible_master_mask_sha256':sha(HERE/'master-masks'/(name+'-visible.png')),'whole_contour':rel(HERE/'master-masks'/(name+'-complete-contour.png')),'whole_contour_sha256':sha(HERE/'master-masks'/(name+'-complete-contour.png')),'occluded_master_mask':rel(HERE/'master-masks'/(name+'-occluded.png')),'occluded_master_mask_sha256':sha(HERE/'master-masks'/(name+'-occluded.png')),'provider_inputs':[{k:v for k,v in r.items() if k!='image'} for r in (family_rows.get(name) or [])],'visible_master_rgb_restyled':False if state==developed else None,'native_visual_review':'pending','release_accepted':False};records.append(record)
 # Matching empty painting contributes ONLY inside removed functional source
 # silhouettes/contact halo. Unrelated city infrastructure stays byte-identical.
 empty_painted=Image.open(HERE/'background/native-empty-v2.png').convert('RGBA');removal=whole_union.filter(ImageFilter.MaxFilter(5));background=empty_painted.copy();save(HERE/'background/removal-mask.png',removal);save(HERE/'background/assembled-native.png',background)
 for variant in ('empty','early','base','upgraded','coastal','moored','grail'):
  scene=background.copy()
  for f in sorted(families,key=lambda f:contours.DEPTHS[f['id']]):
   name=f['id'];state=f['states'][0 if variant in ('base','early') else -1]
   if variant=='empty':continue
   if variant=='early' and name not in ('foundryHall','grog','dwellingThug','dwellingRavager','scrapExchange'):continue
   if name=='codeOfProgress' and variant!='grail':continue
   if name=='shipyard':state='ship' if variant in ('moored','grail') else 'shipyard' if variant=='coastal' else None
   if state:scene.alpha_composite(layers[state])
  save(REPORT/(variant+'-native.png'),scene)
 allscene=background.copy()
 for f in sorted(families,key=lambda f:contours.DEPTHS[f['id']]):allscene.alpha_composite(layers[f['states'][-1]])
 save(REPORT/'all-developed-reassembly-native.png',allscene)
 write(HERE/'derived-state-plan.json',{'status':'authored configuration','whole_master':rel(master_path),'whole_master_sha256':sha(master_path),'native_canvas':[800,374],'whole_master_checkpoint':rel(HERE/'complete-design/review-checkpoint.json'),'whole_master_checkpoint_sha256':sha(HERE/'complete-design/review-checkpoint.json'),'contour_annotations':rel(HERE/'visible_contours.py'),'contour_annotations_sha256':sha(HERE/'visible_contours.py'),'deriver':rel(Path(__file__)),'deriver_sha256':sha(Path(__file__)),'background':rel(HERE/'background/assembled-native.png'),'background_sha256':sha(HERE/'background/assembled-native.png'),'states':records,'occlusions':occlusions,'source_only':True,'active_source_changed':False,'native_verified':False,'release_accepted':False})
 print('Derived36actualsource states and matching source reassemblies; no canonical write.',flush=True)

if __name__=='__main__':derive()
