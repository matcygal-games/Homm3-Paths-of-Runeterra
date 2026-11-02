"""Whole-master geometry, traced after the coordinator's complete-city checkpoint.

These projected outlines describe painted source pixels, never procedural art.
The selected city master establishes the streets, doors and building identities.
"""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageOps

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/complete-town-20261027-v2'
MASTER=HERE/'complete-city-master-v2.png'
CANVAS=(800,374)

# Source traces in the approved whole-city 800x374 projection. Courtyard street
# terrain and retaining support remain separate fixed landscape. Rear architecture
# may be deliberately occluded by nearer institutions; genuine reconstruction is
# required for those hidden surfaces, not an old isolated building substitute.
SITES={
 'throneHall':{'states':['villageHall','townHall','cityHall','capitol'],'top':'capitol','rect':[77,16,142,147],'door':[163,153],'z':163,'poly':[(82,58),(107,50),(116,36),(127,34),(128,17),(141,16),(145,44),(154,51),(166,52),(174,68),(185,75),(202,85),(211,98),(212,125),(219,129),(214,141),(199,146),(183,153),(169,162),(151,155),(145,150),(127,148),(112,144),(89,144),(78,134),(75,122),(78,102),(81,94)]},
 'crownBastion':{'states':['fort','citadel','castle'],'top':'castle','rect':[202,3,443,146],'door':[439,144],'z':149,'poly':[(207,75),(218,68),(220,47),(247,43),(263,38),(280,29),(294,26),(295,21),(308,20),(309,30),(318,25),(321,20),(332,18),(335,22),(345,20),(346,12),(357,11),(360,21),(368,20),(374,10),(383,5),(395,6),(403,14),(406,24),(416,22),(420,19),(429,22),(437,21),(441,14),(450,13),(458,19),(462,26),(472,19),(473,13),(482,11),(489,13),(491,5),(503,4),(512,13),(514,22),(526,25),(533,25),(536,21),(546,24),(549,29),(561,27),(568,29),(577,31),(581,28),(589,38),(600,39),(605,36),(615,39),(619,44),(628,47),(633,73),(643,78),(644,105),(627,116),(602,114),(584,110),(566,108),(545,104),(532,104),(526,112),(507,116),(492,119),(472,122),(457,126),(449,138),(441,148),(429,147),(422,137),(426,129),(431,124),(424,115),(403,113),(389,111),(379,116),(366,117),(350,110),(327,111),(306,108),(290,106),(270,106),(249,109),(229,106),(218,99),(211,89)]},
 'arcaneAthenaeum':{'states':['mageGuild1','mageGuild2','mageGuild3','mageGuild4'],'top':'mageGuild4','rect':[240,56,146,103],'door':[326,149],'z':159,'poly':[(243,101),(250,92),(253,82),(258,78),(260,67),(267,62),(270,56),(278,61),(281,70),(284,73),(290,71),(296,65),(301,68),(305,56),(311,52),(317,61),(319,71),(327,71),(333,67),(335,60),(342,57),(349,64),(351,79),(357,81),(364,93),(375,98),(380,111),(380,133),(385,142),(381,149),(366,155),(351,154),(341,154),(329,157),(315,155),(304,150),(287,147),(273,147),(258,145),(246,138),(240,126)]},
 'dwellingLegion':{'states':['dwellingLvl1','dwellingUpLvl1'],'top':'dwellingUpLvl1','rect':[583,99,119,77],'door':[639,166],'z':176,'poly':[(586,112),(595,105),(607,105),(611,99),(622,100),(629,104),(638,102),(640,106),(652,104),(662,108),(673,107),(684,111),(686,117),(694,123),(700,130),(700,157),(694,168),(679,173),(660,174),(646,170),(635,172),(622,170),(608,169),(592,164),(584,154),(583,134)]},
 'dwellingHound':{'states':['dwellingLvl2','dwellingUpLvl2'],'top':'dwellingUpLvl2','rect':[89,162,106,72],'door':[137,229],'z':234,'poly':[(94,176),(103,168),(114,163),(130,166),(145,162),(157,167),(169,168),(183,175),(188,184),(190,199),(194,209),(191,219),(181,224),(169,229),(155,232),(141,231),(124,230),(111,225),(99,221),(91,216),(89,202)]},
 'dwellingAxe':{'states':['dwellingLvl3','dwellingUpLvl3'],'top':'dwellingUpLvl3','rect':[4,126,104,76],'door':[57,193],'z':202,'poly':[(10,147),(17,138),(21,132),(32,128),(44,131),(51,126),(61,132),(65,143),(74,147),(87,145),(101,150),(106,162),(106,181),(97,188),(83,194),(64,199),(51,201),(39,197),(24,193),(10,190),(4,181),(5,164)]},
 'dwellingRose':{'states':['dwellingLvl4','dwellingUpLvl4'],'top':'dwellingUpLvl4','rect':[465,104,118,92],'door':[525,188],'z':196,'poly':[(470,126),(476,114),(487,111),(496,105),(509,111),(521,107),(529,112),(542,109),(549,115),(559,114),(571,124),(579,136),(582,156),(578,174),(573,183),(563,189),(547,194),(532,192),(515,190),(499,187),(483,179),(471,173),(465,159)]},
 'dwellingCrimson':{'states':['dwellingLvl5','dwellingUpLvl5'],'top':'dwellingUpLvl5','rect':[245,227,111,103],'door':[308,318],'z':330,'poly':[(251,254),(257,245),(270,240),(279,239),(284,228),(293,233),(299,245),(307,238),(314,243),(321,252),(333,257),(339,267),(348,276),(350,298),(355,307),(350,318),(337,324),(321,326),(308,329),(293,326),(276,323),(263,318),(249,314),(245,298)]},
 'dwellingMinotaur':{'states':['dwellingLvl6','dwellingUpLvl6'],'top':'dwellingUpLvl6','rect':[433,266,152,83],'door':[548,341],'z':349,'poly':[(438,287),(447,278),(459,272),(474,274),(484,268),(496,271),(510,266),(521,274),(533,273),(546,280),(557,277),(569,284),(579,292),(582,306),(581,325),(585,332),(575,341),(559,344),(542,345),(526,347),(507,348),(489,346),(471,344),(454,339),(439,335),(433,322),(434,306)]},
 'bindingRift':{'states':['special4','dwellingLvl7','dwellingUpLvl7'],'top':'dwellingUpLvl7','rect':[414,159,126,103],'door':[480,251],'z':262,'poly':[(420,194),(429,186),(433,175),(444,174),(451,164),(462,168),(470,159),(480,164),(490,175),(503,178),(510,184),(522,190),(528,202),(531,218),(539,231),(538,244),(526,251),(514,255),(496,260),(479,261),(461,259),(446,254),(428,248),(416,240),(414,221)]},
 'gildedCup':{'states':['tavern'],'top':'tavern','rect':[7,208,220,150],'door':[180,346],'z':358,'poly':[(16,256),(28,246),(34,235),(45,228),(56,231),(66,225),(80,221),(87,212),(98,212),(106,220),(117,218),(125,225),(137,226),(151,234),(163,236),(172,245),(186,246),(194,257),(207,261),(215,272),(221,286),(224,308),(227,319),(221,331),(208,338),(194,345),(176,348),(160,351),(142,355),(123,355),(104,350),(85,348),(67,344),(49,339),(32,337),(17,329),(8,317),(7,299),(11,279)]},
 'grandMarket':{'states':['marketplace'],'top':'marketplace','rect':[536,176,135,77],'door':[600,246],'z':253,'poly':[(539,209),(546,198),(555,192),(564,191),(569,184),(579,187),(585,179),(593,184),(602,181),(613,186),(620,184),(629,192),(637,190),(646,201),(656,200),(663,210),(670,218),(669,232),(663,241),(652,246),(636,249),(621,250),(605,253),(591,250),(575,248),(560,246),(547,240),(537,232)]},
 'foundry':{'states':['blacksmith'],'top':'blacksmith','rect':[577,253,220,104],'door':[691,346],'z':357,'poly':[(583,285),(591,276),(605,272),(615,267),(626,272),(635,268),(644,258),(655,253),(664,261),(672,269),(685,269),(698,275),(709,277),(721,283),(736,283),(747,292),(761,290),(773,299),(786,303),(794,316),(796,333),(789,345),(774,349),(758,351),(740,354),(722,355),(704,357),(687,355),(668,352),(651,350),(634,346),(615,343),(601,338),(586,333),(578,321),(577,303)]},
 'crimsonCitadel':{'states':['resourceSilo'],'top':'resourceSilo','rect':[630,178,106,89],'door':[654,260],'z':267,'poly':[(634,208),(645,202),(652,196),(658,185),(669,179),(682,178),(694,183),(702,193),(704,215),(715,219),(726,228),(734,241),(735,254),(725,261),(709,265),(695,266),(678,265),(662,261),(647,258),(632,251),(630,234)]},
 'blackRoseAcademy':{'states':['special1'],'top':'special1','rect':[4,44,75,86],'door':[60,123],'z':130,'poly':[(8,78),(14,71),(18,60),(24,58),(28,48),(36,44),(43,51),(47,58),(54,61),(61,70),(66,80),(70,87),(72,105),(78,113),(73,121),(64,126),(51,129),(40,128),(29,125),(17,121),(7,115),(4,100)]},
 'trifarianHall':{'states':['special2'],'top':'special2','rect':[683,115,69,59],'door':[718,170],'z':174,'poly':[(687,136),(693,129),(699,125),(705,118),(713,115),(720,121),(725,125),(733,125),(739,132),(744,137),(750,146),(751,157),(748,166),(737,171),(723,173),(708,171),(696,168),(685,164),(683,151)]},
 'arenaOfValor':{'states':['special3'],'top':'special3','rect':[190,148,151,90],'door':[272,231],'z':238,'poly':[(196,178),(203,169),(215,162),(228,155),(244,150),(260,148),(276,149),(290,152),(305,157),(319,164),(331,173),(337,185),(340,201),(338,215),(329,223),(315,229),(300,232),(283,236),(267,237),(249,235),(231,232),(215,228),(201,224),(192,216),(190,199)]},
}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 native=ImageOps.fit(Image.open(MASTER).convert('RGB'),CANVAS,method=Image.Resampling.LANCZOS)
 native.save(HERE/'complete-city-native.png')
 records=[]
 for site,entry in SITES.items():
  x,y,w,h=entry['rect'];folder=HERE/'reference-crops'/site;folder.mkdir(parents=True,exist_ok=True)
  native.crop((x,y,x+w,y+h)).resize((w*4,h*4),Image.Resampling.NEAREST).save(folder/'master-native-context-4x.png')
  # The high-resolution source crop is the creative variant reference. It is a
  # whole-city image crop, not accepted transparent architecture or a final mask.
  box=(round(x*Image.open(MASTER).width/800),round(y*Image.open(MASTER).height/374),round((x+w)*Image.open(MASTER).width/800),round((y+h)*Image.open(MASTER).height/374))
  Image.open(MASTER).crop(box).save(folder/'master-context.png')
  records.append({'site':site,**entry,'source_crop':str((folder/'master-context.png').relative_to(ROOT)).replace('\\','/'),'source_crop_sha256':sha(folder/'master-context.png')})
 (HERE/'whole-city-site-plan.json').write_text(json.dumps({'status':'authored configuration','whole_master_sha256':sha(MASTER),'canvas':list(CANVAS),'geometry_basis':'Actual approved complete master, traced after source-design checkpoint. Not the rejected V1 placement.','sites':records,'optional_coast':{'rect':[746,121,53,68],'door':[750,161]},'grail':{'rect':[393,123,19,24],'door':[402,146]},'native_verified':False,'release_accepted':False},indent=2)+'\n')
 board=native.copy();d=ImageDraw.Draw(board)
 for i,(site,entry) in enumerate(SITES.items(),1):
  d.line(entry['poly']+[entry['poly'][0]],fill=(255,225,110),width=1);x,y=entry['door'];d.ellipse((x-2,y-2,x+2,y+2),fill=(20,255,220));d.text((entry['rect'][0]+3,entry['rect'][1]+3),str(i),fill=(255,255,240))
 board.save(REPORT/'whole-city-actual-silhouettes-and-doors.png')
 print(json.dumps({'sites':len(SITES),'states':sum(len(e['states']) for e in SITES.values()),'new_source_layout':True,'master_sha256':sha(MASTER)}))

if __name__=='__main__':main()
