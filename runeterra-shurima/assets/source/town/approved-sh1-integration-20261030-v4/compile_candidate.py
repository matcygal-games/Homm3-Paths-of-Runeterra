"""Compile only SH1 source candidates, with exact native output pins.

No active recipe, generated cache, manifest, content or stage is written.
"""
from build_candidate import *


def generation_ledger():
    names = ["approved-full-raw.png", "approved-full-native.png", "early-states-raw.png", "early-states-native.png",
             "middle-states-raw.png", "middle-states-native.png", "late-states-raw.png", "late-states-native.png",
             "empty-recovery-raw.png", "empty-recovery-native.png", "hidden-face-completion-raw-v1.png", "hidden-face-completion-native-v1.png",
             "sky-inpaint-input-crop-v2.png", "sky-inpaint-removal-mask-v2.png", "sky-inpaint-raw-v2.png", "sky-inpaint-native-crop-v2.png"]
    record = {
        "status": "authored configuration", "workflow": "image-based-painted-2d", "derived_from_blender": False,
        "approved_code": "SH1", "preserved_parent_ledger": ref(HERE/"generation-ledger.json"),
        "sources": {name: ref(HERE/name) for name in names},
        "hidden_face_completion": {
            "tool": "built-in image_gen.imagegen", "use_case": "precise-object-edit", "provider": "OpenAI", "model": "Not exposed by tool",
            "generated_original": "C:/Users/matcy/.codex/generated_images/01a158d4-4bfa-7ad3-9641-2f065f9b313e/exec-5e25862f-ec38-4e8f-86c7-310d63768a64.png",
            "prompt": ref(HERE/"hidden-face-completion-prompt-v1.txt"), "input": ref(HERE/"approved-full-raw.png"),
            "native_conversion": "Uniform whole-scene Lanczos conversion to800x374; only recorded foreground-occluded rear pixels enter the candidate layers.",
        },
        "occluded_sky_completion": {
            "tool": "built-in image_gen.imagegen", "provider": "OpenAI", "model": "Not exposed by tool",
            "generated_original": "C:/Users/matcy/.codex/generated_images/01a158d4-4bfa-7ad3-9641-2f065f9b313e/exec-4370e51a-61f3-4ee2-8ec5-33342b9441b8.png",
            "prompt": ref(HERE/"sky-inpaint-prompt-v2.txt"), "input": ref(HERE/"sky-inpaint-input-crop-v2.png"), "guide_mask": ref(HERE/"sky-inpaint-removal-mask-v2.png"),
            "guide_conversion": "Approved native crop (70,0,196,56), nearest 4x technical editing guide; frozen guide mask separately preserved.",
            "native_conversion": "Ancestral painted ridge/lower-sky source: whole generated crop Lanczos126x56. Final v3 uses the bounded gradient-domain composition receipt, not the historical hard cut.",
            "final_application_mask": ref(HERE/"geometry/sky-recovery-budget.png"),
            "residual": "Historical hard-cut boundary is the v2 rejected defect; v3 has a separate reproducible bounded gradient-domain composition. No final visual acceptance granted.",
        },
        "unselected_preserved_sky_attempt": {"sources": ["sky-recovery-raw-v1.png", "sky-recovery-native-v1.png"], "prompt": "sky-recovery-prompt-v1.txt", "selected": False, "reason": "Whole-scene sky recovery insufficiently matched the approved sky; superseded by bounded crop recovery. Historical edit input was not frozen byte-exact and is not claimed reproducible."},
        "unselected_bounded_sky_repair_v3": {
            "tool":"built-in image_gen.imagegen", "provider":"OpenAI", "model":"Not exposed by tool", "selected":False,
            "generated_original":"C:/Users/matcy/.codex/generated_images/01a158d4-4bfa-7ad3-9641-2f065f9b313e/exec-e1571c98-c6a7-4c3b-806c-bf7f986b606d.png",
            "prompt":ref(HERE/"sky-repair-prompt-v3.txt"),"input":ref(HERE/"sky-repair-input-crop-v3.png"),"guide":ref(HERE/"sky-repair-guide-mask-v3.png"),
            "raw":ref(HERE/"sky-repair-raw-v3.png"),"native":ref(HERE/"sky-repair-native-crop-v3.png"),
            "native_conversion":"Whole generated crop Lanczos to150x65, placed at60,0; attempted composite confined to the frozen recovery budget; proposed background is unselected.",
            "reason":"Actual constrained composite still shows an angled colour transition at immutable original sky. No clear visual improvement over v2; retained as failed bounded repair history, not selected.",
        },
        "selected_v3_painted_recovery": {
            "tool":"built-in image_gen.imagegen","provider":"OpenAI","model":"Not exposed by tool","workflow":"Painted2D sources plus standard bounded gradient-domain raster composition; no scenery geometry generation.",
            "sky_generation":{"original":"C:/Users/matcy/.codex/generated_images/01a158d4-4bfa-7ad3-9641-2f065f9b313e/exec-bd8da004-c310-42ad-b0b9-ea1610174a86.png","input":ref(HERE/"sky-repair-input-crop-v4.png"),"guide":ref(HERE/"sky-repair-guide-mask-v4.png"),"prompt":ref(HERE/"sky-repair-prompt-v4.txt"),"raw":ref(HERE/"sky-repair-raw-v4.png")},
            "finial_generation":{"original":"C:/Users/matcy/.codex/generated_images/01a158d4-4bfa-7ad3-9641-2f065f9b313e/exec-61deb740-0ba7-44ab-85c7-aa4ff5666c7a.png","input":ref(HERE/"civic-finial-removal-input-v1.png"),"guide":ref(HERE/"civic-finial-removal-guide-v1.png"),"prompt":ref(HERE/"civic-finial-removal-prompt-v1.txt"),"raw":ref(HERE/"civic-finial-removal-raw-v1.png")},
            "technical_composition":ref(HERE/"painted-recovery-seamless-conversion-v5.json"),"output":ref(HERE/"painted-recovery-seamless-native-v5.png"),
            "rejected_technical_attempt":"sky-repair-palette-conversion-v4.json (whole-crop palette matching alone did not solve the boundary; preserved, unselected)",
        },
        "v4_tip_ownership_repair":{"source_trace":ref(HERE/"finial-ownership-source-v4.json"),"painted_fill_reused":ref(HERE/"empty-recovery-native.png"),"conversion":ref(HERE/"painted-recovery-seamless-conversion-v5.json"),"scope":"Whole native solar-spire and grey-metal guild-crown tips/edges. Existing genuine painted empty sky is reused only under newly owned architecture; original full RGB is unchanged."},
        "producers": {name: ref(HERE/name) for name in ("build_candidate.py", "blend_painted_recovery.py", "compile_candidate.py", "prepare_contract.py", "verify_candidate.py")},
        "policy_quotes": [
            "Derive click masks/highlights from selected visible silhouettes.",
            "Rear buildings need level landings supporting their complete root, foundation and contact-shadow profiles.",
            "The terrain plate must not contain completed functional architecture.",
        ],
        "scope": "Painted source and deterministic technical annotation/assembly only; no native or final art/rights acceptance.",
    }
    dump(HERE/"generation-ledger-v2.json",record)


