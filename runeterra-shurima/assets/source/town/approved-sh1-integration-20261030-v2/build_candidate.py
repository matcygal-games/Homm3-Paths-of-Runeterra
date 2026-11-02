"""Technical SH1 decomposition and native candidate compilation; never selects art.

All architecture pixels come from preserved, genuinely painted full/early/middle/
late masters. The following coordinates are source-pixel annotations, not artwork.
"""
from pathlib import Path
import hashlib
import io
import json
import sys
from collections import deque

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PROJECT = ROOT / "runeterra-shurima"
REPORT = ROOT / "reports/shurima-sh1-integration-20261030-v2"
OLD = PROJECT / "assets/source/town/approved-sh1-20261029-v1"
sys.path.insert(0, str(ROOT / "scripts"))
from faction_art_compile import create_compiler

SIZE = (800, 374)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def save(path, image):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, compress_level=9, optimize=False)


def ref(path):
    return {"path": path.relative_to(PROJECT).as_posix(), "sha256": sha(path)}


def mask(points):
    result = Image.new("L", SIZE)
    ImageDraw.Draw(result).polygon(points, fill=255)
    return result


def line(points, width=3):
    result = Image.new("L", SIZE)
    ImageDraw.Draw(result).line(points, fill=255, width=width, joint="curve")
    # Pillow's two-pixel oblique raster can leave only diagonal neighbours at
    # shallow turns. Trace the same segment with cardinal centre-line steps;
    # this changes only the editable technical annotation, never painting pixels.
    for (x0,y0),(x1,y1) in zip(points,points[1:]):
        x,y = x0,y0
        sx = 1 if x1>x0 else -1
        sy = 1 if y1>y0 else -1
        dx,dy = abs(x1-x0),abs(y1-y0)
        result.putpixel((x,y),255)
        while (x,y)!=(x1,y1):
            if x==x1:
                y += sy
            elif y==y1:
                x += sx
            elif abs((x+sx-x0)*(y1-y0)-(y-y0)*(x1-x0)) <= abs((x-x0)*(y1-y0)-(y+sy-y0)*(x1-x0)):
                x += sx
            else:
                y += sy
            result.putpixel((x,y),255)
    return result


def report_path(stem):
    number = 1
    while (REPORT/(stem+f"-{number:03d}.json")).exists():
        number += 1
    return REPORT/(stem+f"-{number:03d}.json")


def union(images):
    result = Image.new("L", SIZE)
    for image in images:
        result = ImageChops.lighter(result, image)
    return result


