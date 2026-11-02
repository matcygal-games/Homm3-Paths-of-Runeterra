"""Project genuine painted textile onto explicit 2D equipment surfaces.

Body/action pixels, alpha, scale and source roots remain byte-identical outside
the authored material masks. This is the established T1 physical-plane method.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageOps
import copy,hashlib,json,sys
import assemble_packets as common
S=common.SOURCE;P=common.PROJECT;R=common.REPORT/'heraldry-v1'
CONFIG=json.loads((S/'heraldry-planes-v1.json').read_text())
def perspective(quad,width,height):
 rows=[];rhs=[]
 for (x,y),(u,v) in zip(quad,[(0,0),(width,0),(width,height),(0,height)]):
  rows += [[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]];rhs += [u,v]
 for i in range(8):
  j=max(range(i,8),key=lambda j:abs(rows[j][i]));rows[i],rows[j]=rows[j],rows[i];rhs[i],rhs[j]=rhs[j],rhs[i]
  k=rows[i][i];assert abs(k)>1e-10;rows[i]=[v/k for v in rows[i]];rhs[i]/=k
  for j in range(8):
   if j==i:continue
   k=rows[j][i];rows[j]=[a-k*b for a,b in zip(rows[j],rows[i])];rhs[j]-=k*rhs[i]
 return rhs
def project(base,quad,occluders=()):
 texture=Image.open(S/'heraldry-cloth-raw.png').convert('RGBA');texture=texture.crop((35,20,texture.width-25,texture.height-20))
 factor=4;largequad=[(x*factor,y*factor) for x,y in quad]
 coefficient=perspective(largequad,texture.width,texture.height)
 paint=texture.transform((base.width*factor,base.height*factor),Image.Transform.PERSPECTIVE,coefficient,Image.Resampling.BICUBIC).resize(base.size,Image.Resampling.LANCZOS)
 physical=Image.new('L',base.size);draw=ImageDraw.Draw(physical);draw.polygon(quad,fill=255)
 for polygon in occluders:draw.polygon(polygon,fill=0)
 mask=ImageChops.multiply(paint.getchannel('A'),physical)
 # Cloth cannot occupy air or make the actor opaque outside its selected body.
 mask=ImageChops.multiply(mask,base.getchannel('A'))
 result=Image.composite(paint,base,mask);result.putalpha(base.getchannel('A'))
 difference=ImageChops.difference(result.convert('RGB'),base.convert('RGB'))
 outside=Image.composite(difference,Image.new('RGB',base.size),ImageChops.invert(physical))
 assert outside.getbbox() is None and result.getchannel('A').tobytes()==base.getchannel('A').tobytes()
 return result,mask,difference.getbbox()
def holding():
 units=sorted(json.loads((P/'content/creatures.json').read_text()));board=Image.new('RGBA',(900,220*len(units)),(40,40,40,255));draw=ImageDraw.Draw(board);records=[]
 for i,unit in enumerate(units):
  recipe=json.loads((S/'inputs/technical-recipes'/unit/'battle.json').read_text());frame=next(g for g in recipe['groups'] if g['group']==2)['frames'][0]
  base=Image.open(P/frame['source']).convert('RGBA')
  if unit in ('desertNomad','sandWarrior'):
   prior=P/'assets/source/regional-crests-20261025-v1/creatures/t1-actions-v2/recipes'/unit/'battle.json';rr=json.loads(prior.read_text());ff=next(g for g in rr['groups'] if g['group']==2)['frames'][0];after=Image.open(P/ff['source']).convert('RGBA');mask=Image.new('L',base.size);bbox=None
  else:after,mask,bbox=project(base,CONFIG['units'][unit]['quad'])
  common.png(S/'heraldry-v1'/unit/'holding.png',after);common.png(S/'heraldry-v1'/unit/'holding-mask.png',mask)
  for col,im in enumerate((base,after)):
   crop=im.crop((105,130,330,285));bg=common.checkbg(crop.size);bg.alpha_composite(crop);board.paste(bg,(col*225,i*220+20))
  crop=after.crop((170,205,275,270));bg=common.checkbg(crop.size);bg.alpha_composite(crop);board.paste(bg.resize((315,195),Image.Resampling.NEAREST),(460,i*220+20))
  draw.text((2,i*220),unit+' before / after /3x detail',fill='white')
  records.append({'unit':unit,'input':common.descriptor(P/frame['source']),'output':common.descriptor(S/'heraldry-v1'/unit/'holding.png'),'material_difference_bbox':bbox,'alpha_unchanged':base.getchannel('A').tobytes()==after.getchannel('A').tobytes(),'visual_approval_granted':False})
 common.png(R/'holding-comparison-native-and-3x.png',board);common.put(R/'holding-inventory-v1.json',records)
 common.png(R/'holding-comparison-part1.png',board.crop((0,0,900,1540)))
 common.png(R/'holding-comparison-part2.png',board.crop((0,1540,900,3080)))
 print(json.dumps({'holding_variants':len(records),'preview':str(R/'holding-comparison-native-and-3x.png')}))
def movequad(q,dx=0,dy=0):return [[x+dx,y+dy] for x,y in q]
def annotated_plane(unit,name,g,index,holding_sha,frame_sha):
 q=copy.deepcopy(CONFIG['units'][unit]['quad']);occlusion=[];note='Visible attached physical cloth plane'
 if frame_sha==holding_sha:return q,occlusion,note
 n=name.lower();chimera='Chimera' in unit;rock='Rockbear' in unit or unit=='rockbear';runner=unit in ('ruinRunner','duneVeteran');machine='Sunforged' in unit or unit=='sunforgedColossus'
 if chimera:
  if 'flight' in n or g==0:
   q=[[245,195],[256,198],[254,212],[244,209]]
   if 'flight-3' in n or index==3:q=[[250,202],[256,204],[256,215],[251,213]];note='Near downstroke wing naturally hides left part of neck tab'
  elif 'takeoff-lift' in n:q=movequad(q,0,-12)
  elif 'landing-flare' in n:q=movequad(q,0,-12)
  elif 'landing-contact' in n or 'crouch' in n:q=movequad(q,2,5)
  elif 'attack-up' in n:q=movequad(q,-1,-8)
  elif 'attack-down' in n:q=movequad(q,5,8)
  elif 'attack-front' in n:q=movequad(q,4,-3)
  elif 'brace' in n:q=movequad(q,4,3)
  elif 'fidget' in n:q=movequad(q,-3,1)
  elif 'death' in n or g==5:
   q=[[247,254],[260,256],[260,262],[247,260]];note='Collapsed neck tab flattened at breast, partly under near wing'
  elif 'turn-front' in n or g==7:q=[[228,228],[239,231],[239,246],[229,244]];note='Foreshortened neck tab on frontal turn'
 elif rock:
  if 'quarter' in n:q=movequad(q,-7,1)
  elif 'turn-front' in n or g==7:q=[[234,239],[239,242],[239,252],[234,250]];note='Neck side tab heavily foreshortened behind head in front turn'
  elif 'death' in n or g==5:q=[[235,252],[250,253],[252,261],[235,260]];note='Neck cloth folds down with collapsed living animal'
  elif 'walk-down' in n:q=movequad(q,2,2)
  elif 'walk-passing' in n:q=movequad(q,1,-1)
  elif 'attack-up' in n:q=movequad(q,4,-5)
  elif 'attack-down' in n:q=movequad(q,6,6)
  elif 'attack-front' in n:q=movequad(q,6,0)
  elif 'recoil' in n:q=movequad(q,-3,0)
 elif runner:
  if 'turn-front' in n:q=[[239,221],[244,224],[243,237],[239,236]];note='Saddle side tab nearly edge-on behind rider leg during frontal turn'
  elif 'quarter' in n:q=movequad(q,4,0)
  elif 'death' in n or g==5:q=[[211,253],[225,255],[224,263],[211,261]];note='Saddle cloth folds with bird and rider collapse, behind near thigh'
  elif 'walk-down' in n:q=movequad(q,0,2)
  elif 'walk-passing' in n:q=movequad(q,-1,-2)
  elif 'attack-' in n:q=movequad(q,3,0)
  elif 'recoil' in n:q=movequad(q,-2,-2)
  # Near rider shin is in front of the saddle cloth, never painted over it.
  occlusion=[[[225,225],[233,227],[237,243],[230,245]]]
 elif machine:
  if 'death-fall' in n or 'death-rest' in n or g==22:return None,[],'Hanging cloth pinned under collapsed chassis masonry; no floating crest'
  if 'death-kneel' in n:q=movequad(q,2,8)
  elif 'turn-front' in n or g==7:q=[[212,222],[225,225],[224,245],[212,242]]
  elif 'walk-down' in n:q=movequad(q,1,2)
  elif 'walk-pass' in n:q=movequad(q,-1,0)
  elif 'defend' in n:q=movequad(q,0,4)
  elif 'hit' in n:q=movequad(q,-2,1)
 else:
  if g==0:
   delta=[(-1,0),(0,-1),(0,1),(0,0),(1,-2),(0,0)][index%6];q=movequad(q,*delta)
  elif g==3:q=movequad(q,-3,-1)
  elif g==5 or g==22:
   if index==0:q=[[187,245],[198,244],[201,257],[191,259]]
   else:q=[[184,256],[198,252],[201,260],[187,264]]
   note='Front apron folds across collapsed thigh; near forearm occludes upper-right cloth'
   occlusion=[[[197,251],[204,254],[204,259],[199,258]]]
  elif g in (7,8):q=movequad(q,0,0)
  elif g in (11,12,13):q=movequad(q,2,0)
 return q,occlusion,note
def transformed(im,size,scale,source_root,target_root):
 return im.transform(size,Image.Transform.AFFINE,(1/scale,0,source_root[0]-target_root[0]/scale,0,1/scale,source_root[1]-target_root[1]/scale),Image.Resampling.BICUBIC)
def overlay(base,paint,mask):
 out=Image.composite(paint,base,mask);out.putalpha(base.getchannel('A'));return out
def portrait_parameters(unit,role,size):
 if unit in ('sunPriest','highPriest'):source_root=(740,1140);scale=.068;crop=(350,100,1110,950)
 elif unit=='shurimanArcher':source_root=(625,1190);scale=76/1131;crop=(350,0,1100,1050) if role=='large' else (350,0,1100,850)
 elif unit=='sunArcher':source_root=(625,1190);scale=76/1131;crop=(300,20,1100,1050) if role=='large' else (300,20,1100,870)
 elif unit in ('ruinRunner','duneVeteran'):source_root=(640,1130);scale=.095;crop=(380,30,1200,1020) if role=='large' else (440,30,1000,720)
 elif unit in ('rockbear','elderRockbear'):source_root=(1037,992);scale=.075;crop=(1250,380,1970,1000)
 elif unit in ('sunforgedColossus','awakenedSunforged'):source_root=(590,833);scale=.11;crop=(350,150,1250,850)
 else:
  source_root=(621,1073);scale=157/1254
  crop=(720,440,1100,940) if unit=='sandstoneChimera' else (720,380,1120,940)
  if role=='small':crop=(720,440,1100,820) if unit=='sandstoneChimera' else (720,380,1120,780)
 factor=min(size[0]/(crop[2]-crop[0]),size[1]/(crop[3]-crop[1]))
 dims=(round((crop[2]-crop[0])*factor),round((crop[3]-crop[1])*factor));offset=((size[0]-dims[0])//2,(size[1]-dims[1])//2)
 target_root=((source_root[0]-crop[0])*factor+offset[0],(source_root[1]-crop[1])*factor+offset[1])
 return factor/scale,target_root
def produce():
 units=sorted(json.loads((P/'content/creatures.json').read_text()));records=[];direct={common.rel(p):common.sha(p) for p in (Path(__file__),Path(common.__file__),S/'generation-ledger-v1.json',S/'heraldry-planes-v1.json',S/'heraldry-cloth-raw.png',S/'heraldry-cloth-prompt.txt')};result=[];annotations=[]
 for unit in units:
  directory=S/'inputs/technical-recipes'/unit;recipes={p.stem:json.loads(p.read_text()) for p in sorted(directory.glob('*.json'))}
  for path in sorted(directory.glob('*.json')):direct[common.rel(path)]=common.sha(path)
  prior_t1=unit in ('desertNomad','sandWarrior')
  if prior_t1:
   prior=P/'assets/source/regional-crests-20261025-v1/creatures/t1-actions-v2/recipes'/unit
   recipes={p.stem:json.loads(p.read_text()) for p in sorted(prior.glob('*.json'))}
   for path in sorted(prior.glob('*.json')):direct[common.rel(path)]=common.sha(path)
   # Apply the measured native encounter selector/canvas correction to the prior cohort.
   oldleft=copy.deepcopy(recipes['attackLeft']);oldright=copy.deepcopy(recipes['attackRight'])
   for role,rr in [('attackLeft',oldright),('attackRight',oldleft)]:
    im=Image.open(P/rr['source']).convert('RGBA').crop((32,0,96,64));dest=S/'heraldry-v1'/unit/'resources'/(role+'.png');common.png(dest,im);recipes[role].update(common.descriptor(dest),size=[64,64])
  battle=recipes['battle'];groups={r['group']:r['frames'] for r in battle['groups']};original_root=(battle['pivot']['x'],battle['pivot']['y']);onehex=unit in ('desertNomad','sandWarrior','shurimanArcher','sunArcher','sunPriest','highPriest');root=(196 if onehex else 218,original_root[1]);translation=root[0]-original_root[0]
  standing_sha=groups[2][0]['source_sha256'];cache={};masks={};originals={};semantics={}
  for g,seq in groups.items():
   for index,frame in enumerate(seq):
    key=frame['source_sha256']
    if key in cache:continue
    path=P/frame['source'];assert common.sha(path)==key;direct[common.rel(path)]=key
    raw=Image.open(path).convert('RGBA');base=Image.new('RGBA',raw.size);base.paste(raw,(translation,0))
    if prior_t1:painted=base.copy();mask=Image.new('L',base.size);bbox=None;q=None;note='Prior genuinely painted T1 physical-plane crest retained with its real occluders'
    else:
     q,occluders,note=annotated_plane(unit,path.stem,g,index,standing_sha,key)
     if q is None:painted=base.copy();mask=Image.new('L',base.size);bbox=None
     else:painted,mask,bbox=project(base,q,occluders)
    dest=S/'heraldry-v1'/unit/'native'/(hashlib.sha256(key.encode()).hexdigest()[:16]+'.png');common.png(dest,painted);common.png(dest.with_name(dest.stem+'-mask.png'),mask)
    cache[key]=dest;masks[key]=mask;originals[key]=base;semantics[key]=(g,index)
    annotations.append({'unit':unit,'input':common.descriptor(path),'native_translation_x':translation,'physical_quad':q,'natural_occlusion':note,'output':common.descriptor(dest),'mask':common.descriptor(dest.with_name(dest.stem+'-mask.png')),'native_RGB_difference_bbox':bbox,'alpha_byte_exact_after_declared_translation':painted.getchannel('A').tobytes()==base.getchannel('A').tobytes()})
  standing_key=standing_sha
  for g,seq in groups.items():
   groups[g]=[dict(common.descriptor(cache[f['source_sha256']]),sha256=common.sha(cache[f['source_sha256']])) for f in seq]
  for g in (11,12,13):
   seq=groups[g]
   if len(seq)==5:groups[g]=[seq[0],seq[1],seq[2],seq[2],seq[3],seq[4]]
   elif len(seq)==3:groups[g]=[seq[0],seq[1],seq[1],seq[2]]
  groups[22]=[copy.deepcopy(groups[5][-1])]
  if 20 not in groups:groups[20]=[copy.deepcopy(groups[2][0]),copy.deepcopy(groups[0][0])]
  if 21 not in groups:groups[21]=[copy.deepcopy(groups[0][-1]),copy.deepcopy(groups[2][0])]
  # Native ReverseAnimation flips between TURN_L7 and TURN_R8. Preserve a real
  # frontal painted boundary; never jump from a front actor to an unrelated rear actor.
  front=groups[7][-1] if len(groups[7])>1 else groups[7][0]
  if front['source_sha256']==groups[2][0]['source_sha256']:front=groups[7][0]
  frontimage=Image.open(P/front['source']).convert('RGBA');mirror=Image.new('RGBA',frontimage.size);mirror.paste(ImageOps.mirror(frontimage),(round(2*root[0]-(frontimage.width-1)),0));mirrorpath=S/'heraldry-v1'/unit/'native/turn-boundary-mirror.png';common.png(mirrorpath,mirror)
  quarter=groups[7][1] if len(groups[7])==3 else None
  groups[7]=[copy.deepcopy(groups[2][0])]+([quarter] if quarter else [])+[front]
  groups[8]=[dict(common.descriptor(mirrorpath),sha256=common.sha(mirrorpath))]+([copy.deepcopy(quarter)] if quarter else [])+[copy.deepcopy(groups[2][0])]
  for g,seq in groups.items():
   groups[g]=[dict(copy.deepcopy(frame),frame=i) for i,frame in enumerate(seq)]
  battle['groups']=[{'group':g,'frames':seq} for g,seq in sorted(groups.items())];battle['pivot']={'x':root[0],'y':root[1]}
  # Carry the same painted material through actual existing companion transforms.
  if not prior_t1:
   scales={'shurimanArcher':.04/(76/1131),'sunArcher':.032/(76/1131),'sunPriest':.04/.068,'highPriest':.04/.068,'rockbear':.032/.075,'elderRockbear':.028/.075,'ruinRunner':.032/.095,'duneVeteran':.032/.095,'sandstoneChimera':64/157,'gildedChimera':64/157,'sunforgedColossus':.032/.11,'awakenedSunforged':.032/.11}
   for role,recipe in recipes.items():
    if role=='battle':continue
    rr=[r for r in recipe['groups'][0]['frames']] if role=='map' else [recipe]
    for i,frame in enumerate(rr):
     if role=='map':key=standing_key if len(rr)==1 else next(k for k,v in semantics.items() if v==(0,i))
     elif role in ('attackLeft','attackRight'):
      direction=15 if unit in ('shurimanArcher','sunArcher') else 12
      desired=3 if unit=='sunArcher' else 2
      key=next((k for k,v in semantics.items() if v==(direction,desired)),standing_key)
     else:key=standing_key
     input_path=P/frame['source'];direct[common.rel(input_path)]=common.sha(input_path)
     base=Image.open(input_path).convert('RGBA');paint=Image.open(cache[key]).convert('RGBA');mask=masks[key]
     # A recruitment portrait may deliberately include more torso so the real
     # attachment remains visible; derive it from the genuine standing master,
     # never by fitting the action's opaque bounds or stamping a UI badge.
     if role=='large' and unit in ('shurimanArcher','sunArcher','ruinRunner','duneVeteran','sandstoneChimera','gildedChimera'):
      master=P/battle['generation']['painted_master'];direct[common.rel(master)]=common.sha(master);raw=Image.open(master).convert('RGBA')
      cropbox={'shurimanArcher':(350,0,1100,1050),'sunArcher':(300,20,1100,1050),'ruinRunner':(380,30,1200,1020),'duneVeteran':(380,30,1200,1020),'sandstoneChimera':(720,440,1100,940),'gildedChimera':(720,380,1120,940)}[unit]
      crop=raw.crop(cropbox);factor=min(base.width/crop.width,base.height/crop.height);size=(round(crop.width*factor),round(crop.height*factor));view=crop.resize(size,Image.Resampling.LANCZOS);base=Image.new('RGBA',base.size);base.paste(view,((base.width-size[0])//2,(base.height-size[1])//2))
     if role in ('map','attackLeft','attackRight'):
      ratio=scales[unit];target_root=(64,60) if role=='map' else (32,60)
     else:ratio,target_root=portrait_parameters(unit,role,base.size)
     projected=transformed(paint,base.size,ratio,root,target_root);pm=transformed(mask,base.size,ratio,root,target_root)
     if role=='attackRight':projected=ImageOps.mirror(projected);pm=ImageOps.mirror(pm)
     out=overlay(base,projected,pm);dest=S/'heraldry-v1'/unit/'resources'/(role+('-'+str(i) if role=='map' else '')+'.png');common.png(dest,out);frame.update(common.descriptor(dest));frame.pop('sha256',None)
  provenance=S/'heraldry-v1'/unit/'provenance.json'
  unitrecords=[r for r in annotations if r['unit']==unit]
  common.put(provenance,{'status':'authored configuration','project_adaptation':CONFIG['association'],'official_reference_url':CONFIG['official_reference_url'],'official_reference_sha256':CONFIG['official_reference_sha256'],'painted_material':common.descriptor(S/'heraldry-cloth-raw.png'),'producer':common.descriptor(Path(__file__)),'physical_plane_config':common.descriptor(S/'heraldry-planes-v1.json'),'input_recipes':[common.descriptor(p) for p in sorted(directory.glob('*.json'))],'records':unitrecords,'native_battle_root':root,'native_whole_actor_translation_x':translation,'mirrored_frontal_boundary':common.descriptor(mirrorpath),'existing_flight_takeoff_landing_retained':not onehex,'actual_native_execution':False,'visual_approval_granted':False})
  for role,recipe in recipes.items():
   if not prior_t1:
    recipe['generation']={'image_generation_used':True,'provider':'OpenAI built-in painted imagegen; technical physical-plane composition','model':'not exposed by built-in tool','painted_master':common.rel(S/'heraldry-cloth-raw.png'),'painted_master_sha256':common.sha(S/'heraldry-cloth-raw.png'),'provenance':common.rel(provenance),'method':'Genuine painted2D action/body retained. Genuinely painted textile projected only onto explicit physical clothing/equipment planes; alpha and outside-plane actor pixels preserved.','prompt':'heraldry-cloth-prompt.txt plus pinned original body/action prompts; no synthesized glyph or 3D.'}
   else:recipe['generation']=dict(recipe['generation'],provenance=common.rel(provenance),method='Prior genuine painted2D physical-plane cohort retained; exact native root calibration, terminal corpse, contact and encounter role fixes.')
   recipe['producer_source']=common.rel(Path(__file__));recipe['producer_source_sha256']=common.sha(Path(__file__))
   recipe['production_inputs']=[{'path':path,'sha256':pin} for path,pin in sorted(direct.items())]
   recipe['visual_approval_granted']=False;recipe['acceptance']='Painted2D source candidate; current physical-plane source review and native motion/crest/rights acceptance remain distinct.'
   dest=S/'recipe-payload-heraldry-v1'/unit/(role+'.json');common.put(dest,recipe)
  result.append({'unit':unit,'unique_painted_action_inputs':len(cache),'recipes':len(recipes),'whole_actor_root_translation_x':translation})
 common.put(R/'physical-annotations-v1.json',annotations);common.put(R/'production-summary-v1.json',result)
 print(json.dumps(result))
if __name__=='__main__':
 if '--produce' in sys.argv:produce()
 else:holding()
