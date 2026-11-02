"""Technical mask/composition of provider-painted cloth faces; no artwork synthesis."""
from pathlib import Path
import hashlib,json,sys,copy
from PIL import Image,ImageDraw,ImageChops

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[4]
WORKSPACE=PROJECT.parent
REPORT=WORKSPACE/'build/reports/regional-crests-20261025-v1/shurima-unit-art/pilot-v2-final'
UNITS={'desertNomad':('grounded-standing-v1','505cb96a8e7956258f10e5577f63a52007334d4097b532022c672cba083a0535'), 'sandWarrior':('grounded-standing-v2','9660e46c141fbaae94e39117d685c3bf5473be3f1e637aef54d11c57cf009d31')}
CROP=(380,480,830,820)
PLANE=[(223,40),(270,40),(295,60),(320,110),(345,135),(393,173),(419,200),(406,222),(352,247),(315,267),(292,285),(279,322),(250,321),(227,300),(190,281),(148,263),(98,257),(75,246),(99,203),(120,165),(143,144),(178,150),(208,142),(221,120),(220,90)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,sort_keys=True,indent=2)+'\n',encoding='utf8')
def pin(p):return {'source':p.relative_to(PROJECT).as_posix(),'source_sha256':sha(p)}
def native(im):return im.transform((450,400),Image.Transform.AFFINE,(1/.074,0,640-193/.074,0,1/.074,1070-266/.074),Image.Resampling.BICUBIC)
def mirror(im):
 out=Image.new('RGBA',im.size);out.paste(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(386-(im.width-1),0));return out
def guard(original,candidate,mask):
 assert candidate.getchannel('A').tobytes()==original.getchannel('A').tobytes(),'alpha changed'
 rgbdelta=ImageChops.difference(original.convert('RGB'),candidate.convert('RGB'))
 outside=Image.composite(rgbdelta,Image.new('RGB',original.size),ImageChops.invert(mask))
 assert outside.getbbox() is None,'RGB changed outside physical cloth plane'
 assert rgbdelta.getbbox() is not None,'no positive RGB difference inside plane'
 return rgbdelta
def assemble(unit,expected=None):
 n,h=UNITS[unit];old=PROJECT/'assets/source/creatures/painted-v2'/unit/(n+'.png')
 assert sha(old)==(expected or h),'old master hash guard'
 d=SOURCE/unit;im=Image.open(old).convert('RGBA');paint=Image.open(d/'painted-cloth-provider-v2.png').convert('RGBA').resize((450,340),Image.Resampling.LANCZOS)
 mask=Image.new('L',(450,340));ImageDraw.Draw(mask).polygon(PLANE,fill=255)
 # Restore original alpha exactly, including the outer silhouette and contact shadow.
 rgb=Image.composite(paint,im.crop(CROP),mask);rgb.putalpha(im.crop(CROP).getchannel('A'))
 out=im.copy();out.paste(rgb,CROP[:2]);out.putalpha(im.getchannel('A'))
 fullmask=Image.new('L',im.size);fullmask.paste(mask,CROP[:2])
 delta=guard(im,out,fullmask)
 out.save(d/'holding-source-candidate.png',compress_level=9);fullmask.save(d/'physical-plane-mask.png',compress_level=9)
 v=native(im)
 # Nearest sampling only inside the hand-defined painted cloth face retains
 # the provider's small negative channels. The body remains original bicubic.
 nearest=out.transform((450,400),Image.Transform.AFFINE,(1/.074,0,640-193/.074,0,1/.074,1070-266/.074),Image.Resampling.NEAREST)
 native_mask=fullmask.transform((450,400),Image.Transform.AFFINE,(1/.074,0,640-193/.074,0,1/.074,1070-266/.074),Image.Resampling.NEAREST)
 oldalpha=v.getchannel('A');v=Image.composite(nearest,v,native_mask);v.putalpha(oldalpha)
 v.save(d/'holding-native-right.png',compress_level=9);mirror(v).save(d/'holding-native-left.png',compress_level=9)
 recipe={'recipe_type':'vcmi_animation','unit':unit,'canvas':[450,400],'pivot':{'x':193,'y':266},'generateShadow':0,'generateOverlay':1,'output_path':'Content/Sprites/runeterra/shurima/creatures/'+unit+'/holding-pilot.json','production_status':'painted-master-complete-unapproved','status':'authored configuration','visual_approval_granted':False,'groups':[{'group':2,'frames':[dict(pin(d/'holding-native-right.png'),source_canvas=[450,400])]}],'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','painted_master':pin(d/'holding-source-candidate.png')['source'],'painted_master_sha256':sha(d/'holding-source-candidate.png'),'provenance':(SOURCE/'pilot-provenance.json').relative_to(PROJECT).as_posix(),'prompt':'cloth-prompt.txt: exact provider prompt; private raw receipts retained outside export','method':'Provider-painted physical cloth face, hand-defined interior mask, original alpha restored; fixed .074 affine source-to-native transform. Nearest only inside cloth mask; original bicubic pixels elsewhere.'},'credits':{'author':'Project-directed built-in imagegen; technical 2D composition','license':None,'redistribution':'unresolved; release prohibited'},'acceptance':'HOLDING PILOT ONLY. Does not replace complete battle/action/map/portrait resources.'}
 write(d/'holding-pilot-recipe.json',recipe)
 native_delta=guard(native(im),v,native_mask)
 mutant=out.copy();point=(650,150);r,g,b,a=mutant.getpixel(point);mutant.putpixel(point,(r^1,g,b,a));mutant_rejected=False
 try:guard(im,mutant,fullmask)
 except AssertionError as exc:mutant_rejected='outside physical cloth plane' in str(exc)
 assert mutant_rejected,'one RGB bit outside mask escaped guard'
 assert ImageChops.difference(im,out).getchannel('A').getextrema()==(0,0)
 return {'unit':unit,'old_master':pin(old),'plane':PLANE,'source_crop':CROP,'candidate':pin(d/'holding-source-candidate.png'),'native':pin(d/'holding-native-right.png'),'alpha_byte_exact':True,'outside_plane_rgb_byte_exact':True,'source_diff_bbox_RGB':delta.getbbox(),'native_diff_bbox_RGB':native_delta.getbbox(),'one_RGB_bit_outside_mutant_rejected':mutant_rejected,'RGB_only_inside_change_detected_with_zero_alpha_delta':True}
