"""One matched source-review cohort; no canonical selection or game publication.

The user requested visual comparison before choosing. This continues the existing
art correction checkpoint and deliberately grants no formal physical acceptance.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageChops, ImageDraw

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
SIZE=(800,374)

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def rel(path):
    return Path(path).relative_to(PROJECT).as_posix()

def image(path):
    return Image.open(path).convert("RGBA")

def mask(path):
    im=Image.open(path).convert("L")
    if im.size!=SIZE:
        raise ValueError("Source matte camera mismatch")
    return im

def fit(im,size):
    ratio=min(size[0]/im.width,size[1]/im.height)
    return im.resize((max(1,round(im.width*ratio)),max(1,round(im.height*ratio))),Image.Resampling.LANCZOS)

def main():
    out=HERE/"review-pair-v3"
    if out.exists():
        raise ValueError("Preserve prior review bytes; do not overwrite a cohort")
    baseline=read(HERE/"frame-index-v1.json")
    physical=HERE/"physical-contract-v1"
    matte_paths={}
    for state in baseline["frames"]:
        candidate=HERE/"contour-repair-v2/revision-v2/masks"/(state+".png")
        if candidate.exists():
            matte_paths[state]=candidate
    matte_paths.update({
        "blacksmith":physical/"contour-proposal-v2/blacksmith-proposed-mask.png",
        "special2":physical/"lower-protector-contour-proposal-v3/special2-proposed-mask.png",
        "dwellingLvl5":physical/"lower-protector-contour-proposal-v3/dwellingLvl5-proposed-mask.png",
        "dwellingUpLvl5":physical/"right-institutions-contour-proposal-v3/protector-proposed-mask.png",
        "special3":physical/"right-institutions-contour-proposal-v3/gateway-proposed-mask.png",
        "ship":physical/"short-coast-contour-proposal-v5/ship-mask.png",
        "shipyard":physical/"short-dock-contour-proposal-v4/shipyard-mask.png"})
    alphas={state:mask(path) for state,path in matte_paths.items()}
    recover=mask(physical/"guild-plinth-recovery-proposal-v2/mageGuild3-hidden-recovery-mask.png")
    if recover.histogram()[255]!=67:
        raise ValueError("Genuine whole Library pillar changed")
    alphas["mageGuild3"]=ImageChops.lighter(alphas["mageGuild3"],recover)
    # The independent artist whole scene is assembled before any output frame.
    whole=image(HERE/"complete-native-v6-separated.png")
    short=image(HERE/"short-complete-pier-native-v1.png")
    ordinary=Image.new("L",SIZE)
    for site,record in baseline["sites"].items():
        if site not in ("coast","grail"):
            ordinary=ImageChops.lighter(ordinary,alphas[record["states"][-1]])
    coast_roi=Image.new("L",SIZE);ImageDraw.Draw(coast_roi).rectangle((0,160,146,258),fill=255)
    coast_roi=ImageChops.subtract(coast_roi,ordinary)
    whole=Image.composite(short,whole,coast_roi)
    # Preserve the visible part of the genuinely recovered complete Library foot.
    visible_recover=ImageChops.subtract(recover,alphas["dwellingUpLvl2"])
    if visible_recover.histogram()[255]!=22:
        raise ValueError("Library visible masonry repair is not the reviewed22pixels")
    recovery_source=image(HERE/"guild3-plinth-recovery-native-v1.png")
    whole=Image.composite(recovery_source,whole,visible_recover)
    connector=read(HERE/"cloud-crop-transform-v2.json")
    corridor=Image.new("L",SIZE);ImageDraw.Draw(corridor).line([tuple(p) for p in connector["path"]],fill=255,width=3)
    if ImageChops.multiply(corridor,ordinary).getbbox():
        raise ValueError("Painted public corridor touches actual building alpha")
    source=image(HERE/"cloud-connector-crop-native-v2.png")
    painted=whole.copy();painted.paste(source,tuple(connector["source_box"][:2]))
    whole=Image.composite(painted,whole,corridor)
    # All below are matched derivatives of this exact curated whole painting.
    layers={}
    for state,record in baseline["frames"].items():
        if state=="grail":
            continue
        if state=="ship":
            src=short.copy()
        elif state=="shipyard":
            src=image(HERE/"short-dock-only-native-v1.png")
        elif record["source_painting"].endswith("complete-native-v5-selected.png"):
            src=whole.copy()
        else:
            src=image(PROJECT/record["source_painting"])
        if state=="mageGuild3":
            src=Image.composite(recovery_source,src,recover)
        src.putalpha(alphas[state]);layers[state]=src
    grail_source=image(HERE/"grail-lantern-master-v1.png")
    grail_actor=grail_source.crop(grail_source.getchannel("A").point(lambda a:255 if a>8 else 0).getbbox())
    grail_actor=fit(grail_actor,(19,35));grail=Image.new("RGBA",SIZE);grail.alpha_composite(grail_actor,(584-grail_actor.width//2,352-grail_actor.height));layers["grail"]=grail
    highest=[site["states"][-1] for name,site in baseline["sites"].items() if name not in ("coast","grail")]
    architecture=Image.new("L",SIZE)
    for state in highest+["ship"]:
        architecture=ImageChops.lighter(architecture,layers[state].getchannel("A"))
    background=Image.composite(image(HERE/"empty-plate-native-v1.png"),whole,architecture)
    def scene(states):
        result=background.copy()
        for state in sorted(states,key=lambda key:baseline["frames"][key]["depth"]):
            result.alpha_composite(layers[state])
        return result
    full=scene(highest+["ship"])
    if full.tobytes()!=whole.tobytes():
        raise ValueError("Matched review full scene does not reproduce its prior whole painting")
    base_states=[]
    for name,site in baseline["sites"].items():
        if name in ("coast","grail"):
            continue
        base_states.append(site["states"][1] if name in ("kinkou","protector") else site["states"][0])
    middle=["townHall" if s=="capitol" else "citadel" if s=="castle" else "mageGuild2" if s=="mageGuild3" else s for s in highest]
    cases={"empty":background,"full":full,"ordinary-full":scene(highest),"base":scene(base_states),
        "middle":scene(middle),"early":scene(["villageHall","fort","tavern","dwellingLvl1","special1"]),
        "dock":scene(highest+["shipyard"]),"grail":scene(highest+["grail"]),
        "protector-absent":scene([s for s in highest if s!="dwellingUpLvl5"]),
        "gateway-absent":scene([s for s in highest if s!="special3"]),
        "kinkou-absent":scene([s for s in highest if s!="dwellingUpLvl2"]),
        "workshop-absent-coast":scene([s for s in highest if s!="blacksmith"]+["ship"])}
    out.mkdir()
    whole.save(out/"complete-painted-master-native.png")
    coast_roi.save(out/"protected-coast-source-roi.png");corridor.save(out/"painted-cloud-corridor-mask.png")
    index={"status":"authored configuration","cohort":"corrected review V3","user_choice_pending":True,
        "native_screenshots":False,"formal_physical_acceptance":False,"production_compilation_performed":False,
        "canonical_selection_changed":False,"release_accepted":False,
        "limits":"Matched source-review images only. Formal support/route/click and production/native verification remain pending; user visual choice holds final selection.",
        "views":{},"source_frames":{},"alpha_inputs":{s:{"path":rel(p),"sha256":sha(p)} for s,p in matte_paths.items()},
        "complete_scene":{"path":rel(out/"complete-painted-master-native.png"),"sha256":sha(out/"complete-painted-master-native.png")},
        "highest_state_order":sorted(highest+["ship"],key=lambda key:baseline["frames"][key]["depth"]),
        "whole_painting_recomposition_exact":True}
    for name,im in cases.items():
        path=out/(name+"-native.png");im.save(path);index["views"][name]={"path":rel(path),"sha256":sha(path)}
    (out/"frames").mkdir()
    for state,im in layers.items():
        path=out/"frames"/(state+".png");im.save(path);index["source_frames"][state]={"path":rel(path),"sha256":sha(path),"depth":baseline["frames"][state]["depth"]}
    (out/"review-index.json").write_text(json.dumps(index,indent=2)+"\n")
    print(json.dumps({"matched_pair":str(out),"states":len(layers),"views":len(cases),"highest_full_exact":True,"user_choice_pending":True,"formal_acceptance":False}))

if __name__=="__main__":
    main()
