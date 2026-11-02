"""Bilgewater hover-only candidates; no town, artwork, click or gameplay changes."""
import argparse,json,sys
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'scripts'))
import town_hover_outlines as h
BASE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
if not out.is_relative_to(ROOT/'reports')or out.exists():raise ValueError('Use fresh workspace report path')
out.mkdir(parents=True);traces=h.read(BASE/'traces.json');selections={};rows=[]
for name,row in traces['states'].items():
 source=ROOT/row['source']['path'];assert h.digest(source)==row['source']['sha256'];image=h.load(source);alpha=h.binary(image.getchannel('A'));mask=alpha
 if row['points_native']:
  envelope=Image.new('L',h.SIZE);ImageDraw.Draw(envelope).polygon([tuple(p)for p in row['points_native']],fill=255);mask=ImageChops.multiply(alpha,envelope)
 target=out/(name+'-mask.png');mask.save(target);selections['bilgewater/'+name]={'path':target.relative_to(ROOT).as_posix(),'sha256':h.digest(target)};rows.append({'state':name,'painted_source':row['source'],'mask_sha256':h.digest(target),'method':row['method']})
h.write(out/'mask-selections.json',selections);h.candidate(ROOT,out/'gallery',('bilgewater',),selections);h.write(out/'receipt.json',{'status':'design proposal','producer_sha256':h.digest(__file__),'traces_sha256':h.digest(BASE/'traces.json'),'states':rows,'source_mutations':0,'click_mutations':0,'selected_recipe_mutations':0,'runtime_observed':False});print(out)