def main():
 REPORT.mkdir(parents=True,exist_ok=True)
 generations=[]
 for u in UNITS:
  d=SOURCE/u;generations.append({'unit':u,'provider_painted':pin(d/'painted-cloth-provider-v2.png'),'edit_target':pin(d/'cloth-edit-target-3x.png'),'prompt':pin(d/'channel-repair-prompt.txt'),'previous_painted_edit':pin(d/'painted-cloth-provider-v1.png'),'previous_prompt':pin(d/'cloth-prompt.txt'),'body_source':pin(PROJECT/'assets/source/creatures/painted-v2'/u/(UNITS[u][0]+'.png'))})
 write(SOURCE/'pilot-provenance.json',{'status':'authored configuration','scope':'two ordinary holding pilots only','provider':'OpenAI built-in imagegen','generations':generations,'technical_producer':pin(Path(__file__)),'identity':'Shurima regional Sun Disc; project gameplay affiliation for local nomads, no assertion of imperial allegiance','private_reference_url':'https://universe.leagueoflegends.com/images/shurima_crest_icon.png','private_reference_sha256':'4a49e2bdfa9d4ebf411585d6877239edb0425aa14db9e67af4e6390b29c2c365','private_reference_access_date':'2026-10-25','private_reference_pixels_redistributed':False,'visual_approval_granted':False,'native_execution':False})
 runs=[];records=[]
 for _ in range(2):
  records=[assemble(u) for u in UNITS];runs.append({p.relative_to(SOURCE).as_posix():sha(p) for u in UNITS for p in sorted((SOURCE/u).glob('holding-*.png'))})
 assert runs[0]==runs[1]
 rejected=False
 try:assemble('desertNomad','0'*64)
 except AssertionError:rejected=True
 assert rejected
 sys.path.insert(0,str(WORKSPACE/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima');compiled=[]
 for run in [1,2]:
  pins={}
  for u in UNITS:
   outputs,proof=compiler.plan(PROJECT,SOURCE/u/'holding-pilot-recipe.json');write(REPORT/f'pilot-compiler-{run}-{u}.json',proof)
   for name,data in outputs.items():
    path=REPORT/f'pilot-compiler-{run}'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
  compiled.append(pins)
 assert compiled[0]==compiled[1]
 board=Image.new('RGBA',(660,360),(45,45,45,255));draw=ImageDraw.Draw(board)
 for row,u in enumerate(UNITS):
  d=SOURCE/u;n=UNITS[u][0];old=native(Image.open(PROJECT/'assets/source/creatures/painted-v2'/u/(n+'.png')).convert('RGBA'))
  for col,im in enumerate([old,Image.open(d/'holding-native-right.png'),Image.open(d/'holding-native-left.png')]):
   board.alpha_composite(im.crop((145,175,260,285)),(col*220,row*180+30));draw.text((col*220+3,row*180+8),u+' '+['before','candidate R','candidate L'][col],fill='white')
 board.save(REPORT/'holding-pilots-native1x.png',compress_level=9)
 # Enlargement is review only; original native pixels above remain authoritative.
 board.resize((1320,720),Image.Resampling.NEAREST).save(REPORT/'holding-pilots-review2x.png',compress_level=9)
 write(REPORT/'pilot-technical-v1.json',{'status':'authored configuration','scope':'one ordinary holding pose per T1 variant; all other actions/consumers still pending','assembly_passes':2,'real_assembly_byte_exact':runs[0]==runs[1],'real_compiler_passes':2,'real_compiler_byte_exact':compiled[0]==compiled[1],'negative_old_master_hash_refused':rejected,'records':records,'output_hashes':compiled[0],'live_selection_changed':False,'native_window_used':False,'visual_approval_granted':False})
 print(json.dumps({'holding_pilots':2,'deterministic':True,'native_board_sha256':sha(REPORT/'holding-pilots-native1x.png')}))
if __name__=='__main__':main()
