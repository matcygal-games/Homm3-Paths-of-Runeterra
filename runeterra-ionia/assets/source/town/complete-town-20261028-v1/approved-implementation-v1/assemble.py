"""Lossless approved IL4 town decomposition; no canonical or stage writes."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageChops,ImageFilter

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-ionia')
SIZE=(800,374)
APPROVED='f2e766e5a3c40c09e478d7944ac84996a7d96de26e3e415fe546e3174a2a0afc'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def image(p):return Image.open(p).convert('RGBA')
def mask(p):return Image.open(p).convert('L')
def ref(p):return {'path':rel(p),'sha256':sha(p)}
def union(items):
 o=Image.new('L',SIZE)
 for im in items:o=ImageChops.lighter(o,im)
 return o
def fit(im,size):
 r=min(size[0]/im.width,size[1]/im.height)
 return im.resize((max(1,round(im.width*r)),max(1,round(im.height*r))),Image.Resampling.LANCZOS)
def main():
 assert sha(HERE/'approved-full.png')==APPROVED,'Approved full drift'
 full=image(HERE/'approved-full.png');idx=read(BASE/'frame-index-v1.json');p=BASE/'physical-contract-v1'
 paths={s:BASE/'contour-repair-v2/revision-v2/masks'/f'{s}.png' for s in idx['frames'] if (BASE/'contour-repair-v2/revision-v2/masks'/f'{s}.png').exists()}
 paths.update({'blacksmith':p/'contour-proposal-v2/blacksmith-proposed-mask.png','special2':p/'lower-protector-contour-proposal-v3/special2-proposed-mask.png','dwellingLvl5':p/'lower-protector-contour-proposal-v3/dwellingLvl5-proposed-mask.png','dwellingUpLvl5':p/'right-institutions-contour-proposal-v3/protector-proposed-mask.png','special3':p/'right-institutions-contour-proposal-v3/gateway-proposed-mask.png','ship':p/'short-coast-contour-proposal-v5/ship-mask.png','shipyard':p/'short-dock-contour-proposal-v4/shipyard-mask.png'})
 alphas={s:mask(path) for s,path in paths.items()}
 corrections=read(HERE/'contour-corrections.json')
 for state,spec in corrections['states'].items():
  d=ImageDraw.Draw(alphas[state])
  for poly in spec.get('add',[]):d.polygon([tuple(q)for q in poly],fill=255)
  for poly in spec.get('remove',[]):d.polygon([tuple(q)for q in poly],fill=0)
 # Narrow technical edge matting: retain real mixed/native painted edges just
 # outside the held inward-cut roof profiles, never extend structural feet.
 for state,spec in corrections.get('edge_matting',{}).items():
  src=full if state in ('capitol','castle','dwellingUpLvl7','dwellingUpLvl5','special3','ship') else image(PROJECT/idx['frames'][state]['source_painting'])
  band=ImageChops.subtract(alphas[state].filter(ImageFilter.MaxFilter(9)),alphas[state]);a=alphas[state];ap=a.load();bp=band.load();rgb=src.load()
  for box in spec['bounds']:
   for y in range(box[1],box[3]):
    for x in range(box[0],box[2]):
     if not bp[x,y]:continue
     r,g,b,_=rgb[x,y]
     if spec['mode']=='warm-wood':keep=r>b+7 and r>g*1.03
     else:keep=not(b>r+25 and b>g+10 and (r+g+b)>390) and not(r>g*1.23 and b>g*1.05)
     if keep:ap[x,y]=255
 recovery=mask(p/'guild-plinth-recovery-proposal-v2/mageGuild3-hidden-recovery-mask.png')
 assert recovery.histogram()[255]==67
 alphas['mageGuild3']=ImageChops.lighter(alphas['mageGuild3'],recovery)
 highest=[r['states'][-1]for name,r in idx['sites'].items()if name not in ('coast','grail')]+['ship']
 frames={};sources={}
 for state,row in idx['frames'].items():
  if state=='grail':continue
  if state=='ship':source=BASE/'short-complete-pier-native-v1.png'
  elif state=='shipyard':source=BASE/'short-dock-only-native-v1.png'
  elif state in highest:source=HERE/'approved-full.png'
  else:source=PROJECT/row['source_painting']
  actor=image(source)
  if state=='mageGuild3':actor=Image.composite(image(BASE/'guild3-plinth-recovery-native-v1.png'),actor,recovery)
  actor.putalpha(alphas[state]);frames[state]=actor;sources[state]=ref(source)
 raw=BASE/'grail-lantern-master-v1.png';g=image(raw);g=fit(g.crop(g.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()),(19,35));actor=Image.new('RGBA',SIZE);actor.alpha_composite(g,(584-g.width//2,352-g.height));frames['grail']=actor;sources['grail']=ref(raw)
 architecture=union(frames[s].getchannel('A')for s in highest)
 # Actual scenery outside architecture retains approved whole-painting pixels.
 # Genuine empty terrain is used only under the extracted institution silhouettes.
 background=Image.composite(image(BASE/'empty-plate-native-v1.png'),full,architecture)
 def compose(states):
  out=background.copy()
  for s in sorted(states,key=lambda s:idx['frames'][s]['depth']):out.alpha_composite(frames[s])
  return out
 actual=compose(highest)
 assert actual.tobytes()==full.tobytes(),'Approved full decoded RGBA mismatch'
 out=HERE/'prepared';out.mkdir(exist_ok=True);background.save(out/'background.png')
 index={'status':'authored configuration','canvas':list(SIZE),'ordinary_land_sites':16,'sites':idx['sites'],'background':ref(out/'background.png'),'complete_scene':ref(HERE/'approved-full.png'),'complete_scene_states':sorted(highest,key=lambda s:idx['frames'][s]['depth']),'frames':{},'decoded_rgba_exact':True,'native_execution':False,'release_accepted':False}
 for state,actor in frames.items():
  folder=out/'structures'/state;folder.mkdir(parents=True,exist_ok=True);actor.save(folder/'layer.png',compress_level=9,optimize=False)
  a=actor.getchannel('A');rgba=Image.new('RGBA',SIZE,(255,255,255,0));rgba.putalpha(a.point(lambda n:255 if n>=8 else 0));rgba.save(folder/'area.png')
  edge=ImageChops.subtract(a.filter(ImageFilter.MaxFilter(3)),a.filter(ImageFilter.MinFilter(3))).point(lambda n:255 if n else 0);rgba.putalpha(edge);rgba.save(folder/'border.png')
  box=a.point(lambda n:255 if n>=8 else 0).getbbox();crop=actor.crop(box)
  for kind,canvas in [('campaign',(58,64)),('icon',(150,70))]:
   small=fit(crop,(canvas[0]-4,canvas[1]-4));icon=Image.new('RGBA',canvas);icon.alpha_composite(small,((canvas[0]-small.width)//2,canvas[1]-small.height));icon.save(folder/(kind+'.png'))
  row=idx['frames'][state];index['frames'][state]={'site':row['site'],'depth':row['depth'],'source_painting':sources[state]['path'],'source_painting_sha256':sources[state]['sha256'],'source_transform':'identity native architectural matte; separate raw Grail global fit','source_bounds':list(box),**ref(folder/'layer.png')}
 ordinary=[s for s in highest if s!='ship'];base=[r['states'][1]if site in('kinkou','protector')else r['states'][0]for site,r in idx['sites'].items()if site not in('coast','grail')]
 middle=[{'capitol':'townHall','castle':'citadel','mageGuild3':'mageGuild2'}.get(s,s)for s in ordinary]
 cases={'empty':[],'full':highest,'base':base,'middle':middle,'early':['villageHall','fort','tavern','dwellingLvl1','special1'],'dock':ordinary+['shipyard'],'grail':ordinary+['grail']}
 for site,record in idx['sites'].items():
  cases['absent-'+site]=[s for s in highest if s not in record['states']]
 for s in frames:cases['state-'+s]=[s]+[x for x in highest if idx['frames'][x]['site']!=idx['frames'][s]['site']]
 views=HERE/'views';views.mkdir(exist_ok=True)
 for name,states in cases.items():compose(states).save(views/(name+'.png'))
 dump(HERE/'frame-index.json',index)
 diff=ImageChops.difference(actual,full)
 dump(HERE/'reconstruction-check.json',{'status':'authored configuration','approved':ref(HERE/'approved-full.png'),'background':index['background'],'states':index['complete_scene_states'],'decoded_RGBA_sha256':hashlib.sha256(actual.tobytes()).hexdigest(),'approved_decoded_RGBA_sha256':hashlib.sha256(full.tobytes()).hexdigest(),'decoded_RGBA_equal':actual.tobytes()==full.tobytes(),'RGBA_difference_bounds':diff.getbbox(),'changed_pixels':sum(a!=b for a,b in zip(actual.getdata(),full.getdata())),'compilation_performed':False,'physical_verified':False,'native_execution':False})
 print(json.dumps({'frames':len(frames),'views':len(cases),'decoded_RGBA_equal':True,'frame_index':rel(HERE/'frame-index.json')}))
if __name__=='__main__':main()
