"""Bounded SH1 candidate checks; isolated copies only, no hardlinks or selection."""
from prepare_contract import *
import re
import faction_town_layout as native_layout


def native_probe(kind):
    contract = read(HERE/"layout-acceptance-contract-v2.json")
    patch = read(HERE/"candidate-integration-patch.json")
    with tempfile.TemporaryDirectory(prefix="sh1-regression-",dir=REPORT) as temporary:
        project=Path(temporary)
        shutil.copytree(HERE,project/HERE.relative_to(PROJECT))
        shutil.copytree(REPORT/"native-candidate",project/"assets/generated")
        faction=read(PROJECT/"content/factions.json")
        faction["shurima"]["town"]["structures"]=patch["structures"]
        design=read(PROJECT/"design/town-visuals.json")
        design.update(patch["design_patch"])
        def replace(path,image):
            save(project/path,image)
            checksum=sha(project/path)
            def visit(value):
                if isinstance(value,dict):
                    if value.get("path")==path:value["sha256"]=checksum
                    for item in value.values():visit(item)
                elif isinstance(value,list):
                    for item in value:visit(item)
            visit(contract)
        def load(reference):return Image.open(project/reference["path"]).convert("L")
        plan=contract["silhouette_plan"]
        if kind=="displaced-real-building-and-masks":
            site=next(s for s in contract["sites"] if s["id"]=="rockbears")
            dy=35
            paths={site["silhouette_mask"]["path"]}
            site["box"][1]+=dy;site["entrance"][1]+=dy
            for state in site["states"]:
                paths.add(contract["frames"][state]["path"])
                row=plan["states"][state]
                row["entrance"][1]+=dy
                paths.update(row[key]["path"] for key in ("body_mask","foundation_mask","door_mask","approach_mask"))
                animation=read(project/"assets/generated/Content/Sprites"/faction["shurima"]["town"]["structures"][state]["animation"])
                resource=animation["basepath"]+animation["sequences"][0]["frames"][0]
                selected=project/"assets/generated/Content/Sprites"/resource
                im=Image.open(selected).convert("RGBA");moved=Image.new("RGBA",SIZE);moved.paste(im,(0,dy));save(selected,moved)
            for path in paths:
                im=Image.open(project/path)
                moved=Image.new(im.mode,SIZE);moved.paste(im,(0,dy));replace(path,moved)
        elif kind=="real-foundation-support-removed":
            reference=plan["support_mask"];support=load(reference)
            ImageDraw.Draw(support).rectangle((0,198,164,222),fill=0)
            replace(reference["path"],support)
        elif kind=="approach-through-solid-building":
            reference=plan["states"]["capitol"]["approach_mask"]
            approach=load(reference)
            ImageDraw.Draw(approach).line((400,100,400,120),fill=255,width=2)
            replace(reference["path"],approach)
        elif kind=="disconnected-paths":
            reference=plan["paths_mask"];paths=load(reference);paths.putpixel((1,1),255);replace(reference["path"],paths)
        elif kind=="changed-selected-frame":
            animation=read(project/"assets/generated/Content/Sprites"/faction["shurima"]["town"]["structures"]["capitol"]["animation"])
            selected=project/"assets/generated/Content/Sprites"/(animation["basepath"]+animation["sequences"][0]["frames"][0])
            im=Image.open(selected).convert("RGBA");im.putpixel((400,90),(255,0,0,255));save(selected,im)
        contract_path=project/HERE.relative_to(PROJECT)/"layout-acceptance-contract-v2.json"
        dump(contract_path,contract)
        design["layout_contract"]["sha256"]=sha(contract_path)
        dump(project/"design/town-visuals.json",design)
        errors,deps=native_layout.inspect(project,{"factions":faction},"shurima")
        expected={"positive":None,"displaced-real-building-and-masks":"Actual foundation lacks level support", "real-foundation-support-removed":"Actual foundation lacks level support", "approach-through-solid-building":"Approach passes through its own solid building", "disconnected-paths":"disconnected components", "changed-selected-frame":"Current selected town pixels differ"}[kind]
        ok=not errors if expected is None else any(expected in error for error in errors)
        return {"case":kind,"passed":ok,"expected_error_contains":expected,"actual_errors":errors,"declared_dependencies":len(deps)}


