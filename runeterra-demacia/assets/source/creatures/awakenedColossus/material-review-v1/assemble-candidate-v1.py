"""Reproduce candidate conversion twice in isolated copied projects."""
from pathlib import Path
import sys,json,hashlib,re,copy,shutil
from PIL import Image,ImageDraw,ImageOps
P=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(P/'scripts'))
from animation import assemble
from raster import convert
B=Path(__file__).parent;R=P/'build/reports/art-review/current-20261020/upper/awakened-material'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(d,indent=2)+'\n')
def rel(p):return Path(p).relative_to(P).as_posix()
def proof(p):return {'path':rel(p),'sha256':sha(p)}
geo=read(R/'geometry-v4.json');selected={x['group']:x for x in geo['cameras']}
jobs=read(B/'jobs-v1.json')+read(B/'jobs-v2.json')+read(B/'jobs-v3.json')
index=[]
for j in jobs:
 out=P/j['output'];inp=P/j['target'];pr=P/j['prompt_path']
 index.append({'id':j['id'],'source':proof(inp),'output':proof(out),'prompt':proof(pr),'tool':'built-in image_gen.imagegen','selected_for_candidate':any(c['atlas']==rel(out) for c in selected.values()) or j['id'] in ['master','map-attack']})
write(B/'prompt-set-index-v1.json',{'generations':index,'status':'authored configuration; no final art or runtime acceptance','generated_path_records':[proof(B/f'generated-paths-v{v}.json') for v in [1,2,3]],'rejected_projection_reports':[proof(R/f'geometry-v{v}.json') for v in [1,2,3]],'selected_projection':proof(R/'geometry-v4.json')})
prov=proof(B/'prompt-set-index-v1.json')
frames={(m['group'],m['frame']):P/m['source'] for m in geo['frames']}
active=P/'assets/recipes/creatures/awakenedColossus-battle.json';battle=read(active)
before=proof(active)
adjustments=[]
for group in battle['groups']:
 for frame in group['frames']:
  gg,ii=map(int,re.search(r'g(\d+)-f(\d+)',frame['source']).groups());source=frames[(gg,ii)]
  dx=12 if gg==1 and ii==1 else 11 if gg==1 and ii==3 else 0
  if dx:
   out=B/'idle-reanchored-v1'/source.name;out.parent.mkdir(exist_ok=True)
   im=Image.open(source).convert('RGBA');move=Image.new('RGBA',im.size);move.alpha_composite(im,(dx,0));move.save(out)
   adjustments.append({'group':gg,'frame':ii,'translation':[dx,0],'source':proof(source),'output':proof(out),'basis':'Exact existing selected idle-stability-v1 integer x translation retained; no new fitting or pixel repaint.'});source=out
  frame['source']=rel(source);frame['sha256']=sha(source)
battle['provenance']=prov;battle['material_revision']={'scope':'Material-only full action family; old geometry/camera/placement preserved with explicit native measurements','prompt_set':prov,'geometry':proof(R/'geometry-v4.json'),'previous_selected_recipe':before,'idle_integer_reanchors':adjustments,'status':'authored configuration; native review pending; release blocked'}
battle['status']='material-candidate; native review pending; release blocked'
recipes={'assets/recipes/creatures/awakenedColossus-battle.json':battle}
for suffix in ['large','small','map-frame']:
 key=f'assets/recipes/creatures/awakenedColossus-{suffix}.json';d=read(P/key);d['source']=rel(B/'master-material-v1.png');d['source_sha256']=sha(B/'master-material-v1.png');d['provenance']=prov;d['previous_selected_recipe']=proof(P/key);d['material_revision']={'prompt_set':prov,'scope':'Same pose/crop/native placement; petricite material correction only.'};recipes[key]=d
attack=Image.open(B/'map-attack-material-v1.png').convert('RGBA');picture=ImageOps.contain(attack.crop((81,91,1303,1123)),(62,52),Image.Resampling.LANCZOS);layer=Image.new('RGBA',(64,64));layer.alpha_composite(picture,(1,64-picture.height))
for side,im in [('Left',layer),('Right',ImageOps.mirror(layer))]:
 src=B/f'attack{side}-native-v1.png';im.save(src);key=f'assets/recipes/map-attacks/awakenedColossus-attack{side}.json';d=read(P/key);d['source']=rel(src);d['source_sha256']=sha(src);d['provenance']=prov;d['previous_selected_recipe']=proof(P/key);recipes[key]=d
