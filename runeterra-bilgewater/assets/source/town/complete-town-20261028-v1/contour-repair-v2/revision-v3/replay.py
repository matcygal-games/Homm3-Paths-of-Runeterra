"""Seal all seven ordinary remedies using the complete painted Buhru reveal.

The Buhru alpha is intentionally the original full silhouette: genuine wall/
plinth recovery eliminates foreign Tavern pixels without cutting a false gap.
No held frame, prior proposal, canonical source or stage is changed.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent;PARENT=HERE.parent
SOURCE=PARENT.parent;PROJECT=PARENT.parents[4]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/contour-repair-v2-revision-v3'
PRIOR='211ec32a1998f2e0e57b711fea9f26fa6bfb378b1ae023dfd851b126e04337de'
EXPECTED_SOURCE='db43e4fe97090b10a5ceaa65676d127b17e9ce06edcae53a24e4f60dbbb508d2'
REMEDIED={'castle','capitol','blacksmith','townHall','cityHall','citadel','dwellingUpLvl4'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path):return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}
def main():
 priorpath=PARENT/'revision-v2/proposal-manifest-v2.json';assert sha(priorpath)==PRIOR
 prior=json.loads(priorpath.read_text(encoding='utf-8'))
 source_record_path=SOURCE/'underlap-buffers-v3/source-record.json'
 source_record=json.loads(source_record_path.read_text(encoding='utf-8'))
 sourcepath=PROJECT/source_record['source'];assert sha(sourcepath)==source_record['source_sha256']==EXPECTED_SOURCE
 assert source_record['delta']==[0,0]
 (HERE/'masks').mkdir(exist_ok=True,parents=True);REPORT.mkdir(exist_ok=True,parents=True)
 records=[]
 for row in prior['states']:
  state=row['state']
  if state!='dwellingUpLvl4':
   path=PROJECT/row['proposed_frame_coordinate_alpha']['path'];assert sha(path)==row['proposed_frame_coordinate_alpha']['sha256']
   nr=dict(row);nr['state_input_unchanged']=state not in REMEDIED;records.append(nr);continue
  framepath=PROJECT/row['before_frame']['path'];assert sha(framepath)==row['before_frame']['sha256']
  original=Image.open(framepath).convert('RGBA');alpha=original.getchannel('A')
  out=HERE/'masks'/(state+'.png');alpha.save(out)
  nr={'state':state,'site':row['site'],'before_frame':ref(framepath),'source_painting':ref(sourcepath),
   'delta':[0,0],'proposed_frame_coordinate_alpha':ref(out),
   'before_alpha_bytes_sha256':hashlib.sha256(alpha.tobytes()).hexdigest(),
   'after_alpha_bytes_sha256':hashlib.sha256(alpha.tobytes()).hexdigest(),
   'removed_alpha_pixels':0,'added_actual_source_architecture_pixels':0,
   'unchanged_alpha':True,'state_input_unchanged':False,
   'painted_source_RGB_edited_by_this_worker':False,
   'source_RGB_changed_by_art_owner_genuine_reveal':True,
   'genuine_reveal_record':ref(source_record_path),
   'root_or_pose_transform_changed':False,
   'reason':'Complete genuine wall/plinth replaces former Tavern overlap. Preserve the original whole Temple alpha instead of introducing the rejected diagonal notch.'}
  records.append(nr)
  mapped=Image.open(sourcepath).convert('RGBA');after=mapped.copy();after.putalpha(alpha)
  bounds=alpha.getbbox();box=(bounds[0]-4,bounds[1]-4,bounds[2]+4,bounds[3]+4);size=(box[2]-box[0],box[3]-box[1]);canvas=Image.new('RGB',(size[0]*3,size[1]+20),(25,28,32));d=ImageDraw.Draw(canvas)
  for col,(label,image) in enumerate([('COMPLETE REVEAL',mapped),('REJECTED ORIGINAL',original),('FINAL PROPOSAL',after)]):
   tile=Image.new('RGBA',size,(190,190,190,255));td=ImageDraw.Draw(tile)
   for y in range(0,size[1],8):
    for x in range(0,size[0],8):
     if (x//8+y//8)%2:td.rectangle((x,y,x+7,y+7),fill=(140,140,140,255))
   tile.alpha_composite(image.crop(box));canvas.paste(tile.convert('RGB'),(col*size[0],20));d.text((col*size[0]+2,3),label,fill='white')
  canvas.save(REPORT/(state+'-native.png'));canvas.resize((canvas.width*4,canvas.height*4),Image.Resampling.NEAREST).save(REPORT/(state+'-4x.png'))
 result=dict(prior)
 result.update({'scope':'Final proposed ordinary subset: seven remedies across30 states. Six alpha repairs plus one whole-silhouette genuine Temple RGB recovery;23 state inputs unchanged. Roost pair/coast pair/Grail remain outside this worker ownership.',
  'prior_incomplete_draft':ref(priorpath),'revision_replay':ref(Path(__file__)),
  'complete_buhru_reveal_record':ref(source_record_path),'states':records,
  'changed_states':sorted(REMEDIED),'unchanged_states':[r['state']for r in records if r['state_input_unchanged']],
  'unchanged_alpha_states':[r['state']for r in records if r.get('unchanged_alpha')],
  'deferred_states':[],'independent_review_pending':True,'release_accepted':False})
 assert len(records)==30 and len(result['unchanged_states'])==23
 (HERE/'proposal-manifest-v3.json').write_text(json.dumps(result,indent=2)+'\n')
 (REPORT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Bilgewater final ordinary matte proposals</title><style>body{background:#171b20;color:#eee;font:16px Arial;max-width:1200px;margin:25px auto}img{max-width:100%}a{color:#ddc080}</style><h1>Final ordinary-state proposal subset</h1><p>Seven demonstrated remedies.23 state inputs unchanged; the Temple keeps its original full alpha over a genuinely painted recovered wall/plinth. The other six revised alpha files and held inputs are pinned in the manifest. Not native or final art acceptance.</p><img src="dwellingUpLvl4-native.png"><p><a href="../contour-repair-v2/index.html">Initial five repairs</a> · <a href="../contour-repair-v2-revision-v2/citadel-native.png">Citadel recovered source and alpha</a></p>',encoding='utf-8')
 print(json.dumps({'manifest':str(HERE/'proposal-manifest-v3.json'),'sha256':sha(HERE/'proposal-manifest-v3.json'),'remedied':len(result['changed_states']),'unchanged_inputs':len(result['unchanged_states']),'unchanged_alpha_arrays':len(result['unchanged_alpha_states']),'prior_draft_unchanged':sha(priorpath)==PRIOR},indent=2))
if __name__=='__main__':main()
