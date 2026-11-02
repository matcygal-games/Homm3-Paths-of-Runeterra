"""Pixel-following contact annotation inside manually read semantic ground zones.

The source pixels are read-only. A roof/eave/tail is never automatically ground:
the final contiguous opaque edge must lie inside the explicit manual native
wall/plinth/stair-foot zone. All other source pixels retain full silhouettes.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageChops
from semantic_ground_points_v1 import GROUND_POINTS,EAVE_POINTS
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=HERE/'physical-v9'
REPORT=ROOT/'build/reports/complete-town-20261027-v2/semantic-v9'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def alpha(im,t):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
def main():
 selection=load(HERE/'candidate-clearance-v2/selection.json');old={r['state']:r for r in load(HERE/'physical-v7/annotations.json')['states']};records=[];layers={};roots={}
 for row in selection['states']:
  state=row['state'];im=Image.open(ROOT/row['native_layer']).convert('RGBA');body=alpha(im,128);zone=Image.new('L',(800,374));points=old[state]['manual_native_contact_polyline'];ImageDraw.Draw(zone).line([tuple(p) for p in points],fill=255,width=20);
  for gx,gy in GROUND_POINTS[state]:ImageDraw.Draw(zone).rectangle((gx-1,gy-4,gx+1,gy+1),fill=255)
  root=Image.new('L',(800,374));p=body.load();z=zone.load();dest=root.load();bb=body.getbbox();rejected=[]
  for x in range(bb[0],bb[2]):
   ys=[y for y in range(bb[1],bb[3]) if p[x,y]]
   if not ys:continue
   bottom=ys[-1]
   if not z[x,bottom]:rejected.append([x,bottom]);continue
   # Trace the real contiguous ground-facing edge, not sparse alpha specks.
   for y in range(bottom,max(bb[1]-1,bottom-4),-1):
    if not p[x,y] or not z[x,y]:break
    dest[x,y]=255
  if not root.getbbox():raise ValueError('Empty semantic contact '+state)
  if {tuple(p) for p in rejected}!={tuple(p) for p in EAVE_POINTS.get(state,[])}:raise ValueError('Unclassified excluded source endpoint '+state+': '+str(rejected))
  folder=OUT/state;save(folder/'foundation.png',root);save(folder/'manual-semantic-ground-zone.png',zone);save(folder/'body.png',body);save(folder/'silhouette.png',alpha(im,8));view=im.copy();color=Image.new('RGBA',(800,374),(20,255,220,0));color.putalpha(root);view.alpha_composite(color);bb=alpha(im,8).getbbox();save(folder/'contact-review-4x.png',view.crop(bb).resize(((bb[2]-bb[0])*4,(bb[3]-bb[1])*4),Image.Resampling.NEAREST));layers[state]=im;roots[state]=root
  records.append({'state':state,'site':row['site'],'depth':row['native_z'],'layer':row['native_layer'],'layer_sha256':sha(ROOT/row['native_layer']),'manual_native_contact_polyline':points,'additional_manually_classified_ground_points':GROUND_POINTS[state],'manual_classification_source_sha256':sha(HERE/'semantic_ground_points_v1.py'),'semantic_zone_width':20,'semantic_zone_sha256':sha(folder/'manual-semantic-ground-zone.png'),'excluded_opaque_column_endpoints_outside_semantic_zone':rejected,'foundation':(folder/'foundation.png').relative_to(ROOT).as_posix(),'foundation_sha256':sha(folder/'foundation.png'),'pixels':root.histogram()[255],'bbox':list(root.getbbox()),'status':'authored configuration','review_required':'Manual semantic-zone truth and full ground-contact adequacy must be independently reviewed.'})
 sites={s['id']:s for s in selection['sites']};pairs=[]
 for a in sites.values():
  ru=Image.new('L',(800,374))
  for s in a['states']:ru=ImageChops.lighter(ru,roots[s])
  for b in sites.values():
   if a['native_z']>=b['native_z']:continue
   bu=Image.new('L',(800,374))
   for s in b['states']:bu=ImageChops.lighter(bu,alpha(layers[s],128))
   hit=ImageChops.multiply(ru,bu)
   if not hit.getbbox():continue
   combinations=[]
   for rs in a['states']:
    for fs in b['states']:
     m=ImageChops.multiply(roots[rs],alpha(layers[fs],128))
     if m.getbbox():combinations.append({'rear_state':rs,'front_state':fs,'pixels':m.histogram()[255],'bbox':list(m.getbbox())})
   folder=REPORT/(a['id']+'--'+b['id']);save(folder/'intersection.png',hit);pairs.append({'behind':a['id'],'front':b['id'],'pixels':hit.histogram()[255],'bbox':list(hit.getbbox()),'state_pairs':combinations})
 write(OUT/'annotations.json',{'status':'authored configuration','script_sha256':sha(Path(__file__)),'method':'Contiguous selected alpha128 ground-facing edge strictly inside individually manually annotated native wall/plinth/foot zones; no global all-column ground assumption.','states':records});write(REPORT/'all-state-contact-intersections.json',{'status':'authored configuration','states':len(records),'pairs':pairs,'approved':False});print(json.dumps({'states':len(records),'pairs':[(r['behind'],r['front'],r['pixels']) for r in pairs]}))
if __name__=='__main__':main()
