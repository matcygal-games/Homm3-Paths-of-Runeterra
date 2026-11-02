"""NX1 completion plan; prior approved candidate remains read-only history."""
from copy import deepcopy
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'approved-nx1-20261029-v1'
spec=importlib.util.spec_from_file_location('nx1_prior_plan',PRIOR/'nx1_plan.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
SIZE=prior.SIZE
SITES=deepcopy(prior.SITES)
# Whole visible bodies/attached courts, including previously missed edge roofs.
SITES['gildedCup']['poly']=[(0,190),(22,192),(29,206),(35,210),(46,210),(61,207),(68,205),(77,204),(79,200),(83,205),(91,209),(102,220),(105,233),(116,233),(120,240),(126,242),(145,240),(151,248),(158,255),(165,261),(173,276),(176,288),(174,323),(159,332),(136,337),(103,343),(72,341),(48,344),(0,336)]
SITES['foundry']['poly']=[(467,283),(483,274),(501,270),(514,264),(535,251),(546,246),(558,239),(564,230),(569,229),(577,237),(587,240),(602,238),(615,242),(630,239),(636,232),(643,235),(648,244),(657,245),(670,248),(676,254),(698,261),(720,269),(725,280),(735,290),(765,288),(799,295),(799,373),(682,373),(681,354),(638,352),(606,354),(562,349),(523,344),(493,339),(477,310)]
SITES['grandMarket']['poly']=[(164,275),(170,268),(177,260),(183,251),(190,255),(203,260),(215,260),(224,262),(235,255),(244,249),(250,251),(255,257),(271,261),(285,266),(301,270),(316,274),(316,244),(315,228),(328,222),(348,218),(362,219),(378,229),(382,241),(371,251),(355,262),(345,279),(345,291),(356,304),(363,315),(351,325),(334,336),(296,337),(265,331),(221,332),(192,328),(169,327)]
# The shared original masonry buttress is retained as the barracks end cap.
SITES['dwellingLegion']['poly']=[(144,217),(160,208),(167,202),(178,200),(188,196),(195,191),(205,190),(214,185),(230,184),(242,188),(242,249),(146,249)]
SITES['dwellingLegion']['z']=249
SITES['dwellingAxe']['z']=248
ROUTES={
 'arcaneAthenaeum':[(68,96),(121,96),(129,96)],
 'blackRoseAcademy':[(177,96),(224,96),(234,104)],
 'dwellingCrimson':[(686,166),(648,176),(632,187)],
 'dwellingHound':[(585,230),(528,230),(518,235)],
 'dwellingMinotaur':[(277,181),(297,181),(308,192),(308,194)],
 'crimsonCitadel':[(570,166),(563,166),(553,176),(553,183),(550,183)],
 'bindingRift':[(754,270),(772,288)],
}
COAST=dict(box=(366,315,124,59),boat_box=(420,322,64,52),z=370,
           landing=(405,342),water=[(367,362),(391,356),(431,359),(489,357),(491,374),(365,374)],
           description='Optional supported river quay descends from the foreground road to an off-screen river below the scene. Native SHIPYARD availability controls it; SHIP is the complete quay-and-moored-boat replacement because the Noxus building lineage upgrades shipyard. Inland background stays exact.')
