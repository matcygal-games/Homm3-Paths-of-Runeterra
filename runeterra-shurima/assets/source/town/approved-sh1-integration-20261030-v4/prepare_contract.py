"""Prepare the unchanged native silhouette-v2 consumer's SH1 source contract."""
from build_candidate import *
import copy
import shutil
import tempfile

REASONS = {
    ("guild","chimera"): "The nearer Chimera statue wing projects over a small far-right Sun Archive gallery return. Its pedestal is on the lower terrace and its bounded wing hides only a non-access root projection of that higher gallery; the Archive door is unobstructed.",
    ("defenses","chimera"): "The lower Chimera terrace's winged statue projects in front of the far-left Sunward Bastion wall. Its bounded wing pixels hide only a non-access part of the higher wall foot; the main fortress gate and approach remain clear.",
    ("archers","market"): "The nearer Bazaar awning projects over the far-right lower edge of the Archer Court's higher fence platform. The Archer gate and its west-front access remain visible; a painted rear completion supplies the fence when the market is absent.",
    ("tavern","coast"): "The foreground moored skiff mast projects across a small right-hand Caravanserai perimeter edge. The house gate and its supported approach remain clear; the mast-free painted wall is restored when the vessel is absent.",
}
LEVELS = {
    "guild":"Upper Sun Archive gallery landing, native root band y130Ã¢â‚¬â€œ138",
    "defenses":"Upper Sunward Bastion wall landing, native root band y130Ã¢â‚¬â€œ138",
    "chimera":"Lower Chimera pedestal terrace, native root band y174Ã¢â‚¬â€œ184",
    "archers":"Raised Archer Court fence landing, native root band y273Ã¢â‚¬â€œ283",
    "market":"Lower Bazaar foreground apron, native root band y308Ã¢â‚¬â€œ318",
    "tavern":"Dry Caravanserai perimeter landing, native root band y304Ã¢â‚¬â€œ313",
    "coast":"Lower quay pilings and moored hull at native y328Ã¢â‚¬â€œ357",
}


def scene_without(idx, absent):
    result = Image.open(HERE/"background-native.png").convert("RGBA")
    for state in idx["complete_scene_states"]:
        if idx["states"][state]["site"] != absent:
            result.alpha_composite(Image.open(PROJECT/idx["states"][state]["frame"]["path"]).convert("RGBA"))
    return result


