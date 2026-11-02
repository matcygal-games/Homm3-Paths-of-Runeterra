"""Individually classified native wall/plinth/stair-foot endpoints.

These supplement the manually traced contours, preserving complete little feet
at line butt-caps and irregular step corners. Coordinates were inspected against
the actual native state boards; they are not a blanket opaque-column exemption.
The separate eave list is independently checkable against the selected pixels.
"""
GROUND_POINTS={
 'villageHall':[(98,156),(99,156),(100,157),(196,160),(197,159)],
 'townHall':[(90,160),(91,160),(92,160),(93,160),(205,162),(206,162)],
 'cityHall':[(81,157),(82,157),(83,157),(213,160)],
 'capitol':[(77,143),(78,147),(217,150),(218,149)],
 'fort':[(228,131),(229,131),(617,134)],
 'citadel':[(257,134),(258,135),(587,137),(588,137)],
 'castle':[(202,115),(203,115),(643,116),(644,115)],
 'mageGuild1':[(275,153),(350,154)],
 'mageGuild2':[(261,150),(262,151)],
 'mageGuild3':[(247,151),(248,151),(377,154)],
 'mageGuild4':[(241,146),(384,152),(385,151)],
 'dwellingLvl1':[(590,161)],
 'dwellingUpLvl1':[(584,157),(700,163)],
 'dwellingLvl2':[(95,223),(186,223),(187,223)],
 'dwellingUpLvl2':[(89,213),(90,213),(91,214),(92,214),(93,214),(192,226),(193,225)],
 'dwellingLvl3':[(10,187),(39,196)],
 'dwellingUpLvl3':[(38,188),(39,188),(40,189),(45,192),(46,193),(47,193),(48,194),(49,195),(50,197),(51,197),(52,199)],
 'dwellingLvl4':[(472,181),(575,185),(576,184)],
 'dwellingUpLvl4':[(537,195),(581,180),(582,179)],
 'dwellingLvl5':[(251,319),(252,320),(347,321),(348,321)],
 'dwellingUpLvl5':[(246,312),(355,318)],
 'dwellingLvl6':[(441,338),(442,338),(575,341)],
 'dwellingUpLvl6':[(436,331),(437,331),(438,331),(582,335)],
 'special4':[(427,269),(428,270)],
 'dwellingLvl7':[(415,275),(416,275)],
 'dwellingUpLvl7':[(408,264),(533,267)],
 'tavern':[(8,326),(9,327),(225,335)],
 'marketplace':[],
 'blacksmith':[(582,335),(583,335),(790,343),(791,342)],
 'resourceSilo':[(665,249),(767,250),(768,250)],
 'special1':[(5,121),(6,121),(77,129)],
 'special2':[(697,153)],
 'special3':[(190,204),(191,204),(339,218),(340,217)],
 'shipyard':[(748,180),(796,190)],
 'ship':[(748,177)],
 'grail':[(221,142),(233,143)],
}
EAVE_POINTS={
 'dwellingUpLvl1':[(701,131)],
 'dwellingUpLvl3':[(4,155)],
 'dwellingUpLvl5':[(245,293)],
 'dwellingUpLvl6':[(433,306),(434,308),(435,309),(583,319)],
 'marketplace':[(536,217),(537,220),(667,222),(668,225),(669,225),(670,220)],
}
