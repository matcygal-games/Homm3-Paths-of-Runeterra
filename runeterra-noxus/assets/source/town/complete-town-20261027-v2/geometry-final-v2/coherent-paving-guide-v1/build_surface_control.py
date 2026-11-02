"""Background-only art edit regions, separate from immutable physical masks.
No building silhouette/root is used to derive an edit or protection region.
"""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageChops,ImageDraw,ImageFilter
G=Path(__file__).resolve().parent;R=G.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def masks(polys):
 im=Image.new('L',(800,374));d=ImageDraw.Draw(im)
 for p in polys:d.polygon(p,fill=255)
 return im
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def main():
 out=G/'paint-controls/revised-v3';base=Image.open(G/'paint-controls/horizontal-and-step-surface-interiors.png').convert('L');bg=Image.open(G/'reference/reference-empty-native.png').convert('RGBA')
 # Complete visible ground/court and retaining-masonry envelopes, read on
 # the EMPTY800x374reference, including all paving under future town layers.
 fields={
 'west_work_front_masonry_cap_and_face':[(0,199),(27,202),(54,206),(73,211),(75,216),(54,212),(27,208),(0,205)],
 'left_middle_perimeter_wall_faces':[(0,253),(52,242),(70,242),(84,250),(102,253),(137,262),(178,272),(204,278),(203,284),(179,283),(141,272),(107,264),(83,261),(65,254),(47,260),(0,271)],
 'hound_front_retaining_brick_faces':[(95,236),(140,236),(180,240),(210,245),(218,243),(225,247),(223,270),(211,270),(205,263),(177,261),(144,255),(111,251),(95,250)],
 'whole_rear_upper_plateau_and_retaining_cap':[(344,44),(412,41),(486,43),(534,50),(569,63),(590,78),(590,83),(551,84),(516,84),(474,83),(431,82),(402,78),(377,71),(345,66)],
 'whole_lower_main_avenue_and_side_masonry':[(350,277),(372,275),(385,289),(397,311),(409,327),(426,348),(452,369),(462,373),(345,373),(345,358),(353,345),(361,333),(366,317),(363,302),(353,289)],
 'upper_west_paving_and_retaining_masonry':[(25,84),(108,82),(165,85),(206,95),(243,103),(245,114),(197,123),(179,128),(146,130),(111,116),(77,105),(27,103)],
 'civic_west_work_court_and_front_cap':[(0,144),(67,143),(115,148),(164,159),(202,174),(212,191),(204,203),(162,211),(90,214),(73,207),(0,201)],
 'arena_full_court_under_future_source_and_masonry':[(185,162),(221,158),(281,159),(312,164),(327,176),(327,186),(334,215),(318,229),(294,240),(252,239),(220,230),(195,216),(183,197)],
 'menagerie_and_rift_frontage_complete_ground':[(439,158),(467,155),(518,157),(563,158),(600,164),(601,190),(614,199),(616,214),(578,224),(562,232),(551,239),(518,243),(479,240),(443,232),(416,222),(411,210),(420,196),(428,182)],
 'upper_east_quay_and_retaining_front':[(527,105),(665,105),(665,121),(704,125),(722,139),(772,148),(772,159),(731,163),(719,164),(682,172),(652,170),(617,162),(594,154),(550,157),(527,154)],
 'market_complete_court_and_retaining_masonry':[(544,196),(589,195),(628,196),(668,201),(705,210),(728,218),(727,231),(713,237),(684,244),(646,249),(613,245),(578,237),(551,227),(540,217)],
 'silo_whole_loading_quay_top_cap_face':[(639,234),(656,236),(683,238),(714,239),(744,238),(778,238),(778,264),(751,267),(716,270),(678,269),(655,270),(643,261)],
 'rift_lower_court_and_vertical_front':[(410,246),(444,242),(481,243),(522,242),(546,248),(560,255),(559,271),(552,280),(537,287),(505,291),(466,289),(440,285),(421,283),(410,270),(405,258)],
 'minotaur_whole_court_and_front_cap':[(431,291),(467,287),(506,288),(543,292),(576,301),(594,310),(591,335),(582,349),(556,357),(515,359),(481,354),(447,345),(430,336),(407,331),(408,319),(430,316)],
 'inn_upper_court_and_terrace_faces':[(18,271),(55,267),(91,267),(127,272),(163,281),(201,289),(230,301),(245,312),(235,332),(213,340),(177,344),(137,338),(101,326),(66,312),(35,302),(18,291)],
 'crimson_complete_court_and_masonry':[(242,281),(276,275),(311,277),(339,287),(351,301),(370,316),(391,321),(393,347),(368,356),(331,354),(297,349),(270,343),(246,332),(233,318),(236,301)],
 'hound_middle_court_and_retaining_front':[(85,203),(140,201),(199,208),(246,210),(281,203),(309,203),(328,210),(334,220),(320,232),(290,240),(244,250),(217,258),(202,264),(173,265),(133,258),(100,254),(85,245)]}
 retaining=json.loads((G/'retaining-geometry.json').read_text())['face_witness_polygons'];surface=ImageChops.lighter(base,masks(list(fields.values())+list(retaining.values())))
 # The two-pixel transition allowance comes from background material
 # boundaries, never from building roots or silhouettes.
 fringe=surface.filter(ImageFilter.MaxFilter(5));fringe=ImageChops.subtract(fringe,surface);surface=ImageChops.lighter(surface,fringe)
 nature={
 'academy_left_existing_nature':[(10,132),(26,129),(31,133),(31,147),(23,151),(10,150)],
 'arena_behind_torch_trees':[(181,173),(194,169),(211,177),(212,190),(202,197),(183,193)],
 'avenue_left_middle_trees':[(355,185),(370,184),(377,198),(375,219),(364,224),(356,212)],
 'menagerie_rear_left_greenery':[(440,153),(451,156),(453,168),(439,171),(436,164)],
 'upper_east_banked_nature':[(601,159),(618,168),(637,170),(658,173),(683,161),(700,161),(708,171),(719,177),(719,188),(707,199),(695,199),(674,194),(650,188),(624,181),(609,190),(601,182)],
 'coast_existing_cliff':[(704,163),(720,160),(735,166),(744,175),(751,190),(747,203),(733,206),(720,196),(711,183)],
 'rift_right_cypress_and_vegetation':[(565,238),(580,244),(589,254),(585,267),(578,279),(559,280),(557,269),(559,253)],
 'west_middle_court_tree_island':[(225,253),(235,251),(240,242),(249,241),(254,253),(265,250),(270,247),(279,248),(280,263),(268,266),(255,272),(241,275),(231,273),(224,268),(220,262)],
 'crimson_foreground_tree_island':[(246,329),(259,332),(277,338),(302,341),(326,337),(342,335),(350,340),(350,350),(336,356),(311,359),(282,358),(259,351),(247,342)],
 'minotaur_foundry_corner_nature':[(583,340),(590,337),(596,345),(594,357),(584,357)]}
 protected=masks(nature.values());d=ImageDraw.Draw(protected)
 props={'arena_brazier':[169,167,187,204],'avenue_upper_left_pier':[357,178,379,235],'avenue_middle_brazier':[339,235,361,280],'rift_left_pier':[402,231,427,262],'foundry_right_brazier':[775,308,795,335],'rear_bastion_left_torch':[386,66,405,111],'rear_bastion_middle_torch':[418,86,437,117],'rear_bastion_right_torch':[465,68,484,106],'rear_bastion_east_torch':[504,65,523,104],'upper_quay_torch':[710,105,730,129],'coast_quay_left_torch':[739,128,759,150],'coast_quay_right_torch':[758,137,778,158],'market_right_torch':[719,189,742,224]}
 for box in props.values():d.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=255)
 # Only the actual flame/bowl/pier stays immutable. The torch-lit road and
 # retaining-wall faces around it must receive the same whole-scene paint.
 foreground_prop=[(379,326),(381,330),(382,334),(386,336),(387,338),(383,341),(383,345),(385,347),(383,349),(374,349),(371,346),(373,342),(371,340),(370,338),(370,336),(375,334),(377,329)]
 d.polygon(foreground_prop,fill=255)
 surface=ImageChops.subtract(surface,protected)
 # Actual new constructed stairs remain edit surfaces within nature banks;
 # this is a source-proven construction exception, not generic water edit.
 links=json.loads((G/'five-required-links.json').read_text())['links'];constructed=Image.new('L',(800,374))
 for link in links:
  for key in('step_mask','landing_mask'):constructed=ImageChops.lighter(constructed,Image.open(R/link[key]['path']).convert('L'))
 surface=ImageChops.lighter(surface,constructed)
 visible_water=Image.open(G/'structural-contract/terrain-trace/water.png').convert('L');surface=ImageChops.subtract(surface,visible_water)
 # Sky and distant mountains/forest never enter the explicit surface fields.
 ImageDraw.Draw(surface).rectangle((0,0,799,39),fill=0)
 save(out/'paintable-whole-scene-surfaces.png',surface);save(out/'immutable-background-outside-surfaces.png',ImageChops.invert(surface));save(out/'nature-and-props-protected.png',protected);save(out/'bounded-transition-fringe.png',ImageChops.multiply(fringe,surface));save(out/'fixed-structural-walking-and-support-boundaries.png',ImageChops.subtract(base,base.filter(ImageFilter.MinFilter(3))))
 overlay=bg.copy();color=Image.new('RGBA',bg.size,(30,150,255,0));color.putalpha(surface.point(lambda a:135 if a else 0));overlay.alpha_composite(color);save(out/'editable-surface-overlay-native.png',overlay)
 isolated=bg.copy();isolated.putalpha(surface);save(out/'empty-background-surface-source-only.png',isolated)
 record={'status':'design proposal','source':ref(G/'reference/reference-empty-native.png'),'paintable_mask':ref(out/'paintable-whole-scene-surfaces.png'),'immutable_background_mask':ref(out/'immutable-background-outside-surfaces.png'),'protected_nature_props_mask':ref(out/'nature-and-props-protected.png'),'material_surface_envelopes':fields,'retaining_face_witnesses':retaining,'protected_nature_polygons':nature,'protected_prop_boxes':props,'transition_fringe_pixels':2,'all_paving_under_future_buildings_included':True,'building_masks_used_as_paint_exclusion':False,'floor_or_support_derived_from_root_masks':False,'physical_support_and_walking_masks_are_separate_and_unchanged':True,'paintable_includes':['Horizontal pavers/streets/workcourts, including underneath future buildings','Actual public flights and landings','Retaining masonry TOP/CAP/FACE inside bounded background-only envelopes','Bounded natural transition fringes, clipped to nature/prop/water protection'],'hard_geometry_constraints':'Exact original source contours, relative heights, five links, allexistingsteps and all36 town layers remain fixed; painting texture never authorizes new horizontal support or a new stair.','limitations':['This is a reviewable authored ART edit envelope, not a material/visual pass. Inspect native overlay before compositing.','Protected nature/prop envelopes are intentionally explicit; final composite must preserve exact pixels outside the approved mask.','The actual public structural positive does not approve the user-rejected reference appearance.']};(out/'SURFACE-CONTROL.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'surface_control':str(out/'SURFACE-CONTROL.json'),'sha256':sha(out/'SURFACE-CONTROL.json'),'editable_pixels':surface.histogram()[255],'does_not_subtract_buildings':True}))
if __name__=='__main__':main()
