"""Pin coordinator's independently reviewed painted V7 background, no selection."""
from pathlib import Path
from copy import deepcopy
import hashlib,json
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BG=ROOT/'assets/source/town/coordinator-village-background-20261024-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
handoff=BG/'FROZEN-HANDOFF-V7.json'
if sha(handoff)!='0ba42bc7577621cf6ff798ba4006151fe3f4407465a47862430e1228939fad9f':raise ValueError('Frozen background handoff changed')
packet=load(handoff)
for name,digest in packet['files'].items():
 if sha(ROOT/name)!=digest:raise ValueError('Frozen background dependency changed '+name)
source=ROOT/packet['background']['path'];annotation=ROOT/packet['water_annotation']['path']
original=Image.open(source);rgba=original.convert('RGBA');rgba_path=HERE/'background-rgba-v7.png';rgba.save(rgba_path,compress_level=9)
if rgba.convert('RGB').tobytes()!=original.convert('RGB').tobytes():raise ValueError('RGBA technical admission changed painted RGB pixels')
water=Image.open(annotation).convert('L').point(lambda p:255 if p>=128 else 0)
rows=[]
for y in range(374):
 bb=water.crop((0,y,800,y+1)).getbbox()
 if bb:rows.append((y,bb[0],bb[2]-1))
polygon=[[left,y] for y,left,right in rows]+[[right,y] for y,left,right in reversed(rows)]
drawn=Image.new('L',(800,374));ImageDraw.Draw(drawn).polygon(polygon,fill=255)
if ImageChops.difference(water,drawn).getbbox():raise ValueError('Water row contour must reconstruct actual diagnostic mask exactly')
def simplify(points):
 out=[]
 for p in points:
  while len(out)>=2 and (out[-1][0]-out[-2][0])*(p[1]-out[-1][1])==(out[-1][1]-out[-2][1])*(p[0]-out[-1][0]):out.pop()
  out.append(p)
 return out
polygon=simplify(polygon)
drawn=Image.new('L',(800,374));ImageDraw.Draw(drawn).polygon(polygon,fill=255)
if ImageChops.difference(water,drawn).getbbox():raise ValueError('Simplified water contour changed pixels')
record={'status':'authored configuration','background':packet['background'],'technical_rgba_source':{'path':str(rgba_path.relative_to(ROOT)).replace('\\','/'),'sha256':sha(rgba_path),'painted_rgb_bytes_unchanged':True,'alpha':255},'frozen_background_handoff':str(handoff.relative_to(ROOT)).replace('\\','/'),'frozen_background_handoff_sha256':sha(handoff),'water_annotation':packet['water_annotation'],'water_polygon':polygon,'water_polygon_reconstructs_mask_exactly':True,'water_scope':'Source-side annotation of independently inspected painted bay, not native adventure terrain or a general semantic water detector. Whole hull and dry house/fort/quarry controls separately reviewed.','generation_record':str((BG/'generation-v7.json').relative_to(ROOT)).replace('\\','/'),'generation_record_sha256':sha(BG/'generation-v7.json'),'assembly_script':str((BG/'assemble_background_v7.py').relative_to(ROOT)).replace('\\','/'),'assembly_script_sha256':sha(BG/'assemble_background_v7.py')}
save(HERE/'background-adoption.json',record)
recipe=deepcopy(load(ROOT/'assets/recipes/town/background.json'));raw=load(BG/'generation-v7.json')
recipe.update(source=record['technical_rgba_source']['path'],source_sha256=sha(rgba_path),source_canvas=[800,374],canvas=[800,374],fit='exact',status='authored configuration',production_status='painted-master-complete-unapproved',visual_approval_granted=False,selection_record='assets/production/town/community-selection-v2.json',selection_status='authored configuration',acceptance='Selected finite source-composition review only; native UI/art/rights/release acceptance remain separate.')
recipe['inputs']=[{'path':record[key],'sha256':record[key+'_sha256']} for key in ('generation_record','assembly_script')]
recipe['generation']={'image_generation_used':True,'tool':'image_gen.imagegen','provider':'OpenAI built-in imagegen','model':'Not exposed by the built-in tool','model_id_exposed':False,'prompt':raw['prompt'] if 'prompt' in raw else json.dumps(raw['prompts'],ensure_ascii=False,indent=2),'painted_master':packet['background']['path'],'painted_master_sha256':sha(source),'generation_record':record['generation_record'],'method':'Genuine imagegen whole-scene and local painted2D edits; technical crop/resample/bounded composition through pinned assembly. No procedural paving, 3D or render paintovers.','technical_producer':{'path':record['assembly_script'],'sha256':record['assembly_script_sha256']},'provenance_record':str((HERE/'background-adoption.json').relative_to(ROOT)).replace('\\','/'),'provenance_record_sha256':sha(HERE/'background-adoption.json'),'visual_approval_granted':False}
save(HERE/'background-recipe.json',recipe)
print(json.dumps({'background_sha256':sha(source),'water_contour_points':len(polygon),'mask_exact':True}))
