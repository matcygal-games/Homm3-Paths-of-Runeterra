"""Compose two genuine painted terrain edits; all building masters stay exact."""
from pathlib import Path
from copy import deepcopy
import hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=HERE/'candidate-access-v2'
REPORT=ROOT/'build/reports/complete-town-20261027-v2/access-v3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
 base=HERE/'candidate-access-v1';selection=deepcopy(load(base/'selection.json'));background=Image.open(ROOT/selection['terrain']['native']).convert('RGBA');original=background.copy();patches=[]
 for name,box in [('rift-support-crop-master-v2.png',(390,230,560,300)),('rift-connector-master-v4.png',(399,254,431,287))]:
  source=HERE/'terrain'/name;patch=Image.open(source).convert('RGBA').resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS);background.alpha_composite(patch,(box[0],box[1]));patches.append({'master':rel(source),'sha256':sha(source),'native_rectangle':list(box),'conversion':'Uniform LANCZOS resize and exact alpha composition only.'})
 native=HERE/'terrain/rift-support-connected-native-v1.png';save(native,background)
 selection['terrain'].update(native=rel(native),native_sha256=sha(native),bounded_repair={'patches':patches,'script':rel(Path(__file__)),'script_sha256':sha(Path(__file__)),'preserved_outside_native_rectangle':[390,230,560,300]})
 recipes={n:deepcopy(load(base/'candidate-recipes'/n)) for n in selection['recipes']};recipe=recipes['assets/recipes/town/background.json'];recipe.update(source=rel(native),source_sha256=sha(native),sha256=sha(native));recipe['generation']={'image_generation_used':True,'provider':'OpenAI built-in image_gen','model':'Not exposed by built-in tool','prompt':load(HERE/'terrain/rift-support-crop-generation-v2.json')['prompt']+'\n\nCONNECTOR EDIT: '+load(HERE/'terrain/rift-connector-generation-v4.json')['prompt'],'painted_master':rel(HERE/'terrain/rift-support-crop-master-v2.png'),'painted_master_sha256':sha(HERE/'terrain/rift-support-crop-master-v2.png'),'generation_record':rel(HERE/'terrain/rift-support-crop-generation-v2.json'),'generation_record_sha256':sha(HERE/'terrain/rift-support-crop-generation-v2.json'),'bounded_repair':selection['terrain']['bounded_repair']}
 selection['recipes']={}
 for name,recipe in recipes.items():p=OUT/'candidate-recipes'/name;write(p,recipe);selection['recipes'][name]=sha(p)
 # Correct per-state real gate/foot intents; actual corridor masks follow later.
 for row in selection['states']:
  if row['state']=='dwellingLvl4':row['entrance_intent']=[548,192];row['gate_intent']=[547,175]
  if row['state']=='dwellingUpLvl4':row['entrance_intent']=[509,190];row['gate_intent']=[508,177]
 write(OUT/'selection.json',selection);write(OUT/'factions.candidate.json',load(base/'factions.candidate.json'))
 rows={r['state']:r for r in selection['states']};layers={s:Image.open(ROOT/r['native_layer']).convert('RGBA') for s,r in rows.items()}
 save(REPORT/'empty-native.png',background)
 for mode in ('full','base','early','rose-absent','rift-absent','guild-absent','coast','grail'):
  chosen=[site['states'][0] if mode=='base' else site['top'] for site in selection['sites'] if site['id'] not in ('coast','grail')]
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  for m,s in [('rose-absent','dwellingUpLvl4'),('rift-absent','dwellingUpLvl7'),('guild-absent','mageGuild4')]:
   if mode==m:chosen.remove(s)
  if mode=='coast':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  out=background.copy()
  for state in sorted(chosen,key=lambda s:rows[s]['native_z']):out.alpha_composite(layers[state])
  save(REPORT/(mode+'-native.png'),out)
  if mode in ('full','base'):save(REPORT/(mode+'-rift-context-6x.png'),out.crop((390,160,570,300)).resize((1080,840),Image.Resampling.NEAREST))
 save(REPORT/'empty-rift-context-6x.png',background.crop((390,230,560,300)).resize((1020,420),Image.Resampling.NEAREST))
 print(json.dumps({'candidate':rel(OUT),'background':rel(native),'background_sha256':sha(native),'building_appearance_changed':False}))
if __name__=='__main__':main()