def main():
    idx=read(HERE/"candidate-frames.json");plan=read(HERE/"site-plan-v2.json")
    checks=[]
    approved=Image.open(HERE/"approved-full-native.png").convert("RGBA")
    complete=Image.open(HERE/"fully-built-replayed.png").convert("RGBA")
    checks.append({"case":"pixel-exact-approved-full-composition","passed":approved.tobytes()==complete.tobytes(),"approved_source":ref(HERE/"approved-full-native.png"),"replayed":ref(HERE/"fully-built-replayed.png")})
    background=Image.open(HERE/"background-native.png").convert("RGBA")
    removal=Image.open(HERE/"geometry/removal-mask.png").convert("L")
    # Difference must be empty outside actual selected architecture unions.
    changed=ImageChops.difference(background,approved).convert("RGB");changed=union(changed.split()).point(lambda p:255 if p else 0)
    checks.append({"case":"all-original-visible-pixels-preserved","passed":ImageChops.subtract(changed,removal).getbbox() is None})
    named_sky={state+":"+str(point):Image.open(HERE/"derived"/(state+"_area.png")).getchannel("A").getpixel(point) for state,point in [("capitol",(379,38)),("mageGuild3",(561,24)),("special1",(252,33))]}
    window_alpha=Image.open(HERE/"derived/dwellingUpLvl7_area.png").getchannel("A").getpixel((170,17))
    checks.append({"case":"reviewed-free-sky-wedges-transparent-and-enclosed-blue-window-owned","passed":not any(named_sky.values()) and window_alpha==255,"reviewer_witness_alpha":named_sky,"window_native_coordinate":[170,17],"window_alpha":window_alpha,"scope":"Concrete review regressions only; all-state silhouette visual acceptance remains independent."})
    source_root=HERE.relative_to(PROJECT)
    witnesses=[]
    states=idx["states"]
    all_masks={state:Image.open(HERE/"geometry"/(state+"-body.png")).convert("L") for state in states}
    sheet=Image.new("RGB",(260*4,200*9),(28,28,28));draw=ImageDraw.Draw(sheet)
    for number,(state,row) in enumerate(sorted(states.items())):
        area=Image.open(HERE/"derived"/(state+"_area.png")).getchannel("A")
        higher=union(all_masks[s] for s,r in states.items() if r["site"]!=row["site"] and r["z"]>row["z"])
        visible=ImageChops.subtract(area,higher)
        points=[(x,y) for y in range(374) for x in range(800) if visible.getpixel((x,y))]
        witness=max(points,key=lambda p:min(p[0],799-p[0],p[1],373-p[1])) if points else None
        witnesses.append({"state":state,"exposed_click_pixels_even_against_all_higher_state_unions":len(points),"witness":witness,"area_equals_source_alpha":area.tobytes()==all_masks[state].tobytes()})
        scene=background.copy()
        for maximum in idx["complete_scene_states"]:
            selected=state if states[maximum]["site"]==row["site"] else maximum
            scene.alpha_composite(Image.open(PROJECT/states[selected]["frame"]["path"]).convert("RGBA"))
        save(REPORT/"state-scenes"/(state+".png"),scene)
        frame=Image.open(PROJECT/row["frame"]["path"]).convert("RGBA")
        box=frame.getchannel("A").getbbox();cropped=frame.crop(box)
        # Native1:1 actual sprite crops, padded for review, never enlarged.
        canvas=Image.new("RGBA",(260,176),(40,40,40,255));canvas.alpha_composite(cropped,((260-cropped.width)//2,max(0,176-cropped.height)))
        tile=(number%4*260,number//4*200)
        sheet.paste(canvas.convert("RGB"),tile);draw.text((tile[0]+8,tile[1]+180),state,fill="white")
    save(REPORT/"all35-native-sprite-crops.png",sheet)
    dump(REPORT/"click-witnesses.json",witnesses)
    checks.append({"case":"all35-native-area-masks-exposed-and-exact","passed":len(witnesses)==35 and all(r["area_equals_source_alpha"] and r["witness"] for r in witnesses),"minimum_exposed_pixels":min(r["exposed_click_pixels_even_against_all_higher_state_unions"] for r in witnesses)})
    library_path=ROOT/"vcmi-develop/vcmi-develop/config/buildingsLibrary.json"
    raw=re.sub(r"//[^\n]*","",library_path.read_text(encoding="utf-8"));raw=re.sub(r",\s*([}\]])",r"\1",raw)
    library=json.loads(raw);own=read(PROJECT/"content/factions.json")["shurima"]["town"]["buildings"]
    buildings={state:{**library.get(state,{}),**own[state]} for state in own}
    def ancestry(state):
        result=[state]
        while buildings[result[-1]].get("upgrades"):result.append(buildings[result[-1]]["upgrades"])
        return result
    def native_selection(built):
        families={}
        for state in built:
            chain=ancestry(state);families.setdefault(chain[-1],[]).append((len(chain),state))
        return [max(family)[1] for family in families.values()]
    selected=native_selection(list(own))
    family_check=set(selected)==set(idx["complete_scene_states"]) and "ship" in selected and "shipyard" not in selected
    dock=all_masks["shipyard"];vessel=all_masks["ship"]
    checks.append({"case":"real-native-upgrade-family-max-selection-including-inherited-ship","passed":family_check and ImageChops.subtract(dock,vessel).getbbox() is None and native_selection(["shipyard"])==["shipyard"],"library_sha256":sha(library_path),"native_consumer_sha256":sha(ROOT/"vcmi-develop/vcmi-develop/client/windows/CCastleInterface.cpp"),"ship_inherited_upgrades":buildings["ship"].get("upgrades"),"maximum_selected_states":selected,"ship_includes_whole_dock":ImageChops.subtract(dock,vessel).getbbox() is None})
    for kind in ("positive","displaced-real-building-and-masks","real-foundation-support-removed","approach-through-solid-building","disconnected-paths","changed-selected-frame"):
        checks.append(native_probe(kind))
    before=read(REPORT/"protected-inputs-before.json")
    protected={path:{"before":checksum,"after":sha(Path(path)),"unchanged":sha(Path(path))==checksum} for path,checksum in before.items()}
    dump(REPORT/"protected-inputs-after.json",protected)
    checks.append({"case":"canonical-T7-shared-and-approved-inputs-preserved","passed":all(row["unchanged"] for row in protected.values())})
    result={"status":"authored configuration","candidate_only":True,"runtime_verified":False,"release_accepted":False,"no_canonical_or_stage_writes":True,"no_hardlinks":True,"checks":checks,"executed_cases":len(checks),"passed":sum(bool(c["passed"]) for c in checks),"ok":all(c["passed"] for c in checks)}
    dump(report_path("candidate-regressions"),result)
    print(json.dumps(result))
    return result


if __name__=="__main__":
    result=main();sys.exit(0 if result["ok"] else 2)
