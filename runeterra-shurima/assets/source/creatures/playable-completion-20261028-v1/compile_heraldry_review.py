"""Actual strict consumer replay and native-size action views of painted patches."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import json,hashlib,sys,copy
import assemble_packets as common
S=common.SOURCE;P=common.PROJECT;R=common.REPORT/'heraldry-v1'
def main():
 sys.path.insert(0,str(P.parent/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima');recipes=sorted((S/'recipe-payload-heraldry-v1').rglob('*.json'));runs=[];receipts=[];boards=[]
 for run in (1,2):
  pins={}
  for path in recipes:
   outputs,receipt=compiler.plan(P,path)
   if run==1:receipts.append(receipt)
   for name,data in outputs.items():
    pins[name]=hashlib.sha256(data).hexdigest()
    if run==1:
     target=R/'compiled'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  runs.append(pins)
 assert runs[0]==runs[1]
 for path in [p for p in recipes if p.name=='battle.json']:
  battle=json.loads(path.read_text());unit=path.parent.name;groups={r['group']:r['frames'] for r in battle['groups']};count=sum(len(v) for v in groups.values());rows=(count+5)//6
  for facing in ('right','native-left-samehex'):
   board=Image.new('RGBA',(1590,260*rows),(35,35,35,255));draw=ImageDraw.Draw(board);i=0
   for g,seq in groups.items():
    frames=[]
    for j,frame in enumerate(seq):
     im=Image.open(P/frame['source']).convert('RGBA')
     if facing!='right':
      shifted=Image.new('RGBA',im.size);shifted.paste(ImageOps.mirror(im),(-58 if battle['pivot']['x']==196 else -14,0));im=shifted
     crop=im.crop((90,55,355,295));bg=common.checkbg(crop.size);bg.alpha_composite(crop);board.paste(bg,((i%6)*265,(i//6)*260+18));draw.text(((i%6)*265+2,(i//6)*260+2),f'g{g:02} f{j:03}',fill='white');i+=1
     anim=common.checkbg((265,240));anim.alpha_composite(crop);frames.append(anim.convert('RGB'))
    if len(frames)>1:
     dest=R/unit/f'g{g:02}-{facing}.gif';dest.parent.mkdir(parents=True,exist_ok=True);frames[0].save(dest,save_all=True,append_images=frames[1:],duration=170,loop=0,disposal=2)
   common.png(R/unit/(facing+'-all-actions-native1x.png'),board)
  # Dedicated exact both-facing locomotion and terminal corpse review.
  panel=Image.new('RGBA',(1590,550),(35,35,35,255));draw=ImageDraw.Draw(panel)
  for j,frame in enumerate(groups[0]):
   im=Image.open(P/frame['source']).convert('RGBA');crop=im.crop((90,55,355,295));bg=common.checkbg(crop.size);bg.alpha_composite(crop);panel.paste(bg,(j*265,20));draw.text((j*265,0),unit+' walk '+str(j),fill='white')
  for j,(role,g,index) in enumerate([('holding',2,0),('terminal corpse',22,0),('turnL last',7,-1),('turnR first',8,0)]):
   im=Image.open(P/groups[g][index]['source']).convert('RGBA');crop=im.crop((90,55,355,295));bg=common.checkbg(crop.size);bg.alpha_composite(crop);panel.paste(bg,(j*265,300));draw.text((j*265,280),role,fill='white')
  common.png(R/unit/'walk-hold-death-turn-native1x.png',panel)
  # Actual companion pictures, exactly the recipe frame(s), no zoomed substitute.
  companion=Image.new('RGBA',(600,160),(35,35,35,255));d=ImageDraw.Draw(companion)
  for j,role in enumerate(('map','attackLeft','attackRight','large','small')):
   rr=json.loads((path.parent/(role+'.json')).read_text());source=rr['groups'][0]['frames'][0]['source'] if role=='map' else rr['source'];im=Image.open(P/source).convert('RGBA');bg=common.checkbg(im.size);bg.alpha_composite(im);companion.paste(bg,(j*120,22));d.text((j*120+2,2),role,fill='white')
  common.png(R/unit/'companions-native1x.png',companion);boards.append(unit)
 common.put(R/'actual-compiler-proof-v3.json',{'status':'authored configuration','actual_shared_compiler_passes':2,'recipes':len(recipes),'physical_outputs':len(runs[0]),'two_passes_byte_exact':True,'outputs':runs[0],'receipts':receipts,'producer':common.descriptor(Path(__file__)),'source_review_units':boards,'native_execution':False,'visual_approval_granted':False})
 html=['<!doctype html><html><meta charset="utf-8"><title>Shurima painted2D creature review</title><style>body{background:#222;color:#eee;font:16px sans-serif}img{image-rendering:pixelated;max-width:none}figure{overflow:auto}nav a{color:#debc71}section{border-top:1px solid #555;margin-top:25px}</style><h1>Shurima: fourteen painted2D creatures</h1><p>Authored configuration: actual compiled source action/crest review. These are native-size assembled frames, not game screenshots or native acceptance.</p><nav>']
 html += ['<a href="#'+u+'">'+u+'</a> · ' for u in boards];html += ['</nav>']
 for u in boards:
  html += ['<section id="'+u+'"><h2>'+u+'</h2><figure><img src="'+u+'/walk-hold-death-turn-native1x.png"></figure><figure><img src="'+u+'/companions-native1x.png"></figure><p>Full actions: <a href="'+u+'/right-all-actions-native1x.png">right</a> · <a href="'+u+'/native-left-samehex-all-actions-native1x.png">native left placement</a></p>']
  for g in (0,3,5,7,8,11,12,13,14,15,16,20,21):
   q=R/u/f'g{g:02}-right.gif'
   if q.is_file():html+=['<figure><figcaption>group '+str(g)+' — native-size source playback</figcaption><img src="'+u+'/'+q.name+'"></figure>']
  html+=['</section>']
 (R/'index.html').write_text('\n'.join(html),encoding='utf-8')
 print(json.dumps({'recipes':len(recipes),'physical_outputs':len(runs[0]),'two_shared_compiler_passes_byte_exact':True,'review':str(R/'index.html')}))
if __name__=='__main__':main()
