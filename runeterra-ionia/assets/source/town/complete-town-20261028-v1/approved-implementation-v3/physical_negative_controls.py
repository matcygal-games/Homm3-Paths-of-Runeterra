"""Exercise real physical rejection in the isolated Ionia public-consumer fixture.

No production or painted-source writes. Every control starts from the byte-exact
valid baseline and restores all fixture files in a finally block. The translated
building changes the actual source PNG, compiled selected PNG, physical masks,
entrances, all-state site silhouette and every affected contract hash together.
It must reach a physical foundation failure, never a stale-checksum rejection.

The stair and water controls also move an actual whole building into the real
independently authored stair/water masks. Terrain, support and the background
remain unchanged in all three placement controls. No support is fitted to feet
and no artificial water/stair patch is drawn under an otherwise valid building.
"""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import sys

from PIL import Image, ImageChops, ImageDraw

from consumer_replay import changed, direct, encoded, fixture, inspect, inventory, read, sha

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=="runeterra-ionia")


def png(image):
    stream=BytesIO();image.save(stream,format="PNG");return stream.getvalue()


def moved(image,dx,dy):
    result=Image.new(image.mode,image.size);result.paste(image,(dx,dy));return result


def binary(root,reference):
    return Image.open(direct(root,reference["path"])).convert("L")


def count(mask):return mask.histogram()[255]


def polygon(points):
    mask=Image.new("L",(800,374));ImageDraw.Draw(mask).polygon([tuple(p)for p in points],fill=255);return mask


def union(items):
    result=Image.new("L",(800,374))
    for item in items:result=ImageChops.lighter(result,item)
    return result


def rebound(root,contract,updates):
    """Repin every occurrence of an affected direct fixture reference."""
    import hashlib
    def visit(value):
        if isinstance(value,dict):
            if value.get("path")in updates and "sha256"in value:
                value["sha256"]=hashlib.sha256(updates[value["path"]]).hexdigest()
            for item in value.values():visit(item)
        elif isinstance(value,list):
            for item in value:visit(item)
    visit(contract)
    design=read(direct(root,"design/town-visuals.json"))
    contract_name=design["layout_contract"]["path"]
    updates[contract_name]=encoded(contract)
    design["layout_contract"]["sha256"]=hashlib.sha256(updates[contract_name]).hexdigest()
    updates["design/town-visuals.json"]=encoded(design)
    return updates


def translated_control(root,contract,content,control):
    state=control["state"];dx,dy=control["translation"]
    if not all(type(v)is int for v in(dx,dy))or(dx,dy)==(0,0):raise ValueError("A real nonzero integer translation is required")
    site=next(s for s in contract["sites"]if state in s["states"])
    if site["id"]in("coast","grail"):raise ValueError("Translation must use a real ordinary building")
    source=contract["frames"][state];frame=Image.open(direct(root,source["path"])).convert("RGBA")
    original_box=frame.getchannel("A").getbbox()
    if not(0<=original_box[0]+dx<original_box[2]+dx<=800 and 0<=original_box[1]+dy<original_box[3]+dy<=374):
        raise ValueError("Negative translation may not crop any actual source pixel")
    shifted=moved(frame,dx,dy);updates={source["path"]:png(shifted)}
    structure=content["ionia"]["town"]["structures"][state]
    definition=read(direct(root,"assets/generated/Content/Sprites/"+structure["animation"]))
    selected="assets/generated/Content/Sprites/"+definition.get("basepath","")+definition["sequences"][0]["frames"][0]
    updates[selected]=updates[source["path"]]
    record=contract["silhouette_plan"]["states"][state]
    for key in("body_mask","foundation_mask","door_mask","approach_mask"):
        updates[record[key]["path"]]=png(moved(binary(root,record[key]),dx,dy).convert("RGBA"))
    record["entrance"]=[record.get("entrance",site["entrance"])[0]+dx,record.get("entrance",site["entrance"])[1]+dy]
    # Audit-only whole-contact role references stay geometrically consistent too.
    for key,value in contract.get("complete_contact_role_partition",{}).get(state,{}).items():
        if isinstance(value,dict)and"path"in value:
            updates[value["path"]]=png(moved(binary(root,value),dx,dy).convert("RGBA"))
    all_state=union((shifted if name==state else Image.open(direct(root,contract["frames"][name]["path"]))).getchannel("A").point(lambda p:255 if p>=8 else 0)for name in site["states"])
    updates[site["silhouette_mask"]["path"]]=png(all_state.convert("RGBA"))
    box=all_state.getbbox();site["box"]=[box[0],box[1],box[2]-box[0],box[3]-box[1]]
    if len(site["states"])==1:site["entrance"]=record["entrance"]
    foundation=moved(binary(root,record["foundation_mask"]),dx,dy)
    plan=contract["silhouette_plan"]
    unsupported=ImageChops.subtract(foundation,binary(root,plan["support_mask"]))
    stairs=ImageChops.multiply(foundation,binary(root,plan["stairs_mask"]))
    water=ImageChops.multiply(foundation,binary(root,plan["water_mask"]))
    if not count(unsupported)and not count(stairs):raise ValueError("Chosen actual displaced building still has level support")
    if control["kind"]=="stairs-placement"and count(stairs)<3:
        raise ValueError("Stair placement must put at least three actual foot pixels on the actual unchanged stairs")
    if control["kind"]=="water-placement"and count(water)<3:
        raise ValueError("Water placement must put at least three actual foot pixels on the actual unchanged external water")
    render_order=sorted([s for s in plan["complete_scene_states"]if s not in site["states"]]+[state],key=lambda s:content["ionia"]["town"]["structures"][s]["z"])
    scene=Image.open(direct(root,contract["background"]["path"])).convert("RGBA")
    for name in render_order:
        scene.alpha_composite(shifted if name==state else Image.open(direct(root,contract["frames"][name]["path"])).convert("RGBA"))
    return updates,{"state":state,"translation":[dx,dy],"complete_nontransparent_source_pixels_preserved":True,"source_and_compiled_pngs_identical":True,
                    "negative_render_order":render_order,"terrain_support_and_background_unchanged":True,
                    "negative_selected_png_rebound_directly":True,"compiler_executed_during_this_control":False,
                    "shifted_foundation_pixels":count(foundation),"unsupported_pixels":count(unsupported),"stair_pixels":count(stairs),"external_water_pixels":count(water),"physical_intersection_bounds":unsupported.getbbox()},scene,unsupported