def prepare_contract():
    plan = read(HERE/"site-plan-v2.json")
    idx = read(HERE/"candidate-frames.json")
    town = read(PROJECT/"content/factions.json")["shurima"]["town"]
    load = lambda name: Image.open(HERE/"geometry"/name).convert("L")
    sites = []
    structures = copy.deepcopy(town["structures"])
    states = {}
    for original in plan["sites"]:
        sid = original["id"]
        silhouette = load(sid+"-silhouette.png")
        bbox = silhouette.getbbox()
        site = {"id":sid,"states":original["states"],"entrance":original["entrance"],"depth":original["z"],
                "box":[bbox[0],bbox[1],bbox[2]-bbox[0],bbox[3]-bbox[1]],"silhouette_mask":ref(HERE/"geometry"/(sid+"-silhouette.png"))}
        if sid=="coast":
            site["intentional_water"] = True
        sites.append(site)
        for state in site["states"]:
            structures[state].update({"x":0,"y":0,"z":site["depth"]})
            row = {"access_kind":"moored-vessel" if state=="ship" else "open-site" if sid in ("coast","grail","rockbears","sculptors","archers","nomads","market","runners") else "door",
                   "entrance":idx["states"][state]["entrance"],"body_mask":ref(HERE/"geometry"/(state+"-body.png")),
                   "foundation_mask":ref(HERE/"geometry"/(state+"-foundation.png")),"door_mask":ref(HERE/"geometry"/(state+"-door.png")),
                   "approach_mask":ref(HERE/"geometry"/(state+"-approach.png"))}
            if sid=="coast":
                foundation = load(state+"-foundation.png")
                marine = ImageChops.multiply(foundation,load("water.png"))
                if marine.getbbox():
                    path = HERE/"geometry"/(state+"-marine-support.png")
                    save(path,marine)
                    row["marine_support_mask"] = ref(path)
                    row["marine_support_kind"] = "moored-hull" if state=="ship" else "deck-and-pilings"
            states[state] = row
    overlaps = []
    roots = []
    for i,a in enumerate(sites):
        for b in sites[i+1:]:
            am = load(a["id"]+"-silhouette.png")
            bm = load(b["id"]+"-silhouette.png")
            hit = ImageChops.multiply(am,bm)
            if not hit.getbbox():
                continue
            rear,front = (a,b) if a["depth"]<b["depth"] else (b,a)
            pair = rear["id"],front["id"]
            if pair not in REASONS:
                raise ValueError("Unreviewed overlap pair: "+str(pair))
            path = HERE/"geometry"/(pair[0]+"-behind-"+pair[1]+".png")
            save(path,hit)
            overlaps.append({"behind":pair[0],"front":pair[1],"reason":REASONS[pair],"mask":ref(path)})
            rear_roots = union(load(state+"-foundation.png") for state in rear["states"])
            front_body = union(load(state+"-body.png") for state in front["states"])
            hidden = ImageChops.multiply(rear_roots,front_body)
            if hidden.getbbox():
                mask_path = HERE/"geometry"/(pair[0]+"-root-behind-"+pair[1]+".png")
                save(mask_path,hidden)
                case = {"kind":"supported-terrace-projection","behind":pair[0],"front":pair[1],"behind_depth":rear["depth"],"front_depth":front["depth"],
                        "reason":REASONS[pair],"hidden_pixels":hidden.histogram()[255],"hidden_bounds":list(hidden.getbbox()),"mask_sha256":sha(mask_path),
                        "rear_level":LEVELS[pair[0]],"front_level":LEVELS[pair[1]]}
                case_path = HERE/"physical-cases"/(pair[0]+"-"+pair[1]+".json")
                dump(case_path,case)
                absent_path = HERE/"physical-cases"/(pair[0]+"-without-"+pair[1]+".png")
                absent = scene_without(idx,pair[1])
                save(absent_path,absent)
                overlay = Image.open(HERE/"fully-built-replayed.png").convert("RGBA")
                mark = Image.new("RGBA",SIZE,(255,0,80,0))
                mark.putalpha(hidden.point(lambda p:220 if p else 0))
                overlay.alpha_composite(mark)
                overlay_path = HERE/"physical-cases"/(pair[0]+"-"+pair[1]+"-root-overlay.png")
                save(overlay_path,overlay)
                roots.append({"behind":pair[0],"front":pair[1],"reason":REASONS[pair],"mask":ref(mask_path),"source_case":ref(case_path),
                              "evidence":{"complete_scene":ref(HERE/"fully-built-replayed.png"),"front_absent_scene":ref(absent_path),"intersection_overlay":ref(overlay_path)}})
    contract = {"status":"authored configuration","canvas":[800,374],"alpha_threshold":8,"geometry_mode":"silhouette-v2","ordinary_land_sites":16,
                "background":ref(HERE/"background-native.png"),"land_mask":ref(HERE/"geometry/land.png"),"sites":sites,
                "frames":{state:row["frame"] for state,row in idx["states"].items()},
                "silhouette_plan":{"version":2,"support_mask":ref(HERE/"geometry/support.png"),"stairs_mask":ref(HERE/"geometry/stairs.png"),"water_mask":ref(HERE/"geometry/water.png"),
                                   "paths_mask":ref(HERE/"geometry/paths.png"),"complete_scene":ref(HERE/"fully-built-replayed.png"),"complete_scene_states":idx["complete_scene_states"],
                                   "states":states,"overlaps":overlaps,"foundation_occlusions":roots},
                "annotation_limits":"These are source-pixel physical/consumer checks, not final human art or native in-game acceptance. Only exact bounded non-access projections are annotated; no door/approach exemption exists."}
    path = HERE/"layout-acceptance-contract-v2.json"
    dump(path,contract)
    patch = {"status":"authored configuration","candidate_only":True,"selection_authorized":False,
             "structures":structures,"design_patch":{"layout_geometry_mode":"silhouette-v2","layout_contract":ref(path)},
             "native_coast_rule":"config/buildingsLibrary.json: ship inherits upgrades=shipyard; highest built family member must preserve the whole dock+vessel image.",
             "no_gameplay_change":True}
    dump(HERE/"candidate-integration-patch.json",patch)
    return contract,patch


def inspect_in_isolation():
    import faction_town_layout as native_layout
    contract,patch = prepare_contract()
    # This is the real unchanged consumer over ordinary copied files, not a
    # synthetic validator or a weakened production mode.
    with tempfile.TemporaryDirectory(prefix="sh1-physical-proof-",dir=REPORT) as tmp:
        project = Path(tmp)
        source_rel = HERE.relative_to(PROJECT)
        shutil.copytree(HERE,project/source_rel)
        (project/"design").mkdir()
        design = read(PROJECT/"design/town-visuals.json")
        design.update(patch["design_patch"])
        dump(project/"design/town-visuals.json",design)
        faction = read(PROJECT/"content/factions.json")
        faction["shurima"]["town"]["structures"] = patch["structures"]
        dump(project/"content/factions.json",faction)
        shutil.copytree(REPORT/"native-candidate",project/"assets/generated")
        errors,deps = native_layout.inspect(project,{"factions":faction},"shurima")
        result = {"status":"authored configuration","actual_consumer":"scripts/faction_town_layout.py:inspect","consumer_sha256":sha(ROOT/"scripts/faction_town_layout.py"),
                  "errors":errors,"ok":not errors,"declared_dependency_count":len(deps),"canonical_or_stage_mutations":False}
    dump(report_path("native-silhouette-consumer"),result)
    return result


if __name__ == "__main__":
    result = inspect_in_isolation()
    print(json.dumps(result))
    sys.exit(0 if result["ok"] else 2)
