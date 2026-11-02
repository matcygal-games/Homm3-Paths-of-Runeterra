"""Real last landing/connector repair, keeping previous candidates immutable."""
from pathlib import Path
from copy import deepcopy
import hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
OUT=HERE/'candidate-final-v3';REPORT=ROOT/'build/reports/complete-town-20261027-v2/final-v3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
 base=HERE/'candidate-final-v2';s=deepcopy(load(base/'selection.json'));bg=Image.open(ROOT/s['terrain']['native']).convert('RGBA');patches=[]
 for name,box in [('knife-floor-interior-master-v3.png',(0,170,115,212)),('rift-connector-master-v2.png',(388,255,430,286))]:
  p=HERE/'terrain'/name;im=Image.open(p).convert('RGBA').resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS);bg.alpha_composite(im,(box[0],box[1]));patches.append({'master':rel(p),'master_sha256':sha(p),'native_rectangle':list(box),'method':'Uniform painted image scale and exact native composition; no procedural bitmap painting.'})
 native=HERE/'terrain/final-native-v3.png';save(native,bg);s['terrain'].update(native=rel(native),native_sha256=sha(native),last_public_flight_repair={'script':rel(Path(__file__)),'script_sha256':sha(Path(__file__)),'patches':patches});recipes={n:deepcopy(load(base/'candidate-recipes'/n)) for n in s['recipes']};r=recipes['assets/recipes/town/background.json'];r.update(source=rel(native),source_sha256=sha(native),sha256=sha(native));r['generation']['last_public_flight_repair']=s['terrain']['last_public_flight_repair'];s['recipes']={}
 for name,r in recipes.items():p=OUT/'candidate-recipes'/name;write(p,r);s['recipes'][name]=sha(p)
 write(OUT/'selection.json',s);write(OUT/'factions.candidate.json',load(base/'factions.candidate.json'));save(REPORT/'empty-native.png',bg);rows={r['state']:r for r in s['states']}
 for mode in ('full','base','early','coast','grail','guild-absent'):
  chosen=[site['states'][0] if mode=='base' else site['top'] for site in s['sites'] if site['id'] not in ('coast','grail')]
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  if mode=='coast':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  out=bg.copy()
  for state in sorted(chosen,key=lambda a:rows[a]['native_z']):out.alpha_composite(Image.open(ROOT/rows[state]['native_layer']).convert('RGBA'))
  save(REPORT/(mode+'-native.png'),out)
 print(json.dumps({'candidate':rel(OUT),'background_sha256':sha(native)}))
if __name__=='__main__':main()
