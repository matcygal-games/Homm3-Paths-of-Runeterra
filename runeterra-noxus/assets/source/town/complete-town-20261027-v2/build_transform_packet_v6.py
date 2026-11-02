"""Exact root-reviewed whole-family transforms; no canonical mutation."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageOps,ImageChops,ImageFilter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'native-transforms-v6'
DELTAS={'dwellingLvl4':(9,0),'dwellingUpLvl4':(9,0),'dwellingLvl1':(11,-10),'dwellingUpLvl1':(11,-10),'marketplace':(11,-19)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def alpha(im,t):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
def move(im,delta):out=Image.new(im.mode,im.size);out.paste(im,delta);return out
def main():
 s=load(HERE/'candidate-final-v5/selection.json');entries={r['state']:r for r in load(HERE/'entry-spans-v3/entries.json')['states']};records=[]
 for row in s['states']:
  state=row['state'];source=ROOT/row['native_layer'];im=Image.open(source).convert('RGBA');e=entries[state];foundation=Image.open(HERE/'physical-v10'/state/'foundation.png').convert('L');zone=Image.open(HERE/'physical-v10'/state/'manual-semantic-ground-zone.png').convert('L');entry=Image.open(ROOT/e['mask']['path']).convert('L');treads=Image.open(ROOT/e['own_treads']['path']).convert('L');anchor=list(e['entrance']);z=row['native_z'];transform=None;original=im.copy()
  if state in DELTAS:
   dx,dy=DELTAS[state];im=move(im,(dx,dy));foundation=move(foundation,(dx,dy));zone=move(zone,(dx,dy));entry=move(entry,(dx,dy));treads=move(treads,(dx,dy));anchor=[anchor[0]+dx,anchor[1]+dy];z+=dy;transform={'kind':'whole-native-translation','delta':[dx,dy]}
   if alpha(im,8).histogram()!=alpha(original,8).histogram():raise ValueError('Translation clipped '+state)
  elif state=='special2':
   bb=alpha(im,8).getbbox();xy=(710,104);size=(62,52)
   def fit(old,mode):out=Image.new(old.mode,(800,374));out.paste(old.crop(bb).resize(size,mode),xy);return out
   im=fit(im,Image.Resampling.LANCZOS);zone=fit(zone,Image.Resampling.NEAREST);entry=fit(entry,Image.Resampling.NEAREST);treads=fit(treads,Image.Resampling.NEAREST);anchor=[xy[0]+round((anchor[0]-bb[0])*.9),xy[1]+round((anchor[1]-bb[1])*.9)];z=156;transform={'kind':'whole-native-uniform-scale','scale':.9,'pivot':[733.5,158],'offset':[8,-2],'source_alpha8_crop':list(bb),'native_position':list(xy),'native_size':list(size)}
   body=alpha(im,128);foundation=Image.new('L',(800,374));p=body.load();q=zone.load();d=foundation.load()
   for x in range(xy[0],xy[0]+size[0]):
    ys=[y for y in range(xy[1],xy[1]+size[1]) if p[x,y]]
    if not ys:continue
    bottom=ys[-1]
    if not q[x,bottom]:raise ValueError('Unclassified actual scaled Hall foot '+str((x,bottom)))
    for y in range(bottom,bottom-4,-1):
     if not p[x,y] or not q[x,y]:break
     d[x,y]=255
   if foundation.histogram()[255]!=235:raise ValueError('Actual Hall full foot differs from reviewed235 '+str(foundation.histogram()[255]))
  folder=OUT/state
  if transform:
   save(folder/'layer.png',im);solid=alpha(im,128);area=Image.new('RGBA',(800,374),(255,255,255,0));area.putalpha(solid);border=Image.new('RGBA',(800,374),(255,230,100,0));border.putalpha(ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(5)),solid));save(folder/'area.png',area);save(folder/'border.png',border);frame=ref(folder/'layer.png')
   for name,img in [('foundation',foundation),('semantic-zone',zone),('body',solid),('silhouette',alpha(im,8)),('entry',entry),('own-treads',ImageChops.multiply(treads,alpha(im,8)))]:save(folder/(name+'.png'),img)
   foundation_ref=ref(folder/'foundation.png');body_ref=ref(folder/'body.png');silhouette_ref=ref(folder/'silhouette.png');entry_ref=ref(folder/'entry.png');treads_ref=ref(folder/'own-treads.png');zone_ref=ref(folder/'semantic-zone.png')
   crop=alpha(im,8).getbbox();icon=Image.new('RGBA',(150,70));small=ImageOps.contain(im.crop(crop),(146,66),Image.Resampling.LANCZOS);icon.alpha_composite(small,((150-small.width)//2,68-small.height));save(folder/'construction.png',icon)
  else:
   frame=ref(source);foundation_ref=ref(HERE/'physical-v10'/state/'foundation.png');body_ref=ref(HERE/'physical-v10'/state/'body.png');silhouette_ref=ref(HERE/'physical-v10'/state/'silhouette.png');entry_ref=e['mask'];treads_ref=e['own_treads'];zone_ref=ref(HERE/'physical-v10'/state/'manual-semantic-ground-zone.png')
  records.append({'state':state,'site':row['site'],'frame':frame,'native_z':z,'alpha8_bbox':list(alpha(im,8).getbbox()),'foundation_mask':foundation_ref,'body_mask':body_ref,'silhouette_mask':silhouette_ref,'semantic_zone_mask':zone_ref,'door_mask':entry_ref,'own_treads_mask':treads_ref,'entrance':anchor,'transform':transform,'source_before':ref(source),'painted_master':{'path':row['master'],'sha256':row['master_sha256']},'actual_foundation_pixels':foundation.histogram()[255],'construction':ref(folder/'construction.png') if transform else None})
 write(OUT/'states.json',{'status':'authored configuration','script':ref(Path(__file__)),'base_selection':ref(HERE/'candidate-final-v5/selection.json'),'base_entries':ref(HERE/'entry-spans-v3/entries.json'),'states':records,'ordinary_land_sites':17,'native_verified':False,'release_accepted':False});print(json.dumps({'index':ref(OUT/'states.json'),'transformed_states':sum(bool(r['transform'])for r in records)}))
if __name__=='__main__':main()
