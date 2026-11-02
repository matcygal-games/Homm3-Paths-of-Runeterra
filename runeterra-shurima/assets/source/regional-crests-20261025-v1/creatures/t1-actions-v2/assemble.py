"""Project a genuinely provider-painted cloth field onto explicit 2D physical planes.
All body, canvas, alpha, roots, action maps and consumer bounds remain selected inputs.
"""
from pathlib import Path
import json,hashlib,sys,copy
from PIL import Image,ImageDraw,ImageChops
S=Path(__file__).resolve().parent;P=S.parents[4];W=P.parent
R=W/'build/reports/regional-crests-20261025-v1/shurima-unit-art/t1-actions-v2'
PILOT=S.parent/'t1-pilot-v2';READS={}
def sha(p):
 h=hashlib.sha256(p.read_bytes()).hexdigest()
 if p.is_relative_to(P):READS[p.relative_to(P).as_posix()]=h
 return h
def track(p):READS[p.relative_to(P).as_posix()]=sha(p);return p
def load(p):return json.loads(track(p).read_text(encoding='utf8'))
def png(p):return Image.open(track(p)).convert('RGBA')
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,sort_keys=True,indent=2)+'\n',encoding='utf8')
def pin(p):return {'source':p.relative_to(P).as_posix(),'source_sha256':sha(p)}
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def affine(im,canvas=(450,400),root=(193,266),scale=.074,method=Image.Resampling.NEAREST):
 return im.transform(canvas,Image.Transform.AFFINE,(1/scale,0,640-root[0]/scale,0,1/scale,1070-root[1]/scale),method)
def mirror(im,root=(193,266)):
 out=Image.new(im.mode,im.size);out.paste(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(2*root[0]-(im.width-1),0));return out
def rgbdiff(a,b):return ImageChops.difference(a.convert('RGB'),b.convert('RGB'))
def guard(a,b,mask,positive=True):
 assert a.getchannel('A').tobytes()==b.getchannel('A').tobytes(),'alpha changed'
 d=rgbdiff(a,b);outside=Image.composite(d,Image.new('RGB',a.size),ImageChops.invert(mask))
 assert outside.getbbox() is None,'RGB outside physical cloth plane'
 if positive:assert d.getbbox() is not None,'missing intended RGB edit'
 return d.getbbox()
def composite(base,paint,mask):
 out=Image.composite(paint,base,mask);out.putalpha(base.getchannel('A'));return out
def perspective(quad):
 # Inverse homography: destination physical cloth quad -> painted crop coordinates.
 rows=[];rhs=[]
 for (x,y),(u,v) in zip(quad,[(0,0),(450,0),(450,340),(0,340)]):
  rows += [[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]];rhs += [u,v]
 for i in range(8):
  pivot=max(range(i,8),key=lambda j:abs(rows[j][i]));rows[i],rows[pivot]=rows[pivot],rows[i];rhs[i],rhs[pivot]=rhs[pivot],rhs[i]
  k=rows[i][i];assert abs(k)>1e-10
  rows[i]=[v/k for v in rows[i]];rhs[i]/=k
  for j in range(8):
   if j==i:continue
   k=rows[j][i];rows[j]=[a-k*b for a,b in zip(rows[j],rows[i])];rhs[j]-=k*rhs[i]
 return rhs
