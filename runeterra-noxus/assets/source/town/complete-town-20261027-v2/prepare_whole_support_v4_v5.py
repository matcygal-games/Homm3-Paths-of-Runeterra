"""Reproduce whole terrain repair, then the demonstrated Minotaur apron fix.

Every architecture source and selected frame remains unchanged. Only genuine
painted background images are cropped/scaled/composed; no acceptance is granted.
"""
from pathlib import Path
from copy import deepcopy
import argparse,hashlib,json
from PIL import Image,ImageOps,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def rel(p):return p.relative_to(ROOT).as_posix()
def ref(p):return {'path':rel(p),'sha256':sha(p)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--minotaur-apron',action='store_true');args=ap.parse_args();version=5 if args.minotaur_apron else 4;out=HERE/f'candidate-final-v{version}';report=ROOT/f'build/reports/complete-town-20261027-v2/final-v{version}';base=HERE/'candidate-final-v3';s=deepcopy(load(base/'selection.json'));master=HERE/'terrain/whole-support-master-v4.png';record=HERE/'terrain/whole-support-generation-v4.json';bg=ImageOps.fit(Image.open(master).convert('RGBA'),(800,374),method=Image.Resampling.LANCZOS);corrections=[]
 if args.minotaur_apron:
  correction=HERE/'terrain/minotaur-apron-master-v5.png';crecord=HERE/'terrain/minotaur-apron-generation-v5.json';crop=(0,71,2172,643);patch=ImageOps.fit(Image.open(correction).convert('RGBA').crop(crop),(183,49),method=Image.Resampling.LANCZOS);bg.alpha_composite(patch,(407,316));corrections.append({'source':ref(correction),'generation_record':ref(crecord),'source_crop':list(crop),'native_rectangle':[407,316,590,365],'method':'Remove generated black letterbox; uniformly fit genuine painted crop and compose at exact native context.'})
 native=HERE/f'terrain/final-native-v{version}.png';save(native,bg);s['terrain'].update(master=rel(master),master_sha256=sha(master),native=rel(native),native_sha256=sha(native),whole_ground_repair={'master':ref(master),'record':ref(record),'corrections':corrections,'script':ref(Path(__file__)),'geometric_admission':False});recipes={n:deepcopy(load(base/'candidate-recipes'/n)) for n in s['recipes']};r=recipes['assets/recipes/town/background.json'];r.update(source=rel(native),source_sha256=sha(native),sha256=sha(native));r['generation']={'image_generation_used':True,'provider':'OpenAI built-in image_gen','model':'Not exposed by built-in tool','prompt':load(record)['prompt'],'painted_master':rel(master),'painted_master_sha256':sha(master),'generation_record':rel(record),'generation_record_sha256':sha(record),'whole_ground_repair':s['terrain']['whole_ground_repair']};s['recipes']={}
 for name,r in recipes.items():p=out/'candidate-recipes'/name;write(p,r);s['recipes'][name]=sha(p)
 write(out/'selection.json',s);write(out/'factions.candidate.json',load(base/'factions.candidate.json'));save(report/'empty-native.png',bg);rows={r['state']:r for r in s['states']}
 for mode in ('full','base','early','coast','grail','guild-absent'):
  chosen=[site['states'][0] if mode=='base' else site['top'] for site in s['sites'] if site['id'] not in ('coast','grail')]
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  if mode=='coast':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  im=bg.copy()
  for state in sorted(chosen,key=lambda k:rows[k]['native_z']):im.alpha_composite(Image.open(ROOT/rows[state]['native_layer']).convert('RGBA'))
  save(report/(mode+'-native.png'),im)
 for name,im in [('empty',bg),('full',Image.open(report/'full-native.png')),('base',Image.open(report/'base-native.png'))]:
  save(report/(name+'-minotaur-apron-6x.png'),im.crop((407,316,590,365)).resize((1098,294),Image.Resampling.NEAREST))
 print(json.dumps({'candidate':rel(out),'terrain':ref(native),'source_master':ref(master),'corrections':len(corrections)}))
if __name__=='__main__':main()