# Tight whole architectural/enclosure forms. Courts inside an actual fence or
# contiguous platform remain part of that site's painted footprint; unbounded
# approach streets, adjacent buildings and surrounding terrain are excluded.
FORMS = {
    "oathkeepers": [(15,92),(29,77),(56,72),(71,66),(79,53),(84,52),(85,24),(90,22),(95,27),(95,45),(101,28),(110,12),(120,1),(129,0),(137,6),(146,17),(154,34),(158,49),(158,11),(166,9),(173,13),(178,9),(181,15),(183,25),(181,27),(183,68),(195,67),(197,75),(213,77),(214,105),(202,110),(199,116),(173,124),(144,124),(124,117),(103,115),(79,112),(44,107),(17,105)],
    "memorial": [(234,111),(247,100),(250,88),(251,43),(254,35),(257,50),(258,62),(266,57),(270,53),(278,59),(284,67),(296,70),(293,75),(280,78),(279,99),(297,110),(297,128),(280,132),(235,132)],
    "civic": [(310,83),(334,76),(337,59),(372,59),(381,40),(423,40),(425,61),(443,61),(449,50),(452,59),(453,79),(476,78),(493,93),(493,126),(470,134),(326,135),(310,125)],
    "guild": [(494,109),(517,104),(541,104),(548,91),(552,60),(556,59),(556,31),(563,26),(570,26),(578,30),(581,58),(584,89),(585,104),(600,106),(606,116),(605,127),(585,138),(495,138)],
    "defenses": [(612,97),(626,72),(627,51),(640,48),(645,48),(649,57),(655,74),(687,74),(690,66),(697,65),(699,74),(730,74),(733,52),(740,51),(742,45),(751,45),(753,55),(763,55),(767,75),(787,88),(799,90),(799,131),(763,137),(710,135),(612,138)],
    "rockbears": [(9,175),(31,157),(61,152),(91,164),(127,168),(148,182),(158,205),(130,215),(20,213),(9,205)],
    "sculptors": [(177,181),(186,166),(208,158),(221,145),(238,156),(272,155),(289,174),(302,192),(280,201),(181,201)],
    "priests": [(324,169),(339,151),(369,149),(391,149),(421,152),(435,178),(433,195),(418,199),(329,199)],
    "runners": [(451,187),(472,172),(494,160),(516,151),(535,172),(562,178),(574,204),(566,221),(452,222)],
    "chimera": [(580,152),(595,146),(603,139),(598,129),(599,118),(610,118),(623,122),(637,130),(644,137),(649,134),(654,132),(663,133),(666,137),(666,146),(686,150),(689,176),(668,184),(584,184)],
    "buriedTemple": [(684,193),(704,177),(719,170),(783,168),(795,187),(796,221),(781,229),(687,228)],
    "smith": [(2,269),(17,252),(36,250),(43,223),(58,223),(65,253),(102,247),(150,259),(164,280),(153,303),(4,309)],
    "archers": [(174,235),(196,233),(214,225),(224,219),(244,217),(247,226),(271,228),(292,227),(298,236),(298,255),(288,274),(250,276),(232,283),(183,284),(176,267)],
    "market": [(245,280),(266,269),(293,266),(308,248),(312,250),(329,260),(352,264),(381,282),(393,301),(376,317),(255,318)],
    "nomads": [(404,258),(417,254),(437,251),(453,252),(462,247),(472,239),(472,231),(476,232),(478,237),(495,243),(503,242),(505,235),(508,237),(506,243),(516,248),(518,234),(524,232),(537,236),(537,247),(542,248),(544,251),(551,250),(558,255),(559,264),(570,272),(578,277),(576,309),(553,318),(407,316)],
    "tavern": [(580,263),(589,252),(594,237),(613,230),(629,218),(633,214),(638,216),(650,222),(665,234),(691,232),(712,231),(716,247),(735,248),(742,264),(757,274),(757,301),(734,313),(699,309),(675,313),(623,305),(587,306)],
    "coast": [(673,314),(690,310),(706,314),(721,324),(721,340),(713,345),(705,344),(699,340),(698,346),(692,348),(687,344),(680,343),(676,350),(672,347)],
    "grail": [(347,229),(351,228),(353,233),(383,219),(386,216),(386,209),(390,205),(397,206),(400,212),(399,219),(425,230),(428,225),(431,227),(433,249),(428,250),(426,239),(400,227),(400,243),(407,247),(404,251),(379,249),(379,245),(384,241),(384,228),(355,240),(354,250),(347,249)],
}

