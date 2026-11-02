"""Source-bound checks for the finite Bandle hover candidates; no visual approval."""
import argparse,json,sys
from pathlib import Path
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'scripts'))
import town_hover_outlines as h
BASE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=Path,required=True);args=parser.parse_args();out=args.candidate.resolve()
traces=json.loads((BASE/'traces.json').read_text())['states'];receipt=json.loads((out/'receipt.json').read_text());assert receipt['traces_sha256']==h.digest(BASE/'traces.json')
assert len(traces)==35;checks=[]
for name,row in traces.items():
 source=ROOT/row['source']['path'];im=h.load(source);mask=Image.open(out/(name+'-architecture.png')).convert('L');alpha=h.binary(im.getchannel('A'))
 assert h.digest(source)==row['source']['sha256'],name
 assert ImageChops.subtract(mask,alpha).getbbox() is None,name
 assert mask.getbbox(),name
 assert not any(mask.histogram()[1:255]),name
 border=Image.open(out/'gallery/bandlecity'/name/'border.png').convert('RGBA')
 assert {c for n,c in border.getcolors(800*374)} <= {(0,0,0,0),h.GOLD,h.SHADOW},name
 assert not ImageChops.multiply(mask,border.getchannel('A')).getbbox(),name
 if row['points_native']:assert receipt['states'][name]['removed_alpha_pixels']>0,name
 checks.append({'state':name,'selected_painting_unchanged':True,'subset_of_selected_alpha':True,'binary_nonempty':True,'shared_style':True,'no_interior_outline':True,'architecture_accuracy':'pending independent review'})
h.write(out/'checks.json',{'status':'authored configuration','states_checked':len(checks),'passed':True,'checks':checks,'runtime_observed':False})
print('PASS '+str(len(checks))+' candidate geometry/source/style checks; actual architectural review remains separate')
