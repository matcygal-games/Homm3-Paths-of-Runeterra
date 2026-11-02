"""Record actual built-in generation inputs without claiming model/rights approval."""
from pathlib import Path
import hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record(folder,master='master.png',prompt='prompt.txt',output='generation.json',reference=None):
 p=HERE/folder/master;q=HERE/folder/prompt
 data={'status':'authored configuration','image_generation_used':True,'provider':'OpenAI built-in imagegen','model':None,'model_note':'Built-in tool did not expose a concrete model identifier','created':'2026-10-24','master':p.relative_to(HERE).as_posix(),'master_sha256':sha(p),'canvas':list(Image.open(p).size),'prompt_file':q.relative_to(HERE).as_posix(),'prompt_sha256':sha(q),'prompt':q.read_text(encoding='utf-8'),'method':'Genuine painted2D image generation, no3D render or procedural painting','references_note':'Original HoMM3 native references and official Riot Zaun environment researched as style/identity guidance; no source reference pixels composited','visual_approval_granted':False,'runtime_verified':False,'rights_review':'pending external review'}
 if reference:
  r=HERE/reference;data['edit_reference']={'path':reference,'sha256':sha(r)}
 (HERE/folder/output).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
record('background')
record('background','master-v2.png','prompt-v2.txt','generation-v2.json','background/master.png')
record('background','master-v3.png','prompt-v3.txt','generation-v3.json','background/master-v2.png')
for tier in [2,6,7]:
 record('dwellingLvl'+str(tier))
 record('dwellingUpLvl'+str(tier),reference='dwellingLvl'+str(tier)+'/master.png')
