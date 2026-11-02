"""Bind explicit semantic annotations to a released real town-frame cohort.

This produces owned technical source masks and the existing silhouette-v2
contract. It never edits source-owner frames, recipes, canonical data or helpers.
No annotation is inferred from a desired passing footing result.
"""
from pathlib import Path
import argparse,hashlib,json,re,sys
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
WORKSPACE=PROJECT.parent
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_town_layout as actual


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def encoded(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def source(name,pin):
 p=actual._direct_reference_path(PROJECT,name)
 if sha(p)!=pin:raise ValueError('Released source changed: '+name)
 return p

def image(p):
 im=Image.open(p).convert('RGBA')
 if im.size!=(800,374):raise ValueError('Native image required')
 return im

def blank():return Image.new('L',(800,374))
def union(values):
 out=blank()
 for im in values:out=ImageChops.lighter(out,im)
 return out

def trace(definition):
 # These are explicit manual semantic shapes, never bounding-box substitutes.
 out=blank();draw=ImageDraw.Draw(out)
 for poly in definition.get('polygons',[]):draw.polygon([tuple(p) for p in poly],fill=255)
 for line in definition.get('lines',[]):draw.line([tuple(p) for p in line['points']],fill=255,width=line['width'])
 for xy in definition.get('pixels',[]):draw.point(tuple(xy),fill=255)
 if not out.getbbox():raise ValueError('Manual semantic annotation is empty')
 return out


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--index',required=True)
 parser.add_argument('--index-sha256',required=True)
 parser.add_argument('--annotations',required=True)
 parser.add_argument('--out-name',required=True)
 args=parser.parse_args()
 if not re.fullmatch('[a-z0-9-]+',args.out_name):raise ValueError('Unique direct output name required')
 index_path=source(args.index,args.index_sha256)
 annotation_path=Path(args.annotations).resolve()
 if not annotation_path.is_relative_to(HERE):raise ValueError('Annotations must be owned source')
 annotations=read(annotation_path);index=read(index_path)
 if annotations['state_index_sha256']!=args.index_sha256:raise ValueError('Annotations bind another cohort')
 background=source(annotations['background']['path'],annotations['background']['sha256'])
 if set(annotations['states'])!=set(index['states']):raise ValueError('Every real state requires an explicit semantic record')
 out=HERE/args.out_name;out.mkdir(exist_ok=False)
 report=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1'/args.out_name
 report.mkdir(parents=True,exist_ok=False)
 def save_mask(name,mask):
  dest=out/(name+'.png');mask.convert('RGB').save(dest);return ref(dest)
 terrain={}
 for role in ('land','support','stairs','water','paths'):
  value=annotations['terrain'][role];path=source(value['path'],value['sha256'])
  terrain[role]=ref(path)
 # A vertical retaining face is land ownership, not a walkable street.
 # This authoring guard strengthens the truthful semantic annotation without
 # changing the unchanged public consumer or declaring any new runtime field.
 terrain_masks={role:actual._binary_mask(PROJECT,value,set(),role,empty=role in ('stairs','water')) for role,value in terrain.items()}
 if ImageChops.subtract(terrain_masks['paths'],ImageChops.lighter(terrain_masks['support'],terrain_masks['stairs'])).getbbox():
  raise ValueError('Authored street crosses unwalkable retaining face/unclassified terrain')
 frames={};bodies={};full={};physical={};site_states={}
 for key,row in index['states'].items():
  frame_path=source(row['frame'],row['frame_sha256'])
  frame=image(frame_path);frames[key]=ref(frame_path)
  full[key]=frame.getchannel('A').point(lambda a:255 if a>=8 else 0)
  bodies[key]=frame.getchannel('A').point(lambda a:255 if a>=128 else 0)
  site_states.setdefault(row['site'],[]).append(key)
  authored=annotations['states'][key]
  if not isinstance(authored.get('contact_interpretation'),str) or len(authored['contact_interpretation'])<30:
   raise ValueError('Whole semantic contact explanation required: '+key)
  masks={role:trace(authored[role]) for role in ('foundation','door','approach')}
  # Only genuinely visible selected contact pixels become the footing mask.
  # The manual source trace remains preserved verbatim for outline review.
  masks['foundation']=ImageChops.multiply(masks['foundation'],full[key])
  if not masks['foundation'].getbbox():raise ValueError('No real visible manual contact: '+key)
  selected={'access_kind':authored['access_kind'],'entrance':authored['entrance'],
   'body_mask':save_mask(key+'-body',bodies[key])}
  for role,mask in masks.items():selected[role+'_mask']=save_mask(key+'-'+role,mask)
  if 'marine_support_kind' in authored:
   selected['marine_support_kind']=authored['marine_support_kind']
   marine=trace(authored['marine_support'])
   selected['marine_support_mask']=save_mask(key+'-marine',marine)
  physical[key]=selected
  # Evidence is an actual source composition plus labelled technical overlays.
  scene=image(background);scene.alpha_composite(frame)
  for role,color in [('foundation',(255,200,20)),('door',(255,30,150)),('approach',(30,240,100))]:
   over=Image.new('RGBA',(800,374),color+(0,));over.putalpha(masks[role].point(lambda p:170 if p else 0));scene=Image.alpha_composite(scene,over)
  scene.convert('RGB').save(report/(key+'-contact-overlay.png'))
 sites=[];silhouettes={}
 for site_id,keys in site_states.items():
  data=annotations['sites'][site_id]
  silhouette=union(full[k] for k in keys);silhouettes[site_id]=silhouette
  x0,y0,x1,y1=silhouette.getbbox()
  depths={index['states'][k]['z'] for k in keys}
  if len(depths)!=1:raise ValueError('Family z values differ: '+site_id)
  sites.append({'id':site_id,'states':keys,'box':[x0,y0,x1-x0,y1-y0],
   'depth':depths.pop(),'entrance':data['entrance'],
   'intentional_water':site_id=='coast','silhouette_mask':save_mask(site_id+'-silhouette',silhouette)})
 if len(sites)!=18:raise ValueError('Actual Bilgewater requires16 ordinary sites + coast/Grail')
 overlaps=[]
 for row in annotations['overlaps']:
  a,b=row['behind'],row['front']
  mask=ImageChops.multiply(silhouettes[a],silhouettes[b])
  if not mask.getbbox():raise ValueError('Authored overlap has no actual pixels: '+a+'/'+b)
  overlaps.append({'behind':a,'front':b,'reason':row['reason'],'mask':save_mask(a+'--'+b+'-overlap',mask)})
 complete=annotations['complete_scene_states']
 scene=image(background)
 for key in complete:scene.alpha_composite(image(PROJECT/frames[key]['path']))
 scene_path=out/'complete-scene.png';scene.save(scene_path)
 # Explicit visual cases preserve the real selected family relationships and
 # actual native z order supplied by the source owner; no generic ghost states.
 for name,selection in annotations.get('evidence_scenes',{}).items():
  composition=image(background)
  for key in selection:composition.alpha_composite(image(PROJECT/frames[key]['path']))
  composition.save(out/('scene-'+name+'.png'))
  composition.convert('RGB').save(report/('scene-'+name+'.png'))
 contract={'canvas':[800,374],'alpha_threshold':8,'geometry_mode':'silhouette-v2',
  'ordinary_land_sites':16,'background':ref(background),'land_mask':terrain['land'],
  # The unchanged source consumer recursively verifies/exports every path/SHA
  # reference, including these editable technical production inputs.
  'editable_sources':[ref(annotation_path),ref(index_path),ref(Path(__file__).resolve())]+annotations.get('selected_editable_sources',[]),
  'frames':frames,'sites':sites,'silhouette_plan':{'version':2,
  'support_mask':terrain['support'],'stairs_mask':terrain['stairs'],'water_mask':terrain['water'],
  'paths_mask':terrain['paths'],'states':physical,'overlaps':overlaps,
  'foundation_occlusions':annotations.get('foundation_occlusions',[]),
  'complete_scene_states':complete,'complete_scene':ref(scene_path)}}
 dest=out/'layout-contract.json';dest.write_bytes(encoded(contract))
 receipt={'status':'authored configuration','state_index':ref(index_path),'annotations':ref(annotation_path),
  'contract':ref(dest),'frames':frames,'source_owner_frames_modified':False,
  'public_consumer_run':False,'native_executed':False,'release_accepted':False}
 (report/'binding-receipt.json').write_bytes(encoded(receipt))
 print(json.dumps(receipt['contract']))

if __name__=='__main__':main()
