"""Source-measured, guarded graphics-only offset proposal; no content writes."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import hashlib,json
import assemble_packets as common
S=common.SOURCE;P=common.PROJECT;R=common.REPORT/'heraldry-v1';payload=S/'recipe-payload-heraldry-v1'
# Manual release landmarks read from the final native climax4 detail view, not
# guesses about raw master dimensions. Two-pixel uncertainty remains explicit.
LANDMARKS={
 'shurimanArcher':[(223,201),(226,209),(223,217)],
 'sunArcher':[(222,217),(229,220),(226,224)],
 'sunPriest':[(226,195),(227,207),(228,231)],
 'highPriest':[(225,195),(230,208),(229,230)]}
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
 content=load(P/'content/creatures.json');rows=[];patch=[]
 board=Image.new('RGBA',(1200,2000),(35,35,35,255));draw=ImageDraw.Draw(board)
 for i,(u,points) in enumerate(LANDMARKS.items()):
  battle=load(payload/u/'battle.json');groups={g['group']:g['frames'] for g in battle['groups']};offset=content[u]['graphics']['missile']['offset'];candidate={}
  for j,(prefix,g,(x,y)) in enumerate(zip(('upper','middle','lower'),(14,15,16),points)):
   source=P/groups[g][3]['source'];im=Image.open(source).convert('RGBA');bg=common.checkbg(im.size);bg.alpha_composite(im);d=ImageDraw.Draw(bg)
   old=(197+offset[prefix+'X'],265+offset[prefix+'Y']);balanced=round(x-199.5);right=round(x-197);yy=y-265;candidate.update({prefix+'X':balanced,prefix+'Y':yy})
   # Diagnostic markers only; these are never production sprites or source art.
   for point,color in (((x,y),'yellow'),(old,'red'),((197+balanced,265+yy),'cyan')):
    xx,yy0=point;d.line((xx-2,yy0,xx+2,yy0),fill=color);d.line((xx,yy0-2,xx,yy0+2),fill=color)
   crop=bg.crop((155,160,265,285)).resize((396,450),Image.Resampling.NEAREST);board.paste(crop,(j*400,i*500+25));draw.text((j*400+2,i*500+2),u+' '+prefix+' yellow=landmark red=current cyan=balanced',fill='white')
   rows.append({'unit':u,'group':g,'climax_one_based':4,'frame_zero_based':3,'source':common.descriptor(source),'manual_native_release_landmark':[x,y],'manual_uncertainty_px':2,'current_offset':{prefix+'X':offset[prefix+'X'],prefix+'Y':offset[prefix+'Y']},'current_local_origin_right':old,'current_origin_minus_landmark_right':[old[0]-x,old[1]-y],'current_local_origin_left':[247-offset[prefix+'X'],265+offset[prefix+'Y']],'native_full_canvas_mirrored_landmark':[449-x,y],'balanced_facing_offset_proposal':{prefix+'X':balanced,prefix+'Y':yy},'balanced_right_error':[197+balanced-x,0],'balanced_left_error':[(247-balanced)-(449-x),0],'right_only_offset_proposal':{prefix+'X':right,prefix+'Y':yy}})
  patch.append({'unit':u,'json_pointer':'/'+u+'/graphics/missile/offset','before':offset,'after_balanced_design_proposal':candidate,'apply_only_after_native_shooting_review':True})
 authority={}
 for name in ('BattleAnimationClasses.cpp','BattleStacksController.cpp','CreatureAnimation.cpp'):
  path=P.parent/'vcmi-develop/vcmi-develop/client/battle'/name;authority[path.relative_to(P.parent).as_posix()]=common.sha(path)
 result={'status':'design proposal','content_changed':False,'content_guard_sha256':common.sha(P/'content/creatures.json'),'scope':'four shooter graphics offsets only; no shots, damage, bonuses or projectile count changes','authority':authority,'formula_right_local':[197,'+offsetX',265,'+offsetY'],'formula_left_local':[247,'-offsetX',265,'+offsetY'],'full450_canvas_mirror':'x -> 449-x','inherent_shared_engine_origin_difference_px':5,'balanced_choice':'minimize maximum left/right source error: offsetX=round(nativeX-199.5); native test must assess the remaining2/3px and manual2px uncertainty','actual_source_landmarks':rows,'guarded_patch_proposal':patch,'native_execution':False,'runtime_verified':False,'required_native_checks':['actual climax4 arrow/pellet release up/front/down on both facings','confirm geometry against stack native position, not review-image crop','no duplicate physical shot, infinite pause or creature-casting substitution'],'diagnostic_markers_are_review_only':True}
 common.png(R/'projectile-origin-diagnostic-v1.png',board);common.put(R/'graphics-offset-proposal-v1.json',result)
 print(json.dumps({'manual_source_landmarks':len(rows),'content_changed':False,'status':'design proposal'}))
if __name__=='__main__':main()
