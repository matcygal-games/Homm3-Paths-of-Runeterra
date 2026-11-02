"""Selective genuine painted rest-pose assembly. Never edits frozen sources.

No drawing, anatomy transformation, crop-to-window, or battle-cohort rescaling.
The full actor is isolated at alpha128 with edge preservation; fixed scale and
explicit physical source registrations apply to each new painted cohort.
"""
from __future__ import annotations
import argparse,copy,hashlib,io,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter,ImageOps,ImageDraw

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PROJECT=HERE.parents[4]
WORKSPACE=PROJECT.parent
REPORT=WORKSPACE/'reports/targon-compact-holding-20261028-v1'
sys.path.insert(0,str(BASE))
from components import components
sys.path.insert(0,str(WORKSPACE/'scripts'))
from faction_art_compile import create_compiler
sys.path.insert(0,str(PROJECT/'scripts'))
from creature_art_policy import recipe_errors
UNITS=['solariSunforger','crystalIbex','crestedCrystalIbex','solariSunhawk','crownedSunhawk','stellacorn','resplendentStellacorn']
CANVAS=(450,400)
CALIBRATION={
 'solariSunforger':{'master':'solariSunforger-compact-crest-v2-public.png','scale':0.199,
    'anchors':[[498,492],[1058,493],[498,978],[1060,979]],
    'note':'Same approximately79px skull-to-boot human as the frozen complete polearm supplement; upright polearm is foreshortened, never shortened.'},
 'stellacorn':{'master':'stellacorn-compact-tail-v3-public.png','scale':0.21,
    'anchors':[[456,522],[1110,525],[475,1009],[1125,1010]],
    'note':'Fixed108px horn-to-hoof control, matching frozen108px animal role. Natural near-frontal rest, closed wings and hidden tail; no body shrink.'},
 'resplendentStellacorn':{'master':'resplendentStellacorn-compact-tail-v3-public.png','scale':0.21,
    'anchors':[[474,514],[1099,515],[485,1009],[1115,1009]],
    'note':'Fixed107px horn-to-hoof control against frozen108px role, same mature body scale; closed wings and hidden tail.'},
}
CHECK=False
WRITTEN={}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).relative_to(PROJECT).as_posix()
def write(p,raw):
 p=Path(p)
 if CHECK:
  assert p.is_file() and p.read_bytes()==raw,'Source replay differs: '+str(p)
 else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 WRITTEN[rel(p)]=hashlib.sha256(raw).hexdigest()
