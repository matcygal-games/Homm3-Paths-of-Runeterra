"""Pin the coordinator's saved pure-painted building edits; no artwork generation."""
import hashlib,json
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[4]
parents={'cityHall':'assets/source/town/buildings-v2/townHall/master.png','citadel':'assets/source/town/buildings-v1/fort/master.png','mageGuild2':'assets/source/town/buildings-v1/mageGuild1/master.png'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for key,parent in parents.items():
 folder=Path(__file__).parent/key;path=folder/'master.png';prompt=folder/'prompt.txt';out=folder/'master-generation.json'
 if out.exists():raise ValueError('Refusing to overwrite versioned provenance')
 with Image.open(path) as im:size=list(im.size);mode=im.mode;alpha=list(im.getchannel('A').getextrema())
 value=dict(key=key,status='authored configuration',image_generation_used=True,provider='OpenAI built-in imagegen',model='not exposed by built-in tool',master=path.relative_to(root).as_posix(),master_sha256=sha(path),dimensions=size,mode=mode,alpha_extrema=alpha,prompt=prompt.relative_to(root).as_posix(),prompt_sha256=sha(prompt),parent=parent,parent_sha256=sha(root/parent),derived_from_blender=False,selected_for_build=False,visual_approval_granted=False,native_execution=False,redistribution='pending')
 out.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(key=key,sha256=sha(out))))
