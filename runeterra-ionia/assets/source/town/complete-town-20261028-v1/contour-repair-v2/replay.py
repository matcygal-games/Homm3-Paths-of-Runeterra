"""Technical alpha annotations only; does not write source art or held frames.

Each roof profile is a manually inspected native-coordinate contour.  It is
intersected with the immutable original alpha, so this proposal cannot invent
building pixels or alter any painted RGB.  Lower yard/footing ownership remains
unchanged.  The two library notches remove the separately owned Kinkou roof.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
SOURCE = HERE.parent
REPORT = PROJECT / 'build/reports/complete-town-20261028-v1/contour-repair-v2'
EXCLUDED = {'blacksmith','special2','dwellingLvl5','dwellingUpLvl5',
            'special3','shipyard','ship','grail'}
INDEX_SHA = 'b3cf81047127a6f52e3130e106936cb4a92d6bb70f78a52cce3b2d4987a1caa5'

# The manually traced upper architectural envelope, from left to right.
# This does not replace the original side/bottom contour or courtyard alpha.
ROOFS = {
 'townHall': [
  (0,83),(309,83),(313,78),(320,78),(325,75),(327,74),(329,66),
  (330,65),(331,69),(335,72),(342,74),(349,74),(353,72),(356,68),
  (358,64),(362,59),(365,55),(369,49),(371,47),(371,44),(373,44),
  (374,48),(379,50),(389,52),(396,53),(397,49),(399,49),(400,53),
  (407,54),(417,54),(419,52),(421,52),(421,56),(422,60),(425,65),
  (429,69),(434,72),(443,75),(450,77),(456,77),(461,76),(467,73),
  (471,71),(473,70),(475,68),(476,68),(476,75),(799,75)],
 'cityHall': [
  (0,82),(306,82),(315,78),(320,75),(321,66),(322,64),(324,65),
  (324,69),(331,69),(337,66),(339,61),(337,58),(336,55),(335,51),
  (336,49),(338,50),(339,54),(343,57),(348,58),(354,57),(359,54),
  (364,49),(369,44),(371,40),(373,40),(374,43),(383,44),(392,44),
  (400,44),(401,40),(403,40),(404,45),(410,52),(416,57),(422,60),
  (429,62),(433,62),(435,60),(436,60),(436,65),(442,68),(451,72),
  (455,73),(456,69),(457,68),(458,72),(461,74),(465,76),(469,75),
  (471,73),(472,71),(474,71),(474,78),(799,78)],
 'capitol': [
  (0,78),(289,78),(292,74),(298,73),(305,76),(311,76),(314,72),
  (315,64),(316,62),(317,62),(318,66),(322,70),(329,72),(334,70),
  (334,64),(332,61),(332,56),(331,51),(331,48),(333,48),(333,51),
  (337,55),(342,57),(347,58),(351,55),(355,49),(359,43),(363,38),
  (364,34),(366,34),(366,37),(371,40),(376,42),(381,42),(387,41),
  (388,37),(388,33),(390,30),(392,31),(392,37),(394,41),(400,43),
  (405,43),(407,41),(409,41),(411,47),(415,54),(420,59),(428,62),
  (435,63),(439,62),(443,59),(447,54),(449,54),(448,60),(445,66),
  (442,70),(450,74),(457,76),(463,78),(468,77),(473,75),(476,72),
  (478,72),(478,80),(799,80)],
 'citadel': [
  (0,83),(501,83),(510,83),(516,79),(521,80),(521,62),(516,57),
  (513,54),(516,54),(521,55),(527,54),(533,51),(537,47),(539,43),
  (541,40),(541,38),(543,38),(544,42),(547,46),(553,49),(559,51),
  (561,50),(563,49),(564,49),(564,53),(560,56),(555,59),(555,63),
  (567,66),(599,66),(601,63),(606,61),(607,58),(607,56),(604,56),
  (605,54),(607,53),(613,51),(618,47),(621,44),(622,41),(622,38),
  (624,38),(625,42),(628,47),(632,50),(637,52),(642,54),(646,53),
  (648,52),(649,52),(649,56),(646,59),(642,61),(642,74),(649,76),
  (654,82),(660,84),(799,84)],
 'castle': [
  (0,57),(486,57),(486,55),(489,54),(494,51),(496,48),(497,46),
  (499,46),(500,49),(504,52),(510,54),(513,54),(513,57),(512,60),
  (508,62),(507,72),(517,73),(528,74),(531,56),(532,48),(535,46),
  (537,44),(537,41),(540,41),(542,40),(546,37),(548,34),(545,34),
  (542,33),(539,32),(537,31),(537,30),(541,30),(546,29),(549,27),
  (552,26),(553,23),(555,23),(555,26),(558,29),(562,30),(565,29),
  (567,28),(568,28),(568,31),(564,33),(560,34),(559,36),(562,38),
  (566,40),(569,40),(572,38),(572,41),(569,44),(566,46),(564,47),
  (564,61),(571,62),(594,62),(596,61),(597,51),(596,49),(594,48),
  (592,46),(592,44),(593,43),(595,44),(599,43),(602,41),(605,38),
  (605,36),(602,35),(600,34),(599,32),(601,31),(604,32),(608,31),
  (610,29),(610,27),(612,27),(612,30),(615,32),(619,33),(622,32),
  (624,30),(625,30),(625,33),(621,35),(617,36),(617,38),(620,40),
  (624,42),(627,42),(630,40),(631,40),(631,43),(627,46),(624,48),
  (624,58),(631,60),(634,60),(640,61),(641,61),(646,57),(650,53),
  (652,50),(654,49),(655,52),(660,56),(664,58),(668,59),(669,58),
  (671,58),(671,64),(799,64)],
 'dwellingUpLvl7': [
  (0,0),(196,0),(196,27),(199,23),(201,18),(200,15),(201,12),
  (204,8),(207,5),(210,7),(215,8),(220,10),(225,12),(230,15),
  (233,18),(234,21),(233,25),(231,27),(230,30),(229,33),(228,35),
  (231,36),(233,37),(234,39),(234,43),(233,45),(233,47),(238,49),
  (242,52),(799,52)],
}
NOTCH = [(238,169),(248,170),(261,171),(267,170),(270,168),
         (273,171),(276,173),(281,177),(284,181),(284,190),(235,190)]
SAMPLES = {
 'townHall':[(435,57)], 'cityHall':[(360,45)],
 'capitol':[(433,26),(347,36)],
 'castle':[(545,18),(607,19),(498,44)],
 'citadel':[(637,42)],'dwellingUpLvl7':[(244,22),(238,10)],
 'mageGuild2':[(258,175),(267,177),(273,179)],
 'mageGuild3':[(258,175),(267,177),(273,179)]}

def sha(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
 return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}

def checker(size):
 image=Image.new('RGB',size,(205,205,205));draw=ImageDraw.Draw(image)
 for y in range(0,size[1],8):
  for x in range(0,size[0],8):
   if (x//8+y//8)%2:draw.rectangle((x,y,x+7,y+7),fill=(155,155,155))
 return image

def main():
 global ROOFS
 ROOFS=json.loads((HERE/'roof-profiles-v2.json').read_text(encoding='utf-8'))
 index_path=SOURCE/'frame-index-v1.json'
 assert sha(index_path)==INDEX_SHA,'Immutable index changed'
 index=json.loads(index_path.read_text(encoding='utf-8'))
 (HERE/'masks').mkdir(parents=True,exist_ok=True)
 REPORT.mkdir(parents=True,exist_ok=True)
 annotation={'status':'authored configuration','method':'Manually inspected native roof profiles and library foreign-roof negative-air notches; alpha only.',
  'roof_profiles':ROOFS,'roof_profile_authoring_data':ref(HERE/'roof-profiles-v2.json'),'library_foreign_roof_notch':NOTCH,'input_index':ref(index_path)}
 (HERE/'annotations.json').write_text(json.dumps(annotation,indent=2)+'\n')
 records=[];cards=[]
 for state,row in index['frames'].items():
  if state in EXCLUDED:continue
  frame_path=PROJECT/row['path'];source_path=PROJECT/row['source_painting']
  assert sha(frame_path)==row['sha256'],state+' frame drift'
  assert sha(source_path)==row['source_painting_sha256'],state+' source drift'
  original=Image.open(frame_path).convert('RGBA');alpha=original.getchannel('A')
  proposal=alpha.copy()
  if state in ROOFS:
   keep=Image.new('L',(800,374),0)
   ImageDraw.Draw(keep).polygon(ROOFS[state]+[(799,373),(0,373)],fill=255)
   proposal=ImageChops.darker(alpha,keep)
  if state in ('mageGuild2','mageGuild3'):
   ImageDraw.Draw(proposal).polygon(NOTCH,fill=0)
  if state=='castle':
   # The separate 17-pixel sliver at this coordinate is verified blue sky,
   # not a detached architectural finial (all RGB blue-dominant, native view).
   ImageDraw.Draw(proposal).rectangle((517,54,523,61),fill=0)
  assert not ImageChops.subtract(proposal,alpha).getbbox(),'No new RGB/architecture may be invented'
  for xy in SAMPLES.get(state,[]):assert alpha.getpixel(xy)>0 and proposal.getpixel(xy)==0,(state,xy)
  out=HERE/'masks'/(state+'.png');proposal.save(out)
  changed=ImageChops.difference(alpha,proposal)
  changed_count=sum(value>0 for value in changed.tobytes())
  if state not in SAMPLES:assert proposal.tobytes()==alpha.tobytes(),state+' unrequested matte change'
  after=original.copy();after.putalpha(proposal)
  bounds=alpha.getbbox();bounds=(max(0,bounds[0]-3),max(0,bounds[1]-3),min(800,bounds[2]+3),min(374,bounds[3]+3))
  before_native=original.crop(bounds);after_native=after.crop(bounds)
  w,h=before_native.size
  presentation=Image.new('RGB',(w*3,h+20),(27,30,34));d=ImageDraw.Draw(presentation)
  for i,(label,actor) in enumerate([('SOURCE',Image.open(source_path).convert('RGBA').crop(bounds)),('BEFORE',before_native),('PROPOSAL',after_native)]):
   cell=checker((w,h)).convert('RGBA');cell.alpha_composite(actor)
   presentation.paste(cell.convert('RGB'),(i*w,20));d.text((i*w+2,3),label,fill='white')
  presentation.save(REPORT/(state+'-native.png'))
  if state in SAMPLES:
   presentation.resize((presentation.width*4,presentation.height*4),Image.Resampling.NEAREST).save(REPORT/(state+'-4x.png'))
  records.append({'state':state,'site':row['site'],'before_frame':ref(frame_path),'source_painting':ref(source_path),
   'proposed_alpha':ref(out),'before_alpha_bytes_sha256':hashlib.sha256(alpha.tobytes()).hexdigest(),
   'after_alpha_bytes_sha256':hashlib.sha256(proposal.tobytes()).hexdigest(),
   'removed_alpha_pixels':changed_count,'added_alpha_pixels':0,'architecture_rgb_changed':0,
   'demonstrated_samples_removed':[list(xy)for xy in SAMPLES.get(state,[])],
   'unchanged_alpha':proposal.tobytes()==alpha.tobytes()})
  cards.append('<section><h2>'+state+'</h2><p>'+str(changed_count)+' alpha pixels removed; painted RGB and roots unchanged.</p><a href="'+state+'-native.png"><img src="'+state+'-native.png"></a></section>')
 assert len(records)==27
 manifest={'status':'authored configuration','scope':'Technical matte proposals only. Rejected v1 remains immutable; art owner alone adopts reviewed proposals into a new cohort.',
  'input_index':ref(index_path),'annotations':ref(HERE/'annotations.json'),'replay':ref(Path(__file__)),
  'states':records,'changed_states':[r['state']for r in records if not r['unchanged_alpha']],
  'unchanged_states':[r['state']for r in records if r['unchanged_alpha']],
  'native_execution':False,'release_accepted':False}
 (HERE/'proposal-manifest-v1.json').write_text(json.dumps(manifest,indent=2)+'\n')
 doc='<!doctype html><meta charset="utf-8"><title>Ionia technical contour proposals</title><style>body{background:#171b20;color:#eee;font:15px Arial;max-width:1200px;margin:25px auto}img{max-width:100%;height:auto}section{margin:30px 0}a{color:#ddc080}</style><h1>Ionia alpha-only proposals</h1><p>Native source / rejected v1 / proposed contour. Painted RGB, registration and all held frames are unchanged. Technical review only, no native or final art acceptance.</p>'+''.join(cards)
 (REPORT/'index.html').write_text(doc,encoding='utf-8')
 print(json.dumps({'proposal_manifest':str(HERE/'proposal-manifest-v1.json'),'changed_states':manifest['changed_states'],'unchanged_states':len(manifest['unchanged_states']),'removed_pixels':sum(r['removed_alpha_pixels']for r in records)},indent=2))

if __name__=='__main__':main()
