"""Resumable town-only candidate assembly from genuine painted 2D masters.

No active recipe, manifest, content, generated resource or stage is changed.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import sys
from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPORT = ROOT / "build/reports/urban-town-community-20261024-v3"
PAINTED = ROOT / "assets/source/town/painted-community-20261024-v2"
SITES = {
    "throneHall": ([330,22,120,112], ["villageHall","townHall","cityHall","capitol"]),
    "crownBastion": ([660,35,114,104], ["fort","citadel","castle"]),
    "arcaneAthenaeum": ([107,67,98,111], ["mageGuild1","mageGuild2","mageGuild3","mageGuild4"]),
    "dwellingLegion": ([1,241,151,130], ["dwellingLvl1","dwellingUpLvl1"]),
    "dwellingHound": ([153,220,117,115], ["dwellingLvl2","dwellingUpLvl2"]),
    "dwellingAxe": ([450,269,132,101], ["dwellingLvl3","dwellingUpLvl3"]),
    "dwellingRose": ([2,142,107,94], ["dwellingLvl4","dwellingUpLvl4"]),
    "dwellingCrimson": ([205,145,114,84], ["dwellingLvl5","dwellingUpLvl5"]),
    "dwellingMinotaur": ([631,155,123,100], ["dwellingLvl6","dwellingUpLvl6"]),
    "bindingRift": ([493,57,123,108], ["special4","dwellingLvl7","dwellingUpLvl7"]),
    "gildedCup": ([272,226,155,146], ["tavern"]),
    "grandMarket": ([110,165,88,64], ["marketplace"]),
    "foundry": ([635,271,142,100], ["blacksmith"]),
    "crimsonCitadel": ([567,170,61,64], ["resourceSilo"]),
    "shipyard": ([752,175,48,65], ["shipyard","ship"]),
    "grail": ([621,54,34,83], ["grail"]),
    "blackRoseAcademy": ([2,23,98,105], ["special1"]),
    "trifarianHall": ([340,136,110,87], ["special2"]),
    "arenaOfValor": ([466,181,100,80], ["special3"]),
}
NEW = {"dwellingLvl3","dwellingUpLvl3","dwellingLvl4","dwellingUpLvl4","dwellingLvl7","dwellingUpLvl7"}
WATER = [[800,132],[791,146],[784,162],[781,185],[779,209],[782,230],[800,239]]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p): return Path(p).relative_to(ROOT).as_posix()
def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def write(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def save(p,im):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=False,compress_level=9)
def mask(im): return im.getchannel("A").point(lambda x:255 if x>=128 else 0)
def count(im): return sum(im.histogram()[128:])
def fit(im,rect):
    alpha=im.getchannel("A");bb=alpha.point(lambda v:255 if v>=8 else 0).getbbox()
    if not bb or alpha.getextrema()[0]==255: raise ValueError("Actual nonempty transparent building required")
    subject=ImageOps.contain(im.crop(bb),(rect[2]-4,rect[3]-4),Image.Resampling.LANCZOS)
    xy=(rect[0]+(rect[2]-subject.width)//2,rect[1]+rect[3]-2-subject.height)
    out=Image.new("RGBA",(800,374));out.alpha_composite(subject,xy)
    return out,list(bb),list(xy),list(subject.size)

def prepare():
    REPORT.mkdir(parents=True,exist_ok=True)
    before=HERE/"input-recipes.json"
    if not before.exists():
        write(before,{rel(p):load(p) for p in sorted((ROOT/"assets/recipes/town").rglob("*.json"))})
    templates=load(before)
    faction=load(ROOT/"content/factions.json")["noxus"]["town"]
    states={b for _,bs in SITES.values() for b in bs}
    if states!=set(faction["structures"]) or len(states)!=36: raise ValueError("36 exact existing states required")
    background=ImageOps.fit(Image.open(HERE/"background-master-v1.png").convert("RGBA"),(800,374),method=Image.Resampling.LANCZOS)
    save(HERE/"background-native.png",background)
    from PIL import ImageDraw
    water=Image.new("L",(800,374));ImageDraw.Draw(water).polygon(WATER,fill=255)
    save(HERE/"water-annotation.png",water)
    records=[];recipes={};layers={};sites=[]
    for site,(rect,buildings) in SITES.items():
        site_record={"id":site,"composition_rectangle":rect,"native_z":rect[1]+rect[3],"buildings":buildings}
        sites.append(site_record)
        for state in buildings:
            base=deepcopy(templates[f"assets/recipes/town/structures/{state}-animation.json"])
            if (PAINTED/state/"master.png").is_file():
                master=PAINTED/state/"master.png";generation=PAINTED/state/"generation.json"
            else:
                master=ROOT/base["generation"]["painted_master"]
                generation=ROOT/base["generation"]["generation_record"]
            im=Image.open(master).convert("RGBA");layer,crop,xy,size=fit(im,rect)
            folder=HERE/"structures"/state
            save(folder/"layer.png",layer);layers[state]=layer
            solid=mask(layer);area=Image.new("RGBA",(800,374),(255,255,255,0));area.putalpha(solid)
            edge=ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(5)),solid)
            border=Image.new("RGBA",(800,374),(255,230,100,0));border.putalpha(edge)
            save(folder/"area.png",area);save(folder/"border.png",border)
            icon=Image.new("RGBA",(150,70));thumb=ImageOps.contain(im.crop(crop),(145,65),Image.Resampling.LANCZOS)
            icon.alpha_composite(thumb,((150-thumb.width)//2,70-thumb.height));save(HERE/"construction"/(state+".png"),icon)
            footing=solid.copy();bounds=solid.getbbox()
            footing.paste(0,(0,0,800,max(0,bounds[3]-7)))
            row={"state":state,"site":site,"composition_rectangle":rect,"native_z":rect[1]+rect[3],"master":rel(master),"master_sha256":sha(master),"generation_record":rel(generation),"generation_record_sha256":sha(generation),"native_layer":rel(folder/"layer.png"),"native_layer_sha256":sha(folder/"layer.png"),"source_crop":crop,"native_position":xy,"native_size":size,"click_bbox":list(bounds),"click_pixels":count(solid),"footing_water_pixels":count(ImageChops.multiply(footing,water)),"visual_approval_granted":False}
            records.append(row)
            gen={"image_generation_used":True,"provider":"OpenAI built-in imagegen","model":"Not exposed by the built-in tool","model_disclosure":"Not exposed by the builtin tool.","prompt":load(generation)["prompt"],"painted_master":rel(master),"painted_master_sha256":sha(master),"generation_record":rel(generation),"generation_record_sha256":sha(generation),"conversion":{"method":"Uniform alpha-crop/contain of genuine painted 2D source; forced-depth site placement, no perspective warping or artificial art.","source_crop":crop,"placement_box":rect,"native_position":xy,"native_size":size,"site":site,"assembly_script":rel(Path(__file__)),"assembly_script_sha256":sha(Path(__file__))}}
            for role in ("animation","area","border"):
                recipe=deepcopy(templates[f"assets/recipes/town/structures/{state}-{role}.json"])
                source=folder/({"animation":"layer.png","area":"area.png","border":"border.png"}[role])
                recipe.update(production_status="painted-master-complete" if role=="animation" else "derived-technical-mask-complete",status="built-unreviewed",source_sha256=sha(source),sha256=sha(source),source_canvas=[800,374],fit="exact",visual_approval_granted=False)
                recipe["building_contract"].update(full_canvas_placement={"x":0,"y":0,"z":row["native_z"]},native_ground_contact=rect,name=faction["buildings"][state].get("name",state))
                recipe["generation"]=deepcopy(gen)
                if role=="animation":
                    recipe["groups"][0]["frames"][0].update(source=rel(source),source_sha256=sha(source),sha256=sha(source))
                else:
                    recipe.update(source=rel(source))
                    recipe["generation"]["image_generation_used"]=False
                    recipe["generation"]["method"]="Alpha128 area mask or two-pixel outward MaxFilter5 border of exact painted native layer."
                    recipe["generation"]["conversion"]["mask_method"]="Exact alpha128 silhouette; area is binary silhouette, border is two-pixel outward MaxFilter5 minus silhouette."
                recipes[f"assets/recipes/town/structures/{state}-{role}.json"]=recipe
    icons=deepcopy(templates["assets/recipes/town/buildingIcons.json"])
    for frame in icons["frames"]:
        p=HERE/"construction"/(frame["building"]+".png")
        frame.update(source=rel(p),sha256=sha(p),source_sha256=sha(p))
    icons["generation"]={"image_generation_used":False,"provider":None,"model":None,"method":"Actual per-building painted master uniform-crop construction icons, native sparse IDs unchanged.","assembly_script":rel(Path(__file__)),"assembly_script_sha256":sha(Path(__file__))}
    recipes["assets/recipes/town/buildingIcons.json"]=icons
    bg=deepcopy(templates["assets/recipes/town/background.json"])
    bg.update(source=rel(HERE/"background-native.png"),source_sha256=sha(HERE/"background-native.png"),sha256=sha(HERE/"background-native.png"),source_canvas=[800,374],fit="exact",production_status="painted-master-complete",status="built-unreviewed",visual_approval_granted=False)
    bg["generation"]={"image_generation_used":True,"provider":"OpenAI built-in imagegen","model":"Not exposed by the built-in tool","prompt":load(HERE/"background-generation.json")["prompt"],"painted_master":rel(HERE/"background-master-v1.png"),"painted_master_sha256":sha(HERE/"background-master-v1.png"),"generation_record":rel(HERE/"background-generation.json"),"generation_record_sha256":sha(HERE/"background-generation.json"),"conversion":"Uniform cover-fit to native800x374; no lens or perspective distortion."}
    recipes["assets/recipes/town/background.json"]=bg
    for path,value in recipes.items(): write(HERE/"candidate-recipes"/path,value)
    data={"status":"authored configuration","canvas":[800,374],"site_count":19,"state_count":36,"ordinary_land_sites":17,"optional_coast_sites":1,"grail_sites":1,"sites":sites,"states":records,"recipes":{p:sha(HERE/"candidate-recipes"/p) for p in recipes},"terrain":{"master":rel(HERE/"background-master-v1.png"),"master_sha256":sha(HERE/"background-master-v1.png"),"native":rel(HERE/"background-native.png"),"native_sha256":sha(HERE/"background-native.png"),"water_polygon":WATER},"visual_approval_granted":False,"coast_semantics":"ship replaces shipyard, both at the identical location/depth; ship master includes dock+boat"}
    write(HERE/"selection.json",data)
    overlap=[]
    for i,a in enumerate(records):
        for b in records[i+1:]:
            if a["site"]!=b["site"]:
                n=count(ImageChops.multiply(mask(layers[a["state"]]),mask(layers[b["state"]])))
                if n: overlap.append([a["state"],b["state"],n])
    wet=[r for r in records if r["site"] not in ("shipyard","grail") and r["footing_water_pixels"]]
    write(REPORT/"candidate-geometry.json",{"overlaps":overlap,"wet_dry_foundations":wet,"site_count":19,"state_count":36})
    def compose(mode):
        chosen=[]
        for site,(rect,bs) in SITES.items():
            if site in ("shipyard","grail"): continue
            chosen.append(bs[0] if mode=="base" else bs[-1])
        if mode in ("coast","moored"): chosen.append("shipyard" if mode=="coast" else "ship")
        if mode=="grail": chosen.append("grail")
        out=background.copy()
        for state in sorted(chosen,key=lambda s:next(r["native_z"] for r in records if r["state"]==s)):out.alpha_composite(layers[state])
        return out
    save(REPORT/"empty-native.png",background)
    for mode in ("base","upgraded","coast","moored","grail"):save(REPORT/(mode+"-native.png"),compose(mode))
    print(json.dumps({"states":len(records),"recipes":len(recipes),"overlap_count":len(overlap),"wet_count":len(wet)}))

if __name__=="__main__": prepare()
