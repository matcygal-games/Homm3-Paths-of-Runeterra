"""Independently trace frozen V5 background floors; no building/root masks imported."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import hashlib,json
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[4]; REPORT=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2'
SOURCE=HERE.parent/'terrain/final-native-v5.png'
FLOORS={
'rear_upper_court':[(343,45),(410,43),(489,46),(522,54),(551,69),(574,77),(542,79),(473,81),(432,79),(405,77),(379,71),(347,62)],
'upper_west_court':[(28,91),(110,85),(158,87),(212,100),(243,105),(245,110),(188,111),(170,109),(147,106),(113,102),(80,99),(31,100)],
'academy_landing':[(25,119),(54,116),(77,118),(78,124),(74,130),(24,129)],
'west_civic_court':[(1,147),(32,146),(68,149),(109,153),(151,163),(180,169),(195,175),(204,184),(206,196),(172,203),(137,206),(91,205),(45,202),(1,198)],
'college_court':[(242,110),(278,104),(322,104),(360,110),(377,116),(379,126),(401,132),(408,137),(395,143),(368,146),(332,146),(299,143),(272,142),(239,142),(234,137),(254,127),(261,122),(246,119)],
'arena_court':[(207,161),(242,158),(280,161),(306,167),(322,175),(326,182),(315,186),(284,187),(244,184),(211,179),(197,172)],
'kennel_court':[(107,216),(150,210),(199,214),(240,213),(281,207),(307,205),(319,211),(319,220),(295,226),(265,233),(229,236),(188,236),(145,231),(111,222)],
'menagerie_court':[(455,139),(481,136),(517,134),(547,137),(569,145),(574,154),(557,160),(532,162),(503,159),(474,153),(455,148)],
'east_upper_court':[(606,129),(634,123),(667,124),(693,128),(713,136),(719,146),(710,156),(684,164),(654,166),(623,159),(596,152),(593,146)],
'martial_quay':[(721,150),(767,149),(771,153),(771,158),(719,158)],
'rift_upper_court':[(417,212),(439,205),(466,201),(501,201),(535,205),(551,212),(542,226),(520,233),(490,235),(458,231),(432,225),(417,220)],
'rift_lower_court':[(420,254),(449,252),(481,250),(517,249),(549,253),(552,264),(542,271),(509,275),(473,278),(438,276),(419,268)],
'market_court':[(553,206),(589,199),(623,200),(661,204),(699,210),(723,217),(727,225),(714,230),(680,239),(648,243),(616,241),(579,233),(551,225),(541,218)],
'silo_lower_quay':[(700,245),(717,244),(737,246),(757,251),(770,257),(770,261),(753,264),(732,261),(711,258),(698,253)],
'inn_court':[(21,278),(56,271),(90,270),(121,274),(151,282),(184,289),(209,296),(235,306),(243,314),(232,321),(211,324),(181,324),(148,322),(111,313),(77,305),(48,297),(22,291)],
'crimson_court':[(247,286),(274,280),(305,280),(326,286),(338,292),(341,301),(328,308),(302,313),(276,310),(252,303),(241,294)],
'minotaur_upper_court':[(436,297),(464,292),(495,292),(532,297),(568,304),(590,312),(588,316),(569,320),(531,324),(494,324),(458,318),(434,310)],
'minotaur_painted_apron_v5':[(408,319),(434,318),(463,320),(492,322),(525,323),(554,322),(583,319),(589,322),(588,338),(577,345),(548,351),(515,352),(483,347),(453,341),(430,334),(408,330)],
'foundry_court':[(600,279),(633,273),(672,275),(714,282),(745,294),(769,305),(782,315),(782,326),(771,332),(742,338),(701,340),(663,335),(629,328),(600,320),(592,312),(593,298)],
'inn_lower_avenue':[(0,367),(44,354),(75,350),(101,351),(133,350),(164,348),(183,349),(207,358),(235,365),(268,365),(286,361),(320,361),(351,352),(367,351),(384,358),(397,374),(0,374)],
'forecourt_east_avenue':[(401,354),(426,351),(449,352),(480,359),(517,363),(557,362),(590,354),(613,350),(625,352),(627,359),(641,374),(406,374)],
'east_foreground_avenue':[(658,354),(682,353),(713,352),(750,349),(779,341),(799,341),(799,374),(674,374),(665,364)],
'central_public_avenue':[(437,132),(457,132),(442,160),(422,191),(409,213),(404,240),(411,263),(421,284),(431,307),(437,329),(448,347),(455,354),(448,361),(431,358),(416,341),(404,321),(391,294),(376,272),(362,257),(353,241),(358,219),(371,199),(391,173),(413,147)],
'west_middle_connection':[(94,238),(108,235),(126,240),(151,242),(178,246),(198,252),(205,259),(199,264),(176,263),(146,257),(120,253),(99,250)],
'crimson_rear_connection':[(280,269),(307,264),(330,264),(345,270),(353,280),(350,291),(338,293),(325,283),(301,280),(282,278)],
'east_rear_connection':[(608,173),(624,176),(649,181),(674,184),(702,188),(720,196),(717,202),(693,198),(663,192),(634,188),(617,186),(607,181)]
}
STAIRS={
'academy_public_stair':[(26,131),(78,131),(77,145),(27,145)],
'west_upper_public_stair':[(148,113),(176,113),(194,143),(169,144)],
'bastion_public_stair':[(435,86),(461,86),(456,129),(431,129)],
'college_public_stair':[(355,150),(368,148),(384,171),(374,177)],
'arena_public_stair':[(303,194),(318,193),(333,214),(320,219)],
'kennel_public_stair':[(75,211),(89,211),(103,237),(94,241)],
'menagerie_public_stair':[(558,171),(576,171),(593,193),(579,199)],
'east_upper_public_stair':[(584,123),(602,123),(616,141),(601,145)],
'east_rear_public_stair':[(623,168),(635,168),(647,185),(635,189)],
'rift_public_stair':[(465,237),(482,236),(498,247),(482,250)],
'silo_public_stair':[(671,243),(687,243),(699,266),(684,271)],
'inn_rear_public_stair':[(198,260),(210,259),(224,277),(211,281)],
'inn_front_public_stair':[(126,328),(157,325),(164,347),(136,352)],
'inn_avenue_public_stair':[(174,348),(187,347),(207,369),(193,373)],
'foundry_front_public_stair':[(624,348),(640,348),(663,369),(650,373)]
}
WATER=[(736,85),(752,105),(752,127),(773,146),(780,157),(769,162),(744,163),(744,170),(753,178),(753,190),(763,208),(775,226),(783,246),(790,266),(799,287),(799,373),(799,85)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def mask(polys):
 m=Image.new('L',(800,374));d=ImageDraw.Draw(m)
 for p in polys:d.polygon(p,fill=255)
 return m
def main():
 assert sha(SOURCE)=='d068f192b852110ee774592541855527e91904027b38f3733fe93eaf4f126017'
 floors=mask(FLOORS.values());stairs=mask(STAIRS.values());water=mask([WATER]);land=ImageChops.invert(water);support=ImageChops.subtract(ImageChops.multiply(floors,land),stairs);walkable=ImageChops.multiply(ImageChops.lighter(floors,stairs),land)
 for name,m in [('support',support),('stairs',stairs),('water',water),('land',land),('walkable-plane',walkable)]:m.save(HERE/(name+'.png'))
 record={'status':'authored configuration','source':{'path':SOURCE.relative_to(ROOT).as_posix(),'sha256':sha(SOURCE)},'scope':'Current V5 background only. Vertices independently read from native/grid enlarged empty source; no building source, root or semantic-zone mask loaded. Unknown pixels excluded. Levels use actual horizontal paving; stairs excluded from support, included in walking. LAND is only external-water complement and never implies floor.','level_floor_polygons':[{'id':k,'vertices':v} for k,v in FLOORS.items()],'public_stair_flight_polygons':[{'id':k,'vertices':v} for k,v in STAIRS.items()],'water_polygon':WATER,'native_executed':False,'architectural_acceptance':False,'script_sha256':sha(Path(__file__))}
 write(HERE/'background-plane-trace-v5.json',record)
 im=Image.open(SOURCE).convert('RGBA')
 for m,c in [(support,(0,255,80)),(stairs,(255,40,20)),(water,(0,80,255))]:t=Image.new('RGBA',im.size,(*c,0));t.putalpha(m.point(lambda a:90 if a else 0));im.alpha_composite(t)
 im.save(REPORT/'background-floor-stair-trace-v5.png')
 print(json.dumps({'source_sha256':sha(SOURCE),'floor_planes':len(FLOORS),'stair_flights':len(STAIRS),'support_pixels':support.histogram()[255],'walkable_pixels':walkable.histogram()[255]}))
if __name__=='__main__':main()
