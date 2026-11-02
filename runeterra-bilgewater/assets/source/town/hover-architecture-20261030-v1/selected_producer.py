"""Reproduce Bilgewater hover-only masks from pinned painted layers and editable contours."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageFilter
GOLD=(225,190,80,255);SHADOW=(38,29,15,208);SIZE=(800,374)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def produce(project,traces,output):
 project=Path(project).resolve();output=Path(output).resolve()
 if output.exists() and any(output.iterdir()):raise ValueError('Use an empty reproduction destination')
 output.mkdir(parents=True,exist_ok=True)
 rows=json.loads(Path(traces).read_text())['states'];result={}
 for name,row in sorted(rows.items()):
  path=(project/row['source']['path']).resolve()
  if not path.is_relative_to(project) or sha(path)!=row['source']['sha256']:raise ValueError('Selected painting changed '+name)
  with Image.open(path) as image:
   if image.mode!='RGBA' or image.size!=SIZE:raise ValueError('Expected native RGBA layer')
   alpha=image.getchannel('A').point(lambda v:255 if v>=128 else 0)
  if row['points_native']:
   env=Image.new('L',SIZE);ImageDraw.Draw(env).polygon([tuple(p) for p in row['points_native']],fill=255);mask=ImageChops.multiply(alpha,env)
  else:mask=alpha
  if not mask.getbbox():raise ValueError('Empty architecture '+name)
  near=mask.filter(ImageFilter.MaxFilter(3));far=mask.filter(ImageFilter.MaxFilter(5));gold=ImageChops.subtract(near,mask);shadow=ImageChops.subtract(far,near)
  border=Image.new('RGBA',SIZE);s=Image.new('RGBA',SIZE,SHADOW);s.putalpha(shadow.point(lambda v:208 if v else 0));border.alpha_composite(s);s=Image.new('RGBA',SIZE,GOLD);s.putalpha(gold);border.alpha_composite(s)
  target=output/name;target.mkdir();mask.save(target/'architecture-mask.png');border.save(target/'border.png');result[name]={'architecture_sha256':sha(target/'architecture-mask.png'),'border_sha256':sha(target/'border.png')}
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--traces',type=Path,default=Path(__file__).with_name('traces.json'));p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(produce(a.project,a.traces,a.output),indent=2))
