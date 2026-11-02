"""Final source-only registered dry quay landings; genuine painted floor inputs."""
from pathlib import Path
from copy import deepcopy
import hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=HERE/'candidate-final-v1'
REPORT=ROOT/'build/reports/complete-town-20261027-v2/final-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
 base=HERE/'candidate-clearance-v2';selection=deepcopy(load(base/'selection.json'));background=Image.open(ROOT/selection['terrain']['native']).convert('RGBA');master=HERE/'terrain/silo-support-master-v1.png';patch=Image.open(master).convert('RGBA').crop((0,15,2170,725)).resize((139,44),Image.Resampling.LANCZOS);background.alpha_composite(patch,(645,231));silo_stage=HERE/'terrain/silo-landing-native-v1.png';save(silo_stage,background)
 # A real already-painted unobstructed paving crop supplies the tiny upper quay
 # strip. Exact crop/composition preserves the existing coast water below y163.
 quay=background.crop((680,244,740,254));background.alpha_composite(quay,(710,149));native=HERE/'terrain/final-native-v1.png';save(native,background)
 repair={'script':rel(Path(__file__)),'script_sha256':sha(Path(__file__)),'silo_painted_master':rel(master),'silo_painted_master_sha256':sha(master),'silo_source_crop':[0,15,2170,725],'silo_registered_rectangle':[645,231,784,275],'upper_quay_painted_floor_source':rel(silo_stage),'upper_quay_painted_floor_source_sha256':sha(silo_stage),'upper_quay_source_crop':[680,244,740,254],'upper_quay_destination':[710,149,770,159],'method':'Uniform resize and exact registered composition of genuine painted2D floor/court inputs; no procedural geometry or bitmap-painted architecture. Water below y163 unchanged.'}
 selection['terrain'].update(native=rel(native),native_sha256=sha(native),east_support_repair=repair);recipes={n:deepcopy(load(base/'candidate-recipes'/n)) for n in selection['recipes']};recipe=recipes['assets/recipes/town/background.json'];recipe.update(source=rel(native),source_sha256=sha(native),sha256=sha(native));recipe['generation']['east_support_repair']=repair;selection['recipes']={}
 for name,recipe in recipes.items():p=OUT/'candidate-recipes'/name;write(p,recipe);selection['recipes'][name]=sha(p)
 write(OUT/'selection.json',selection);write(OUT/'factions.candidate.json',load(base/'factions.candidate.json'));rows={r['state']:r for r in selection['states']};save(REPORT/'empty-native.png',background)
 for mode in ('full','base','early','coast','grail','guild-absent'):
  chosen=[site['states'][0] if mode=='base' else site['top'] for site in selection['sites'] if site['id'] not in ('coast','grail')]
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  if mode=='coast':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  out=background.copy()
  for state in sorted(chosen,key=lambda s:rows[s]['native_z']):out.alpha_composite(Image.open(ROOT/rows[state]['native_layer']).convert('RGBA'))
  save(REPORT/(mode+'-native.png'),out)
 for name,im in [('empty',background),('full',Image.open(REPORT/'full-native.png'))]:
  save(REPORT/(name+'-silo-support-8x.png'),im.crop((640,226,784,278)).resize((1152,416),Image.Resampling.NEAREST));save(REPORT/(name+'-martial-support-8x.png'),im.crop((685,140,780,170)).resize((760,240),Image.Resampling.NEAREST))
 print(json.dumps({'candidate':rel(OUT),'background_sha256':sha(native),'masters_preserved':True}))
if __name__=='__main__':main()
