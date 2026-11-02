"""Reproduce the native dock-under-ship source repair from two locked paintings.

No creative imagery or transforms: retain all existing ship RGBA outside actual
dock support, alpha-composite the old dock under the old selected ship, then
derive click/highlight masks with the existing technical threshold convention.
"""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image,ImageChops,ImageFilter
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
INPUTS={
 'dock':('ownership-separation-v5/states/shipyard/frame.png','31dd6a5734d5874ba64479ef14cbfc633f4795c26c2503a61f1c043421a2895c'),
 'ship':('ownership-separation-v5/states/ship/frame.png','c5d5ff8d97149260293aa59721121d8395bbdc9d72ffad083ac755a064bf8449')}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def replay(destination):
 destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
 paintings={}
 for key,(name,pin)in INPUTS.items():
  path=HERE/name
  if sha(path)!=pin:raise ValueError('Locked existing coast painting changed: '+name)
  paintings[key]=Image.open(path).convert('RGBA')
 dock,ship=paintings['dock'],paintings['ship']
 merged=Image.alpha_composite(dock,ship);composite=ship.copy()
 composite.paste(merged,(0,0),dock.getchannel('A').point(lambda alpha:255 if alpha else 0))
 alpha=composite.getchannel('A')
 area=Image.new('RGBA',(800,374),(255,255,255,0));area.putalpha(alpha.point(lambda value:255 if value>=8 else 0))
 edge=ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(3)),alpha.filter(ImageFilter.MinFilter(3))).point(lambda value:255 if value else 0)
 border=Image.new('RGBA',(800,374),(255,255,255,0));border.putalpha(edge)
 for name,image in [('frame',composite),('alpha_mask',alpha),('area',area),('border',border)]:
  image.save(destination/(name+'.png'),compress_level=9,optimize=False)
 return {name:sha(destination/(name+'.png'))for name in ('frame','alpha_mask','area','border')}
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
 print(json.dumps(replay(parser.parse_args().out),indent=2,sort_keys=True))