mapkey='assets/recipes/creatures/awakenedColossus-map.json';maprecipe=read(P/mapkey);maprecipe['provenance']=prov;maprecipe['previous_selected_recipe']=proof(P/mapkey)
selections=[];runs=[]
for run in [1,2]:
 sandbox=R/f'assembly-run{run}';sandbox.mkdir(exist_ok=True);receipts=[]
 def cp(s):
  dest=sandbox/s;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(P/s,dest)
 def gather(d):
  if isinstance(d,dict):
   if 'source' in d and isinstance(d['source'],str) and d['source'].startswith('assets/source/'):cp(d['source'])
   for v in d.values():gather(v)
  if isinstance(d,list):
   for v in d:gather(v)
 for key,d in recipes.items():
  candidate=B/'recipes-v1'/Path(key).parent.name/Path(key).name;write(candidate,d);gather(d);write(sandbox/key,d)
  result=assemble(sandbox,sandbox/key) if d['recipe_type']=='vcmi_animation' else convert(sandbox,sandbox/key);receipts.append(result)
  if run==1:selections.append({'active_recipe':key,'old_sha256':sha(P/key),'candidate_recipe':rel(candidate),'new_sha256':sha(candidate),'output_path':d['output_path']})
 md=copy.deepcopy(maprecipe);md['groups'][0]['frames'][0]['sha256']=sha(sandbox/md['groups'][0]['frames'][0]['source']);write(sandbox/mapkey,md)
 candidate=B/'recipes-v1'/Path(mapkey).parent.name/Path(mapkey).name;write(candidate,md);receipts.append(assemble(sandbox,sandbox/mapkey))
 if run==1:selections.append({'active_recipe':mapkey,'old_sha256':sha(P/mapkey),'candidate_recipe':rel(candidate),'new_sha256':sha(candidate),'output_path':md['output_path']})
 outputs={f.relative_to(sandbox/'assets/generated').as_posix():sha(f) for f in (sandbox/'assets/generated').rglob('*') if f.is_file()};write(R/f'assembly-run{run}-receipts.json',{'receipts':receipts,'outputs':outputs});runs.append(outputs)
assert runs[0]==runs[1], 'Isolated real converter outputs differ'
write(B/'candidate-selection.json',{'unit':'awakenedColossus','recipes':selections,'prompt_set':prov,'changed_groups':[g['group'] for g in battle['groups']],'geometry':proof(R/'geometry-v4.json'),'all_native_sole_deltas_zero':all(m['sole_delta']==0 for m in geo['frames']),'max_bounds_delta':max(m['max_bound_delta'] for m in geo['frames']),'min_silhouette_iou':min(m['iou'] for m in geo['frames']),'isolated_assembly_runs':2,'deterministic_outputs':len(runs[0]),'output_sha256':runs[0],'active_assets_modified':False,'art_accepted':False,'runtime_tested':False,'limitations':['Material looks rougher and less cartoon-outlined at native size, but final artistic acceptance is not granted.','G30 material-v1 uses one uniform atlas camera refit to all six poses, plus old-footprint-band integer registration; maximum native bound delta4px.','Existing exact fidget x reanchors +12/+11 remain; seven ticks and 0.7 seconds unchanged.','Rejected geometry-v1/v2/v3 projections are historical attempts, not selection evidence.']})
# Native UI/action mosaic: copy/composite only, never recolor the bitmap art.
outroot=R/'assembly-run1/assets/generated/Content/Sprites/runeterra/demacia/creatures/awakenedColossus';board=Image.new('RGB',(820,260),'#465044');dr=ImageDraw.Draw(board)
for i,name in enumerate(['large.png','small.png','map-idle.png','attackLeft.png','attackRight.png']):
 for row,root in enumerate([P/'assets/generated/Content/Sprites/runeterra/demacia/creatures/awakenedColossus',outroot]):
  im=Image.open(root/name).convert('RGBA');board.paste(im,(20+i*150,30+row*115),im);dr.text((20+i*150,14+row*115),('selected ' if row==0 else 'material ')+name,fill='white')
board.save(R/'native-ui-comparison-v1.png')
print(json.dumps({'deterministic':True,'outputs':len(runs[0]),'selection':rel(B/'candidate-selection.json'),'recipes':len(selections)}))
