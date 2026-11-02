"""Isolated material candidate exports; never modifies active selections."""
from pathlib import Path
import sys,json,hashlib,re,copy,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageOps
P=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(P/'scripts'))
from creature_padding import crop_padding
from animation import assemble
from raster import convert
B=Path(__file__).parent
R=P/'build/reports/art-review/current-20261020/upper/awakened-material'
R.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(d,indent=2)+'\n')
def rel(p):return Path(p).relative_to(P).as_posix()
def bounds(im,t=128):return im.getchannel('A').point(lambda a:255 if a>=t else 0).getbbox()
def mask(im):return np.array(im.getchannel('A'))>=128
def cell(im,i,layout):
 c,r=layout;w,h=im.width/c,im.height/r;x,y=i%c*w,i//c*h
 return im.resize((round(w),round(h)),Image.Resampling.LANCZOS,box=(x,y,x+w,y+h)),(x,y,w,h)
mapping=read(B/'selected-mapping.json');active=read(P/'assets/recipes/creatures/awakenedColossus-battle.json')
prod=read(P/'assets/source/creatures/awakenedColossus/colossus-rig-v2/painted-actions-production-v1.json')
converted={a['group']:a['converted_frames'] for a in prod['actions']}
metrics=[];sources={};cameras=[]
for row in mapping:
 g=row['group'];v=3 if (B/f'g{g:02}-material-v3.png').exists() else 2 if (B/f'g{g:02}-material-v3.png').exists() else 1
 src=B/f'g{g:02}-material-v{v}.png';old=Image.open(P/row['atlas']).convert('RGBA');new=Image.open(src).convert('RGBA')
 scale=row['scale']*old.width/new.width;offset=list(row['offset'])
 if g==30:
  mat=[];target=[]
  for ii,ff in enumerate(row['frames']):
   part,_=cell(new,ii,row['layout']);bb=bounds(part);ob=bounds(Image.open(P/converted[g][ii]['output']).convert('RGBA'));dx0,dy0=ff['placement']['native_translation']
   for nx,ny,tx,ty in [(bb[0],bb[1],ob[0]-dx0,ob[1]-dy0),(bb[2],bb[3],ob[2]-dx0,ob[3]-dy0)]:
    mat.extend([[nx,1,0],[ny,0,1]]);target.extend([tx,ty])
  solution=np.linalg.lstsq(np.array(mat),np.array(target),rcond=None)[0];scale=float(solution[0]);offset=[round(float(v)) for v in solution[1:]]
  write(R/'g30-uniform-camera-v3.json',{'rule':'One uniform scalar and one shared translation fitted to all6pose bounding corners, not independent frame fits. Existing native placement-v4 offsets remain.','scale':scale,'offset':offset,'fit_rms':float(np.sqrt(np.mean((np.array(mat)@solution-np.array(target))**2))),'source_sha256':sha(src)})
 # Only explicit whole-atlas normalization, with the unchanged measured camera.
 # Per-pose fitting is forbidden. Existing native translations remain exact.
 for i,frame in enumerate(row['frames']):
  _,(x,y,w,h)=cell(new,i,row['layout']);part=new.resize((round(w*scale),round(h*scale)),Image.Resampling.LANCZOS,box=(x,y,x+w,y+h))
  dx,dy=frame['placement']['native_translation'];out=Image.new('RGBA',(450,400));out.alpha_composite(part,(offset[0]+dx,offset[1]+dy))
  raw=B/'native-untrimmed-v3'/f'g{g:02}-f{i:03}.png';raw.parent.mkdir(exist_ok=True);out.save(raw)
  dest=B/'native-candidate-v3'/raw.name;crop_padding(raw,dest,P)
  original=Image.open(P/converted[g][i]['output']).convert('RGBA');ob,nb=bounds(original),bounds(out)
  def contact(im):
   arr=mask(im);bb=bounds(im);ys,xs=np.where(arr[max(0,bb[3]-4):bb[3]]);return float(xs.mean())
  rx=round(contact(original)-contact(out));ry=ob[3]-nb[3]
  if rx or ry:
   moved=Image.new('RGBA',out.size);moved.alpha_composite(out,(rx,ry));out=moved;out.save(raw)
   dest=B/'native-candidate-v3'/raw.name
   # The first padded projection remains as history. Registered output has a different versioned filename.
   dest=dest.with_stem(dest.stem+'-registered');crop_padding(raw,dest,P)
  nb=bounds(out);a,b=mask(original),mask(out)
  edge=max(abs(ob[k]-nb[k]) for k in range(4));iou=float(np.logical_and(a,b).sum()/np.logical_or(a,b).sum())
  item={'group':g,'frame':i,'old_alpha128_bounds':list(ob),'new_alpha128_bounds':list(nb),'max_bound_delta':edge,'sole_delta':nb[3]-ob[3],'whole_frame_registration':[rx,ry],'iou':iou,'source':rel(dest),'sha256':sha(dest)}
  metrics.append(item);sources[(g,i)]=dest
 cameras.append({'group':g,'atlas':rel(src),'atlas_sha256':sha(src),'version':v,'scale':scale,'offset':offset,'old_cell':row['cell'],'new_cell':[new.width/row['layout'][0],new.height/row['layout'][1]],'rule':'Original measured camera, exact whole-atlas normalization, original placement-v4 translations; no per-frame fitting.'})
write(R/'geometry-v3.json',{'frames':metrics,'cameras':cameras,'summary':[{'group':r['group'],'max_delta':max(m['max_bound_delta'] for m in metrics if m['group']==r['group']),'max_sole_delta':max(abs(m['sole_delta']) for m in metrics if m['group']==r['group']),'min_iou':min(m['iou'] for m in metrics if m['group']==r['group'])} for r in mapping],'active_assets_modified':False,'visual_approval_granted':False})
for start in range(0,len(mapping),5):
 section=mapping[start:start+5];board=Image.new('RGB',(1320,len(section)*380),'#455146');draw=ImageDraw.Draw(board)
 for rowidx,row in enumerate(section):
  g=row['group']
  for i in range(len(row['frames'])):
   for newflag,path in [(False,P/converted[g][i]['output']),(True,sources[(g,i)])]:
    im=Image.open(path).convert('RGBA');comp=Image.new('RGBA',im.size,'#455146' if not newflag else '#ded6c2');comp.alpha_composite(im)
    xx=i*220;yy=rowidx*380+(190 if newflag else 0);board.paste(comp.convert('RGB').crop((110,90,330,275)),(xx,yy+5));draw.text((xx+3,yy+2),f'g{g}f{i} '+('material' if newflag else 'selected'),fill='white' if not newflag else 'black')
 board.save(R/f'actions-native-part{start//5+1}-v3.png')
print(json.dumps(read(R/'geometry-v3.json')['summary']))
