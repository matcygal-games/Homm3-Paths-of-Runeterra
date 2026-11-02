"""Technical size/camera correction using unchanged painted pixels; candidate only."""
from pathlib import Path
from collections import deque
import argparse, hashlib, io, json
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageDraw
HERE=Path(__file__).resolve().parent; P=HERE.parents[3]; W=P.parent
UNITS=('resistanceBlade','resistanceVeteran'); ROOT=(197,266); SCALE=.80
PREVIEW_GROUPS={0,1,2,3,4,12}; PREVIEW_SCALE=.54; PREVIEW_ROOT=(50,116)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def data(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def png(im):
 s=io.BytesIO();im.save(s,format='PNG');return s.getvalue()
def components(core):
 seen=np.zeros(core.shape,bool);h,w=core.shape;result=[]
 for y,x in zip(*np.nonzero(core)):
  if seen[y,x]:continue
  todo=deque([(int(y),int(x))]);seen[y,x]=True;piece=[]
  while todo:
   yy,xx=todo.popleft();piece.append((yy,xx))
   for ny in range(max(0,yy-1),min(h,yy+2)):
    for nx in range(max(0,xx-1),min(w,xx+2)):
     if core[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;todo.append((ny,nx))
  result.append(piece)
 return result

def recover(master,entry):
 box=entry['source_crop']; pad=96
 expanded=(max(0,box[0]-pad),max(0,box[1]-pad),min(master.width,box[2]+pad),min(master.height,box[3]+pad))
 tile=master.crop(expanded).convert('RGBA');a=np.asarray(tile.getchannel('A'));parts=components(a>=180)
 x0,y0=box[0]-expanded[0],box[1]-expanded[1];x1,y1=box[2]-expanded[0],box[3]-expanded[1]
 # Pick the connected painted actor by its original cell occupancy. Recovery
 # is limited to that same connected subject; adjacent actors remain excluded.
 primary=max(parts,key=lambda c:sum(y0<=y<y1 and x0<=x<x1 for y,x in c))
 mask=np.zeros(a.shape,np.uint8)
 for y,x in primary:mask[y,x]=255
 keep=Image.fromarray(mask).filter(ImageFilter.MaxFilter(5))
 rgba=np.asarray(tile).copy();rgba[:,:,3]=np.where(np.asarray(keep)>0,rgba[:,:,3],0)
 isolated=Image.fromarray(rgba)
 outside=sum(not(y0<=y<y1 and x0<=x<x1) for y,x in primary)
 # A connected subject that still touches the expanded envelope would be
 # incomplete or contaminated, so it is an explicit failure for manual review.
 border=any((x==0 and expanded[0]>0)or(y==0 and expanded[1]>0)or(x==tile.width-1 and expanded[2]<master.width)or(y==tile.height-1 and expanded[3]<master.height) for y,x in primary)
 if border:raise ValueError('Connected actor crosses recovery envelope: '+str((entry['unit'],entry['group'],entry['frame'])))
 scale=entry['scale']; resized=isolated.resize((round(tile.width*scale),round(tile.height*scale)),Image.Resampling.LANCZOS)
 origin=(round(ROOT[0]-(entry['source_root'][0]-expanded[0])*scale),round(ROOT[1]-(entry['source_root'][1]-expanded[1])*scale))
 result=Image.new('RGBA',(450,400));result.alpha_composite(resized,origin)
 floor=result.getchannel('A').point(lambda v:255 if v>=180 else 0).getbbox()[3]
 registered=Image.new('RGBA',(450,400));registered.alpha_composite(result,(0,ROOT[1]-floor))
 return registered,{'source_native_floor_before_registration':floor,'ground_translation_pixels':ROOT[1]-floor,'expanded_crop':list(expanded),'connected_recovered_opaque_pixels':outside,'source_sha256':sha(P/entry['painted_master'])}

def affine(image,scale,root=ROOT,canvas=(450,400),anchor=ROOT):
 return image.transform(canvas,Image.Transform.AFFINE,(1/scale,0,root[0]-anchor[0]/scale,0,1/scale,root[1]-anchor[1]/scale),Image.Resampling.BICUBIC)
def run(out):
 if out.exists():raise ValueError('new output required')
 out.mkdir(parents=True)
 lineage_path=P/'assets/source/creatures/playable-completion-20261028-v2-portable/frame-lineage.json'
 lineage=json.loads(lineage_path.read_text())['frames']
 entries={(e['unit'],e['group'],e['frame']):e for e in lineage if e.get('unit')in UNITS and 'group'in e}
 receipt={'status':'authored configuration','battle_scale':SCALE,'battle_root':list(ROOT),'preview_scale':PREVIEW_SCALE,'preview_root':list(PREVIEW_ROOT),'units':{},'source_pins':{},'producer_sha256':sha(__file__),'candidate_only':True}
 receipt['source_pins'][str(lineage_path.relative_to(P))]=sha(lineage_path)
 boards=[]
 for unit in UNITS:
  recipe=HERE/'before-recipes'/f'{unit}-battle.json';r=json.loads(recipe.read_text());receipt['source_pins'][str(recipe.relative_to(P))]=sha(recipe)
  frames={};old={};records=[]
  for group in r['groups']:
   g=group['group']
   for i,f in enumerate(group['frames']):
    p=P/f['source'];image=Image.open(p).convert('RGBA');old[g,i]=image;receipt['source_pins'][f['source']]=sha(p)
    e=entries[unit,g,i];recovered=None
    if sha(p)!=f['source_sha256']or sha(p)!=e['native']['source_sha256']:raise ValueError('Selected frame changed since source lineage')
    if 'source_crop'in e:
     masterp=P/e['painted_master'];receipt['source_pins'][e['painted_master']]=sha(masterp)
     if sha(masterp)!=e['painted_master_sha256']:raise ValueError('Painted master changed since lineage')
     image,recovered=recover(Image.open(masterp).convert('RGBA'),e)
    frames[g,i]=affine(image,SCALE)
    records.append({'group':g,'frame':i,'source':f['source'],'recovery':recovered})
  # Rebuild native-turn join after scale: keep the exact engine's 58px
  # one-hex world shift instead of accidentally scaling that shift too.
  frames[7,0]=frames[2,0].copy();frames[8,max(i for g,i in frames if g==8)]=frames[2,0].copy()
  end=max(i for g,i in frames if g==7);v=Image.new('RGBA',(450,400));v.alpha_composite(ImageOps.mirror(frames[7,end]),(-58,0));frames[8,0]=v
  details=[];sheet=Image.new('RGB',(900,230*len(r['groups'])),(65,60,51));d=ImageDraw.Draw(sheet)
  for row,group in enumerate(r['groups']):
   g=group['group'];d.text((3,row*230+2),unit+' group '+str(g)+' before (top), corrected (bottom)',fill='white')
   for i in range(len(group['frames'])):
    image=frames[g,i];dest=out/unit/'battle'/f'g{g:02d}-f{i:03d}.png';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(png(image))
    b=image.getchannel('A').point(lambda x:255 if x>=8 else 0).getbbox()
    info={'group':g,'frame':i,'battle_sha256':sha(dest),'battle_alpha8_bounds':list(b)}
    if g in PREVIEW_GROUPS:
     # UI uses the complete same-size repaired actor with one fixed camera;
     # never fit individual poses. Both native120/130px centered crops fit.
     preview=affine(image,PREVIEW_SCALE/SCALE,canvas=(100,130),anchor=PREVIEW_ROOT)
     pd=out/unit/'preview'/f'g{g:02d}-f{i:03d}.png';pd.parent.mkdir(parents=True,exist_ok=True);pd.write_bytes(png(preview));pb=preview.getchannel('A').point(lambda x:255 if x>=8 else 0).getbbox();info['preview_alpha8_bounds']=list(pb);info['preview_sha256']=sha(pd)
    details.append(info)
    for top,im in [(row*230+22,old[g,i]),(row*230+122,image)]:
     crop=im.crop((97,126,297,286));crop.thumbnail((145,100));tile=Image.new('RGBA',(145,100),(65,60,51,255));tile.alpha_composite(crop);sheet.paste(tile.convert('RGB'),(i*150,top))
  sheet.save(out/(unit+'-all-actions.png'));receipt['units'][unit]={'frames':details,'records':records}
 for name,pin in receipt['source_pins'].items():
  if sha(P/name)!=pin:raise ValueError('Input changed during production: '+name)
 (out/'receipt.json').write_bytes(data(receipt))
 (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Ionia T6 size correction candidates</title><style>body{background:#302b25;color:white;font:16px sans-serif}img{image-rendering:pixelated;max-width:none}</style><h1>Ionia T6 size and clipping candidates</h1><p>Authored configuration; candidate only. Before and corrected frames at native scale. Fixed20%battle size reduction; recovered original painted sword overflow; independent safe preview camera.</p>'+''.join('<h2>'+u+'</h2><img src="'+u+'-all-actions.png">'for u in UNITS),encoding='utf-8')
 return receipt
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);v=a.parse_args();print(json.dumps({'units':list(run(v.output)['units'])}))
