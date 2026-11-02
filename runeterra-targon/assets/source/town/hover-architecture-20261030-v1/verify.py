"""Verify source pins and geometry of finite Targon hover candidates."""
import argparse,json,sys
from pathlib import Path
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'scripts'))
import town_hover_outlines as h
BASE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=Path,required=True);args=parser.parse_args();out=args.candidate.resolve();selection=h.read(BASE/'selection.json');receipt=h.read(out/'receipt.json');assert receipt['selection_sha256']==h.digest(BASE/'selection.json');assert len(selection['states'])==35
checks=[]
for name,row in selection['states'].items():
 source=ROOT/row['source']['path'];assert h.digest(source)==row['source']['sha256'];image=h.load(source);alpha=h.binary(image.getchannel('A'));mask=Image.open(out/(name+'-mask.png')).convert('L');assert mask.getbbox() and not any(mask.histogram()[1:255]);assert not ImageChops.subtract(mask,alpha).getbbox()
 border=Image.open(out/'gallery/targon'/name/'border.png').convert('RGBA');assert {c for n,c in border.getcolors(800*374)}<={(0,0,0,0),h.GOLD,h.SHADOW};assert not ImageChops.multiply(mask,border.getchannel('A')).getbbox()
 if not row['remove_exterior_sky']:assert not ImageChops.difference(mask,alpha).getbbox()
 checks.append({'state':name,'source_unchanged':True,'binary_native_subset':True,'nonempty':True,'shared_style':True,'no_interior_outline':True})
h.write(out/'checks.json',{'status':'authored configuration','passed':True,'states_checked':len(checks),'checks':checks,'runtime_observed':False,'architectural_accuracy':'pending independent source review'});print('PASS35 source/geometry/style checks')
