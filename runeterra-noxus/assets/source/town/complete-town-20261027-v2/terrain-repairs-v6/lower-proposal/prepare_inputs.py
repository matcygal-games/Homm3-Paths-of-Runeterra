"""Bounded deterministic reference crops and geometry guides; no artwork."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
TOWN=HERE.parents[1]
ROOT=TOWN.parents[3]
BOXES={'tavern':(0,300,270,374),'foundry':(570,305,800,374)}
STATES={'tavern':'tavern','foundry':'blacksmith'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 bgp=TOWN/'terrain/final-native-v5.png';bg=Image.open(bgp).convert('RGBA')
 sel=json.loads((TOWN/'candidate-final-v5/selection.json').read_text())
 rows={r['state']:r for r in sel['states']}
 pins={'terrain':{'path':bgp.relative_to(ROOT).as_posix(),'sha256':sha(bgp)},'selection_sha256':sha(TOWN/'candidate-final-v5/selection.json'),'frames':{r['state']:{'path':r['native_layer'],'sha256':sha(ROOT/r['native_layer'])}for r in sel['states']},'masters':{r['state']:{'path':r['master'],'sha256':sha(ROOT/r['master'])}for r in sel['states']},'crop_boxes':BOXES}
 for name,box in BOXES.items():
  bg.crop(box).save(HERE/f'{name}-target-v1.png')
  im=bg.copy();im.alpha_composite(Image.open(ROOT/rows[STATES[name]]['native_layer']).convert('RGBA'));im.crop((box[0],max(0,box[1]-130),box[2],box[3])).save(HERE/f'{name}-architecture-context-v1.png')
  mask=Image.open(TOWN/f'physical-v10/{STATES[name]}/foundation.png').convert('L');guide=bg.copy();col=Image.new('RGBA',bg.size,(255,0,40,255));guide.paste(col,(0,0),mask);guide.crop(box).save(HERE/f'{name}-root-guide-v1.png')
 (HERE/'input-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
if __name__=='__main__':main()
