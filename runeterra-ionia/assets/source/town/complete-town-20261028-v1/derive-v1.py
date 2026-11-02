"""Deterministic technical extraction of the complete painted Ionia community.

This module paints no art. It consumes own genuine full-scene paintings, manual
silhouette mattes and a separately painted transparent civic ornament. Outputs
remain candidate sources; root owns production integration and native testing.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
SIZE = (800, 374)
PREFIX = "Content/Sprites/runeterra/ionia/"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def rel(path):
    return Path(path).relative_to(PROJECT).as_posix()

def png(im):
    stream = io.BytesIO()
    im.convert("RGBA").save(stream, format="PNG")
    return stream.getvalue()

def matte(polygons):
    im = Image.new("L", SIZE)
    draw = ImageDraw.Draw(im)
    for polygon in polygons:
        draw.polygon([tuple(p) for p in polygon], fill=255)
    return im.filter(ImageFilter.MaxFilter(3))

def native(name):
    im = Image.open(HERE / name).convert("RGBA")
    if im.size != SIZE:
        raise ValueError("Full-scene source is not native800x374: " + name)
    return im

def fit(im, size):
    scale = min(size[0] / im.width, size[1] / im.height)
    return im.resize((max(1, round(im.width*scale)), max(1, round(im.height*scale))), Image.Resampling.LANCZOS)

def render():
    plan = json.loads((HERE / "site-silhouettes-v6.json").read_text(encoding="utf-8"))
    masks = json.loads((HERE / "state-mattes-v1.json").read_text(encoding="utf-8"))
    master = native("complete-native-v5-selected.png")
    empty = native("empty-plate-native-v1.png")
    images = {"full": master, "base": native("base-selected-native-v2.png"),
              "middle":native("middle-selected-native-v2.png"), "late":native("late-selected-native-v2.png"),
              "dock":native("dock-only-native-v1.png")}
    sources = {"full":"complete-native-v5-selected.png", "base":"base-selected-native-v2.png",
               "middle":"middle-selected-native-v2.png", "late":"late-selected-native-v2.png",
               "dock":"dock-only-native-v1.png"}
    allmask = Image.new("L", SIZE)
    site_masks = {}
    for name, site in plan["sites"].items():
        site_masks[name] = matte([site["polygon"], *site.get("extra_polygons", [])])
        allmask = ImageChops.lighter(allmask, site_masks[name])
    background = Image.composite(empty, master, allmask)
    output = {}
    def put(name, image):
        output[name] = png(image)
    put("prepared-v1/town/background.png", background)
    put("prepared-v1/geometry/architecture-union.png", allmask)
    index = {"status":"authored configuration", "canvas":list(SIZE), "ordinary_land_sites":16,
             "background":{}, "frames":{}, "sites":{}, "release_accepted":False,
             "method":"Complete whole-town painting first, then full-canvas actual painted architecture extraction; no per-state crop fitting."}
    special_source = {"villageHall":"base", "townHall":"middle", "cityHall":"late", "fort":"base",
                      "citadel":"middle", "mageGuild1":"base", "mageGuild2":"middle",
                      "special1":"late", "special2":"late", "shipyard":"dock"}
    for tier in range(1,8):
        special_source["dwellingLvl"+str(tier)] = "base"
    layers = {}
    for name, site in plan["sites"].items():
        index["sites"][name] = {"states":site["keys"],"depth":site["z"],"entrance":site["entrance"],
                                  "identity":site["identity"],"intentional_water":name=="coast"}
        union = Image.new("L", SIZE)
        for state in site["keys"]:
            source = special_source.get(state,"full")
            if state == "shipyard":
                alpha = matte(masks["shipyard_polygons"])
            elif state in masks["overrides"]:
                alpha = matte(masks["overrides"][state]["polygons"])
            else:
                alpha = site_masks[name].copy()
            layer = images[source].copy()
            layer.putalpha(alpha)
            layers[state] = layer
            union = ImageChops.lighter(union,alpha)
            put("prepared-v1/town/structures/"+state+"/layer.png",layer)
            body = alpha.point(lambda a:255 if a>=128 else 0)
            area = Image.new("RGBA", SIZE,(255,255,255,0));area.putalpha(body)
            put("prepared-v1/town/structures/"+state+"/area.png",area)
            border=Image.new("RGBA",SIZE,(255,220,90,0));border.putalpha(ImageChops.subtract(body.filter(ImageFilter.MaxFilter(3)),body))
            put("prepared-v1/town/structures/"+state+"/border.png",border)
            sprite=layer.crop(alpha.getbbox())
            for role,canvas,limit,bottom in [("campaign",(58,64),(56,62),64),("icon",(150,70),(146,66),68)]:
                panel=Image.new("RGBA",canvas);small=fit(sprite,limit);panel.alpha_composite(small,((canvas[0]-small.width)//2,bottom-small.height));put("prepared-v1/town/structures/"+state+"/"+role+".png",panel)
            index["frames"][state]={"site":name,"depth":site["z"],"source_painting":rel(HERE/sources[source]),"source_painting_sha256":sha(HERE/sources[source]),"source_transform":"identity native full-canvas; manual visible architectural alpha only", "source_bounds":list(alpha.getbbox())}
        put("prepared-v1/geometry/sites/"+name+".png",union)
    grail=masks["grail"];original=Image.open(HERE/grail["source"]).convert("RGBA")
    if original.getchannel("A").getextrema()[0]!=0:
        raise ValueError("Genuine Grail painting requires transparent background")
    sprite=original.crop(original.getchannel("A").point(lambda a:255 if a>8 else 0).getbbox());sprite=fit(sprite,grail["native_fit"])
    layer=Image.new("RGBA",SIZE);origin=(grail["bottom_center"][0]-sprite.width//2,grail["bottom_center"][1]-sprite.height);layer.alpha_composite(sprite,origin);layers["grail"]=layer;alpha=layer.getchannel("A")
    for role,im in [("layer",layer),("area",None),("border",None)]:
        if role=="area":
            im=Image.new("RGBA",SIZE,(255,255,255,0));im.putalpha(alpha.point(lambda a:255 if a>=128 else 0))
        elif role=="border":
            body=alpha.point(lambda a:255 if a>=128 else 0);im=Image.new("RGBA",SIZE,(255,220,90,0));im.putalpha(ImageChops.subtract(body.filter(ImageFilter.MaxFilter(3)),body))
        put("prepared-v1/town/structures/grail/"+role+".png",im)
    for role,canvas,limit,bottom in [("campaign",(58,64),(56,62),64),("icon",(150,70),(146,66),68)]:
        panel=Image.new("RGBA",canvas);piece=fit(original.crop(original.getchannel("A").getbbox()),limit);panel.alpha_composite(piece,((canvas[0]-piece.width)//2,bottom-piece.height));put("prepared-v1/town/structures/grail/"+role+".png",panel)
    put("prepared-v1/geometry/sites/grail.png",alpha.point(lambda a:255 if a>=8 else 0))
    index["sites"]["grail"]={"states":["grail"],"depth":grail["z"],"entrance":[584,351],"identity":"Separate optional Lantern of Accord civic ornament","intentional_water":False}
    index["frames"]["grail"]={"site":"grail","depth":grail["z"],"source_painting":rel(HERE/grail["source"]),"source_painting_sha256":sha(HERE/grail["source"]),"source_transform":"Uniform whole-objectfit with preserved genuinealpha", "source_bounds":list(alpha.getbbox()),"native_origin":list(origin),"native_size":list(sprite.size)}
    if len(layers)!=35:
        raise ValueError("Actual Ionia contract requires35states")
    for height in (120,130):
        put("prepared-v1/ui/creatureBackground"+str(height)+".png",background.crop((350,40,600,300)).resize((100,height),Image.Resampling.LANCZOS))
    for state,key in (("village","villageHall"),("fort","castle")):
        actor=layers[key];sprite=actor.crop(actor.getchannel("A").getbbox())
        for variant in ("normal","built"):
            for scale,size in (("large",(58,64)),("small",(48,32))):
                panel=background.resize(size,Image.Resampling.LANCZOS);small=fit(sprite,(size[0]-2,size[1]-3));panel.alpha_composite(small,((size[0]-small.width)//2,size[1]-small.height))
                if variant=="built":
                    # Technical original-interface construction-day indicator.
                    d=ImageDraw.Draw(panel);d.line((size[0]-10,2,size[0]-3,9),fill=(210,48,32),width=2);d.line((size[0]-10,9,size[0]-3,2),fill=(210,48,32),width=2)
                put("prepared-v1/town/icons/"+state+"_"+variant+"_"+scale+".png",panel)
    # Source previews use the actual chain substitutions, not all states piled up.
    def scene(states):
        result=background.copy()
        for state in sorted(states,key=lambda s:index["frames"][s]["depth"]):
            result.alpha_composite(layers[state])
        return result
    full_states=[s["keys"][-1] for name,s in plan["sites"].items() if name!="coast"]
    developed=scene(full_states)
    complete=scene(full_states+["ship"])
    if complete.tobytes()!=master.tobytes():
        raise ValueError("Highest complete scene no longer exactly reproduces selected whole painting")
    cases={"empty":background,"full":developed,"coast":complete,
           "grail":scene(full_states+["grail"]),
           "base":scene([s["keys"][0] if name not in ("kinkou","protector") else s["keys"][1] for name,s in plan["sites"].items() if name!="coast"]),
           "early":scene(["villageHall","fort","tavern","dwellingLvl1","special1"]),
           "dock":scene(full_states+["shipyard"]),
           "guild-absent":scene([s for s in full_states if not s.startswith("mageGuild")]),
           "inn-absent":scene([s for s in full_states if s!="tavern"]),
           "disciple-absent":scene([s for s in full_states if s!="dwellingUpLvl1"]),
           "harmony-absent":scene([s for s in full_states if s!="special4"])}
    for name,im in cases.items():
        put("prepared-v1/previews/"+name+"-native.png",im)
    return output,index

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write",action="store_true")
    parser.add_argument("--seal",action="store_true")
    args=parser.parse_args()
    output,index=render()
    pins={name:hashlib.sha256(data).hexdigest() for name,data in sorted(output.items())}
    expected=HERE/"expected-products-v1.json"
    if args.seal:
        if expected.exists():
            raise ValueError("Never overwrite a sealed source cohort")
        expected.write_text(json.dumps({"status":"authored configuration","products":pins},indent=2)+"\n")
    elif expected.exists() and json.loads(expected.read_text(encoding="utf-8"))["products"]!=pins:
        raise ValueError("Replayed candidate PNGs differ from sealed exact source outputs")
    if args.write:
        for name,data in output.items():
            path=HERE/name
            if path.exists() and path.read_bytes()!=data:
                raise ValueError("Refusing to overwrite different existing candidate output: "+name)
        for name,data in output.items():
            path=HERE/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        index["background"]={"path":rel(HERE/"prepared-v1/town/background.png"),"sha256":pins["prepared-v1/town/background.png"]}
        for state,record in index["frames"].items():
            name="prepared-v1/town/structures/"+state+"/layer.png";record.update({"path":rel(HERE/name),"sha256":pins[name]})
        index_path=HERE/"frame-index-v1.json"
        content=json.dumps(index,indent=2,ensure_ascii=False)+"\n"
        if index_path.exists() and index_path.read_text(encoding="utf-8")!=content:
            raise ValueError("Refusing to overwrite a different frame index")
        index_path.write_text(content,encoding="utf-8")
    print(json.dumps({"status":"authored configuration","states":len(index["frames"]),"source_outputs":len(output),"all_outputs_reproduced":True,"highest_complete_painting_exact":True,"native_execution":False,"release_accepted":False}))

if __name__=="__main__":
    main()
