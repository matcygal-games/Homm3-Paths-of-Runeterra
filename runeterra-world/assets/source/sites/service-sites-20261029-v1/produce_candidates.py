"""Candidate-only technical sprite conversion. No selection, content or manifest writes."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib,json

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
WORKSPACE=PROJECT.parent
REPORT=WORKSPACE/'reports/world-service-art-20261029-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf8')
def main():
 requests=json.loads((HERE/'generation-requests.json').read_text(encoding='utf8'))
 identities=json.loads((PROJECT/'design/world-identities.json').read_text(encoding='utf8'))
 records={x['id']:x for x in identities['sites']}
 inventory=[];board=Image.new('RGB',(960,470),(72,79,64));draw=ImageDraw.Draw(board)
 for i,(id,request) in enumerate(requests['sites'].items()):
  folder=HERE/id;master=folder/'master-v1.png';source=Image.open(master).convert('RGBA')
  box=source.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()
  if not box or box[0]<=0 or box[1]<=0 or box[2]>=source.width or box[3]>=source.height:raise ValueError('Clipped whole painted silhouette: '+id)
  sprite=source.crop(box);sprite.thumbnail((88,88),Image.Resampling.LANCZOS)
  pos=((96-sprite.width)//2,94-sprite.height);native=Image.new('RGBA',(96,96));native.alpha_composite(sprite,pos)
  frame=folder/'native-v1.png';native.save(frame)
  identity=records.get(id,{'id':id,'status':'design proposal','canonical_basis':'Piltovan precision craft and local hextech tooling supply materials/motifs only.','project_fiction':'Optional local resource workshop newly proposed from user brief; no registration or reward rule selected.','sources':['riot-region-piltover','user-hex-press-refinery-brief']})
  save(folder/'identity-source-record.json',identity)
  generation={'provider':'OpenAI built-in image_gen','model':'not exposed by tool','request':request['prompt'],'provider_original_sha256':sha(folder/'provider-original.png'),'master_sha256':sha(master),'provider_file_basename':request['provider_file_basename'],'metadata_processing':'RGBA decoded pixels preserved; metadata removed in portable master and derived frame. Provider original retained separately.','art_process':'New painted bitmap generated from text; no3D pipeline, no source illustration/Blender input.','visual_approval_granted':False,'redistribution':'unresolved'}
  save(folder/'generation-v1.json',generation)
  source_name=frame.relative_to(PROJECT).as_posix()
  recipe={'recipe_type':'vcmi_animation','production_status':'painted-master-complete-unapproved','output_path':f'Content/Sprites/runeterra/world/sites/{id}/map.json','canvas':[96,96],'pivot':{'x':48,'y':94},'groups':[{'group':0,'generateShadow':1,'generateOverlay':0,'frames':[{'frame':0,'source':source_name,'source_sha256':sha(frame),'sha256':sha(frame),'source_canvas':[96,96]}]}],'generation':generation,'production_inputs':[{'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)} for p in [master,folder/'prompt-v1.txt',folder/'generation-v1.json',folder/'identity-source-record.json',Path(__file__)]],'credits':{'author':'Runeterra project-directed built-in image generation','license':'pending','redistribution':'unresolved'},'visual_approval_granted':False}
  save(folder/'recipe-candidate.json',recipe)
  alpha=native.getchannel('A');bbox=alpha.point(lambda a:255 if a>=8 else 0).getbbox()
  calibration={'status':'design proposal','source_box':list(box),'source_canvas':list(source.size),'native_canvas':[96,96],'native_position':list(pos),'native_size':list(sprite.size),'native_alpha8_bbox':list(bbox),'native_frame_sha256':sha(frame),'pivot':[48,94],'candidate_mask':['VVV','BBV','BAV'],'candidate_visitableFrom':['---','---','+++'],'door_intent_native':[48,87],'mask_authority':'Matches existing world site convention as a candidate only; grounded body footprint versus roof/shadow overhang and actual visit access require mechanics/native review.','shadow_policy':'Existing generateShadow1 convention plus close painted contact shading; projected appearance/doubling unobserved.','native_execution':'not_run','visual_acceptance':'pending','coastal_or_new_terrain_effect':False}
  save(folder/'calibration-candidate.json',calibration)
  x=(i%3)*320;y=(i//3)*235
  draw.text((x+8,y+7),id,fill='white');board.paste(native,(x+12,y+39),native);board.paste(native.resize((192,192),Image.Resampling.NEAREST),(x+118,y+32),native.resize((192,192),Image.Resampling.NEAREST))
  for p in [master,frame,folder/'recipe-candidate.json',folder/'calibration-candidate.json']:
   inventory.append({'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
  # Diagnostic tile grid, never selected art.
  diagnostic=Image.new('RGBA',(384,384),(63,75,59,255));diagnostic.alpha_composite(native.resize((384,384),Image.Resampling.NEAREST));dd=ImageDraw.Draw(diagnostic)
  for n in [0,128,256,383]:dd.line((n,0,n,383),fill=(230,230,200,130));dd.line((0,n,383,n),fill=(230,230,200,130))
  for yy,row in enumerate(calibration['candidate_mask']):
   for xx,c in enumerate(row):dd.text((xx*128+8,yy*128+8),c,fill=(255,240,110,255))
  diagnostic.save(REPORT/(id+'-mask-diagnostic.png'))
 REPORT.mkdir(parents=True,exist_ok=True);board.save(REPORT/'native-sprite-board.png')
 save(REPORT/'candidate-inventory.json',{'status':'design proposal','canonical_selected':False,'files':inventory})
 print(json.dumps({'status':'design proposal','sites':len(requests['sites']),'inventory_entries':len(inventory),'canonical_selected':False}))
if __name__=='__main__':main()