def pose(unit,name,spec,texture,texturemask,config):
 old=P/spec['master'];assert sha(old)==spec['master_sha256'];base=png(old)
 oldnative=P/spec['old_native'];assert sha(oldnative)==spec['old_native_sha256'];nativebase=png(oldnative)
 if spec.get('frozen_holding_pilot'):
  painted=png(PILOT/unit/'holding-source-candidate.png');mask=png(PILOT/unit/'physical-plane-mask.png').getchannel('R');native=png(PILOT/unit/'holding-native-right.png');nm=affine(mask)
 elif spec.get('quad') is None:
  painted=base.copy();mask=Image.new('L',base.size);native=nativebase.copy();nm=Image.new('L',native.size)
 else:
  coeff=perspective(spec['quad']);paint=texture.transform(base.size,Image.Transform.PERSPECTIVE,coeff,Image.Resampling.BICUBIC);mask=texturemask.transform(base.size,Image.Transform.PERSPECTIVE,coeff,Image.Resampling.NEAREST)
  visible=Image.new('L',base.size);draw=ImageDraw.Draw(visible);draw.polygon(spec['visible_cloth_polygon'],fill=255)
  if spec.get('flask_occluder_bounds'):draw.ellipse(spec['flask_occluder_bounds'],fill=0)
  if spec.get('spear_occluder_line'):draw.line(spec['spear_occluder_line'],fill=0,width=config['spear_occluder_width_source'])
  mask=ImageChops.multiply(mask,visible);painted=composite(base,paint,mask);nm=affine(mask);native=composite(nativebase,affine(painted),nm)
 positive=spec.get('quad') is not None or spec.get('frozen_holding_pilot',False)
 sourcebbox=guard(base,painted,mask,positive);nativebbox=guard(nativebase,native,nm,positive)
 # Real RGB-only mutation outside the physical plane must be rejected by this guard.
 mutant=painted.copy();pixel=(650,150);r,g,b,a=mutant.getpixel(pixel);mutant.putpixel(pixel,(r^1,g,b,a));refused=False
 try:guard(base,mutant,mask,positive)
 except AssertionError as exc:refused='outside physical cloth plane' in str(exc)
 assert refused
 d=S/unit;save(d/'masters'/(name+'.png'),painted);save(d/'masks'/(name+'.png'),mask);save(d/'native'/(name+'.png'),native);save(d/'native-masks'/(name+'.png'),nm)
 oldleft=png(oldnative.with_name(name+'-left.png'));leftmask=mirror(nm);left=composite(oldleft,mirror(native),leftmask);guard(oldleft,left,leftmask,positive);save(d/'native'/(name+'-left.png'),left)
 return {'pose':name,'old_master':pin(old),'old_native':pin(oldnative),'master':pin(d/'masters'/(name+'.png')),'native':pin(d/'native'/(name+'.png')),'mask':pin(d/'masks'/(name+'.png')),'source_RGB_diff_bbox':sourcebbox,'native_RGB_diff_bbox':nativebbox,'alpha_byte_exact':True,'outside_physical_plane_RGB_byte_exact':True,'one_RGB_bit_outside_mutant_refused':refused,'natural_occlusion':spec.get('natural_occlusion'),'frozen_holding_pilot':spec.get('frozen_holding_pilot',False)}
