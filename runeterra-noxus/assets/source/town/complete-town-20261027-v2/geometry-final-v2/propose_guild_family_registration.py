"""Whole coherent Guild family up2px registration proposal, all sources preserved."""
from pathlib import Path
from PIL import Image, ImageChops
from collections import deque
import hashlib,json
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];TOWN=HERE.parent;REPORT=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2/guild-family-up2-proposal-v1'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 REPORT.mkdir(parents=True,exist_ok=False);selection=json.loads((TOWN/'candidate-final-v6/selection.json').read_text());rows={row['state']:row for row in selection['states']};index=json.loads((TOWN/'native-transforms-v6/states.json').read_text());states={row['state']:row for row in index['states']};targets=['mageGuild1','mageGuild2','mageGuild3','mageGuild4'];layers={state:Image.open(ROOT[row['frame']['path']]if False else ROOT/row['frame']['path']).convert('RGBA')for state,row in states.items()};moved=dict(layers);roots={state:Image.open(ROOT/row['foundation_mask']['path']).convert('L')for state,row in states.items()};doors={state:Image.open(ROOT/row['door_mask']['path']).convert('L')for state,row in states.items()};treads={state:Image.open(ROOT/row['own_treads_mask']['path']).convert('L')for state,row in states.items()}
 def move(image):
  out=Image.new(image.mode,image.size);out.paste(image,(0,-2));return out
 def alpha(image,threshold):return image.getchannel('A').point(lambda a:255 if a>=threshold else 0)
 def union(images):
  out=Image.new('L',(800,374))
  for image in images:out=ImageChops.lighter(out,image)
  return out
 support=Image.open(HERE/'final-v6-trace-v2/support.png').convert('L');records=[]
 for state in targets:
  moved[state]=move(layers[state]);roots[state]=move(roots[state]);doors[state]=move(doors[state]);treads[state]=move(treads[state]);folder=REPORT/'states'/state;folder.mkdir(parents=True)
  for name,image in [('frame',moved[state]),('root',roots[state]),('door',doors[state]),('own-treads',treads[state])]:image.save(folder/(name+'.png'),compress_level=9)
  assert alpha(moved[state],8).histogram()==alpha(layers[state],8).histogram()
  gap=ImageChops.subtract(roots[state],support);records.append({'state':state,'original_frame':states[state]['frame'],'proposed_frame_sha256':sha(folder/'frame.png'),'full_root_pixels':roots[state].histogram()[255],'support_gap_pixels':gap.histogram()[255],'root_outside_actual_frame_alpha8':ImageChops.subtract(roots[state],alpha(moved[state],8)).histogram()[255],'site_native_depth':159,'proposed_entrance':[states[state]['entrance'][0],states[state]['entrance'][1]-2]})
 conflicts=[]
 for rear,rrow in states.items():
  for front,frow in states.items():
   if rrow['site']==frow['site']or rrow['native_z']>=frow['native_z']:continue
   hit=ImageChops.multiply(doors[rear],alpha(moved[front],128))
   if hit.getbbox():conflicts.append({'rear':rear,'front':front,'pixels':hit.histogram()[255],'bbox':hit.getbbox()})
 c=json.loads((HERE/'town-layout.json').read_text());walk=np.asarray(Image.open(ROOT/c['source_walkable_plane']['path']).convert('L'))>0;body=np.logical_or.reduce([np.asarray(alpha(image,128))>0for image in moved.values()]);free=walk&~body;start=(164,163);goal=(384,250);q=deque([start]);seen={start}
 while q:
  x,y=q.popleft()
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<800 and 0<=yy<374 and free[yy,xx]and(xx,yy)not in seen:seen.add((xx,yy));q.append((xx,yy))
 background=Image.open(TOWN/'terrain/final-native-v6.png').convert('RGBA')
 for mode in ('full','base','guild3','early'):
  chosen=[site['states'][0]if mode=='base'else site['top']for site in selection['sites']if site['id']not in ('coast','grail')]
  if mode=='guild3':chosen=[state for state in chosen if state!='mageGuild4']+['mageGuild3']
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern','mageGuild1']
  for suffix,frames in [('before',layers),('after',moved)]:
   image=background.copy()
   for state in sorted(chosen,key=lambda s:states[s]['native_z']):image.alpha_composite(frames[state])
   image.save(REPORT/(mode+'-'+suffix+'.png'))
   if mode=='guild3':image.crop((225,135,350,180)).resize((1000,360),Image.Resampling.NEAREST).save(REPORT/(mode+'-'+suffix+'-route8x.png'))
 rear=union([roots[s]for s in ('fort','citadel','castle')]);front=union([alpha(moved[s],128)for s in targets]);root_hit=ImageChops.multiply(rear,front);arena=alpha(moved['special3'],128);college_root=union([roots[s]for s in targets]);arena_hit=ImageChops.multiply(college_root,arena)
 result={'status':'design proposal','whole_family_delta':[0,-2],'preserved_site_depth':159,'states':records,'all36_full_entry_conflicts':conflicts,'actual_bodyfree_civic_to_main_route':goal in seen,'fixed_floor_and_streets':True,'new_bastion_college_root_pixels':root_hit.histogram()[255],'new_college_arena_root_pixels':arena_hit.histogram()[255],'source_selected':False,'stage_published':False}
 (REPORT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
