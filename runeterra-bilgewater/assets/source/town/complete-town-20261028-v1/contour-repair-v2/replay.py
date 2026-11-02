"""Source-pinned technical matte proposals, never canonical/frame writes.

Skyline profiles and thin architectural parts are hand-inspected annotations.
Only the two demonstrated missing mast/chimney regions add alpha, sampling the
unchanged mapped painted source.  Genuine rear-wall reveals remain deferred.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageChops

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent
PROJECT=HERE.parents[4]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/contour-repair-v2'
INDEX_SHA='c5eb6af7e638b86a879b51fda03236f0c86eb7f6763724bd4ec6b329139ac0e3'
EXCLUDED={'dwellingLvl5','dwellingUpLvl5','shipyard','ship','grail'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path):return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}
def draw_lines(draw,lines):
 for line in lines:draw.line([tuple(xy)for xy in line[:-1]],fill=255,width=line[-1])
def checker(size):
 out=Image.new('RGBA',size,(190,190,190,255));d=ImageDraw.Draw(out)
 for y in range(0,size[1],8):
  for x in range(0,size[0],8):
   if (x//8+y//8)%2:d.rectangle((x,y,x+7,y+7),fill=(140,140,140,255))
 return out

def main():
 indexpath=SOURCE/'derived-v1/states.json';assert sha(indexpath)==INDEX_SHA
 index=json.loads(indexpath.read_text(encoding='utf-8'))
 annotations=json.loads((HERE/'annotations-v1.json').read_text(encoding='utf-8'))
 (HERE/'masks').mkdir(exist_ok=True,parents=True);REPORT.mkdir(exist_ok=True,parents=True)
 records=[];cards=[]
 for state,row in index['states'].items():
  if state in EXCLUDED:continue
  framepath=PROJECT/row['frame'];sourcepath=SOURCE/row['source']
  assert sha(framepath)==row['frame_sha256'],state+' frame drift'
  assert sha(sourcepath)==row['source_sha256'],state+' painted source drift'
  before=Image.open(framepath).convert('RGBA');alpha=before.getchannel('A')
  raw=Image.open(sourcepath).convert('RGBA');mapped=Image.new('RGBA',(800,374));mapped.paste(raw,tuple(row.get('delta',[0,0])))
  if state in annotations['deferred_until_painted_reveal']:
   records.append({'state':state,'site':row['site'],'before_frame':ref(framepath),'source_painting':ref(sourcepath),
    'delta':row.get('delta',[0,0]),'status':'deferred pending genuine art-owner source reveal',
    'reason':annotations['deferred_until_painted_reveal'][state]})
   continue
  proposal=alpha.copy()
  profile=annotations['roof_profiles'].get(state)
  if profile:
   keep=Image.new('L',(800,374));d=ImageDraw.Draw(keep)
   d.polygon([tuple(xy)for xy in profile]+[(799,373),(0,373)],fill=255)
   for polygon in annotations['existing_architecture_keep_polygons'].get(state,[]):d.polygon([tuple(xy)for xy in polygon],fill=255)
   draw_lines(d,annotations['existing_architecture_keep_lines'].get(state,[]))
   proposal=ImageChops.darker(alpha,keep)
  additions=annotations['verified_missing_architecture_additions'].get(state)
  if state in ('castle','cityHall'):
   # The old broad skyline mask also clipped the real thin flag poles. Restore
   # only these manually traced architectural parts from the mapped source.
   additions={'polygons':annotations['existing_architecture_keep_polygons'][state],
    'lines':annotations['existing_architecture_keep_lines'].get(state,[]),
    'reason':'Real attached mast/flag/rigging contours in the unchanged mapped source; old envelope clipped these while retaining neighboring sky.'}
  if additions:
   d=ImageDraw.Draw(proposal)
   for polygon in additions['polygons']:d.polygon([tuple(xy)for xy in polygon],fill=255)
   draw_lines(d,additions['lines'])
  if state=='castle':
   for xy in [(119,18),(94,49)]:assert proposal.getpixel(xy)==0,(state,xy)
  if state=='capitol':
   for xy in [(370,14),(432,48)]:assert proposal.getpixel(xy)==0,(state,xy)
  if state=='townHall':assert alpha.getpixel((388,51))==0 and proposal.getpixel((388,51))==255
  if state=='blacksmith':
   for xy in [(230,210),(230,224)]:assert alpha.getpixel(xy)==0 and proposal.getpixel(xy)==255
   assert proposal.getpixel((205,200))==0
  out=HERE/'masks'/(state+'.png');proposal.save(out)
  removed=sum(p>0 for p in ImageChops.subtract(alpha,proposal).tobytes())
  added=sum(p>0 for p in ImageChops.subtract(proposal,alpha).tobytes())
  if not profile:assert proposal.tobytes()==alpha.tobytes(),state+' unintended change'
  bounds=ImageChops.lighter(alpha,proposal).getbbox();box=(max(0,bounds[0]-4),max(0,bounds[1]-4),min(800,bounds[2]+4),min(374,bounds[3]+4))
  size=(box[2]-box[0],box[3]-box[1]);canvas=Image.new('RGB',(size[0]*3,size[1]+20),(25,28,32));d=ImageDraw.Draw(canvas)
  after=mapped.copy();after.putalpha(proposal)
  for col,(title,im) in enumerate([('MAPPED SOURCE',mapped),('BEFORE',before),('PROPOSAL',after)]):
   tile=checker(size);tile.alpha_composite(im.crop(box));canvas.paste(tile.convert('RGB'),(col*size[0],20));d.text((col*size[0]+2,3),title,fill='white')
  canvas.save(REPORT/(state+'-native.png'))
  if profile:canvas.resize((canvas.width*4,canvas.height*4),Image.Resampling.NEAREST).save(REPORT/(state+'-4x.png'))
  record={'state':state,'site':row['site'],'before_frame':ref(framepath),'source_painting':ref(sourcepath),
   'delta':row.get('delta',[0,0]),'proposed_frame_coordinate_alpha':ref(out),
   'before_alpha_bytes_sha256':hashlib.sha256(alpha.tobytes()).hexdigest(),
   'after_alpha_bytes_sha256':hashlib.sha256(proposal.tobytes()).hexdigest(),
   'removed_alpha_pixels':removed,'added_actual_source_architecture_pixels':added,
   'unchanged_alpha':proposal.tobytes()==alpha.tobytes(),
   'painted_source_RGB_edited':False,'root_or_pose_transform_changed':False}
  if additions:record['addition_source_proof']=additions['reason']
  records.append(record)
  if profile:cards.append('<section><h2>'+state+'</h2><p>'+str(removed)+' alpha pixels removed; '+str(added)+' actual-source architectural pixels restored.</p><a href="'+state+'-native.png"><img src="'+state+'-native.png"></a></section>')
 assert len(records)==30
 manifest={'status':'authored configuration','scope':'Partial technical matte proposals only. Four Roost/coast states belong to the physical owner; Grail is excluded. Two genuine reveal states are explicitly deferred.',
  'input_index':ref(indexpath),'annotations':ref(HERE/'annotations-v1.json'),'replay':ref(Path(__file__)),
  'states':records,'changed_states':[r['state']for r in records if r.get('unchanged_alpha')is False],
  'unchanged_states':[r['state']for r in records if r.get('unchanged_alpha')is True],
  'deferred_states':[r['state']for r in records if 'proposed_frame_coordinate_alpha'not in r],
  'frozen_frames_edited':False,'canonical_or_stage_writes':False,'native_execution':False,'release_accepted':False}
 (HERE/'proposal-manifest-v1.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (REPORT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Bilgewater alpha proposals</title><style>body{background:#171b20;color:#eee;font:15px Arial;max-width:1250px;margin:25px auto}img{max-width:100%}section{margin:30px 0}</style><h1>Bilgewater alpha-only proposals</h1><p>Source-pinned technical candidates, not final source or native acceptance. The new mast/chimney pixels come from the unchanged genuine source buffers, never code-painted architecture. Citadel and Buhru underlap remain deferred.</p>'+''.join(cards),encoding='utf-8')
 print(json.dumps({'manifest':str(HERE/'proposal-manifest-v1.json'),'sha256':sha(HERE/'proposal-manifest-v1.json'),'changed':manifest['changed_states'],'unchanged':len(manifest['unchanged_states']),'deferred':manifest['deferred_states']},indent=2))

if __name__=='__main__':main()
