"""Technical immutable native-image contact atlases for genuine crest-only edits."""
from pathlib import Path
import hashlib,io,json,math
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[3];S=Path(__file__).resolve().parent
UNITS=('chemJack','reinforcedChemJack','chemtechConstruct','reinforcedConstruct','chemBaronEnforcer','cyberneticGuard','chemBaronAgent','masterAlchemist','sumpReclaimer','hydraulicReclaimer')
ROLES=('battle','map','large','small','attackLeft','attackRight')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(x):return(json.dumps(x,indent=2,sort_keys=True)+'\n').encode()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Frozen contact input differs: '+str(p))
 p.write_bytes(b)
def png(p,im):
 b=io.BytesIO();im.save(b,format='PNG',compress_level=9,optimize=False);put(p,b.getvalue())
def rel(p):return p.relative_to(P).as_posix()

def prepare(unit):
 frozen=S/unit/'preparation-v2.json'
 if frozen.is_file():
  record=json.loads(frozen.read_text());sheet=Image.new('RGBA',tuple(record['canvas']));draw=ImageDraw.Draw(sheet);cw,ch=record['cell_size']
  for entry in record['entries']:
   slot=entry['slots'][0];source=P/slot['source']
   if sha(source)!=slot['source_sha256']:raise ValueError('Frozen painted native input changed: '+str(source))
   im=Image.open(source).convert('RGBA').crop(entry['crop']).resize(tuple(entry['atlas_size']),Image.Resampling.NEAREST);sheet.alpha_composite(im,tuple(entry['atlas_position']));i=entry['index'];title=slot['role']+(f' g{slot["group"]:02d}/f{slot["frame"]:02d}' if slot['group'] is not None else '')
   draw.text(((i%record['columns'])*cw+4,(i//record['columns'])*ch+3),title,fill=(150,160,150,255))
  png(S/unit/'contact-input-v1.png',sheet)
  return {'unit':unit,'frozen_contexts':len(record['entries']),'contact_replay_exact':True}
 entries={};recipepins=[];slots=[]
 for role in ROLES:
  rp=P/f'assets/recipes/creatures/{unit}-{role}.json';recipe=json.loads(rp.read_text());recipepins.append({'path':rel(rp),'sha256':sha(rp)})
  if role=='battle':
   g=recipe['generation']
   if g.get('image_generation_used') is not True or 'OpenAI' not in g.get('provider',''):raise ValueError('Selected source is not declared genuine painted2D: '+unit)
  contexts=[(g['group'],i,P/f['source']) for g in recipe['groups'] for i,f in enumerate(g['frames'])] if role in ('battle','map') else [(None,None,P/'assets/generated'/recipe['output_path'])]
  for group,frame,path in contexts:
   im=Image.open(path).convert('RGBA');pixelsha=hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest();slot={'role':role,'group':group,'frame':frame,'source':rel(path),'source_sha256':sha(path),'pixel_sha256':pixelsha}
   if pixelsha not in entries:
    bounds=im.getchannel('A').point(lambda v:255 if v>=8 else 0).getbbox()
    if not bounds:raise ValueError('Empty selected unit image: '+str(path))
    x0,y0,x1,y1=bounds;bounds=[max(0,x0-4),max(0,y0-4),min(im.width,x1+4),min(im.height,y1+4)]
    entries[pixelsha]={'image':im,'crop':bounds,'slots':[],'original_canvas':list(im.size),'pixel_sha256':pixelsha}
   entries[pixelsha]['slots'].append(slot);slots.append(slot)
 entries=list(entries.values());cols=8;cw,ch=224,160;scale=min([1.6]+[min((cw-20)/(x['crop'][2]-x['crop'][0]),(ch-28)/(x['crop'][3]-x['crop'][1])) for x in entries]);rows=math.ceil(len(entries)/cols)
 sheet=Image.new('RGBA',(cols*cw,rows*ch));draw=ImageDraw.Draw(sheet)
 for i,entry in enumerate(entries):
  im=entry.pop('image').crop(entry['crop']);size=[max(1,round(im.width*scale)),max(1,round(im.height*scale))];pos=[(i%cols)*cw+(cw-size[0])//2,(i//cols)*ch+20+(ch-28-size[1])//2]
  sheet.alpha_composite(im.resize(size,Image.Resampling.NEAREST),tuple(pos));label=entry['slots'][0];title=label['role']+(f' g{label["group"]:02d}/f{label["frame"]:02d}' if label['group'] is not None else '')
  draw.text(((i%cols)*cw+4,(i//cols)*ch+3),title,fill=(150,160,150,255));entry.update(index=i,atlas_position=pos,atlas_size=size,uniform_display_scale=scale)
 folder=S/unit;png(folder/'contact-input-v1.png',sheet)
 record={'status':'authored configuration','unit':unit,'purpose':'Technical same-pose native contact atlas, not game artwork; original regions remain immutable','canvas':list(sheet.size),'cell_size':[cw,ch],'columns':cols,'rows':rows,'entries':entries,'original_slot_count':len(slots),'distinct_native_contexts':len(entries),'source_recipes':recipepins,'source_rendering':'Actual selected painted2D unit images; no historical3D/rig producer run','selected_or_staged':False};put(folder/'preparation-v1.json',enc(record));return {'unit':unit,'contexts':len(entries),'slots':len(slots),'canvas':list(sheet.size),'display_scale':scale}

if __name__=='__main__':
 print(json.dumps([prepare(u) for u in UNITS],indent=2))
