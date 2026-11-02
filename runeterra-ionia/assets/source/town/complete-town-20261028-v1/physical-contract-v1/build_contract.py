"""Bind authored semantic annotations to an explicitly frozen Ionia town cohort.

No canonical writes, artwork changes, frame repositioning or support fitted to
feet. Unknown overlaps and any unreviewed hidden contact fail preparation.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import sys
from PIL import Image,ImageDraw,ImageChops

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=="runeterra-ionia")
WORKSPACE=PROJECT.parent
sys.path.insert(0,str(WORKSPACE/"scripts"))
import faction_town_layout as consumer


def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+"\n",encoding="utf-8")
def blank():return Image.new("L",(800,374))
def union(items):
    out=blank()
    for item in items:out=ImageChops.lighter(out,item)
    return out
def polygon(points):
    out=blank();ImageDraw.Draw(out).polygon([tuple(p)for p in points],fill=255);return out
def lines(items,width):
    out=blank();d=ImageDraw.Draw(out)
    for item in items:d.line([tuple(p)for p in item],fill=255,width=width)
    return out
def direct(name):
    if not isinstance(name,str)or"\\"in name:raise ValueError("Nonportable project reference")
    path=PROJECT/name
    if path.absolute()!=path.resolve()or not path.resolve().is_relative_to(PROJECT)or path.stat().st_nlink!=1:
        raise ValueError("Source is not direct unaliased own input: "+name)
    return path
def verify(ref):
    path=direct(ref["path"])
    if sha(path)!=ref["sha256"]:raise ValueError("Frozen input changed: "+ref["path"])
    return path
def ref(path):return{"path":path.relative_to(PROJECT).as_posix(),"sha256":sha(path)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze",type=Path,required=True)
    parser.add_argument("--freeze-sha256",required=True)
    parser.add_argument("--terrain",type=Path,required=True)
    parser.add_argument("--contacts",type=Path,required=True)
    parser.add_argument("--generated",type=Path,required=True)
    parser.add_argument("--label",required=True)
    args=parser.parse_args()
    args.freeze=args.freeze.absolute();args.terrain=args.terrain.absolute();args.contacts=args.contacts.absolute()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,60}",args.label):raise ValueError("Unsafe unique binding label")
    if sha(args.freeze)!=args.freeze_sha256:raise ValueError("Freeze record changed")
    frozen=read(args.freeze);terrain=read(args.terrain);annotations=read(args.contacts)
    if terrain.get("status")!="authored configuration"or annotations.get("status")!="authored configuration":
        raise ValueError("Provisional observations cannot become an accepted physical contract")
    index=read(verify(frozen["frame_index"]));background=verify(frozen["background"])
    proposed_factions=verify(frozen["factions_proposal"]);content={"factions":read(proposed_factions)}
    town=content["factions"]["ionia"]["town"]
    if set(frozen["frames"])!=set(town["buildings"]):raise ValueError("Frozen frames do not cover actual state keys")
    if not isinstance(frozen.get("complete_scene"),dict):raise ValueError("Freeze needs the independently selected whole painting reference")
    complete_painting=verify(frozen["complete_scene"])
    target=HERE/("binding-"+args.label);target.mkdir(exist_ok=False)
    fixture=HERE/("fixture-"+args.label);fixture.mkdir(exist_ok=False)
    images={state:Image.open(verify(item)).convert("RGBA")for state,item in frozen["frames"].items()}
    complete=frozen.get("complete_scene_states")
    if not isinstance(complete,list):raise ValueError("Freeze needs exact selected complete-state order")
    def compose(selected):
        scene=Image.open(background).convert("RGBA")
        for name in selected:scene.alpha_composite(images[name])
        return scene
    if compose(complete).tobytes()!=Image.open(complete_painting).convert("RGBA").tobytes():
        raise ValueError("Actual selected layers do not reproduce the independently selected whole painting")
    terrain_root=target/"terrain";terrain_root.mkdir()
    def save_mask(name,image):
        path=target/name;path.parent.mkdir(parents=True,exist_ok=True);image.convert("RGBA").save(path);return ref(path)
    water=union(polygon(p)for p in terrain["water_polygons"])
    land=ImageChops.subtract(polygon(terrain["land_boundary"]),water)
    stairs=union(polygon(x["polygon"])for x in terrain["public_stair_observations"])
    support=ImageChops.subtract(union([*[polygon(p)for p in terrain["level_regions"].values()],
                                     *[polygon(p)for p in terrain.get("public_level_way_regions",{}).values()]]),union([water,stairs]))
    paths=lines(terrain["public_path_lines"],terrain.get("path_width",3))
    unwalkable_path=ImageChops.subtract(paths,union([support,stairs]))
    dump(target/"terrain-measurements.json",{"status":"authored configuration",
        "scope":"Own authoring guard; dry ownership of a retaining face never makes it an actual level street",
        "public_path_outside_observed_level_ground_or_stairs_pixels":unwalkable_path.histogram()[255],
        "unsupported_path_bounds":unwalkable_path.getbbox(),"consumer_execution":False,"release_accepted":False})
    if unwalkable_path.getbbox():raise ValueError("Authored public path leaves actual independently observed horizontal ground/stairs; no retaining-face street is permitted")
    roles={};physical={};states={};site_records=[]
    by_site={}
    for state,row in index["frames"].items():by_site.setdefault(row["site"],[]).append(state)
    painted_sources={}
    for row in index["frames"].values():
        if"source_painting"in row:
            source_ref={"path":row["source_painting"],"sha256":row["source_painting_sha256"]}
            verify(source_ref);painted_sources[source_ref["path"]]=source_ref
    # Actual native upgrade/builds relationships determine replacement families.
    # Mere visual proximity is never authority to collapse coexisting services.
    site_for={state:site for site,names in by_site.items()for state in names}
    native_links=[]
    for state in images:
        for field,previous in(("upgrades",town["buildings"][state].get("upgrades")),
                              ("builds",town["structures"][state].get("builds"))):
            if previous is None:continue
            if previous not in site_for or site_for[previous]!=site_for[state]:
                raise ValueError("Actual native replacement relation crosses the authored physical sites: "+state+"/"+str(previous))
            native_links.append({"state":state,"native_field":field,"replaced_state":previous,"site":site_for[state]})
    for site,names in by_site.items():
        reached={names[0]}
        while True:
            new=reached|{r["state"]for r in native_links if r["replaced_state"]in reached}|{r["replaced_state"]for r in native_links if r["state"]in reached}
            if new==reached:break
            reached=new
        if reached!=set(names):raise ValueError("Unrelated coexisting buildings cannot share one replacement site: "+site)
    assembly_root=target/"assemblies";assembly_root.mkdir()
    assemblies=[]
    def assembly(name,selected,purpose):
        path=assembly_root/(name+".png");compose(selected).save(path)
        assemblies.append({"name":name,"selected_states":selected,"image":ref(path),"purpose":purpose,"native_execution":False})
    assembly("complete-selected",complete,"Exact independently selected complete painting reproduction")
    assembly("empty",[],"All constructible institutions absent; permanent terrain ownership inspection")
    for site,names in by_site.items():
        rest=[s for s in complete if s not in names]
        assembly("absent-"+site,rest,"Finite whole-site absence/underlap ownership inspection; not an assertion that removing prerequisite buildings is a reachable native game state")
        for state in names:
            selected=sorted(rest+[state],key=lambda s:town["structures"][s]["z"])
            assembly("state-"+state,selected,"Actual state in the complete surrounding painted settlement; visual replacement probe, not a native build-order or prerequisite-reachability assertion")
    dump(target/"canonical-replacements-and-assemblies.json",{
        "status":"authored configuration","actual_native_links":native_links,"families":by_site,
        "all_distinct_sites_remain_independent":True,"native_replacement_source":frozen["factions_proposal"],
        "assemblies":assemblies,"native_execution":False,"release_accepted":False})
    for site,names in by_site.items():
        observation=annotations["sites"][site]
        if observation.get("pending")or observation.get("rejected_approach_observation"):
            raise ValueError("Pending actual contact or rejected access trace must be resolved against final source: "+site)
        silhouette=union(images[s].getchannel("A").point(lambda p:255 if p>=8 else 0)for s in names)
        box=silhouette.getbbox();depths={town["structures"][s]["z"]for s in names}
        if len(depths)!=1:raise ValueError("One physical site has inconsistent native depths")
        record={"id":site,"states":names,"depth":next(iter(depths)),"entrance":observation["entrance"],
                "box":[box[0],box[1],box[2]-box[0],box[3]-box[1]],"intentional_water":site=="coast",
                "silhouette_mask":save_mask("sites/"+site+".png",silhouette)}
        site_records.append(record)
        for state in names:
            spec={**observation,**observation.get("state_overrides",{}).get(state,{})}
            full=images[state].getchannel("A").point(lambda p:255 if p>=8 else 0)
            body=images[state].getchannel("A").point(lambda p:255 if p>=128 else 0)
            contacts=union([lines(spec["contact_lines"],annotations.get("contact_band_width",3)),
                            *[polygon(p)for p in spec.get("contact_islands",[])]])
            contacts=ImageChops.multiply(contacts,full)
            entry=blank()
            if "own_entry_region"in spec:
                x0,y0,x1,y1=spec["own_entry_region"];ImageDraw.Draw(entry).rectangle((x0,y0,x1-1,y1-1),fill=255)
                entry=ImageChops.multiply(entry,contacts)
            foundation=ImageChops.subtract(contacts,entry)
            door=polygon(spec["door_polygon"])
            approach=lines([spec["approach"]],spec.get("approach_width",3))
            root="states/"+state+"/"
            states[state]={"access_kind":spec.get("access_kind","door"),"entrance":spec["entrance"],
                           "body_mask":save_mask(root+"body.png",body),"foundation_mask":save_mask(root+"foundation.png",foundation),
                           "door_mask":save_mask(root+"door.png",door),"approach_mask":save_mask(root+"approach.png",approach)}
            roles[state]={"complete_contact_mask":save_mask(root+"complete-contact.png",contacts),
                          "own_entry_contact_mask":save_mask(root+"own-entry-contact.png",entry),
                          "partition":"complete = structural foundation union actual own entry contacts; disjoint, no contact deleted"}
            if site=="coast":
                marine=ImageChops.multiply(water,ImageChops.multiply(full,union([foundation,door,approach])))
                states[state].update(marine_support_kind=spec["marine_support_kind"],marine_support_mask=save_mask(root+"marine.png",marine))
            physical[state]=(foundation,door,approach)
    measurements={}
    for state,(foundation,door,approach)in physical.items():
        marine=Image.open(PROJECT/states[state]["marine_support_mask"]["path"]).getchannel("R")if"marine_support_mask"in states[state]else blank()
        allowed=union([support,marine])
        unsupported=ImageChops.subtract(foundation,allowed)
        own_blocked=ImageChops.multiply(approach,ImageChops.subtract(images[state].getchannel("A").point(lambda p:255 if p>=128 else 0),door))
        measurements[state]={"foundation_pixels":foundation.histogram()[255],
                             "unsupported_foundation_pixels":unsupported.histogram()[255],"unsupported_bounds":unsupported.getbbox(),
                             "foundation_on_stairs":ImageChops.multiply(foundation,stairs).histogram()[255],
                             "foundation_on_external_water":ImageChops.multiply(foundation,water).histogram()[255],
                             "approach_blocked_by_own_body":own_blocked.histogram()[255]}
    dump(target/"measured-geometry.json",{"status":"authored configuration","scope":"Diagnostic measurements only; not a public consumer pass or semantic approval.","states":measurements,"native_execution":False,"release_accepted":False})
    all_sites={x["id"]:x for x in site_records}
    overlaps=[];occlusions=[]
    for i,a in enumerate(site_records):
        for b in site_records[i+1:]:
            back,front=(a,b)if a["depth"]<b["depth"]else(b,a)
            back_union=union(images[s].getchannel("A").point(lambda p:255 if p>=8 else 0)for s in back["states"])
            front_union=union(images[s].getchannel("A").point(lambda p:255 if p>=8 else 0)for s in front["states"])
            overlap=ImageChops.multiply(back_union,front_union)
            if not overlap.getbbox():continue
            pair=back["id"]+"/"+front["id"]
            reason=annotations.get("overlap_reasons",{}).get(pair)
            if not isinstance(reason,str)or len(reason.strip())<20:raise ValueError("Actual overlap needs authored source disposition: "+pair)
            overlaps.append({"behind":back["id"],"front":front["id"],"reason":reason,
                             "mask":save_mask("overlaps/"+pair.replace("/","--")+".png",overlap)})
            root_union=union(physical[s][0]for s in back["states"])
            front_body=union(images[s].getchannel("A").point(lambda p:255 if p>=128 else 0)for s in front["states"])
            hidden=ImageChops.multiply(root_union,front_body)
            if hidden.getbbox():
                case=annotations.get("foundation_cases",{}).get(pair)
                if back["id"]=="coast"or not isinstance(case,dict):
                    raise ValueError("Actual complete foundation occlusion needs source repair or explicit reviewed supported-terrace case: "+pair+" ("+str(hidden.histogram()[255])+" pixels)")
                case_reason=case.get("reason");rear_level=case.get("rear_level");front_level=case.get("front_level")
                if(not isinstance(case_reason,str)or len(case_reason.strip())<40
                   or not isinstance(rear_level,str)or len(rear_level.strip())<8
                   or not isinstance(front_level,str)or len(front_level.strip())<8 or rear_level==front_level):
                    raise ValueError("Foundation case needs truthful distinct authored terrace levels and a bounded source reason: "+pair)
                access=union(union([physical[s][1],physical[s][2]])for s in back["states"])
                if ImageChops.multiply(hidden,access).getbbox()or hidden.tobytes()==root_union.tobytes():
                    raise ValueError("No door/approach or whole-root foundation waiver is permitted: "+pair)
                case_root=target/"foundation-cases"/pair.replace("/","--");case_root.mkdir(parents=True)
                mask_ref=save_mask("foundation-cases/"+pair.replace("/","--")+"/intersection.png",hidden)
                picked=list(complete)
                for site_key,field in((back,"behind_state"),(front,"front_state")):
                    chosen=case.get(field)
                    if chosen is not None:
                        if chosen not in site_key["states"]:raise ValueError("Case uses a foreign source state")
                        picked=[chosen if s in site_key["states"]else s for s in picked]
                full_case=compose(picked)
                absent=compose([s for s in picked if s not in front["states"]])
                full_path=case_root/"complete.png";absent_path=case_root/"front-absent.png";overlay_path=case_root/"all-state-contact-intersection.png"
                full_case.save(full_path);absent.save(absent_path)
                tint=Image.new("RGBA",(800,374));tint.paste((255,40,20,210),(0,0),hidden)
                Image.alpha_composite(full_case,tint).save(overlay_path)
                variants=[]
                for rear_state in back["states"]:
                    for front_state in front["states"]:
                        pixels=ImageChops.multiply(physical[rear_state][0],images[front_state].getchannel("A").point(lambda p:255 if p>=128 else 0))
                        if pixels.getbbox():variants.append({"behind_state":rear_state,"front_state":front_state,"pixels":pixels.histogram()[255],"bounds":pixels.getbbox(),"behind_frame_sha256":frozen["frames"][rear_state]["sha256"],"front_frame_sha256":frozen["frames"][front_state]["sha256"]})
                record={"kind":"supported-terrace-projection","behind":back["id"],"front":front["id"],
                        "behind_depth":back["depth"],"front_depth":front["depth"],"reason":case_reason,
                        "rear_level":rear_level,"front_level":front_level,"hidden_pixels":hidden.histogram()[255],
                        "hidden_bounds":list(hidden.getbbox()),"mask_sha256":mask_ref["sha256"],
                        "variant_intersections":variants,"semantic_review":"Authored case awaiting independent pixel/source review; no native or release acceptance."}
                case_path=case_root/"source-case.json";dump(case_path,record)
                occlusions.append({"behind":back["id"],"front":front["id"],"reason":case_reason,"mask":mask_ref,
                    "source_case":ref(case_path),"evidence":{"complete_scene":ref(full_path),"front_absent_scene":ref(absent_path),"intersection_overlay":ref(overlay_path)}})
    contract={"geometry_mode":"silhouette-v2","canvas":[800,374],"alpha_threshold":8,"ordinary_land_sites":16,
              "background":ref(background),"land_mask":save_mask("terrain/land.png",land),
              "frames":frozen["frames"],"sites":site_records,
              "silhouette_plan":{"version":2,"support_mask":save_mask("terrain/support.png",support),
                  "stairs_mask":save_mask("terrain/stairs.png",stairs),"water_mask":save_mask("terrain/water.png",water),
                  "paths_mask":save_mask("terrain/paths.png",paths),"states":states,"overlaps":overlaps,
                  "foundation_occlusions":occlusions,"complete_scene_states":complete,"complete_scene":ref(complete_painting)},
              "complete_contact_role_partition":roles,
              "canonical_replacement_evidence":ref(target/"canonical-replacements-and-assemblies.json"),
              "authoring_sources":[ref(args.freeze),frozen["frame_index"],frozen["factions_proposal"],ref(args.terrain),ref(args.contacts),ref(Path(__file__)),*painted_sources.values(),*annotations.get("authoring_references",[])]}
    contract_path=target/"town-layout.json";dump(contract_path,contract)
    # Isolated public-consumer fixture: only explicit current inputs and actual
    # compiler outputs, never a stale full mod or unrelated creature recipes.
    dependencies=set();visited_json=set()
    def collect(value):
        if isinstance(value,dict):
            if isinstance(value.get("path"),str)and isinstance(value.get("sha256"),str):
                path=verify(value);dependencies.add(path)
                if path.suffix.lower()==".json"and path not in visited_json:
                    visited_json.add(path);collect(read(path))
            for item in value.values():collect(item)
        elif isinstance(value,list):
            for item in value:collect(item)
    collect(contract);dependencies.add(contract_path)
    for path in dependencies:
        destination=fixture/path.relative_to(PROJECT);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,destination)
    dump(fixture/"content/factions.json",content["factions"])
    dump(fixture/"design/town-visuals.json",{"layout_geometry_mode":"silhouette-v2","layout_contract":ref(contract_path)})
    generated=args.generated.absolute()
    for state in images:
        animation="Content/Sprites/"+town["structures"][state]["animation"]
        definition=read(generated/animation)
        resources=[animation,*["Content/Sprites/"+definition.get("basepath","")+frame for sequence in definition["sequences"]for frame in sequence["frames"]]]
        for name in resources:
            destination=fixture/"assets/generated"/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(generated/name,destination)
    name="Content/Sprites/"+town["townBackground"]
    destination=fixture/"assets/generated"/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(generated/name,destination)
    errors,refs=consumer.inspect(fixture,content,"ionia")
    receipt={"status":"authored configuration","freeze_sha256":args.freeze_sha256,"contract":ref(contract_path),
             "public_consumer":{"path":"scripts/faction_town_layout.py","sha256":sha(WORKSPACE/"scripts/faction_town_layout.py")},
             "fixture":fixture.relative_to(PROJECT).as_posix(),"public_consumer_errors":errors,"dependency_count":len(refs),
             "actual_states":len(images),"source_physical_consumer_passed":not errors,
             "independent_semantic_review_pending":True,"physical_geometry_accepted":False,"native_execution":False,"release_accepted":False}
    dump(target/"binding-receipt.json",receipt)
    # Reuse exact state assemblies; overlays only visualize authored semantics.
    # These tiny transparent PNGs are diagnostics, never replacement game art.
    cards=[]
    for state,record in states.items():
        overlay=Image.new("RGBA",(800,374))
        marine=Image.open(PROJECT/record["marine_support_mask"]["path"]).getchannel("R")if"marine_support_mask"in record else blank()
        unsupported=ImageChops.subtract(physical[state][0],union([support,marine]))
        for mask,color in((support,(70,255,70,28)),(stairs,(255,130,0,90)),(water,(30,90,255,45)),
                           (paths,(0,220,255,190)),(physical[state][0],(100,255,0,255)),
                           (physical[state][1],(0,180,255,145)),(physical[state][2],(255,0,210,230)),
                           (unsupported,(255,0,0,255))):
            tint=Image.new("RGBA",(800,374));tint.paste(color,(0,0),mask);overlay=Image.alpha_composite(overlay,tint)
        overlay_name="semantic-overlay-"+state+".png";overlay.save(target/overlay_name)
        cards.append('<article><h2>'+html.escape(state)+'</h2><p>'+html.escape(site_for[state])+'</p><div class="stack"><img src="assemblies/state-'+state+'.png"><img class="annotation" src="'+overlay_name+'"></div><p>Foundation: lime; door/frontage: blue; approach: magenta; path: cyan; unsupported foot: red. Measured unsupported pixels: '+str(measurements[state]["unsupported_foundation_pixels"])+'.</p></article>')
    (target/"semantic-review.html").write_text('<!doctype html><meta charset="utf-8"><title>Ionia exact physical annotations</title><style>body{font:15px system-ui;background:#181b20;color:#eee;max-width:850px;margin:auto}article{margin:36px 0}.stack{width:800px;height:374px;position:relative}.stack img{position:absolute;inset:0;width:800px;height:374px}.stack .annotation{opacity:.8}.stack:hover .annotation{opacity:0}h2{margin-bottom:4px}p{line-height:1.5}</style><h1>Ionia authored physical annotations</h1><p>Exact native-size source compositions and technical mask overlays. Hover an image to hide annotations. Public-consumer errors: '+html.escape(str(errors))+'. These are authored configuration diagnostics, not native game screenshots or art/release acceptance.</p>'+''.join(cards),encoding="utf-8")
    print(json.dumps(receipt,indent=2))
    return 0 if not errors else 2


if __name__=="__main__":raise SystemExit(main())
