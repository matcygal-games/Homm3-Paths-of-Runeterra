"""Verify border-only Bilgewater candidates; no broad faction or native acceptance."""
import argparse,sys
from pathlib import Path
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'scripts'))
import town_hover_outlines as h
BASE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);a=p.parse_args();out=a.candidate.resolve();traces=h.read(BASE/'traces.json');receipt=h.read(out/'receipt.json');assert receipt['traces_sha256']==h.digest(BASE/'traces.json');assert len(traces['states'])==35;rows=[]
for name,row in traces['states'].items():
 source=ROOT/row['source']['path'];assert h.digest(source)==row['source']['sha256'];im=h.load(source);base=h.binary(im.getchannel('A'));mask=Image.open(out/(name+'-mask.png')).convert('L');assert mask.size==h.SIZE and mask.getbbox()and not any(mask.histogram()[1:255]);assert not ImageChops.subtract(mask,base).getbbox();border=Image.open(out/'gallery/bilgewater'/name/'border.png').convert('RGBA');assert {c for n,c in border.getcolors(800*374)}<={(0,0,0,0),h.GOLD,h.SHADOW};assert not ImageChops.multiply(mask,border.getchannel('A')).getbbox()
 if not row['points_native']:assert not ImageChops.difference(mask,base).getbbox()
 rows.append({'state':name,'source_hash_matches':True,'binary_native_subset':True,'nonempty':True,'shared_style':True,'no_interior_tint':True})
h.write(out/'checks.json',{'status':'authored configuration','passed':True,'states_checked':35,'checks':rows,'runtime_observed':False,'scope':'hover borders only'});print('PASS35 source/geometry/style checks')