def path_control(root,contract,control):
    plan=contract["silhouette_plan"];path=binary(root,plan["paths_mask"]);cut=polygon(control["polygon"])
    removed=ImageChops.multiply(path,cut)
    if not count(removed):raise ValueError("Path cut must remove real selected network pixels")
    remaining=ImageChops.subtract(path,cut)
    if not count(remaining):raise ValueError("Path cut must leave the actual remaining network")
    return {plan["paths_mask"]["path"]:png(remaining.convert("RGBA"))},{"polygon":control["polygon"],"removed_path_pixels":count(removed),"remaining_path_pixels":count(remaining)},Image.open(direct(root,contract["background"]["path"])).convert("RGBA"),removed


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--fixture",type=Path,required=True);parser.add_argument("--controls",type=Path,required=True);parser.add_argument("--out",type=Path,required=True);args=parser.parse_args()
    root=fixture(args.fixture);out=args.out.absolute()
    if not out.is_relative_to(PROJECT/"build/reports/complete-town-20261028-v1"):raise ValueError("Report leaves owned unique namespace")
    spec=read(args.controls)
    if len(spec["controls"])!=4 or {c["kind"]for c in spec["controls"]}!={"translated-building","stairs-placement","water-placement","disconnected-path"}:raise ValueError("Exactly four independently meaningful physical controls are required")
    baseline=inventory(root);consumer_before=sha(PROJECT.parent/"scripts/faction_town_layout.py");errors,deps=inspect(root)
    if errors:raise ValueError("Physical controls require a valid actual public-consumer baseline: "+str(errors))
    out.mkdir(parents=True,exist_ok=False);design=read(direct(root,"design/town-visuals.json"));contract_name=design["layout_contract"]["path"]
    receipts=[]
    for control in spec["controls"]:
        contract=read(direct(root,contract_name));content=read(direct(root,"content/factions.json"))
        if control["kind"]=="disconnected-path":updates,measurement,scene,hit=path_control(root,contract,control)
        else:updates,measurement,scene,hit=translated_control(root,contract,content,control)
        updates=rebound(root,contract,updates);tint=Image.new("RGBA",scene.size);tint.paste((255,30,0,210),(0,0),hit)
        Image.alpha_composite(scene,tint).save(out/(control["kind"]+"-actual-physical-perturbation.png"))
        with changed(root,updates):
            observed,_=inspect(root)
            mutation_inventory={name:sha(direct(root,name))for name in sorted(updates)}
        restored=inventory(root)==baseline;restored_errors,_=inspect(root)
        expected="Town walkable mask has disconnected components: global paths"if control["kind"]=="disconnected-path"else"Actual foundation lacks level support or lands on stairs/water: "+control.get("expected_state",control["state"])
        consumer_stable=sha(PROJECT.parent/"scripts/faction_town_layout.py")==consumer_before
        passed=len(observed)==1 and expected in observed[0] and restored and not restored_errors and consumer_stable
        receipts.append({"kind":control["kind"],"expected_physical_error":expected,"observed_errors":observed,"measurement":measurement,"mutated_files":mutation_inventory,"baseline_restored_byte_exact":restored,"restored_public_consumer_errors":restored_errors,"unchanged_public_consumer":consumer_stable,"physical_rejection_passed":passed})
        (out/(control["kind"]+"-receipt.json")).write_bytes(encoded(receipts[-1]))
        if not passed:break
    final=inventory(root);result={"status":"authored configuration","controls_sha256":sha(args.controls),"consumer_sha256":consumer_before,"consumer_sha256_after":sha(PROJECT.parent/"scripts/faction_town_layout.py"),"baseline_public_consumer_errors":errors,"baseline_dependency_count":len(deps),"controls":receipts,"all_requested_physical_controls_executed":len(receipts)==4,"all_physical_controls_passed":len(receipts)==4 and all(r["physical_rejection_passed"]for r in receipts),"fixture_inventory_before":baseline,"fixture_inventory_after":final,"baseline_restored_byte_exact":baseline==final,"native_execution":False,"art_acceptance":False,"release_accepted":False}
    (out/"receipt.json").write_bytes(encoded(result));print(json.dumps({k:result[k]for k in("all_requested_physical_controls_executed","all_physical_controls_passed","baseline_restored_byte_exact")}));return 0 if result["all_physical_controls_passed"]and baseline==final else 2


if __name__=="__main__":raise SystemExit(main())