def dump(p,v):write(p,(json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode())
def png(p,im):
 stream=io.BytesIO();im.save(stream,format='PNG',compress_level=9,optimize=False);write(p,stream.getvalue())
 return {'source':rel(p),'source_sha256':hashlib.sha256(stream.getvalue()).hexdigest(),'source_canvas':list(im.size)}
def read_im(f):return Image.open(PROJECT/f['source']).convert('RGBA')
def same(a,b):return a.tobytes()==b.tobytes()
def recipe_path(u):
 sub='humanoids/'+u+'-battle.json' if u=='solariSunforger' else 'animals/'+u+'/battle.json'
 return BASE/'canonical-recipe-payloads/assets/recipes/creatures'/sub

def isolate_new(u):
 cfg=CALIBRATION[u];path=HERE/cfg['master'];im=Image.open(path).convert('RGBA')
 islands=components(im,128,2000)
 assert len(islands)==4,(u,len(islands))
 # Actual generated atlas positions are measured, not assumed equal cell pitch.
 islands=sorted(islands,key=lambda c:((c['bbox'][1]+c['bbox'][3])//800,c['bbox'][0]))
 frames=[];records=[]
 for i,c in enumerate(islands):
  b=c['bbox'];mask=Image.new('L',im.size,0);px=mask.load()
  for y,x0,x1 in c['runs']:
   for x in range(x0,x1):px[x,y]=255
  mask=mask.filter(ImageFilter.MaxFilter(7))
  alpha=np.minimum(np.asarray(mask),np.asarray(im.getchannel('A')))
  selected=im.copy();selected.putalpha(Image.fromarray(alpha,'L'))
  box=(max(0,b[0]-3),max(0,b[1]-3),min(im.width,b[2]+3),min(im.height,b[3]+3))
  part=selected.crop(box);scale=cfg['scale'];anchor=cfg['anchors'][i]
  part=part.resize((round(part.width*scale),round(part.height*scale)),Image.Resampling.LANCZOS)
  a=np.array(part);a[a[:,:,3]>=250,3]=255;a[a[:,:,3]==0,:3]=0;part=Image.fromarray(a,'RGBA')
  pivot=(196,267) if u=='solariSunforger' else (218,267)
  xy=(round(pivot[0]+(box[0]-anchor[0])*scale),round(pivot[1]+(box[1]-anchor[1])*scale))
  out=Image.new('RGBA',CANVAS);out.alpha_composite(part,xy);frames.append(out)
  records.append({'pose':i,'body_bbox':b,'source_root':anchor,'scale':scale,'native_paste_xy':list(xy)})
 return frames,{'master':rel(path),'master_sha256':sha(path),'calibration':cfg,'poses':records}

def compile_twice(path):
 compiler=create_compiler('targon');a,receipt=compiler.plan(PROJECT,path);b,_=compiler.plan(PROJECT,path)
 assert a==b,'Converter nondeterminism'
 return a,receipt

def decode(recipe,outputs):
 name=recipe['output_path'];animation=json.loads(outputs[name]);root=Path(name).parent
 return {s['group']:[Image.open(io.BytesIO(outputs[(root/f).as_posix()])).convert('RGBA') for f in s['frames']] for s in animation['sequences']}

def outside(im,u,height=120,threshold=128):
 x=150 if u=='solariSunforger' else 170
 mask=np.asarray(im.getchannel('A'))>threshold
 allowed=np.zeros(mask.shape,bool);allowed[155:155+height,x:x+100]=True
 return int((mask&~allowed).sum())

def turn_check(groups,u):
 delta=-58 if u=='solariSunforger' else -14
 assert same(groups[7][0],groups[2][0]),'TURN_L must start at actual HOLDING'
 assert same(groups[8][-1],groups[2][0]),'TURN_R must end at actual HOLDING'
 def world(im,facing,x):
  out=Image.new('RGBA',(800,450));out.alpha_composite(im if facing else ImageOps.mirror(im),(x,0));return out
 assert same(world(groups[7][-1],True,150),world(groups[8][0],False,150+delta)),'Actual native right-to-left world flip breaks'
 assert same(world(groups[7][-1],False,150+delta),world(groups[8][0],True,150)),'Actual native left-to-right world flip breaks'

def crop_check(groups,u):
 # The actual original Roc control qualifies at zero or one opaque boundary
 # feather pixel. No anatomy-loss exceptions are invented for any other unit.
 limit=1 if u=='solariSunhawk' else 0
 for g in [1,2]:
  for im in groups[g]:assert outside(im,u)<=limit,(u,g,outside(im,u))

def endpoints_check(groups):
 hold=groups[2][0]
 assert same(groups[20][0],hold),'Movement/takeoff begins at obsolete holding'
 assert same(groups[21][-1],hold),'Landing/movement end returns to obsolete holding'

def new_frame(u,g,i,im):
 f=png(HERE/'frames'/u/f'g{g:02d}-f{i:03d}.png',im);f['frame']=i;return f

def build(u):
 oldpath=recipe_path(u);old=json.loads(oldpath.read_text());recipe=copy.deepcopy(old)
 oldgroups={g['group']:[read_im(f) for f in g['frames']] for g in old['groups']}
 if u in CALIBRATION:
  holds,pose_record=isolate_new(u)
  if u=='stellacorn':
   # The two large glance keys naturally extend a wing by2px at fixed
   # anatomical scale. Preserve them unselected, and use the two genuine
   # compact breath/ear keys; do not recenter/shrink a figure to pass the UI.
   holds=[holds[0],holds[1],holds[0],holds[1]]
   pose_record['selected_pose_indices']=[0,1,0,1]
   pose_record['unselected_pose_indices']=[2,3]
 else:
  indices=[0,2] if u=='solariSunhawk' else [0,1]
  holds=[oldgroups[7][i].copy() for i in indices];holds=[holds[0],holds[1],holds[0],holds[1]]
  pose_record={'kind':'exact genuine existing painted supplement poses','source_group':7,'source_frames':indices,
    'scale_change':False,'root_change':False,'note':'Natural compact quarter-view body/weight/head angles already exist in the frozen painted cohort; no newly drawn or shrunken body.'}
 oldholds=oldgroups[2][:2];changes=[];groups=copy.deepcopy(oldgroups)
 for g,frames in groups.items():
  if g in [0,7,8,22]:continue
  for i,im in enumerate(frames):
   if g in [1,2]:new=holds[i%len(holds)]
   elif same(im,oldholds[0]):new=holds[0]
   elif same(im,oldholds[1]):new=holds[1]
   else:continue
   frames[i]=new.copy()
 # Preserve action counts/cadence and the actual frontal painted key. For the
 # two newly near-frontal resting stellar bodies, replace the obsolete initial
 # side-looking turnaround key, so the half-turn cannot run backwards first.
 groups[7][0]=holds[0].copy()
 if u=='stellacorn':groups[7][1]=holds[2].copy()
 delta=-58 if u=='solariSunforger' else -14
 join=Image.new('RGBA',CANVAS);join.alpha_composite(ImageOps.mirror(groups[7][-1]),(delta,0))
 groups[8][0]=join
 groups[8][1]=groups[7][-2].copy()
 groups[8][-1]=holds[0].copy()
 assert same(groups[22][0],oldgroups[22][0]),'Persistent corpse must not change'
 assert len(groups[0])==len(oldgroups[0]) and all(same(a,b) for a,b in zip(groups[0],oldgroups[0])),'Unrelated movement changed'
 for rg in recipe['groups']:
  g=rg['group']
  for i,im in enumerate(groups[g]):
   if not same(im,oldgroups[g][i]):
    changes.append({'group':g,'frame':i,'before_source':rg['frames'][i]['source'],'before_sha256':rg['frames'][i]['source_sha256']})
    rg['frames'][i]=new_frame(u,g,i,im)
 # Hash-bound closure is an extension of the truthful preserved painted ledger.
 oldledger=PROJECT/old['generation']['source_generation_ledger'];ledger=json.loads(oldledger.read_text())
 ledger['scope']='Selective compact resting-pose extension; old action source/provenance preserved, no art acceptance'
 ledger['producer_source']=rel(Path(__file__));ledger['producer_sha256']=sha(__file__)
 pins=ledger['files_sha256'];pins[rel(Path(__file__))]=sha(__file__)
 for path in [HERE/'frozen-input-pins.json',HERE/'actual-generation-prompts-v2.json',BASE/'components.py',oldledger]:
  pins[rel(path)]=sha(path)
 for rg in recipe['groups']:
  for f in rg['frames']:pins[f['source']]=f['source_sha256']
 if u in CALIBRATION:
  master=HERE/CALIBRATION[u]['master'];pins[rel(master)]=sha(master)
  ledger['origins'].append({'kind':'image-generation','path':rel(master),'sha256':sha(master)})
 ledgerpath=HERE/'ledgers'/(u+'.json');dump(ledgerpath,ledger)
 recipe['generation'].update({'source_generation_ledger':rel(ledgerpath),'source_generation_ledger_sha256':sha(ledgerpath),
  'producer_source':rel(Path(__file__)),'producer_sha256':sha(__file__),
  'compact_holding_scope':'Selective genuine painted rest poses and exact associated endpoints only; no battle cohort rescaling'})
 recipe['acceptance']='Candidate selective repair; independent native-size art, motion, runtime and rights checks remain pending'
 newpath=HERE/'recipes'/(u+'-battle.json');dump(newpath,recipe)
 errors=recipe_errors(PROJECT,recipe,set());assert not errors,errors
 outputs,receipt=compile_twice(newpath);decoded=decode(recipe,outputs)
 crop_check(decoded,u);turn_check(decoded,u);endpoints_check(decoded)
 oldoutputs,_=create_compiler('targon').plan(PROJECT,oldpath)
 for name,raw in outputs.items():
  path=REPORT/'compiled'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 measurements=[]
 for g in [1,2]:
  for i,im in enumerate(decoded[g]):
   measurements.append({'group':g,'frame':i,'opaque_outside120':outside(im,u),
     'opaque_outside130':outside(im,u,130),'alpha64_outside120':outside(im,u,threshold=64),
     'bbox128':im.getchannel('A').point(lambda x:255 if x>128 else 0).getbbox()})
 mutants=[]
 def reject(label,fn):
  try:fn()
  except AssertionError:mutants.append({'mutation':label,'rejected':True});return
  raise AssertionError('Mutation survived: '+label)
 bad=copy.deepcopy(decoded);bad[2][0]=oldgroups[2][0].copy();reject('restore old clipped HOLDING',lambda:crop_check(bad,u))
 bad=copy.deepcopy(decoded);bad[1][1]=oldgroups[2][1].copy();reject('restore old clipped FIDGET',lambda:crop_check(bad,u))
 bad=copy.deepcopy(decoded);bad[8][0]=groups[7][-1].copy();reject('naive unreflected native TURN join',lambda:turn_check(bad,u))
 bad=copy.deepcopy(decoded);shift=Image.new('RGBA',CANVAS);shift.alpha_composite(ImageOps.mirror(groups[7][-1]),(delta+1,0));bad[8][0]=shift;reject('one pixel wrong native TURN origin',lambda:turn_check(bad,u))
 bad=copy.deepcopy(decoded);bad[8][-1]=oldgroups[2][0].copy();reject('restore obsolete TURN_R endpoint',lambda:turn_check(bad,u))
 bad=copy.deepcopy(decoded);bad[20][0]=oldgroups[2][0].copy();reject('restore obsolete takeoff/movement-start endpoint',lambda:endpoints_check(bad))
 bad=copy.deepcopy(decoded);bad[21][-1]=oldgroups[2][0].copy();reject('restore obsolete landing/movement-end endpoint',lambda:endpoints_check(bad))
 assert same(decoded[22][0],oldgroups[22][0]),'Compiled corpse changed'
 report={'unit':u,'status':'authored configuration','pose_source':pose_record,'changes':changes,
   'changed_frame_count':len(changes),'measurements':measurements,'mutation_controls':mutants,
   'recipe':rel(newpath),'recipe_sha256':sha(newpath),'frozen_recipe':rel(oldpath),'frozen_recipe_sha256':sha(oldpath),
   'outputs':len(outputs),'converter_runs':2,'converter_exact':True,
   'native_world_flip_deltax':delta,'turn_both_facings_exact':True,
   'group_counts_preserved':True,'moving_and_corpse_exact':True,'movement_start_end_holding_exact':True,
   'native_execution':False,'final_art_accepted':False}
 review(u,oldgroups,decoded)
 return report,outputs,oldoutputs

def review(u,old,new):
 out=REPORT/u;out.mkdir(exist_ok=True);crop=(150,155,250,275) if u=='solariSunforger' else (170,155,270,275)
 sheet=Image.new('RGBA',(700,190),(47,46,43,255));d=ImageDraw.Draw(sheet)
 for x,im,label in [(0,old[2][0],'frozen full'),(200,new[2][0],'candidate full')]:
  sheet.alpha_composite(im.crop((120,140,320,290)),(x,25));d.text((x+3,4),label,fill='white')
 for x,im,label in [(420,old[2][0],'old100x120'),(550,new[2][0],'new100x120')]:
  sheet.alpha_composite(im.crop(crop),(x,35));d.text((x+3,4),label,fill='white')
 sheet.convert('RGB').save(out/'comparison-native-1x.png')
 sheet.resize((1400,380),Image.Resampling.NEAREST).convert('RGB').save(out/'comparison-nearest2x.png')
 for name,frames in [('holding',new[2]),('fidget',new[1]),('takeoff',new[20]),('landing',new[21])]:
  images=[]
  for im in frames:
   bg=Image.new('RGBA',(250,160),(47,46,43,255));bg.alpha_composite(im.crop((100,135,350,295)));images.append(bg.convert('RGB'))
  images[0].save(out/(name+'.gif'),save_all=True,append_images=images[1:],duration=200,loop=0,disposal=2)
 for start in [True,False]:
  delta=-58 if u=='solariSunforger' else -14;images=[]
  phases=[(im,start,150 if start else 150+delta) for im in new[7]]+[(im,not start,150+delta if start else 150) for im in new[8]]
  for im,facing,x in phases:
   bg=Image.new('RGBA',(800,450),(47,46,43,255));bg.alpha_composite(im if facing else ImageOps.mirror(im),(x,0));images.append(bg.crop((240,135,530,295)).convert('RGB'))
  images[0].save(out/('turn-start-right.gif' if start else 'turn-start-left.gif'),save_all=True,append_images=images[1:],duration=190,loop=0,disposal=2)

def main():
 global CHECK
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();CHECK=args.check
 pins=json.loads((HERE/'frozen-input-pins.json').read_text())
 # Manifest/content are coordinator guards, not immutable assembly inputs.
 for p,s in pins.items():
  if p not in ['assets/manifest.json','content/creatures.json']:assert sha(PROJECT/p)==s,'Frozen source changed: '+p
 REPORT.mkdir(parents=True,exist_ok=True)
 records=[];alloutputs={};prior={}
 for u in UNITS:
  record,outputs,oldoutputs=build(u);records.append(record);alloutputs.update(outputs);prior.update(oldoutputs)
 dump(HERE/'coverage.json',{'status':'authored configuration','units':records,'native_execution':False,'final_art_accepted':False})
 outputpins={p:hashlib.sha256(raw).hexdigest() for p,raw in sorted(alloutputs.items())}
 changed=[p for p,raw in alloutputs.items() if prior.get(p)!=raw]
 result={'status':'authored configuration','units':len(records),'recipes':len(records),'outputs':len(alloutputs),
  'converter_runs':2,'all_converter_outputs_exact':True,'mutation_controls':sum(len(r['mutation_controls']) for r in records),
  'holding_fidget_measured_frames':sum(len(r['measurements']) for r in records),'both_facing_turn_checks':len(records)*2,
  'changed_output_count':len(changed),'changed_outputs':sorted(changed),'native_execution':False,'art_accepted':False}
 (REPORT/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 (REPORT/'output-pins.json').write_text(json.dumps(outputpins,indent=2,sort_keys=True)+'\n')
 (REPORT/'measurements.json').write_text(json.dumps(records,indent=2,sort_keys=True)+'\n')
 page='<!doctype html><meta charset="utf-8"><title>Targon compact holding repairs</title><style>body{background:#242522;color:#eee;font:16px sans-serif;margin:2rem}a{color:#9dd}section{border-top:1px solid #777;margin-top:2rem;padding-top:1rem}img{max-width:none}</style><h1>Targon compact rest-pose candidates</h1><p>Authored configuration. Actual compiler source reconstruction, not game captures or final art acceptance. Body scale, unrelated actions/cadence, movement and terminal corpses are preserved.</p><p><a href="validation.json">Executed checks</a> | <a href="measurements.json">Shape/crop measurements and exact source changes</a> | <a href="output-pins.json">Actual output hashes</a></p>'
 for u in UNITS:
  page+=f'<section><h2>{u}</h2><img src="{u}/comparison-native-1x.png"><p>Native1x full pose and actual100x120 widget crop.</p>'
  for f in ['holding','fidget','turn-start-right','turn-start-left','takeoff','landing']:page+=f'<img src="{u}/{f}.gif" alt="{f}">'
  page+='</section>'
 (REPORT/'index.html').write_text(page,encoding='utf-8')
 print(json.dumps({'exact_source_check':CHECK,'source_artifacts':len(WRITTEN),**{k:v for k,v in result.items() if k!='changed_outputs'}},indent=2))

if __name__=='__main__':main()
