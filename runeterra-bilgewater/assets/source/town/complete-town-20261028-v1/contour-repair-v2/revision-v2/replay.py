"""Complete the two source-reveal-dependent ordinary matte proposals.

Reuses the held five-state/23-unchanged proposal without rewriting it.  New RGB
comes exclusively from the art owner's pinned genuine reveal buffers.  This
script writes alpha proposals and technical presentations, never game frames.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageChops

HERE=Path(__file__).resolve().parent;BASE=HERE.parent;SOURCE=BASE.parent
PROJECT=BASE.parents[4]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/contour-repair-v2-revision-v2'
PRIOR='d23f0e79c51c86939c3f0197369d81ee2206c8050b37d83a9d2b8da7871d0f41'
REVEAL_INDEX='16975d5b6d9764648cd0b14366e41a87da8e926f9c6329d7e84b93786e0fa80c'
EXPECTED={'dwellingUpLvl4':'7d922f2cc607c30f3fa178c213dec98c181691b942b66c62d4ebeb3975ab0dd0',
          'citadel':'00e7bc0d967440e8016eeae1cd1134915bdc8b6d165677eadc585ace93012c9c'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path):return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}
def main():
 priorpath=BASE/'proposal-manifest-v1.json';assert sha(priorpath)==PRIOR
 prior=json.loads(priorpath.read_text(encoding='utf-8'))
 indexpath=SOURCE/'derived-v1/states.json';assert sha(indexpath)==prior['input_index']['sha256']
 index=json.loads(indexpath.read_text(encoding='utf-8'))
 revealpath=SOURCE/'underlap-buffers-v2/source-index.json';assert sha(revealpath)==REVEAL_INDEX
 reveals=json.loads(revealpath.read_text(encoding='utf-8'))['records']
 annotations=json.loads((HERE/'annotations-v2.json').read_text(encoding='utf-8'))
 (HERE/'masks').mkdir(exist_ok=True,parents=True);REPORT.mkdir(exist_ok=True,parents=True)
 records=[];cards=[]
 for row in prior['states']:
  state=row['state']
  if state not in EXPECTED:
   path=PROJECT/row['proposed_frame_coordinate_alpha']['path'];assert sha(path)==row['proposed_frame_coordinate_alpha']['sha256']
   records.append(row);continue
  original=index['states'][state];framepath=PROJECT/original['frame']
  assert sha(framepath)==original['frame_sha256']
  old=Image.open(framepath).convert('RGBA');alpha=old.getchannel('A')
  reveal=reveals[state];sourcepath=PROJECT/reveal['source'];assert sha(sourcepath)==EXPECTED[state]==reveal['source_sha256']
  assert reveal['delta']==original['delta']
  raw=Image.open(sourcepath).convert('RGBA');mapped=Image.new('RGBA',(800,374));mapped.paste(raw,tuple(reveal['delta']))
  if state=='citadel':
   keep=Image.new('L',(800,374));draw=ImageDraw.Draw(keep)
   draw.polygon([tuple(xy)for xy in annotations['citadel_roof_profile']]+[(799,373),(0,373)],fill=255)
   proposal=ImageChops.darker(alpha,keep);draw=ImageDraw.Draw(proposal)
   for polygon in annotations['citadel_architectural_parts']:draw.polygon([tuple(xy)for xy in polygon],fill=255)
   for line in annotations['citadel_rigging_lines']:draw.line([tuple(xy)for xy in line[:-1]],fill=255,width=line[-1])
  else:
   proposal=alpha.copy();cut=Image.new('L',(800,374));ImageDraw.Draw(cut).polygon([tuple(xy)for xy in annotations['buhru_foreign_roof_removal']],fill=255)
   protected_path=PROJECT/reveal['mask'];assert sha(protected_path)==reveal['mask_sha256']
   protected=Image.open(protected_path).convert('L')
   # No painted recovery pixels can be cut to manufacture a clean contour.
   cut=ImageChops.subtract(cut,protected)
   proposal=ImageChops.subtract(proposal,cut)
   assert not ImageChops.multiply(ImageChops.subtract(alpha,proposal),protected).getbbox()
  maskpath=HERE/'masks'/(state+'.png');proposal.save(maskpath)
  removed=sum(p>0 for p in ImageChops.subtract(alpha,proposal).tobytes());added=sum(p>0 for p in ImageChops.subtract(proposal,alpha).tobytes())
  record={'state':state,'site':row['site'],'before_frame':ref(framepath),'source_painting':ref(sourcepath),
   'delta':reveal['delta'],'proposed_frame_coordinate_alpha':ref(maskpath),
   'before_alpha_bytes_sha256':hashlib.sha256(alpha.tobytes()).hexdigest(),'after_alpha_bytes_sha256':hashlib.sha256(proposal.tobytes()).hexdigest(),
   'removed_alpha_pixels':removed,'added_actual_source_architecture_pixels':added,
   'unchanged_alpha':False,'painted_source_RGB_edited_by_this_worker':False,
   'source_RGB_changed_by_art_owner_genuine_reveal':True,
   'genuine_reveal_lineage':reveal,'root_or_pose_transform_changed':False}
  records.append(record)
  bounds=ImageChops.lighter(alpha,proposal).getbbox();box=(max(0,bounds[0]-4),max(0,bounds[1]-4),min(800,bounds[2]+4),min(374,bounds[3]+4));size=(box[2]-box[0],box[3]-box[1])
  after=mapped.copy();after.putalpha(proposal);canvas=Image.new('RGB',(size[0]*3,size[1]+20),(25,28,32));d=ImageDraw.Draw(canvas)
  for col,(title,im) in enumerate([('REVEALED SOURCE',mapped),('HELD ORIGINAL',old),('PROPOSAL',after)]):
   tile=Image.new('RGBA',size,(190,190,190,255));td=ImageDraw.Draw(tile)
   for y in range(0,size[1],8):
    for x in range(0,size[0],8):
     if (x//8+y//8)%2:td.rectangle((x,y,x+7,y+7),fill=(140,140,140,255))
   tile.alpha_composite(im.crop(box));canvas.paste(tile.convert('RGB'),(col*size[0],20));d.text((col*size[0]+2,3),title,fill='white')
  canvas.save(REPORT/(state+'-native.png'));canvas.resize((canvas.width*4,canvas.height*4),Image.Resampling.NEAREST).save(REPORT/(state+'-4x.png'))
  cards.append('<h2>'+state+'</h2><img src="'+state+'-native.png">')
 result=dict(prior);result.update({'scope':'Thirty ordinary-state alpha proposals: seven demonstrated repairs and23 exact unchanged arrays. Roost pair/coast pair/Grail excluded. No source/frame/canonical/stage writes.',
  'prior_partial_proposal':ref(priorpath),'genuine_reveal_index':ref(revealpath),'revision_annotations':ref(HERE/'annotations-v2.json'),'revision_replay':ref(Path(__file__)),
  'states':records,'changed_states':[r['state']for r in records if not r.get('unchanged_alpha')],
  'unchanged_states':[r['state']for r in records if r.get('unchanged_alpha')], 'deferred_states':[]})
 assert len(records)==30 and len(result['changed_states'])==7 and len(result['unchanged_states'])==23
 (HERE/'proposal-manifest-v2.json').write_text(json.dumps(result,indent=2)+'\n')
 (REPORT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Bilgewater revealed matte completion</title><style>body{background:#171b20;color:#eee;font:15px Arial;margin:25px auto;max-width:1200px}img{max-width:100%}</style><h1>Revealed ordinary-state matte completion</h1><p>Actual art-owner painted recovery buffers; this worker only authors alpha. Earlier five masks remain held unchanged.</p>'+''.join(cards),encoding='utf-8')
 print(json.dumps({'manifest':str(HERE/'proposal-manifest-v2.json'),'sha256':sha(HERE/'proposal-manifest-v2.json'),'changed':result['changed_states'],'unchanged':len(result['unchanged_states']),'prior_unchanged':sha(priorpath)==PRIOR},indent=2))
if __name__=='__main__':main()
