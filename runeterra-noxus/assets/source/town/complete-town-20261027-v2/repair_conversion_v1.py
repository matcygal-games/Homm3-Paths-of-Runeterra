"""Versioned technical recipe repair, preserving the first candidate and sources."""
from pathlib import Path
from copy import deepcopy
import hashlib,json
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def main():
 old=HERE/'candidate';new=HERE/'candidate-compatible-v1'
 selection=deepcopy(load(old/'selection.json'));pins={}
 background=HERE/'terrain/native-rgba-conversion-v1.png'
 source=ROOT/selection['terrain']['native']
 if sha(source)!=selection['terrain']['native_sha256']:raise ValueError('Changed original background')
 rgba=Image.open(source).convert('RGBA');rgba.save(background,compress_level=9)
 if rgba.convert('RGB').tobytes()!=Image.open(source).convert('RGB').tobytes():raise ValueError('RGB pixels changed')
 for p in sorted((old/'candidate-recipes').rglob('*.json')):
  relative=p.relative_to(old/'candidate-recipes').as_posix();recipe=deepcopy(load(p))
  if sha(p)!=selection['recipes'][relative]:raise ValueError('Changed candidate recipe '+relative)
  if relative.endswith('-animation.json'):
   generation=recipe['generation'];record=ROOT/generation['generation_record']
   if sha(record)!=generation['generation_record_sha256']:raise ValueError('Changed genuine provenance record')
   generation['prompt']=load(record)['prompt']
  elif relative=='assets/recipes/town/background.json':
   recipe.update(source=background.relative_to(ROOT).as_posix(),source_sha256=sha(background),sha256=sha(background))
   recipe['generation']['conversion']='Byte-preserving RGB to RGBA format conversion of prior native terrain; no artistic pixel edits.'
  target=new/'candidate-recipes'/relative;write(target,recipe);pins[relative]=sha(target)
 selection['recipes']=pins;selection['terrain']['native']=background.relative_to(ROOT).as_posix();selection['terrain']['native_sha256']=sha(background)
 selection['conversion_repair']={'script':Path(__file__).relative_to(ROOT).as_posix(),'script_sha256':sha(Path(__file__)),'original_candidate_sha256':sha(old/'selection.json'),'changes':['Restore exact genuine generation prompt in each of36animation recipes.','Convert native background RGB to RGBA without changing RGB pixels.'],'visual_approval_granted':False}
 write(new/'selection.json',selection);write(new/'factions.candidate.json',load(old/'factions.candidate.json'))
 print(json.dumps({'candidate':new.relative_to(ROOT).as_posix(),'recipes':len(pins),'all_building_pixels_unchanged':True,'background_rgb_unchanged':True}))
if __name__=='__main__':main()