# Each genuinely painted earlier-state silhouette has its own upper profile;
# final tower outlines are not applied to an early source containing bare sky.
VARIANTS = {
    "dwellingLvl7": [(16,91),(40,81),(49,67),(50,58),(64,54),(89,54),(90,61),(155,61),(162,50),(176,50),(184,59),(187,77),(206,81),(212,99),(199,107),(198,116),(172,124),(144,124),(123,116),(80,112),(43,107),(17,105)],
    "special4": [(15,92),(30,77),(49,71),(51,49),(61,46),(67,55),(89,51),(105,46),(110,53),(155,53),(162,43),(174,43),(183,52),(185,76),(209,77),(213,101),(201,108),(199,116),(172,124),(144,124),(124,117),(80,112),(44,107),(17,105)],
    "villageHall": [(311,84),(333,78),(345,74),(415,74),(426,81),(475,81),(493,95),(493,126),(470,134),(326,135),(311,125)],
    "townHall": [(311,84),(333,78),(344,65),(354,59),(415,59),(426,66),(427,79),(476,79),(493,94),(493,126),(470,134),(326,135),(311,125)],
    "cityHall": [(311,84),(334,77),(339,59),(372,59),(382,51),(422,51),(426,62),(443,62),(450,58),(453,80),(476,79),(493,94),(493,126),(470,134),(326,135),(311,125)],
    "mageGuild1": [(495,111),(517,106),(538,106),(542,96),(549,92),(554,98),(555,105),(600,106),(606,116),(605,127),(585,138),(495,138)],
    "mageGuild2": [(495,111),(517,106),(538,106),(540,83),(547,78),(547,65),(554,64),(560,72),(567,64),(575,70),(579,102),(600,106),(606,116),(605,127),(585,138),(495,138)],
    "fort": [(612,98),(627,96),(645,96),(646,91),(654,90),(657,96),(686,96),(688,90),(697,90),(700,96),(731,96),(733,91),(743,91),(746,96),(788,94),(799,97),(799,131),(763,137),(710,135),(612,138)],
    "citadel": [(612,98),(627,94),(629,73),(636,70),(645,70),(649,76),(652,96),(688,94),(690,87),(697,87),(700,94),(730,94),(733,73),(740,69),(750,71),(754,78),(756,95),(789,91),(799,96),(799,131),(763,137),(710,135),(612,138)],
    "dwellingLvl3": [(10,176),(30,161),(57,155),(90,166),(128,172),(147,186),(157,205),(130,215),(20,213),(10,205)],
    "special2": [(10,175),(29,160),(37,154),(54,150),(73,154),(85,148),(112,150),(129,164),(148,169),(157,187),(158,205),(130,215),(20,213),(10,205)],
    "dwellingLvl4": [(325,170),(340,158),(370,155),(392,151),(420,159),(434,179),(433,195),(418,199),(329,199)],
    "dwellingLvl5": [(452,188),(473,177),(494,176),(506,174),(525,177),(562,180),(574,204),(566,221),(452,222)],
    "dwellingLvl6": [(582,153),(605,145),(619,144),(634,139),(646,145),(659,149),(685,153),(689,176),(668,184),(584,184)],
    "dwellingLvl2": [(174,236),(194,236),(218,230),(244,225),(269,230),(291,231),(298,254),(288,274),(183,283),(176,267)],
    "dwellingLvl1": [(405,260),(418,256),(437,254),(454,252),(474,242),(480,243),(500,250),(521,254),(529,251),(537,252),(545,260),(560,267),(575,281),(576,309),(553,318),(407,316)],
}

# Source terrain stairs are separate from level landings. Keeping their approved
# pixels in the background lets a missing building expose a proper vacant landing.
STAIRS = [
    [(107,107),(137,107),(153,131),(138,139),(121,121)],
    [(253,120),(273,120),(280,136),(253,140)],
    [(378,120),(420,120),(424,136),(375,136)],
    [(528,129),(554,129),(558,146),(525,146)],
    [(352,193),(412,193),(420,211),(346,212)],
    [(621,169),(639,169),(645,195),(620,197)],
    [(618,145),(647,145),(640,168),(616,168)],
]

# Door/frontage anchors have been moved from broad court centres to the actual
# threshold, fence gate or open visitor edge visible in the source paintings.
ACCESS = {
    "oathkeepers": ((112,105), [(112,106),(123,121),(142,141),(159,145)]),
    "memorial": ((264,119), [(264,120),(267,137),(307,147)]),
    "civic": ((400,119), [(400,120),(400,137),(444,146)]),
    "guild": ((541,128), [(541,129),(541,147),(572,147)]),
    "defenses": ((713,135), [(713,136),(713,149),(700,156)]),
    "rockbears": ((94,214), [(94,215),(94,224),(163,227)]),
    "sculptors": ((246,200), [(246,201),(246,212),(309,218)]),
    "priests": ((379,192), [(379,193),(379,212),(362,215),(342,217)]),
    "runners": ((508,221), [(508,222),(508,228),(550,228),(576,232),(576,239)]),
    "chimera": ((630,168), [(630,169),(632,193),(661,204)]),
    "buriedTemple": ((755,228), [(755,229),(755,239),(765,245)]),
    "smith": ((94,307), [(94,308),(95,321),(166,324)]),
    "archers": ((226,280), [(226,281),(227,294),(234,302)]),
    "market": ((326,316), [(326,317),(326,329),(389,331)]),
    "nomads": ((482,316), [(482,317),(482,330),(532,334)]),
    "tavern": ((666,311), [(666,312),(666,320),(660,323)]),
    "coast": ((693,314), [(693,315),(688,317),(678,317),(671,318),(660,323)]),
    "grail": ((391,249), [(391,250),(391,261),(399,264)]),
}