def derive_resource(base,master,mask,kind):
 if kind in ['map','attackRight','attackLeft']:
  paint=affine(master,(96,64),(64,60),.04);nm=affine(mask,(96,64),(64,60),.04)
  if kind=='attackLeft':paint=mirror(paint,(64,60));nm=mirror(nm,(64,60))
 else:
  box=(280,0,1000,800);crop=master.crop(box);m=mask.crop(box);ratio=min(base.width/crop.width,base.height/crop.height);dims=(round(crop.width*ratio),round(crop.height*ratio));paint=Image.new('RGBA',base.size);nm=Image.new('L',base.size);offset=((base.width-dims[0])//2,(base.height-dims[1])//2);paint.paste(crop.resize(dims,Image.Resampling.NEAREST),offset);nm.paste(m.resize(dims,Image.Resampling.NEAREST),offset)
 out=composite(base,paint,nm);guard(base,out,nm);return out,nm
def assembly(config):
 records=[]
 for unit,ud in config['units'].items():
  texture=png(PILOT/unit/'painted-cloth-provider-v2.png').resize((450,340),Image.Resampling.LANCZOS);texturemask=png(PILOT/unit/'physical-plane-mask.png').getchannel('R').crop((380,480,830,820))
  # The mask is derived from the frozen holding pilot; it excludes its original flask.
  for n,spec in ud['poses'].items():records.append({'unit':unit,**pose(unit,n,spec,texture,texturemask,config)})
  d=S/unit;recipes={role:load(P/v['source']) for role,v in ud['recipe_templates'].items()}
  for role,recipe in recipes.items():
   out=copy.deepcopy(recipe)
   if role=='battle':
    for g in out['groups']:
     for frame in g['frames']:
      n=Path(frame['source']).name;f=d/'native'/n;frame.update(pin(f));frame['sha256']=sha(f)
   else:
    oldframe=out['groups'][0]['frames'][0] if role=='map' else out
    base=png(P/oldframe['source']);n=ud['standing'] if role in ['map','large','small'] else 'attack-front-contact-v2';master=png(d/'masters'/(n+'.png'));mask=png(d/'masks'/(n+'.png')).getchannel('R');resource,rm=derive_resource(base,master,mask,role);f=d/'resources'/(role+'.png');save(f,resource);save(d/'resource-masks'/(role+'.png'),rm)
    oldframe=out['groups'][0]['frames'][0] if role=='map' else out;oldframe.update(pin(f))
    if 'sha256' in oldframe:oldframe['sha256']=sha(f)
   out['generation']={'image_generation_used':True,'provider':'OpenAI built-in painted imagegen; technical physical-plane composition','model':'not exposed by built-in tool','prompt':'Pinned t1-pilot-v2 cloth and channel-repair prompts; reused painted cloth material through explicit physical planes. No glyph synthesis or 3D.','painted_master':(PILOT/unit/'painted-cloth-provider-v2.png').relative_to(P).as_posix(),'painted_master_sha256':sha(PILOT/unit/'painted-cloth-provider-v2.png'),'provenance':(S/'provenance.json').relative_to(P).as_posix(),'method':'Fixed native roots and original action cohorts. Painted material is projected only onto hand-defined visible cloth planes, with flask/spear occlusion; original alpha and outside-mask RGB byte-exact.'}
   out['producer_source']=Path(__file__).relative_to(P).as_posix();out['producer_source_sha256']=sha(Path(__file__))
   declared=load(S/'input-pins.json')['inputs']
   out['production_inputs']=[{'path':row['path'],'sha256':row['sha256']} for row in declared]+[{'path':(S/'input-pins.json').relative_to(P).as_posix(),'sha256':sha(S/'input-pins.json')}]
   out['acceptance']='SOURCE CANDIDATE: independent source/action and native motion/art/rights review pending; no live selection.';out['visual_approval_granted']=False;write(S/'recipes'/unit/(role+'.json'),out)
 return records
def main():
 # Validate the selected producer itself and every immutable replay input before
 # loading configuration, images or the shared compiler. Live recipes are outputs.
 declaration=load(S/'input-pins.json')
 for row in declaration['inputs']:
  target=P/row['path'];assert target.resolve().is_relative_to(P.resolve()),'input leaves own project'
  assert target.is_file() and sha(target)==row['sha256'],'missing/stale declared producer input: '+row['path']
 track(Path(__file__));config=load(S/'physical-planes.json');R.mkdir(parents=True,exist_ok=True)
 before={v['source']:sha(P/v['source']) for u in config['units'].values() for v in u['recipe_templates'].values()};assert all(before[v['source']]==v['source_sha256'] for u in config['units'].values() for v in u['recipe_templates'].values())
 content_before=sha(P/'content/creatures.json');assert content_before==config['old_content_sha256']
 # Source artwork closure and source-export reproducibility include these actual reads.
 for unit in config['units']:
  for name in ['cloth-prompt.txt','channel-repair-prompt.txt','painted-cloth-provider-v1.png','cloth-edit-target-3x.png']:track(PILOT/unit/name)
 track(PILOT/'holding-source-lineage.json')
 ancestry=load(S/'action-source-lineage.json');load(S/'painted-material-lineage.json')
 for node in ancestry['nodes']:assert sha(P/node['source'])==node['source_sha256'],'ancestry source changed'
 for node in ancestry['prompt_specifications']:assert sha(P/node['source'])==node['source_sha256'],'ancestry prompt changed'
 runs=[]
 for _ in range(2):
  records=assembly(config);runs.append({p.relative_to(S).as_posix():sha(p) for u in config['units'] for sub in ['masters','masks','native','resources','resource-masks'] for p in sorted((S/u/sub).glob('*.png'))})
 assert runs[0]==runs[1]
 write(S/'provenance.json',{'status':'authored configuration','scope':'T1 two-variant complete six canonical source candidates; no live/native acceptance','producer':pin(Path(__file__)),'physical_planes':pin(S/'physical-planes.json'),'pilot_source_lineage':pin(PILOT/'holding-source-lineage.json'),'private_reference_url':'https://universe.leagueoflegends.com/images/shurima_crest_icon.png','private_reference_sha256':'4a49e2bdfa9d4ebf411585d6877239edb0425aa14db9e67af4e6390b29c2c365','official_pixels_excluded':True,'project_adaptation':'Regional local-caravan affiliation, not canonical imperial ownership or obedience','actual_direct_producer_reads':[{'source':k,'source_sha256':v} for k,v in sorted(READS.items())],'records':records,'visual_approval_granted':False,'native_execution':False})
 sys.path.insert(0,str(W/'scripts'));import faction_art_compile;c=faction_art_compile.create_compiler('shurima');compiled=[];proofs=[]
 for run in [1,2]:
  pins={}
  for recipe in sorted((S/'recipes').rglob('*.json')):
   outputs,proof=c.plan(P,recipe)
   if run==1:proofs.append(proof)
   for name,data in outputs.items():dest=R/f'compiler-{run}'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
  compiled.append(pins)
 assert compiled[0]==compiled[1]
 for unit,ud in config['units'].items():
  names=list(ud['poses']);board=Image.new('RGBA',(145*5,145*((len(names)+4)//5)),(45,45,45,255));draw=ImageDraw.Draw(board)
  for i,n in enumerate(names):
   im=png(S/unit/'native'/(n+'.png'));crop=im.crop((130,175,270,285));board.alpha_composite(crop,((i%5)*145,(i//5)*145+25));draw.text(((i%5)*145+2,(i//5)*145+3),n[:23],fill='white')
  save(R/(unit+'-all-actions-native1x.png'),board)
  for facing in ['right','left']:
   recipe=load(S/'recipes'/unit/'battle.json');groups=recipe['groups'];board=Image.new('RGBA',(145*6,135*len(groups)),(45,45,45,255));draw=ImageDraw.Draw(board)
   for row,g in enumerate(groups):
    for col,frame in enumerate(g['frames']):
     im=png(P/frame['source']);im=mirror(im) if facing=='left' else im;board.alpha_composite(im.crop((130,175,270,285)),(col*145,row*135+20));draw.text((col*145+2,row*135+2),f"g{g['group']} f{col}",fill='white')
   save(R/(unit+'-all-groups-'+facing+'-native1x.png'),board)
  board=Image.new('RGBA',(420,180),(45,45,45,255));draw=ImageDraw.Draw(board)
  for i,role in enumerate(['map','attackLeft','attackRight','large','small']):
   im=png(S/unit/'resources'/(role+'.png'));x=(i%3)*140;y=(i//3)*90;board.alpha_composite(im,(x,y+20));draw.text((x+2,y+2),role,fill='white')
  save(R/(unit+'-five-resources-native1x.png'),board)
 assert all(sha(P/n)==h for n,h in before.items()) and sha(P/'content/creatures.json')==content_before
 write(R/'technical-proof.json',{'status':'authored configuration','actual_assembly_passes':2,'real_assembly_outputs_byte_exact':runs[0]==runs[1],'actual_compiler_passes':2,'real_compiler_outputs_byte_exact':compiled[0]==compiled[1],'canonical_recipe_count':len(proofs),'compiled_files_per_run':len(compiled[0]),'output_hashes':compiled[0],'recipe_pins':[pin(p) for p in sorted((S/'recipes').rglob('*.json'))],'immutable_template_guards':before,'immutable_templates_unchanged':True,'statistics_timing_content_unchanged':content_before,'records':records,'actual_direct_producer_reads':[{'source':k,'source_sha256':v} for k,v in sorted(READS.items())],'visual_approval_granted':False,'live_selection_changed':False,'native_window_used':False,'limits':['Source candidate only. Independent visual/action review and fresh native motion acceptance pending.','Collapsed torso/ground naturally fully occludes the front-apron mark in death-fall and corpse poses.','Map and portrait reductions must be inspected; holding pilot readability does not approve them.']});write(R/'actual-compiler-receipts.json',proofs)
 print(json.dumps({'recipes':len(proofs),'compiled_files_per_run':len(compiled[0]),'assembly_and_compiler_twice_exact':True,'records':len(records)}))
if __name__=='__main__':main()
