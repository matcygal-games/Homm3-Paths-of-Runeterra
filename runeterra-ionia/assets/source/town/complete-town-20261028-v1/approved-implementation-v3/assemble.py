"""Lossless approved IL4 town decomposition; no canonical or stage writes."""
from pathlib import Path
import hashlib,json,math
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
 full=image(HERE/'approved-full.png');idx=read(HERE/'native-state-map.json');p=BASE/'physical-contract-v1'
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
 coast=read(HERE/'coast-matte.json');empty_water=image(BASE/'empty-plate-native-v1.png')
 d=ImageDraw.Draw(alphas['ship']);d.polygon([tuple(q)for q in coast['ship_hull']],fill=255)
 rigging=Image.new('L',SIZE);rd=ImageDraw.Draw(rigging)
 for segment in coast['ship_rigging']:rd.line([tuple(q)for q in segment],fill=255,width=3)
 box=rigging.getbbox()
 for y in range(box[1],box[3]):
  for x in range(box[0],box[2]):
   if not rigging.getpixel((x,y)):continue
   r,g,b,_=full.getpixel((x,y));er,eg,eb,_=empty_water.getpixel((x,y))
   if g<eg-12 or(r>er+18 and r>b+4):alphas['ship'].putpixel((x,y),255)
 # Recover actual dark timber rail/brace pixels that the inherited blue-water
 # key wrongly removed. This bounded band is above the wet hull/deck seam;
 # bright cyan/purple water/reflection pixels are never an opaque timber fill.
 for y in range(202,223):
  for x in range(0,90):
   r,g,b,_=full.getpixel((x,y))
   if(r>g*1.08 and b<r*.88)or(g<70 and b<80 and abs(r-g)<40):alphas['ship'].putpixel((x,y),255)
 rigging_ownership=read(HERE/'rigging-ownership.json')
 separation=read(HERE/'source-separation.json')
 for site,spec in separation['sites'].items():
  boundary=[tuple(q)for q in spec['boundary']]
  keep=Image.new('L',SIZE);d=ImageDraw.Draw(keep);d.polygon([(0,0),(799,0),(799,boundary[-1][1]),*list(reversed(boundary)),(0,boundary[0][1])],fill=255)
  for poly in spec.get('retain',[]):d.polygon([tuple(q)for q in poly],fill=255)
  for state in idx['sites'][site]['states']:alphas[state]=ImageChops.multiply(alphas[state],keep)
 alphas['mageGuild3']=ImageChops.lighter(alphas['mageGuild3'],recovery)
 highest=[r['states'][-1]for name,r in idx['sites'].items()if name not in ('coast','grail')]+['ship']
 frames={};sources={}
 for state,row in idx['frames'].items():
  if state=='grail':continue
  if state=='ship':source=HERE/'approved-full.png'
  elif state=='shipyard':source=BASE/'short-dock-only-native-v1.png'
  elif state in highest:source=HERE/'approved-full.png'
  else:source=PROJECT/row['source_painting']
  actor=image(source)
  if state=='mageGuild3':actor=Image.composite(image(BASE/'guild3-plinth-recovery-native-v1.png'),actor,recovery)
  actor.putalpha(alphas[state]);frames[state]=actor;sources[state]=ref(source)
 raw=BASE/'grail-lantern-master-v1.png';g=image(raw);g=fit(g.crop(g.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()),(19,35));actor=Image.new('RGBA',SIZE);actor.alpha_composite(g,(584-g.width//2,352-g.height));frames['grail']=actor;sources['grail']=ref(raw)
 # Exact inverse matting of genuine thin painted ropes and flag edges against
 # the already genuine clean-water absence plate. No water texture is drawn.
 ownership_region=Image.new('L',SIZE);rd=ImageDraw.Draw(ownership_region)
 for line in rigging_ownership['segments']:rd.line([tuple(q)for q in line['points']],fill=255,width=line['width'])
 for poly in rigging_ownership['polygons']:rd.polygon([tuple(q)for q in poly],fill=255)
 ownership_region=ownership_region.filter(ImageFilter.MaxFilter(3))
 recovered_water=empty_water.copy();recovered_water.paste(image(PROJECT/rigging_ownership['recovered_water']['path']),tuple(rigging_ownership['recovered_water_box'][:2]))
 # Limit the authored contour buffer to actual painted nautical ink/edges,
 # excluding ordinary surrounding water. Threshold measures required inverse
 # coverage against the genuine recovery; it never creates water pixels.
 actual_ownership=Image.new('L',SIZE)
 for y in range(174,220):
  for x in range(12,86):
   if not ownership_region.getpixel((x,y)):continue
   target=full.getpixel((x,y))[:3];back=recovered_water.getpixel((x,y))[:3];needed=0.
   for t,bg in zip(target,back):
    if t<bg and bg:needed=max(needed,(bg-t)/bg)
    elif t>bg and bg<255:needed=max(needed,(t-bg)/(255-bg))
   if needed*255>=55:actual_ownership.putpixel((x,y),255)
 edge_draw=ImageDraw.Draw(actual_ownership)
 for line in rigging_ownership['observed_edge_fragments']:edge_draw.line([tuple(q)for q in line['points']],fill=255,width=line['width'])
 ownership_region=actual_ownership
 rigging_pixels=0
 for y in range(170,223):
  for x in range(6,86):
   if not ownership_region.getpixel((x,y)) or frames['ship'].getpixel((x,y))[3]==255:continue
   target=full.getpixel((x,y))[:3];back=recovered_water.getpixel((x,y))[:3]
   if target==back:continue
   needed=0.
   for t,bg in zip(target,back):
    if t<bg and bg:needed=max(needed,(bg-t)/bg)
    elif t>bg and bg<255:needed=max(needed,(t-bg)/(255-bg))
   alpha=min(255,max(32,math.ceil(needed*255)+2));rgb=[]
   for t,bg in zip(target,back):
    wanted=max(0,min(255,round((t*255-bg*(255-alpha))/alpha)))
    candidates=[n for n in range(max(0,wanted-2),min(255,wanted+2)+1)if(n*alpha+bg*(255-alpha)+127)//255==t]
    if not candidates:raise ValueError('Actual rigging edge cannot reconstruct source')
    rgb.append(min(candidates,key=lambda n:abs(n-wanted)))
   frames['ship'].putpixel((x,y),tuple(rgb)+(alpha,));rigging_pixels+=1
 shadow_records={}
 water_region=Image.new('L',SIZE);wd=ImageDraw.Draw(water_region)
 for poly in read(HERE/'terrain-plan.json')['water_polygons']:wd.polygon([tuple(q)for q in poly],fill=255)
 for state,native in [('ship','short-complete-pier-native-v1.png'),('shipyard','short-dock-only-native-v1.png')]:
  painted=image(BASE/native);region=Image.new('L',SIZE);ImageDraw.Draw(region).polygon([tuple(q)for q in coast[state+'_shadow']],fill=255);region=ImageChops.multiply(region,water_region);region=ImageChops.subtract(region,frames[state].getchannel('A'));box=region.getbbox();changed=0
  for y in range(box[1],box[3]):
   for x in range(box[0],box[2]):
    if not region.getpixel((x,y)) or (state=='ship' and ownership_region.getpixel((x,y))):continue
    target=painted.getpixel((x,y))[:3];back=empty_water.getpixel((x,y))[:3]
    if target==back:continue
    needed=0.
    for t,bg in zip(target,back):
     if t<bg and bg:needed=max(needed,(bg-t)/bg)
     elif t>bg and bg<255:needed=max(needed,(t-bg)/(255-bg))
    alpha=min(255,max(32,math.ceil(needed*255)+2));rgb=[max(0,min(255,round((t*255-bg*(255-alpha))/alpha)))for t,bg in zip(target,back)]
    # Exact native integer compositing, checked channel-by-channel. This is
    # inverse matte extraction of existing painted colours, never code artwork.
    for channel,(t,bg)in enumerate(zip(target,back)):
     candidates=[n for n in range(max(0,rgb[channel]-2),min(255,rgb[channel]+2)+1)if (n*alpha+bg*(255-alpha)+127)//255==t]
     if not candidates:raise ValueError('Painted water alpha cannot reconstruct source exactly')
     rgb[channel]=min(candidates,key=lambda n:abs(n-rgb[channel]))
    frames[state].putpixel((x,y),tuple(rgb)+(alpha,));changed+=1
  shadow_records[state]={'painted_source':ref(BASE/native),'empty_water':ref(BASE/'empty-plate-native-v1.png'),'shadow_pixels':changed,'method':'Exact inverse alpha extraction of bounded existing painted water shadow against genuine clean water. Opaque timber/ropes remain separate.'}
 dump(HERE/'coast-matte-receipt.json',{'status':'authored configuration','states':shadow_records,'new_rigging_edge_pixels':rigging_pixels,'rigging_ownership':ref(HERE/'rigging-ownership.json'),'genuine_recovered_water':ref(PROJECT/rigging_ownership['recovered_water']['path']),'artwork_created_by_code':False})
 underlaps=read(HERE/'rear-underlap-plan.json');underlap_records={}
 for state,spec in underlaps['states'].items():
  native=image(HERE/spec['native']);painted=frames[state].copy();painted.paste(native,tuple(spec['box'][:2]));hidden=ImageChops.multiply(frames[state].getchannel('A'),frames[spec['foreground']].getchannel('A'));frame=Image.composite(painted,frames[state],hidden);frame.putalpha(frames[state].getchannel('A'));frames[state]=frame
  path=HERE/'rear-underlap-inputs'/(state+'-incorporation-mask.png');hidden.save(path)
  underlap_records[state]={'foreground':spec['foreground'],'native':ref(HERE/spec['native']),'box':spec['box'],'incorporation_mask':ref(path),'incorporated_pixels':hidden.histogram()[255]}
 dump(HERE/'rear-underlap-incorporation.json',{'status':'authored configuration','repairs':underlap_records,'approved_full_pixel_change_permitted':False})
 architecture=union(frames[s].getchannel('A').point(lambda a:255 if a else 0)for s in highest)
 # Actual scenery outside architecture retains approved whole-painting pixels.
 # Genuine empty terrain is used only under the extracted institution silhouettes.
 background=Image.composite(image(BASE/'empty-plate-native-v1.png'),full,architecture)
 background=Image.composite(recovered_water,background,ownership_region)
 hidden_plan=read(HERE/'hidden-bed-plan.json')
 hidden_records={}
 for name,spec in hidden_plan['crops'].items():
  state={'guild':'mageGuild3','harmony':'special4','inn':'tavern'}[name]
  patch=image(HERE/'hidden-bed-inputs'/(name+'-native.png'));painted=background.copy();painted.paste(patch,tuple(spec['box'][:2]));region=Image.new('L',SIZE);x0,y0,x1,y1=spec['native_bed'];ImageDraw.Draw(region).rectangle((x0,y0,x1-1,y1-1),fill=255)
  protected=ImageChops.multiply(region,frames[state].getchannel('A').point(lambda a:255 if a==255 else 0));background=Image.composite(painted,background,protected)
  hp=HERE/'hidden-bed-inputs'/(name+'-incorporation-mask.png');protected.save(hp)
  hidden_records[name]={'master':ref(HERE/'hidden-bed-inputs'/(name+'-master.png')),'native':ref(HERE/'hidden-bed-inputs'/(name+'-native.png')),'placement':spec['box'],'incorporation_mask':ref(hp),'protection':'All incorporated pixels covered by exact opaque approved actor '+state}
 dump(HERE/'hidden-bed-incorporation.json',{'status':'authored configuration','repairs':hidden_records,'approved_full_pixel_change_permitted':False})
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
  row=idx['frames'][state];secondary=[]
  if state in underlap_records:secondary.extend([underlap_records[state]['native'],underlap_records[state]['incorporation_mask']])
  if state=='mageGuild3':secondary.extend([ref(BASE/'guild3-plinth-recovery-native-v1.png'),ref(p/'guild-plinth-recovery-proposal-v2/mageGuild3-hidden-recovery-mask.png')])
  if state in shadow_records:secondary.extend([shadow_records[state]['painted_source'],shadow_records[state]['empty_water'],ref(HERE/'coast-matte.json'),ref(HERE/'rigging-ownership.json')])
  transform='Native registered whole-canvas extraction, protected genuine rear underlaps; separate raw Grail global fit'
  if state in shadow_records:transform+='; exact inverse-alpha extraction of the source-painted water reflection against the genuine empty water plate'
  index['frames'][state]={'site':row['site'],'depth':row['depth'],'source_painting':sources[state]['path'],'source_painting_sha256':sources[state]['sha256'],'secondary_sources':secondary,'source_transform':transform,'source_bounds':list(box),**ref(folder/'layer.png')}
 ordinary=[s for s in highest if s!='ship'];base=[r['states'][1]if site in('kinkou','protector')else r['states'][0]for site,r in idx['sites'].items()if site not in('coast','grail')]
 middle=[{'capitol':'townHall','castle':'citadel','mageGuild3':'mageGuild2'}.get(s,s)for s in ordinary]
 cases={'empty':[],'full':highest,'base':base,'middle':middle,'early':['villageHall','fort','tavern','dwellingLvl1','special1'],'dock':ordinary+['shipyard'],'grail':ordinary+['grail']}
 for site,record in idx['sites'].items():
  cases['absent-'+site]=[s for s in highest if s not in record['states']]
 for s in frames:cases['state-'+s]=[s]+[x for x in highest if idx['frames'][x]['site']!=idx['frames'][s]['site']]
 views=HERE/'views';views.mkdir(exist_ok=True)
 for name,states in cases.items():compose(states).save(views/(name+'.png'))
 dump(HERE/'frame-index.json',index)
 # Flat current source closure: no rejected historical RGB frames, private
 # official-control files, absolute source paths or removed mesh dependencies.
 dependencies={}
 def add(path):
  if not path.is_file():raise ValueError('Missing actual editable input '+str(path))
  dependencies[rel(path)]=ref(path)
 def references(value):
  if isinstance(value,dict):
   if isinstance(value.get('path'),str)and isinstance(value.get('sha256'),str):add(PROJECT/value['path'])
   for child in value.values():references(child)
  elif isinstance(value,list):
   for child in value:references(child)
 for name in ('approved-full.png','approved-empty-review.png','selection.json','native-state-map.json','assemble.py','convert_repairs.py','contour-corrections.json','terrain-plan.json','coast-matte.json','coast-matte-receipt.json','rigging-ownership.json','source-separation.json','hidden-bed-plan.json','hidden-bed-incorporation.json','rear-underlap-plan.json','rear-underlap-incorporation.json','painted-repairs-provenance.json'):add(HERE/name)
 for path in paths.values():add(path)
 for record in sources.values():add(PROJECT/record['path'])
 for row in idx['frames'].values():add(PROJECT/row['source_painting'])
 for path in (BASE/'painted-source-provenance-v3.json',BASE/'empty-plate-native-v1.png',BASE/'guild3-plinth-recovery-native-v1.png',BASE/'grail-lantern-master-v1.png',p/'guild-plinth-recovery-proposal-v2/mageGuild3-hidden-recovery-mask.png'):add(path)
 for record in (read(BASE/'painted-source-provenance-v3.json'),read(HERE/'painted-repairs-provenance.json'),read(HERE/'hidden-bed-incorporation.json'),read(HERE/'rear-underlap-incorporation.json'),read(HERE/'coast-matte-receipt.json')):references(record)
 dump(HERE/'art-source-inputs.json',{'status':'authored configuration','method':'Flat portable closure of actual authored source inputs and genuine painted2D master/prompt ancestry. PNG masters are editable frozen artwork; nondeterministic image generation is never rerun by the compiler. Current technical replay reads these exact declared own inputs.','dependencies':[dependencies[n]for n in sorted(dependencies)],'native_execution':False,'release_accepted':False})
 diff=ImageChops.difference(actual,full)
 dump(HERE/'reconstruction-check.json',{'status':'authored configuration','approved':ref(HERE/'approved-full.png'),'background':index['background'],'states':index['complete_scene_states'],'decoded_RGBA_sha256':hashlib.sha256(actual.tobytes()).hexdigest(),'approved_decoded_RGBA_sha256':hashlib.sha256(full.tobytes()).hexdigest(),'decoded_RGBA_equal':actual.tobytes()==full.tobytes(),'RGBA_difference_bounds':diff.getbbox(),'changed_pixels':sum(a!=b for a,b in zip(actual.getdata(),full.getdata())),'compilation_performed':False,'physical_verified':False,'native_execution':False})
 print(json.dumps({'frames':len(frames),'views':len(cases),'decoded_RGBA_equal':True,'frame_index':rel(HERE/'frame-index.json')}))
if __name__=='__main__':main()
