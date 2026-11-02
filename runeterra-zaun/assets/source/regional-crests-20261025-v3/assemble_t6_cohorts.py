"""Finite physical cloth correction; never transforms bodies or draws crest pixels."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
from assemble_clean_cohorts import layer_for,png,put,enc,sha,relative,S,P,W,R
def run(unit,version='t6-v1'):
 prep_path=P/f'assets/source/regional-crests-20261025-v2/{unit}/preparation-v2.json';prep=json.loads(prep_path.read_text());plan_path=S/f'{unit}-attachments-{version}.json';plan=json.loads(plan_path.read_text());assert len(plan['attachments'])==len(prep['entries']);records=[];rejected=[]
 for e,a in zip(prep['entries'],plan['attachments']):
  assert a['index']==e['index'];source=P/e['slots'][0]['source'];assert sha(source)==e['slots'][0]['source_sha256'];old=Image.open(source).convert('RGBA');before=np.array(old);after=before.copy();mask=np.zeros(before.shape[:2],bool);coverages=[]
  for item in a['layers']:
   glyph=Image.open(S/item['painted_variant']).convert('RGBA');layer=np.array(layer_for(glyph,item['surface_quad'],old.size));ink=layer[:,:,3]>0;physical=before[:,:,3]>=248;localmask=ink&physical;coverage=float(localmask.sum()/max(1,ink.sum()));coverages.append(coverage)
   if coverage<.96:rejected.append({'index':e['index'],'coverage':coverage,'layer':len(coverages)-1})
   amount=layer[:,:,3:4].astype(float)/255;mix=np.rint(layer[:,:,:3]*amount+after[:,:,:3]*(1-amount)).astype(np.uint8);after[localmask,:3]=mix[localmask,:3];mask|=localmask
  assert np.array_equal(after[:,:,3],before[:,:,3]) and np.array_equal(after[~mask],before[~mask]);out=S/f'native-candidates-{version}/{unit}/context-{e["index"]:03d}.png';maskpath=S/f'native-candidates-{version}/{unit}/masks/context-{e["index"]:03d}.png';png(out,Image.fromarray(after));png(maskpath,Image.fromarray(mask.astype(np.uint8)*255));records.append({**a,'slots':e['slots'],'source':relative(source),'source_sha256':sha(source),'candidate':relative(out),'candidate_sha256':sha(out),'mask':relative(maskpath),'mask_sha256':sha(maskpath),'host_coverage':coverages,'changed_pixels':int(np.any(after!=before,axis=2).sum()),'all_original_alpha_exact':True,'all_outside_material_RGBA_exact':True})
 for page in range((len(records)+11)//12):
  board=Image.new('RGBA',(1440,600),(42,44,41,255));d=ImageDraw.Draw(board)
  for cell,r in enumerate(records[page*12:page*12+12]):
   old=Image.open(P/r['source']).convert('RGBA');new=Image.open(P/r['candidate']).convert('RGBA');box=old.getchannel('A').point(lambda v:255 if v>=16 else 0).getbbox();a=old.crop(box);b=new.crop(box);scale=min(2,115/max(a.width,1),245/max(a.height,1));size=(round(a.width*scale),round(a.height*scale));x=cell%6*240;y=cell//6*300;board.alpha_composite(a.resize(size,Image.Resampling.NEAREST),(x,y+35));board.alpha_composite(b.resize(size,Image.Resampling.NEAREST),(x+120,y+35));z=r['slots'][0];d.text((x,y),f"{r['index']} {z['role']} {z.get('group','')}/{z.get('frame','')}",fill='white');d.text((x,y+15),'old / new'+(' OCCLUDED' if not r['layers'] else ''),fill='white')
  png(R/f'{unit}-complete-physical-{version}-page-{page}.png',board)
 receipt={'status':'authored configuration','unit':unit,'source_preparation':relative(prep_path),'source_preparation_sha256':sha(prep_path),'attachment_plan':relative(plan_path),'attachment_plan_sha256':sha(plan_path),'producer':relative(Path(__file__)),'producer_sha256':sha(Path(__file__)),'records':records,'rejected_physical_coverage':rejected,'imported_geometry_helper':relative(S/'assemble_clean_cohorts.py'),'imported_geometry_helper_sha256':sha(S/'assemble_clean_cohorts.py'),'no_body_warp':True,'no_original_alpha_change':True,'selected_or_staged':False,'runtime_verified':False,'release_accepted':False};put(S/f'{unit}-assembly-{version}.json',enc(receipt));print(json.dumps({'unit':unit,'contexts':len(records),'rejected':rejected}))
if __name__=='__main__':
 import sys
 for arg in sys.argv[1:]:
  parts=arg.split(':');run(parts[0],parts[1] if len(parts)>1 else 't6-v1')
