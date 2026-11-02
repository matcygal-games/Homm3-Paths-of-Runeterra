"""Exact source-bound context crops and preservation pins, no creative art."""
from pathlib import Path
import hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent;TOWN=HERE.parents[1];ROOT=TOWN.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=TOWN/'terrain/final-native-v12-proposal.png';assert sha(source)=='d594523cc2d00e0fc4f372e8de5e349496bf675f831d6bc9fd47ef7ee2cfee3f'
    bg=Image.open(source).convert('RGBA');guide=TOWN/'geometry-final-v2/connector-source-guide-v12-v2'
    body=Image.open(guide/'all36-actual-body.png').convert('L');roots=Image.open(guide/'all36-actual-structural-contact.png').convert('L')
    pins=[]
    for side,box,context in [('east',(414,168,445,186),(400,155,460,201)),('west',(0,130,14,148),(0,112,45,160))]:
        assert body.crop(box).getbbox() is None;assert roots.crop(box).getbbox() is None
        bg.crop(box).save(HERE/f'{side}-target.png');bg.crop(context).save(HERE/f'{side}-context.png')
        pins.append({'side':side,'core':box,'context':context,'body_pixels':0,'root_pixels':0})
    (HERE/'input-pins.json').write_text(json.dumps({'base_sha256':sha(source),'index_sha256':sha(TOWN/'native-transforms-v12/states.json'),'geometry_guide_sha256':sha(guide/'index.json'),'patches':pins},indent=2)+'\n')
    print(json.dumps(pins))
if __name__=='__main__':main()
