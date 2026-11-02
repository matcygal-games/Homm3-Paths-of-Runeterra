"""Separate whole new Elder painted actors without changing their body pixels."""
from pathlib import Path
import hashlib,json,sys,importlib.util
import numpy as np
from PIL import Image,ImageFilter
HERE=Path(__file__).resolve().parent;PROJECT=next(p for p in HERE.parents if p.name=='runeterra-ixtal');sys.dont_write_bytecode=True
HELPER=HERE.parents[1]/'extract_sources.py';spec=importlib.util.spec_from_file_location('immutable_alpha_component_helper',HELPER);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 config=json.loads((HERE/'pose-roots-v1.json').read_text());cohorts={}
 for kind,selection in config['cohorts'].items():
  source=HERE/selection['file'];im=Image.open(source).convert('RGBA');labels,stats=helper.components(im.getchannel('A'));majors=[k for k,s in stats.items()if s['area']>=2000];expected=4 if kind=='holding' else 16
  assert len(majors)==expected,('Need separate whole painted actors',kind,len(majors))
  def center(k):s=stats[k];return s['sx']/s['area'],s['sy']/s['area']
  columns=2 if kind=='holding' else 4;order=[];by_y=sorted(majors,key=lambda k:center(k)[1])
  for i in range(0,len(by_y),columns):order.extend(sorted(by_y[i:i+columns],key=lambda k:center(k)[0]))
  owners={k:k for k in majors}
  def distance(k,m):
   x,y=center(k);a,b,c,d=stats[m]['bbox'];return max(a-x,0,x-c)**2+max(b-y,0,y-d)**2
  for k,s in stats.items():
   if k not in owners:
    near=min(majors,key=lambda m:distance(k,m))
    if distance(k,near)<=64**2:owners[k]=near
    elif s['area']>=8:raise ValueError('Unassociated body component')
  rows=[]
  for index,k in enumerate(order):
   ids=[a for a,b in owners.items()if b==k];own=np.isin(labels,ids);foreign=np.isin(labels,[a for a,b in owners.items()if b!=k]);expand=np.asarray(Image.fromarray(np.where(own,255,0).astype('uint8')).filter(ImageFilter.MaxFilter(7)))>0;foreign_expand=np.asarray(Image.fromarray(np.where(foreign,255,0).astype('uint8')).filter(ImageFilter.MaxFilter(7)))>0;mask=(expand&~foreign_expand)|own;assert not np.any(mask&foreign)
   pixels=np.array(im);original=pixels.copy();pixels[:,:,3]=np.where(mask,pixels[:,:,3],0);assert np.array_equal(pixels[:,:,:3],original[:,:,:3])and np.array_equal(pixels[:,:,3][own],original[:,:,3][own]);actor=Image.fromarray(pixels);box=actor.getchannel('A').getbbox();out=HERE/'isolated'/f'{kind}-{index:02d}.png';out.parent.mkdir(exist_ok=True);actor.crop(box).save(out,compress_level=9)
   rows.append({'index':index,'source':source.relative_to(PROJECT).as_posix(),'source_sha256':sha(source),'source_canvas':list(im.size),'crop':list(box),'principal_bbox':stats[k]['bbox'],'image':out.relative_to(PROJECT).as_posix(),'sha256':sha(out),'source_rgb_preserved':True,'source_alpha_core_preserved':True,'selected':not(kind=='holding'and index==3)})
  cohorts[kind]=rows
 out=HERE/'isolated-source-map-v1.json';out.write_text(json.dumps({'status':'authored configuration','method':'Whole owned alpha component separation; original RGB and core alpha preserved, no painted body changes','helper':HELPER.relative_to(PROJECT).as_posix(),'helper_sha256':sha(HELPER),'cohorts':cohorts},indent=2)+'\n');print({k:len(v)for k,v in cohorts.items()})
if __name__=='__main__':main()
