"""Record saved builtin painted sources and prompts; does not select or approve art."""
import hashlib,json
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[4]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
items=[('assets/source/creatures/painted-v1','desertNomad-standing-master-v1.png','desertNomad-standing-prompt-v1.txt',None),('assets/source/creatures/painted-v1','sandWarrior-standing-master-v1.png','sandWarrior-standing-prompt-v1.txt','assets/source/creatures/painted-v1/desertNomad-standing-master-v1.png'),('assets/source/town/buildings-v2/townHall','master.png','prompt.txt','assets/source/town/buildings-v1/villageHall/master.png')]
for folder,master,prompt,parent in items:
 path=root/folder/master;promptpath=root/folder/prompt;out=path.with_name(path.stem+'-generation.json')
 if out.exists():raise ValueError('Refusing to overwrite '+str(out))
 with Image.open(path) as im:size=list(im.size);mode=im.mode;alpha=list(im.getchannel('A').getextrema())
 value=dict(status='authored configuration',image_generation_used=True,provider='OpenAI built-in imagegen',model='not exposed by built-in tool',master=path.relative_to(root).as_posix(),master_sha256=sha(path),dimensions=size,mode=mode,alpha_extrema=alpha,prompt=promptpath.relative_to(root).as_posix(),prompt_sha256=sha(promptpath),parent=parent,parent_sha256=sha(root/parent) if parent else None,derived_from_blender=False,selected_for_build=False,visual_approval_granted=False,native_execution=False,redistribution='pending')
 out.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(path=out.relative_to(root).as_posix(),sha256=sha(out))))
