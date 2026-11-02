"""Hand-authored NX1 native contour/entry plan. Candidate; no canonical edits.

Contours follow visible architectural masses, not bounding rectangles. Rear rose
portal is incidental city context. Left/right barrack frontage is deliberately
split at the central buttress; its hidden party walls still require art review.
"""
SIZE = (800, 374)
SITES = {
 'throneHall': dict(label='Imperial Seat', states=['villageHall','townHall','cityHall','capitol'], top='capitol', z=120,
  poly=[(302,58),(317,52),(319,41),(329,41),(329,49),(344,44),(354,43),(354,28),(359,27),(359,22),(363,23),(363,28),(367,29),(367,40),(386,37),(386,28),(393,27),(393,18),(400,17),(400,23),(413,21),(420,20),(420,16),(426,17),(426,34),(442,36),(454,35),(461,42),(478,44),(478,49),(491,50),(492,57),(507,60),(507,113),(476,117),(443,117),(425,121),(380,121),(360,118),(304,121)],
  door=(407,110),foot=[(304,108),(369,108),(383,112),(426,112),(443,108),(506,107),(506,121),(303,123)],
  variants={'villageHall':(326,66,154,54),'townHall':(319,48,170,72),'cityHall':(308,29,192,91)}),
 'crownBastion': dict(label='Noxian Bastion', states=['fort','citadel','castle'], top='castle', z=112,
  poly=[(649,45),(658,43),(660,27),(664,27),(664,16),(668,17),(670,12),(674,15),(679,16),(681,25),(687,29),(695,30),(700,29),(700,24),(704,25),(705,31),(716,29),(723,25),(724,18),(729,17),(732,13),(736,15),(740,23),(746,27),(750,37),(762,40),(764,101),(747,105),(713,110),(652,108)],
  door=(707,93),foot=[(651,96),(765,96),(768,111),(651,112)],variants={'fort':(656,50,106,59),'citadel':(653,30,112,79)}),
 'arcaneAthenaeum': dict(label='War College', states=['mageGuild1','mageGuild2','mageGuild3','mageGuild4'], top='mageGuild4', z=105,
  poly=[(20,65),(35,62),(36,45),(44,44),(46,36),(52,35),(52,4),(58,3),(67,1),(75,0),(83,2),(89,3),(90,29),(93,32),(94,47),(103,46),(107,40),(111,43),(112,62),(119,66),(121,78),(122,100),(93,104),(50,103),(20,107)],
  door=(68,96),foot=[(20,97),(121,96),(125,107),(17,108)],variants={'mageGuild1':(32,69,80,37),'mageGuild2':(27,47,88,59),'mageGuild3':(22,22,98,84)}),
 'blackRoseAcademy': dict(label='Black Rose Academy',states=['special1'],top='special1',z=109,
  poly=[(133,62),(145,61),(146,49),(154,45),(158,36),(164,42),(172,41),(177,36),(185,43),(190,47),(196,39),(201,44),(206,57),(214,60),(216,75),(225,81),(228,101),(194,106),(137,105)],door=(177,96),foot=[(135,96),(224,94),(228,108),(136,110)]),
 'arenaOfValor': dict(label='Arena of Valor',states=['special3'],top='special3',z=198,
  poly=[(4,128),(12,124),(12,115),(17,115),(18,105),(23,105),(24,119),(34,111),(43,110),(46,104),(66,101),(74,97),(88,97),(93,102),(113,101),(126,101),(139,105),(159,102),(163,108),(177,109),(180,113),(198,117),(203,113),(208,116),(209,128),(218,132),(223,146),(220,163),(217,177),(202,185),(182,191),(153,196),(109,201),(60,199),(25,187),(10,177),(4,160)],door=(104,187),foot=[(8,171),(48,183),(105,190),(160,183),(211,169),(217,180),(168,197),(67,202),(9,181)]),
 'dwellingMinotaur': dict(label='Minotaur Reckoning pit',states=['dwellingLvl6','dwellingUpLvl6'],top='dwellingUpLvl6',z=197,
  poly=[(213,151),(221,150),(221,140),(226,141),(229,146),(241,142),(254,139),(262,139),(264,134),(269,133),(270,139),(285,137),(302,140),(305,134),(309,137),(310,144),(324,148),(337,155),(341,165),(336,178),(326,185),(307,192),(277,197),(247,193),(219,184),(212,178)],door=(277,181),foot=[(213,174),(244,181),(277,185),(310,179),(338,168),(334,184),(281,199),(215,184)],variants={'dwellingLvl6':(223,145,109,48)}),
 'trifarianHall': dict(label='Trifarian Hall',states=['special2'],top='special2',z=216,
  poly=[(339,159),(351,156),(353,149),(377,146),(392,141),(397,130),(401,129),(402,137),(411,136),(411,131),(418,132),(418,139),(454,136),(463,131),(470,139),(478,144),(487,148),(511,153),(516,161),(522,161),(524,201),(509,206),(489,207),(483,214),(350,215),(338,208)],door=(429,199),foot=[(339,197),(523,193),(525,211),(487,215),(339,218)]),
 'crimsonCitadel': dict(label='Crimson Citadel storehouse',states=['resourceSilo'],top='resourceSilo',z=180,
  poly=[(516,117),(531,112),(531,105),(543,104),(555,100),(568,100),(572,95),(576,98),(593,101),(598,106),(615,111),(620,118),(622,164),(607,172),(566,178),(520,180)],door=(570,166),foot=[(519,162),(621,157),(624,169),(572,183),(520,182)]),
 'dwellingCrimson': dict(label='Crimson Circlehouse',states=['dwellingLvl5','dwellingUpLvl5'],top='dwellingUpLvl5',z=178,
  poly=[(640,141),(651,138),(652,130),(666,125),(675,122),(676,118),(681,116),(682,111),(687,114),(690,121),(707,124),(718,129),(721,136),(734,138),(736,172),(724,175),(643,178)],door=(686,166),foot=[(641,165),(735,161),(737,176),(642,181)],variants={'dwellingLvl5':(647,125,83,50)}),
 'dwellingLegion': dict(label='Veterans Barracks: left independent frontage',states=['dwellingLvl1','dwellingUpLvl1'],top='dwellingUpLvl1',z=248,
  poly=[(144,217),(160,208),(167,202),(178,200),(188,196),(195,191),(205,190),(214,185),(230,184),(235,187),(236,243),(220,247),(146,249)],door=(203,232),foot=[(145,237),(236,235),(237,248),(145,251)],variants={'dwellingLvl1':(150,197,84,51)}),
 'dwellingAxe': dict(label='Knife-Thrower Guild: right independent frontage',states=['dwellingLvl3','dwellingUpLvl3'],top='dwellingUpLvl3',z=249,
  poly=[(236,186),(250,186),(251,181),(256,182),(257,186),(277,185),(293,187),(297,190),(310,196),(314,201),(329,205),(332,221),(336,241),(318,247),(237,247)],door=(281,232),foot=[(237,237),(333,233),(337,247),(237,250)],variants={'dwellingLvl3':(242,197,88,51)}),
 'dwellingHound': dict(label='Drake-Hound pens',states=['dwellingLvl2','dwellingUpLvl2'],top='dwellingUpLvl2',z=241,
  poly=[(524,189),(535,186),(537,180),(543,181),(544,187),(555,184),(555,177),(562,176),(563,182),(580,179),(588,173),(596,176),(598,182),(616,184),(620,179),(625,182),(626,188),(639,190),(639,197),(651,199),(657,205),(653,229),(633,233),(614,239),(585,242),(555,236),(526,226)],door=(585,230),foot=[(526,218),(556,226),(585,233),(615,229),(652,217),(652,232),(587,244),(526,230)],variants={'dwellingLvl2':(534,185,113,53)}),
 'dwellingRose': dict(label='Brood Sentry pens',states=['dwellingLvl4','dwellingUpLvl4'],top='dwellingUpLvl4',z=243,
  poly=[(651,186),(659,183),(660,177),(665,179),(665,185),(681,180),(683,173),(688,175),(690,180),(706,174),(714,171),(720,166),(725,174),(739,173),(743,178),(754,178),(760,175),(766,178),(768,186),(779,190),(782,202),(788,205),(784,222),(778,237),(654,241)],door=(711,226),foot=[(653,222),(780,220),(781,240),(653,244)],variants={'dwellingLvl4':(658,183,117,55)}),
 'gildedCup': dict(label='Legion Tavern',states=['tavern'],top='tavern',z=343,
  poly=[(0,210),(22,211),(29,206),(35,210),(46,210),(61,207),(68,205),(77,204),(79,200),(83,205),(91,209),(102,220),(105,233),(116,233),(120,240),(126,242),(145,240),(151,248),(158,255),(165,261),(173,276),(176,288),(174,323),(159,332),(136,337),(103,343),(72,341),(48,344),(0,336)],door=(117,310),foot=[(0,323),(103,331),(173,314),(175,333),(107,347),(0,342)]),
 'grandMarket': dict(label='Campaign Market',states=['marketplace'],top='marketplace',z=338,
  poly=[(164,275),(170,268),(177,260),(183,251),(190,255),(203,260),(215,260),(224,262),(235,255),(244,249),(250,251),(255,257),(271,261),(285,266),(301,270),(317,274),(330,275),(341,279),(345,291),(356,304),(363,315),(351,325),(334,336),(296,337),(265,331),(221,332),(192,328),(169,327)],door=(264,319),foot=[(169,318),(217,323),(267,326),(306,325),(348,318),(357,330),(327,340),(268,336),(169,334)]),
 'foundry': dict(label='Legion Armory',states=['blacksmith'],top='blacksmith',z=355,
  poly=[(491,278),(501,270),(514,264),(535,251),(546,246),(558,239),(564,230),(569,229),(577,237),(587,240),(602,238),(615,242),(630,239),(636,232),(643,235),(648,244),(657,245),(670,248),(676,254),(698,261),(720,269),(725,280),(730,303),(736,314),(748,312),(756,318),(772,322),(792,332),(799,332),(799,373),(682,373),(681,354),(638,352),(606,354),(562,349),(523,344),(493,339)],door=(635,322),foot=[(494,328),(562,339),(637,342),(689,337),(733,326),(799,332),(799,373),(682,373),(681,360),(615,357),(493,346)]),
 'bindingRift': dict(label='Greater Binding Vault; T7 and support same plot',states=['special4','dwellingLvl7','dwellingUpLvl7'],top='dwellingUpLvl7',z=290,
  poly=[(718,251),(727,244),(732,235),(740,227),(749,224),(756,216),(761,217),(765,223),(777,229),(785,235),(789,246),(793,247),(794,273),(784,281),(755,286),(719,288)],door=(754,270),foot=[(719,273),(793,266),(794,282),(754,291),(719,291)],variants={'special4':(726,250,62,37),'dwellingLvl7':(723,230,67,57)}),
 'grail': dict(label='Three-principles monument',states=['grail'],top='grail',z=302,
  poly=[(388,228),(398,227),(407,216),(414,222),(420,230),(426,224),(434,221),(440,222),(439,232),(432,241),(432,249),(440,250),(445,247),(449,248),(452,254),(456,253),(456,273),(462,274),(469,283),(472,291),(465,297),(446,300),(407,302),(382,299),(367,291),(368,280),(384,275),(393,267),(393,246),(396,240),(389,235)],door=(421,292),foot=[(367,285),(399,289),(438,289),(472,283),(471,296),(446,304),(389,304),(366,296)])
}
ATLAS = {
 'civic-stages-v1': ['villageHall','townHall','cityHall','fort','citadel','mageGuild1','mageGuild2','mageGuild3'],
 'dwelling-stages-v1': ['dwellingLvl1','dwellingLvl2','dwellingLvl3','dwellingLvl4','dwellingLvl5','dwellingLvl6','special4','dwellingLvl7']
}
# 2 optional coast states have genuine source art but NO invented inland placement.
COAST_STATES = ['shipyard','ship']
UNRESOLVED = [
 'Approved inland NX1 has no coastal berth. shipyard/ship sources are preserved, but their placement and conditional coastal background require coordinator/user decision; do not integrate invisible or floating substitutes.',
 'Barrack/knife guild are visually one long master frontage. This source candidate assigns left/right wings at x236; independent upgraded party-wall/roof completion needs review. The exact approved full reconstruction does not establish independent-state completeness.',
 'Current Noxus authored contract contains17 ordinary plots, optional coast and Grail. Coordinator must explicitly retain that exception to generic16; no site was silently discarded.',
 'Rear rose portal remains incidental context; right foreground Greater Binding Vault alone owns special4/T7. This is an authored mapping proposal, not separately user-approved gameplay architecture.',
 'Adapted visible Noxian emblems derive from approved painting; exact official crest shape and rights remain external review.'
 ,'Short15px route masks currently intersect neighboring contours for War College/Academy/Circlehouse/Hound. Doors themselves are clear. The crowded approved painting does not prove complete independent external paths; resolve by contour/semantic review or coordinator-selected art change before integration.'
 ,'The empty plate is a contour-limited composite and still needs native visual review for residual incidental props, seams and perimeter context. Exact full reconstruction alone does not accept its empty or partial-build appearance.'
]
