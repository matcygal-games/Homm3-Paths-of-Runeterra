"""Freeze background-only V6 candidate trace; no building/root masks loaded."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import importlib.util,hashlib,json,argparse
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];TOWN=HERE.parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',default='final-v6-trace-v1');parser.add_argument('--terrain',default='terrain/final-native-v6.png');parser.add_argument('--sha256',default='0aced09755035e576e1f98010ee740096c27574190375277db7b573c9da0452d');parser.add_argument('--merged-repairs',action='store_true');parser.add_argument('--caps-v13',action='store_true');parser.add_argument('--broad-silo-v13b',action='store_true');parser.add_argument('--final-surfaces-v14',action='store_true');parser.add_argument('--descent-v14',action='store_true');args=parser.parse_args()
 if '/'in args.out or '\\'in args.out or args.out in ('.','..'):raise ValueError('Direct owned trace subdirectory required')
 OUT=HERE/args.out
 OUT.mkdir(parents=True,exist_ok=False)
 spec=importlib.util.spec_from_file_location('old_background_only',HERE/'trace_background.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
 floors=dict(old.FLOORS);stairs=dict(old.STAIRS)
 floors.pop('east_rear_connection',None) # Actual rock/vegetation, not paving.
 # Retaining faces are not stairs. College old flight is replaced by actual
 # new painted level paving; the retained Academy/upperwest flights are read anew.
 for key in ('east_rear_public_stair','college_public_stair','west_upper_public_stair','academy_public_stair','menagerie_public_stair','inn_front_public_stair','inn_avenue_public_stair','foundry_front_public_stair','rift_public_stair'):stairs.pop(key,None)
 stairs.update(academy_public_stair_v6=[(31,130),(65,130),(69,145),(31,146)],west_upper_public_stair_v6=[(148,112),(174,112),(179,127),(148,130)])
 floors.update(academy_horizontal_landing_v6=[(0,119),(30,117),(100,117),(100,130),(76,130),(30,129),(0,128)],academy_northwest_field_v6=[(0,114),(24,114),(24,131),(0,131)],academy_civic_paving_link_v6=[(78,126),(110,126),(112,146),(78,146)],civic_horizontal_court_v6=[(70,133),(225,133),(225,166),(70,166)],civic_college_paving_link_v6=[(210,130),(280,130),(280,160),(210,160)],college_horizontal_court_v6=[(235,130),(397,130),(397,161),(325,161),(325,177),(322,177),(322,162),(235,162)],menagerie_repaired_level_court_v6=[(440,169),(468,163),(594,164),(598,169),(598,197),(579,200),(478,200),(453,195),(440,180)],crimson_repaired_level_court_v6=[(252,309),(266,306),(311,306),(334,313),(352,317),(364,322),(352,330),(320,331),(281,330),(253,327),(245,319)],minotaur_bright_horizontal_cap_v5=[(439,336),(449,337),(461,341),(474,344),(486,346),(486,349),(474,348),(461,345),(449,342),(439,339)],martial_horizontal_quay_cap=[(710,150),(724,150),(724,158),(710,158)],tavern_repaired_floor_v6=[(0,315),(230,315),(230,373),(0,373)],foundry_repaired_floor_v6=[(595,327),(799,327),(799,373),(595,373)],foundry_left_horizontal_cap_v6=[(580,327),(605,327),(605,339),(580,339)],south_cross_avenue=[(365,368),(500,368),(500,373),(365,373)])
 floors['college_horizontal_court_v6']=[(235,130),(397,130),(397,177),(325,177),(325,162),(235,162)]
 # Direct native empty-source inspection shows the Rift forecourt continues
 # to its bright horizontal front cap at y283/284; the old conservative
 # interior stopped at y275/278. Its diagonal left curb joins the avenue
 # below the static pillar, not through that pillar.
 floors['rift_lower_court']=[(427,250),(451,249),(479,246),(519,245),(543,248),(554,255),(557,266),(553,276),(531,280),(495,284),(462,284),(438,282),(421,277),(411,269),(407,259),(417,258),(426,258)]
 floors['minotaur_bright_horizontal_cap_v5']=[(439,336),(449,337),(461,341),(486,345),(486,349),(472,349),(460,345),(449,342),(439,339)]
 if args.merged_repairs:
  floors.pop('central_public_avenue',None)
  floors['central_avenue_full_painted_width']=[(435,130),(455,130),(451,137),(446,145),(438,155),(427,165),(419,175),(415,185),(411,195),(403,201),(400,208),(401,215),(402,233),(401,245),(400,255),(403,262),(410,270),(419,281),(421,290),(426,300),(431,310),(439,323),(449,338),(460,348),(477,360),(492,373),(415,373),(405,356),(400,343),(399,327),(389,321),(383,313),(378,298),(375,280),(365,278),(360,269),(356,255),(353,245),(352,232),(356,223),(375,216),(377,197),(377,190),(371,181),(380,177),(390,169),(401,154),(411,145),(422,136)]
  floors['bastion_left_repaired_level_cap']=[(195,105),(271,105),(271,123),(258,127),(237,131),(215,132),(195,132)]
  floors['bastion_central_repaired_paved_landing']=[(390,134),(402,132),(425,132),(425,152),(390,152)]
  floors['bastion_east_repaired_level_plinth']=[(528,108),(665,108),(665,132),(648,132),(644,140),(626,145),(605,148),(578,151),(548,153),(528,153)]
  stairs.pop('east_upper_public_stair',None)
  stairs['bastion_east_relocated_public_flight']=[(650,139),(666,133),(669,135),(668,140),(646,148),(644,146)]
  floors['hound_repaired_horizontal_court']=[(86,204),(200,204),(200,239),(86,239)]
  stairs.pop('kennel_public_stair',None)
  stairs['hound_west_relocated_public_flight']=[(74,208),(85,208),(86,234),(76,235)]
  floors['silo_left_repaired_level_loading_court']=[(658,240),(711,240),(711,269),(658,269)]
  stairs.pop('silo_public_stair',None)
  stairs['silo_west_relocated_public_flight']=[(640,236),(652,236),(658,260),(647,263),(640,250)]
  floors['crimson_repaired_level_court_v6']=[(245,310),(260,306),(311,306),(337,310),(360,315),(366,322),(356,331),(319,332),(280,331),(251,328),(244,319)]
  floors['crimson_avenue_actual_paved_join']=[(350,318),(366,318),(380,320),(397,320),(397,323),(376,325),(350,325)]
  floors['rift_lower_court']=[(427,250),(451,249),(479,246),(519,245),(543,248),(554,255),(557,266),(553,276),(531,280),(495,284),(462,284),(438,282),(420,277),(410,269),(407,259),(417,258),(426,258)]
  floors['kennel_east_paved_exit_landing']=[(308,212),(331,209),(343,208),(349,201),(354,200),(355,208),(357,213),(355,222),(354,233),(350,233),(348,220),(322,221),(309,220)]
  floors['academy_east_existing_paved_margin']=[(74,129),(77,129),(77,149),(74,149)]
  floors['arena_left_repaired_level_landing']=[(185,195),(213,195),(213,217),(185,217)]
  floors['arena_front_repaired_horizontal_cap']=[(231,221),(298,221),(298,220),(319,220),(319,241),(231,241)]
  floors['v12_fort_right_genuine_paved_corner']=[(448,138),(481,138),(481,152),(448,152)]
  floors['v12_minotaur_genuine_west_apron']=[(430,316),(493,316),(493,353),(430,353)]
  floors['west_civic_court']=[(0,145),(80,145),(120,149),(210,159),(211,194),(195,203),(92,210),(74,207),(0,201)]
  floors['menagerie_market_continuous_pavers']=[(441,194),(599,194),(621,198),(621,209),(553,217),(440,216)]
  floors['rift_left_horizontal_cap']=[(408,263),(415,263),(421,272),(429,276),(427,279),(415,276),(408,268)]
  if args.caps_v13:
   floors['v13_silo_actual_right_horizontal_extension']=[(748,242),(772,242),(772,259),(748,259)]
   floors['v13_arena_actual_right_horizontal_cap']=[(320,220),(333,220),(333,228),(320,228)]
   floors['v13_rift_actual_paved_corner']=[(420,268),(440,268),(440,297),(420,297)]
   if args.broad_silo_v13b:floors['v13_silo_actual_right_horizontal_extension']=[(746,238),(778,238),(778,262),(746,262)]
  floors['rift_right_actual_horizontal_front_cap']=[(535,225),(548,228),(559,231),(561,233),(560,237),(545,237),(535,234)]
  if args.final_surfaces_v14:
   floors['v13_silo_actual_right_horizontal_extension']=[(746,238),(778,238),(778,258),(746,258)]
   floors['v13_rift_actual_paved_corner']=[(420,268),(440,268),(440,282),(420,282)]
   floors['rift_lower_court']=[(427,250),(451,249),(479,246),(519,245),(543,248),(554,255),(557,266),(553,276),(531,280),(495,282),(462,282),(438,282),(420,277),(410,269),(407,259),(417,258),(426,258)]
   floors['main_east_genuine_public_connector_landings']=[(414,168),(444,168),(444,185),(414,185)]
   stairs['main_east_genuine_public_flight']=[(423,177),(430,170),(432,170),(438,173),(436,175),(431,180),(428,181),(424,179)]
   stairs['academy_west_genuine_public_flight']=[(1,132),(7,132),(7,144),(1,144)]
   floors['academy_west_top_landing']=[(0,130),(9,130),(9,131),(0,131)]
   floors['academy_west_bottom_landing']=[(0,145),(9,145),(9,150),(7,151),(5,152),(3,153),(3,154),(0,154)]
  if args.descent_v14:
   stairs['east_genuine_descent_full_tread_strip']=[(665,166),(670,166),(673,179),(683,186),(691,197),(696,210),(690,210),(686,200),(679,193),(673,186),(668,180),(666,174)]
 def mask(polygons):
  im=Image.new('L',(800,374));draw=ImageDraw.Draw(im)
  for points in polygons:draw.polygon(points,fill=255)
  return im
 floor=mask(floors.values());step=mask(stairs.values());water=mask([old.WATER]);ImageDraw.Draw(water).rectangle((590,325,799,373),fill=0);land=ImageChops.invert(water);support=ImageChops.subtract(ImageChops.multiply(floor,land),step);walk=ImageChops.multiply(ImageChops.lighter(floor,step),land)
 if args.final_surfaces_v14:
  # Remove actual old retaining material before overlaying the genuine WEST
  # stairs/landings. The old Civic interior polygon was too broad here.
  for im in (support,walk):
   ImageDraw.Draw(im).rectangle((0,132,24,152),fill=0)
   ImageDraw.Draw(im).rectangle((420,283,440,297),fill=0)
   ImageDraw.Draw(im).polygon([(438,174),(444,174),(444,181),(430,182),(431,178),(435,176)],fill=0)
  west_floor=mask([floors['academy_west_top_landing'],floors['academy_west_bottom_landing']]);west_steps=mask([stairs['academy_west_genuine_public_flight']]);support=ImageChops.lighter(support,west_floor);walk=ImageChops.lighter(walk,ImageChops.lighter(west_floor,west_steps))
 # Exclude a visible static background torch stand, never presume it level.
 for image in (support,walk):ImageDraw.Draw(image).rectangle((780,327,790,331),fill=0)
 source=TOWN/args.terrain;assert sha(source)==args.sha256
 if args.merged_repairs:
  obstacles=[[(358,186),(377,186),(377,234),(358,234)],[(340,237),(360,237),(360,279),(340,279)],[(402,233),(426,233),(426,261),(402,261)],[(427,276),(433,276),(439,283),(438,289),(446,290),(448,303),(444,307),(450,313),(446,315),(431,303),(424,291),(421,286)],[(376,322),(389,321),(397,330),(397,350),(409,355),(406,361),(388,360),(377,354)],[(450,138),(459,133),(474,138),(477,153),(464,156),(452,162),(442,159),(443,145)]]
  nonlevel=mask(obstacles)
  # V12 replaces the actual corner face with genuine horizontal pavers.
  ImageDraw.Draw(nonlevel).rectangle((448,138,481,152),fill=0)
  # The Rift upper court/cap lies behind the lower foreground torch.
  # Its horizontal upper band ends before the retaining front below y282.
  ImageDraw.Draw(nonlevel).rectangle((427,276,437,281),fill=0)
  if args.caps_v13:ImageDraw.Draw(nonlevel).rectangle((420,268,440,297),fill=0)
  support=ImageChops.subtract(support,nonlevel);walk=ImageChops.subtract(walk,nonlevel)
 for name,image in [('support',support),('stairs',step),('water',water),('land',land),('walkable-plane',walk)]:image.save(OUT/(name+'.png'),compress_level=9)
 record={'status':'authored configuration','source':{'path':source.relative_to(ROOT).as_posix(),'sha256':sha(source)},'scope':'Independently read actual background floor/stair/paver interiors. Source-only trace imports no building, entry or root masks. Conservative unclassified boundaries remain unknown; false old eastfront-stair label removed as retaining face.','level_floor_polygons':floors,'public_stair_polygons':stairs,'water_polygon_history':old.WATER,'actual_new_foreground_foundry_dryland_rectangle':[590,325,800,374],'fixed_background_torch_exclusion':[780,327,790,331],'script_sha256':sha(Path(__file__)),'native_verified':False}
 (OUT/'background-plane-trace-v6.json').write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps({'trace':str(OUT),'background_sha256':sha(source),'floors':len(floors),'stairs':len(stairs)}))
if __name__=='__main__':main()