CONTACT_MIN_Y = dict(zip(FORMS, [100,121,124,130,130,207,195,192,216,174,222,300,273,308,309,304,328,242]))
LANDINGS = {
    "oathkeepers": [(10,96),(213,96),(219,115),(176,134),(132,134),(75,121),(12,111)],
    "memorial": [(229,115),(300,113),(304,138),(228,140)],
    "civic": [(305,117),(497,117),(500,139),(309,140)],
    "guild": [(489,122),(622,122),(624,142),(490,144)],
    "defenses": [(607,125),(799,119),(799,144),(610,145)],
    "rockbears": [(4,198),(162,195),(164,216),(131,222),(15,220),(4,210)],
    "sculptors": [(173,188),(307,187),(307,207),(178,209)],
    "priests": [(318,186),(439,186),(441,203),(323,205)],
    "runners": [(445,208),(579,207),(580,229),(449,231)],
    "chimera": [(578,169),(694,167),(696,189),(580,194)],
    "buriedTemple": [(679,215),(799,213),(799,236),(681,237)],
    "smith": [(0,294),(168,290),(169,311),(151,318),(0,317)],
    "archers": [(170,266),(302,262),(303,283),(182,292),(171,285)],
    "market": [(241,302),(399,298),(400,322),(249,326)],
    "nomads": [(400,300),(582,299),(583,322),(403,326)],
    "tavern": [(575,297),(762,293),(764,316),(698,319),(578,314)],
    "coast": [(668,308),(704,308),(725,321),(727,337),(714,349),(681,351),(668,349)],
    "grail": [(343,238),(437,237),(439,254),(345,256)],
}
STREET_LINES = [
    [(159,145),(180,137),(221,139),(255,144),(307,147),(319,144),(348,141),(396,140),(444,146),(474,144),(519,147),(572,147)],
    [(572,147),(574,189),(600,198),(661,204),(677,188),(686,183),(691,178),(695,174),(699,166),(700,156)],
    [(159,145),(164,152),(165,186),(164,227),(166,240),(170,260),(170,291),(166,324),(234,302),(238,294)],
    [(307,147),(310,176),(310,213),(309,218),(315,228),(342,217),(335,220),(335,241),(337,250),(345,254),(363,254),(371,259),(389,266),(399,264)],
    [(399,264),(398,270)],
    [(398,270),(398,311),(389,331),(414,334),(482,330),(532,334),(575,328),(620,323),(660,323)],
    [(576,239),(578,245),(578,273),(579,277),(579,286),(578,290),(578,316),(575,328)],
    [(765,245),(755,239),(744,234),(733,230),(692,230),(683,230),(678,225),(665,215),(661,204)],
    [(660,323),(671,318),(678,317),(688,317)],
]


def boat_mask():
    hull = mask([(693,335),(705,333),(724,337),(754,343),(766,343),(770,337),(773,336),(775,344),(773,357),(768,363),(752,363),(720,355),(696,350)]).filter(ImageFilter.MaxFilter(3))
    sail = mask([(715,329),(752,301),(756,300),(756,339),(723,334)])
    return union([hull,sail,line([(757,296),(757,344)],2),line([(708,338),(757,297)],1)])


def tag_for(state):
    if state in ("villageHall", "fort", "mageGuild1") or state.startswith("dwellingLvl"):
        return "early"
    if state in ("townHall", "citadel", "mageGuild2", "special2", "special4"):
        return "middle"
    if state == "cityHall":
        return "late"
    return "approved"