def compile_candidate():
    generation_ledger()
    idx = read(HERE/"candidate-frames.json")
    compiler = create_compiler("shurima")
    packet = []
    source_prefix = HERE.relative_to(PROJECT).as_posix()
    output_prefix = "Content/Sprites/runeterra/shurima/"

    def common(master):
        return {
            "production_status": "painted-master-complete-unapproved", "visual_approval_granted": False,
            "credits": {"author": "Project-directed original painted2D via built-in OpenAI image_gen; technical SH1 decomposition", "license": None, "redistribution": "Unresolved; no release approval"},
            "generation": {
                "image_generation_used": True, "workflow": "image-based-painted-2d", "derived_from_blender": False,
                "provider": "OpenAI built-in image_gen", "model": "Not exposed by built-in tool",
                "prompt": "Approved SH1 complete town, genuine early/middle/late construction edits and bounded painted hidden-face completion. Exact prompts, ancestry and native conversion are pinned in generation-ledger-v2.json.",
                "painted_master": master.relative_to(PROJECT).as_posix(), "painted_master_sha256": sha(master),
                "source_generation_ledger": source_prefix+"/generation-ledger-v2.json", "source_generation_ledger_sha256": sha(HERE/"generation-ledger-v2.json"),
            },
        }

    def raster(source, output, role):
        size = list(Image.open(source).size)
        return {**common(HERE/"approved-full-raw.png"), "recipe_type":"raster", "output_path":output_prefix+output,
                "role":role, "canvas":size, "source_canvas":size, "source":source.relative_to(PROJECT).as_posix(), "source_sha256":sha(source), "fit":"exact"}

    def put(name, recipe):
        target = HERE/"candidate-recipes"/(name+".json")
        dump(target,recipe)
        packet.append(target)

    put("background",raster(HERE/"background-native.png","town/background.png","town-background"))
    for state,row in sorted(idx["states"].items()):
        master = HERE/("approved-full-raw.png" if row["source_tag"]=="approved" else row["source_tag"]+"-states-raw.png")
        frame = PROJECT/row["frame"]["path"]
        put(state,{**common(master),"recipe_type":"vcmi_animation","output_path":output_prefix+"town/structures/"+state+".json",
            "role":"town-structure-animation","canvas":[800,374],"pivot":{"x":0,"y":0,"basis":"Full native canvas; approved SH1 registration is in exact source pixels"},
            "generateShadow":0,"generateOverlay":0,"groups":[{"group":0,"frames":[{"source":frame.relative_to(PROJECT).as_posix(),"sha256":sha(frame),"source_canvas":[800,374]}]}]})
        for suffix in ("area","border","campaign"):
            put(state+"_"+suffix,raster(HERE/"derived"/(state+"_"+suffix+".png"),"town/structures/"+state+"_"+suffix+".png","town-structure-"+suffix))
    ids = compiler.indexed_building_ids(PROJECT)
    put("buildingIcons",{**common(HERE/"approved-full-raw.png"),"recipe_type":"indexed_animation","output_path":output_prefix+"town/buildingIcons.json",
        "role":"town-construction-icons","canvas":[150,70],"pivot":{"x":0,"y":0,"basis":"Actual native BuildingIDs, including sparse UI slots"},
        "frames":[{"building":key,"frame":number,"source":(HERE/"construction"/(key+".png")).relative_to(PROJECT).as_posix(),
                   "source_sha256":sha(HERE/"construction"/(key+".png")),"source_canvas":[150,70]} for key,number in sorted(ids.items(),key=lambda x:x[1])]})
    runs = []
    receipts = []
    payload = {}
    for run in range(2):
        outputs = {}
        current = []
        for recipe_path in packet:
            values,receipt = compiler.plan(PROJECT,recipe_path)
            if set(values)&set(outputs):
                raise ValueError("Duplicate candidate output")
            outputs.update(values)
            current.append(receipt)
        runs.append({name:hashlib.sha256(data).hexdigest() for name,data in sorted(outputs.items())})
        if run==0:
            payload,receipts = outputs,current
    if runs[0]!=runs[1]:
        raise ValueError("Native compilation changed between actual runs")
    for name,data in payload.items():
        path = REPORT/"native-candidate"/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    result = {"status":"authored configuration","candidate_only":True,"actual_conversion_runs":2,"deterministic":True,
              "converter":"scripts/faction_art_compile.py:create_compiler('shurima').plan", "converter_sha256":sha(ROOT/"scripts/faction_art_compile.py"),
              "logical_recipes":len(packet),"physical_outputs":len(payload),"native_output_pins":runs[0],"receipts":receipts,
              "recipes":[{"recipe":f.relative_to(PROJECT).as_posix(),"sha256":sha(f),"output_path":read(f)["output_path"]} for f in packet],
              "canonical_generated_or_stage_writes":False,"selection_authorized":False}
    dump(HERE/"candidate-selection.json",result)
    dump(report_path("conversion-twice"),result)
    return result


if __name__ == "__main__":
    result = compile_candidate()
    print(json.dumps({key:result[key] for key in ("actual_conversion_runs","deterministic","logical_recipes","physical_outputs")}))
