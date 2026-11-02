"""Explicit negative-air corrections to the held Ionia matte proposal.

Technical alpha edits only.  The previous released proposal is an immutable
input; all new artifacts are written below this separately versioned folder.
"""
from pathlib import Path
import hashlib,json
from collections import deque
from PIL import Image,ImageDraw,ImageChops

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PROJECT=BASE.parents[4]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/contour-repair-v2-revision-v2'
BEFORE='0796cdb995dcce62515666f4040aba8ddad25bdd2e8be00eecbd29c7084e3998'
HOLES={
 'cityHall': [[(434,66),(437,64),(440,62),(442,63),(444,66),(446,68),(433,68)]],
 'citadel': [[(513,61),(518,62),(522,63),(524,63),(524,69),(521,72),(518,73),(516,69)],
             [(553,61),(555,60),(558,59),(559,61),(559,65),(557,68),(554,68)]],
 'castle': [[(533,46),(537,48),(538,50),(538,54),(537,57),(537,63),(533,65)]]
}
SAMPLES={'cityHall':[(438,65)],'citadel':[(519,65),(557,63)],'castle':[(534,49)]}
AIR_COMPONENTS={
 'cityHall': [((431,59,448,70),(438,65))],
 'citadel': [((512,59,526,76),(519,65)),((551,58,563,73),(557,63))],
 'castle': [((531,44,542,72),(534,49))]
}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path):return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}
def main():
 before=BASE/'proposal-manifest-v1.json';assert sha(before)==BEFORE
 manifest=json.loads(before.read_text(encoding='utf-8'))
 (HERE/'masks').mkdir(exist_ok=True,parents=True);REPORT.mkdir(exist_ok=True,parents=True)
 records=[]
 for row in manifest['states']:
  state=row['state'];oldpath=PROJECT/row['proposed_alpha']['path']
  assert sha(oldpath)==row['proposed_alpha']['sha256']
  old=Image.open(oldpath).convert('L');new=old.copy()
  for polygon in HOLES.get(state,[]):ImageDraw.Draw(new).polygon(polygon,fill=0)
  # These are the independently identified external sky pockets, not a global
  # color key.  A bounded seed-connected sky component only refines the hand
  # contour next to dark wooden eaves.  Teal roofs/gold/white stone form stops.
  raw_source=Image.open(PROJECT/row['source_painting']['path']).convert('RGB')
  for bounds,seed in AIR_COMPONENTS.get(state,[]):
   q=deque([seed]);seen=set()
   while q:
    x,y=q.popleft()
    if (x,y) in seen or not(bounds[0]<=x<bounds[2] and bounds[1]<=y<bounds[3]):continue
    seen.add((x,y));r,g,b=raw_source.getpixel((x,y))
    if not(b>70 and b-r>18 and b-g>12):continue
    new.putpixel((x,y),0)
    q.extend([(x-1,y),(x+1,y),(x,y-1),(x,y+1),
              (x-1,y-1),(x+1,y-1),(x-1,y+1),(x+1,y+1)])
  for xy in SAMPLES.get(state,[]):assert old.getpixel(xy)==255 and new.getpixel(xy)==0,(state,xy)
  assert not ImageChops.subtract(new,old).getbbox()
  out=HERE/'masks'/(state+'.png');new.save(out)
  nr=dict(row);nr['proposed_alpha']=ref(out)
  nr['after_alpha_bytes_sha256']=hashlib.sha256(new.tobytes()).hexdigest()
  n=sum(p>0 for p in ImageChops.difference(old,new).tobytes())
  nr['revision_v2_removed_pixels']=n;nr['removed_alpha_pixels']+=n
  records.append(nr)
  if state in HOLES:
   raw=Image.open(PROJECT/row['before_frame']['path']).convert('RGBA')
   bounds=raw.getchannel('A').getbbox();box=(bounds[0]-3,max(0,bounds[1]-3),bounds[2]+3,bounds[3]+3)
   canvas=Image.new('RGB',((box[2]-box[0])*2,box[3]-box[1]+20),(25,27,30));d=ImageDraw.Draw(canvas)
   for col,(name,mask) in enumerate([('HELD PROPOSAL',old),('REVISION V2',new)]):
    frame=raw.copy();frame.putalpha(mask);crop=frame.crop(box);tile=Image.new('RGBA',crop.size,(190,190,190,255));td=ImageDraw.Draw(tile)
    for y in range(0,crop.height,8):
     for x in range(0,crop.width,8):
      if (x//8+y//8)%2:td.rectangle((x,y,x+7,y+7),fill=(140,140,140,255))
    tile.alpha_composite(crop);canvas.paste(tile.convert('RGB'),(col*crop.width,20));d.text((col*crop.width+2,3),name,fill='white')
   canvas.save(REPORT/(state+'-native.png'))
   canvas.resize((canvas.width*4,canvas.height*4),Image.Resampling.NEAREST).save(REPORT/(state+'-4x.png'))
 manifest.update({'states':records,'prior_proposal':ref(before),'revision':'v2 explicit under-eave negative-air notches',
  'revision_annotations':HOLES,'bounded_negative_air_components':AIR_COMPONENTS,'revision_replay':ref(Path(__file__)),
  'genuine_library_underlap_still_required':'Mage Guild2/3 lower-left plinth behind Kinkou roof requires art-owner source proof/recovery; this alpha-only proposal does not invent it.'})
 (HERE/'proposal-manifest-v2.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'manifest':str(HERE/'proposal-manifest-v2.json'),'sha256':sha(HERE/'proposal-manifest-v2.json'),'revision_removed_pixels':sum(r['revision_v2_removed_pixels']for r in records),'held_proposal_unchanged':sha(before)==BEFORE}))
if __name__=='__main__':main()