def native_source(tag):
    return HERE / ("approved-full-native.png" if tag == "approved" else tag + "-states-native.png")


def icon(image, size):
    cropped = image.crop(image.getchannel("A").getbbox())
    cropped.thumbnail((size[0] - 4, size[1] - 4), Image.Resampling.LANCZOS)
    result = Image.new("RGBA", size)
    result.alpha_composite(cropped, ((size[0] - cropped.width) // 2, size[1] - cropped.height - 2))
    return result


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    town = read(PROJECT / "content/factions.json")["shurima"]["town"]
    old = read(OLD / "site-plan-v1.json")
    sites = []
    for original in old["sites"]:
        site = dict(original)
        site["id"] = "oathkeepers" if site["id"] == "colossus" else site["id"]
        site["names"] = {state: town["buildings"][state]["name"] for state in site["states"]}
        site["entrance"] = list(ACCESS[site["id"]][0])
        site["whole_form_polygon"] = FORMS[site["id"]]
        site["trace_status"] = "Native source-pixel architectural/enclosure outline; no 5px planning-budget dilation."
        sites.append(site)
    paintings = {tag: Image.open(native_source(tag)).convert("RGBA") for tag in ("approved", "early", "middle", "late")}
    stair_masks = [mask(points) for points in STAIRS]
    stairs = union(stair_masks)
    # River and side-channel pixels are annotated independently of foundations.
    water = mask([(800,247),(787,252),(779,262),(792,280),(800,282),(800,374),(411,374),(455,357),(487,351),(533,347),(564,339),(596,335),(630,332),(661,329),(692,326),(720,323),(745,319),(773,315),(800,310)])
    land = ImageChops.invert(water)
    frames = {}
    site_unions = {}
    all_removals = []
    for site in sites:
        site_id = site["id"]
        state_masks = []
        for state in site["states"]:
            body = mask(VARIANTS.get(state, FORMS[site_id]))
            if site_id == "coast" and state == "ship":
                body = ImageChops.lighter(body,boat_mask())
            # A two-pixel source fringe captures actual antialiased cornices,
            # fine poles and roof tips. It is limited to the upper architecture,
            # never the root/approach band and never a five-pixel planning budget.
            if site_id not in ("nomads","runners","tavern","coast"):
                fringe = body.filter(ImageFilter.MaxFilter(5))
                fringe_bottom = min(CONTACT_MIN_Y[site_id]-5,105) if site_id in ("civic","guild") else CONTACT_MIN_Y[site_id]-5
                band = mask([(0,0),(799,0),(799,fringe_bottom),(0,fringe_bottom)])
                body = ImageChops.lighter(body,ImageChops.multiply(fringe,band))
            if site_id == "oathkeepers":
                # The great arch's blue sky aperture is not opaque architecture.
                # This bounded RGB alpha-selection preserves the original sky
                # pixels through the hole; it never alters an artwork RGB sample.
                sky = Image.new("L",SIZE)
                sp = sky.load()
                source_pixels = paintings[tag_for(state)].load()
                warm_architecture = Image.new("L",SIZE)
                wp = warm_architecture.load()
                for yy in range(0,56):
                    for xx in range(70,196):
                        red,green,blue,_ = source_pixels[xx,yy]
                        if red>blue+10 and red>=green:
                            wp[xx,yy] = 255
                # Cold antialiased outline pixels touching actual warm masonry
                # remain part of the source object; they are not sky holes.
                protected_edge = warm_architecture.filter(ImageFilter.MaxFilter(5))
                for yy in range(0,56):
                    for xx in range(70,196):
                        red,green,blue,_ = source_pixels[xx,yy]
                        if blue>=135 and blue>red+12 and blue>green+3 and not protected_edge.getpixel((xx,yy)):
                            sp[xx,yy] = 255
                body = ImageChops.subtract(body,sky)
            if site_id in ("oathkeepers", "memorial", "civic", "guild", "priests", "chimera"):
                body = ImageChops.subtract(body, stairs)
            # A gate access strip is part of the actual visitor frontage. It is
            # not an arbitrary hole used to cover a road/body collision.
            entrance, approach_points = ACCESS[site_id]
            if state == "dwellingUpLvl2":
                entrance,approach_points = (226,283),[(226,284),(227,294),(234,302)]
            door = line([(entrance[0]-3, entrance[1]), (entrance[0]+3, entrance[1])], 2)
            if state == "dwellingUpLvl2":
                door = line([(223,283),(229,283)],1)
            approach = line(approach_points, 2)
            if site_id == "coast":
                door = mask([(672,315),(676,310),(701,310),(706,317),(672,323)])
            # All declared door pixels must fit the body's complete source bounds;
            # marine access and the front fence threshold can touch its edge.
            # The genuinely painted boat-free completion supplies the quay's
            # otherwise occluded planks/pilings in the unoccupied dock state.
            frame = Image.open(HERE/"hidden-face-completion-native-v1.png").convert("RGBA") if state=="shipyard" else paintings[tag_for(state)].copy()
            frame.putalpha(body)
            path = HERE / "frames" / (state + ".png")
            save(path, frame)
            save(HERE / "geometry" / (state + "-body.png"), body)
            # The full lower root contour (not a single support pixel) is traced
            # inside the front contact band of the actual opaque source.
            foundation = Image.new("L", SIZE)
            pix = body.load()
            draw = ImageDraw.Draw(foundation)
            bounds = body.getbbox()
            for x in range(bounds[0], bounds[2]):
                ys = [y for y in range(bounds[1], bounds[3]) if pix[x,y]]
                if ys:
                    bottom = max(ys)
                    if bottom >= CONTACT_MIN_Y[site_id]:
                        draw.line((x,max(CONTACT_MIN_Y[site_id],bottom-1),x,bottom),fill=255)
            foundation = ImageChops.multiply(foundation,body)
            save(HERE / "geometry" / (state + "-foundation.png"), foundation)
            save(HERE / "geometry" / (state + "-door.png"), door)
            save(HERE / "geometry" / (state + "-approach.png"), approach)
            area = Image.new("RGBA", SIZE)
            area.putalpha(body)
            border = Image.new("RGBA", SIZE, (245,210,85,0))
            border.putalpha(ImageChops.subtract(body.filter(ImageFilter.MaxFilter(3)),body))
            save(HERE / "derived" / (state + "_area.png"), area)
            save(HERE / "derived" / (state + "_border.png"), border)
            save(HERE / "derived" / (state + "_campaign.png"), icon(frame,(58,64)))
            save(HERE / "construction" / (state + ".png"), icon(frame,(150,70)))
            frames[state] = {"site":site_id,"source_tag":tag_for(state),"frame":ref(path),"body":ref(HERE/"geometry"/(state+"-body.png")),"entrance":list(entrance),"z":site["z"]}
            state_masks.append(body)
        site_unions[site_id] = union(state_masks)
        # Recovery is strictly under the approved fully-built visible state.
        # Earlier painted variants may extend into original visible sky/ground;
        # those extensions must never authorise recolouring the approved full.
        all_removals.append(Image.open(HERE/"geometry"/(site["states"][-1]+"-body.png")).convert("L"))
        save(HERE / "geometry" / (site_id + "-silhouette.png"), site_unions[site_id])
    restorations = []
    hidden_path = HERE / "hidden-face-completion-native-v1.png"
    hidden = Image.open(hidden_path).convert("RGBA")
    # Exact bounded painted hidden-face completion. The fully built foreground
    # covers every replaced pixel, so the approved maximum image remains exact.
    # Earlier sources already show their own unoccluded earlier architecture.
    for rear, front in [("guild","chimera"),("defenses","chimera"),("archers","market"),("tavern","coast")]:
        for state in next(s["states"] for s in sites if s["id"]==rear):
            if frames[state]["source_tag"] == "early":
                continue
            body = Image.open(HERE/"geometry"/(state+"-body.png")).convert("L")
            front_max = Image.open(HERE/"geometry"/(next(s["states"][-1] for s in sites if s["id"]==front)+"-body.png")).convert("L")
            bounded = ImageChops.multiply(body,front_max)
            if bounded.getbbox() is None:
                continue
            original = Image.open(PROJECT/frames[state]["frame"]["path"]).convert("RGBA")
            completed = Image.composite(hidden,original,bounded)
            completed.putalpha(body)
            path = HERE/"frames"/(state+".png")
            save(path,completed)
            frames[state]["frame"] = ref(path)
            mask_path = HERE/"geometry"/(state+"-hidden-by-"+front+".png")
            save(mask_path,bounded)
            record = {"state":state,"front_site":front,"mask":ref(mask_path),"painted_completion":ref(hidden_path),"pixels":bounded.histogram()[255],"bounds":list(bounded.getbbox())}
            restorations.append(record)
            save(HERE/"derived"/(state+"_campaign.png"),icon(completed,(58,64)))
            save(HERE/"construction"/(state+".png"),icon(completed,(150,70)))
    removal = union(all_removals)
    full = paintings["approved"]
    recovery = Image.open(HERE / "empty-recovery-native.png").convert("RGBA")
    background = Image.composite(recovery, full, removal)
    sky_budget = ImageChops.multiply(removal,mask([(70,0),(196,0),(196,55),(70,55)]))
    sky_recovery = full.copy()
    sky_recovery.paste(Image.open(HERE/"sky-inpaint-native-crop-v2.png").convert("RGBA"),(70,0))
    background = Image.composite(sky_recovery,background,sky_budget)
    save(HERE/"geometry/sky-recovery-budget.png",sky_budget)
    save(HERE / "background-native.png", background)
    save(HERE / "geometry/removal-mask.png", removal)
    save(HERE / "geometry/stairs.png", stairs)
    save(HERE / "geometry/water.png", water)
    save(HERE / "geometry/land.png", land)
    support = ImageChops.subtract(ImageChops.multiply(union(mask(p) for p in LANDINGS.values()),land),stairs)
    save(HERE / "geometry/support.png", support)
    # A cardinal pixel-centre path annotation records the painted street route;
    # the wider actual approaches remain separately measured source masks.
    paths = union([line(points,1) for points in STREET_LINES] + [line(points,1) for site_id,(_,points) in ACCESS.items() if site_id != "archers"])
    paths = ImageChops.lighter(paths,line([(226,284),(227,294),(234,302)],1))
    save(HERE / "geometry/paths.png",paths)
    complete = []
    for site in sorted(sites,key=lambda s:s["z"]):
        # Native CCastleInterface groups by getBase() and shows the highest
        # built family member. SHIP inherits upgrades=SHIPYARD from the library.
        complete.append(site["states"][-1])
    scene = background.copy()
    for state in complete:
        scene.alpha_composite(Image.open(PROJECT/frames[state]["frame"]["path"]).convert("RGBA"))
    save(HERE / "fully-built-replayed.png", scene)
    # RGBA getbbox ignores equal-alpha RGB differences; compare RGB explicitly.
    diff = ImageChops.difference(full.convert("RGB"),scene.convert("RGB"))
    save(REPORT / "fully-built-difference.png",diff)
    dump(HERE/"site-plan-v2.json",{"status":"authored configuration","approved_code":"SH1","sites":sites,"native_canvas":[800,374],"source_coordinate_policy":"Tight native architectural/enclosure forms; streets and source stairs are separate terrain. Open courts within an actual fence remain bounded site surfaces, not neighbouring ground."})
    dump(HERE/"candidate-frames.json",{"status":"authored configuration","candidate_only":True,"states":frames,"complete_scene_states":complete,"background":ref(HERE/"background-native.png"),"fully_built_replayed":ref(HERE/"fully-built-replayed.png"),"fully_built_pixel_difference_bbox":diff.getbbox()})
    dump(HERE/"hidden-face-restorations.json",{"status":"authored configuration","restorations":restorations,"source_scope":"Only original foreground-occluded rear pixels, painted from a genuine 2D completion source. All maximum-composition foreground pixels remain exact."})
    print(json.dumps({"states":len(frames),"full_difference_bbox":diff.getbbox()}))


if __name__ == "__main__":
    main()
