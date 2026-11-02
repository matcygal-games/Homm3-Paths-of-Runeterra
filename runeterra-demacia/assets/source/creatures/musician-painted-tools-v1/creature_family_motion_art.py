"""Source-only provenance, measured cameras and exports for rigged families.

This never writes active recipes, generated assets, manifests or staged mods.
An imagegen result is preserved verbatim. Native export requires an explicitly
measured whole-atlas camera; input padding is not assumed to survive generation.
RGBA extrema alone do not prove clean cutouts. Inspect an opaque-background
alpha composite and actual gutters; transparent pixels may contain colored RGB.
This helper never removes a painted halo or synthesizes an alpha mask.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil

from PIL import Image


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, data: dict):
    path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")


def own_folder(project: Path, unit: str, folder: Path) -> Path:
    project=Path(project).resolve();folder=Path(folder)
    if not folder.is_absolute():
        folder=project/folder
    folder=folder.resolve()
    expected=(project/"assets/source/creatures"/unit).resolve()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*",unit) or not folder.is_relative_to(expected) or folder==expected:
        raise ValueError("Family art must stay in an explicit unit-owned source revision folder")
    if not folder.is_dir():
        raise ValueError("Existing source revision folder required")
    return folder


def proof(project: Path, path: Path) -> dict:
    path=Path(path).resolve()
    if not path.is_relative_to(project.resolve()) or not path.is_file():
        raise ValueError("Reference must be an actual project-owned input or private reference")
    return {"path":path.relative_to(project).as_posix(),"sha256":sha(path)}


def record_generation(project: Path, unit: str, folder: Path, metadata_path: Path,
                      group: int, generated: Path, prompt: Path,
                      references: list[Path], atlas_metadata: Path, version: int = 1) -> dict:
    project=Path(project).resolve();folder=own_folder(project,unit,folder)
    if group<0 or version<1:
        raise ValueError("Invalid source group/version")
    generated,prompt,metadata_path,atlas_metadata=map(lambda p:Path(p).resolve(),(generated,prompt,metadata_path,atlas_metadata))
    meta=json.loads(metadata_path.read_text());atlas=json.loads(atlas_metadata.read_text())
    poses=meta["actions"][str(group)]
    columns,rows=atlas["layout"]
    if len(poses)!=columns*rows or any(p["index"]!=i for i,p in enumerate(poses)):
        raise ValueError("Atlas cells must retain every actual ordered pose index")
    refs=[Path(ref).resolve() for ref in references]
    target_ref=atlas.get("padded_output",atlas.get("output"))
    if target_ref and refs[0]!=(project/target_ref).resolve():
        raise ValueError("First imagegen reference must be the actual recorded edit target")
    target=folder/f"paint-action-g{group:02}-atlas-v{version}.png"
    if target.exists() and sha(target)!=sha(generated):
        raise ValueError("Preserve existing generated result; select another explicit version")
    if generated!=target and not target.exists():
        shutil.copyfile(generated,target)
    errors=[]
    with Image.open(target) as image:
        image.load();dimensions=list(image.size);mode=image.mode
        alpha=image.getchannel("A").getextrema() if mode=="RGBA" else None
        if mode!="RGBA" or not alpha or alpha[0]!=0 or alpha[1]<250:
            errors.append("Result does not have genuine transparent RGBA foreground/background")
        cell=[image.width/columns,image.height/rows]
        diagnostics={"requires_opaque_background_composite_visual_review":True}
        if mode=="RGBA":
            alpha_image=image.getchannel("A");histogram=alpha_image.histogram()
            diagnostics.update({"alpha8_bbox":alpha_image.point(lambda value:255 if value>=8 else 0).getbbox(),
                                "fully_transparent_pixels":histogram[0],"faint_alpha1_to7_pixels":sum(histogram[1:8]),
                                "note":"Colored RGB in alpha0pixels is invisible to a correct compositor; extrema do not establish clean interior/gutters or art acceptance."})
    record={"unit":unit,"group":group,"version":version,"tool":"built-in image_gen.imagegen",
            "generated_original":str(generated),"generated_original_sha256":sha(generated),
            "output":target.relative_to(project).as_posix(),"output_sha256":sha(target),
            "prompt":proof(project,prompt),"references":[proof(project,ref) for ref in refs],
            "actual_source_metadata":proof(project,metadata_path),"actual_atlas_metadata":proof(project,atlas_metadata),
            "layout":[columns,rows],"returned_dimensions":dimensions,"returned_cell":cell,
            "grid_integer_aligned":all(value.is_integer() for value in cell),
            "grid_note":"Logical equal-cell extents may fall on half-pixels; export uses one fixed continuous source-box scale, without per-cell fitting.",
            "mode":mode,"alpha_extrema":list(alpha) if alpha else None,
            "alpha_diagnostics":diagnostics,
            "source_input_transform":atlas.get("padding",atlas.get("source_transform")),
            "actual_pose_indices":[pose["index"] for pose in poses],
            "intentional_source_pose_holds":atlas.get("intentional_exact_pose_holds",[]),
            "validation_errors":errors,"status":"generated source candidate; actual grid/camera/native motion review required",
            "visual_approval_granted":False,"active_assets_modified":False}
    write(folder/f"paint-action-g{group:02}-atlas-v{version}-generation.json",record)
    return record


def calibrate_generation(project: Path, generation_record: Path, *, reference_index: int,
                         head_top_y: float, ground_y: float, root_x: float,
                         target_height: float, basis: str, version: int = 1,
                         target_root_x: int = 197) -> dict:
    """Use manually observed head/ground/root landmarks in ONE actual cell.

    Coordinates are in its returned cell, without assuming original512 framing.
    All frames in that atlas share this same uniform scale and translation.
    """
    project=Path(project).resolve();generation_record=Path(generation_record).resolve()
    record=json.loads(generation_record.read_text())
    folder=own_folder(project,record["unit"],generation_record.parent)
    atlas=project/record["output"]
    if sha(atlas)!=record["output_sha256"] or record["validation_errors"]:
        raise ValueError("Generation source changed or failed actual grid/alpha checks")
    if not 0<=reference_index<len(record["actual_pose_indices"]) or not 0<target_height<200 or ground_y<=head_top_y or not basis.strip():
        raise ValueError("Measured whole-atlas body camera requires actual reference landmarks and explanation")
    if type(target_root_x) is not int or not 0 < target_root_x < 450:
        raise ValueError("Native target root must be an integer inside the450pixel frame")
    width,height=record["returned_cell"]
    if not (0<=head_top_y<ground_y<=height and 0<=root_x<=width):
        raise ValueError("Reference landmarks must lie within an actual returned cell")
    scale=target_height/(ground_y-head_top_y)
    result={"unit":record["unit"],"group":record["group"],"version":version,
            "generation_record":proof(project,generation_record),"source":proof(project,atlas),
            "reference_index":reference_index,"source_landmarks":{"head_top_y":head_top_y,"ground_y":ground_y,"root_x":root_x},
            "target":{"height":target_height,"root_x":target_root_x,"ground_y":267,"canvas":[450,400]},
            "scale":scale,"offset":[target_root_x-root_x*scale,267-ground_y*scale],"basis":basis,
            "policy":"One actual returned-atlas camera only. No per-frame scale, recenter, limb/pose warp or inferred generator shrink.",
            "visual_approval_granted":False,"active_assets_modified":False}
    target=folder/f"paint-action-g{record['group']:02}-camera-v{version}.json"
    if target.exists() and json.loads(target.read_text())!=result:
        raise ValueError("Preserve existing measured camera; select a new camera version")
    write(target,result)
    return result


def export_generation(project: Path, generation_record: Path, camera_record: Path,
                      version: int = 1, *, placements: list[dict] | None = None,
                      placement_version: int = 1) -> dict:
    project=Path(project).resolve();generation_record=Path(generation_record).resolve();camera_record=Path(camera_record).resolve()
    record=json.loads(generation_record.read_text());camera=json.loads(camera_record.read_text())
    folder=own_folder(project,record["unit"],generation_record.parent)
    if camera["generation_record"]!=proof(project,generation_record) or camera["source"]!=proof(project,project/record["output"]):
        raise ValueError("Measured camera no longer binds the actual generation source")
    if camera["unit"]!=record["unit"] or camera["group"]!=record["group"]:
        raise ValueError("Camera belongs to another actual source action")
    columns,rows=record["layout"];width,height=record["returned_cell"]
    scale=camera["scale"];size=(round(width*scale),round(height*scale));offset=tuple(round(v) for v in camera["offset"])
    suffix="";placement_path=None
    if placements is not None:
        if type(placement_version) is not int or placement_version<1 or len(placements)!=len(record["actual_pose_indices"]):
            raise ValueError("Provide one versioned whole-frame placement per actual source pose")
        for index,item in enumerate(placements):
            delta=item.get("native_translation")
            if (item.get("index")!=index or not isinstance(delta,list) or len(delta)!=2
                    or any(type(value) is not int for value in delta) or not item.get("basis")
                    or (any(delta) and item.get("reviewed") is not True)):
                raise ValueError("Nonzero complete-frame translations require explicit index, integer delta and reviewed measured basis")
            if set(item)-{"index","native_translation","reviewed","basis","evidence"}:
                raise ValueError("Whole-frame placement cannot request per-frame scale, crop or pose/limb warp")
            for evidence in item.get("evidence",[]):
                if evidence!=proof(project,project/evidence["path"]):
                    raise ValueError("Placement measurement evidence changed")
        placement_path=folder/f"paint-action-g{record['group']:02}-placement-v{placement_version}.json"
        placement_proof={"unit":record["unit"],"group":record["group"],"version":placement_version,
                         "generation_record":proof(project,generation_record),"camera_record":proof(project,camera_record),
                         "placements":placements,"fixed_scale":scale,
                         "policy":"Measured integer translations of COMPLETE rendered frames only; no per-frame resizing, cropping, limb warp or pose synthesis.",
                         "visual_approval_granted":False,"active_assets_modified":False}
        if placement_path.exists() and json.loads(placement_path.read_text())!=placement_proof:
            raise ValueError("Preserve previous measured placements; choose a new placement version")
        write(placement_path,placement_proof)
        suffix=f"-placement-v{placement_version}"
    else:
        placements=[{"index":index,"native_translation":[0,0],"reviewed":False,
                     "basis":"No whole-frame layout correction; native review pending"} for index in record["actual_pose_indices"]]
    dest=folder/f"paint-action-g{record['group']:02}-native-export-v{version}{suffix}"
    dest.mkdir(exist_ok=True);frames=[]
    with Image.open(project/record["output"]) as atlas:
        atlas.load()
        for index in record["actual_pose_indices"]:
            x,y=(index%columns)*width,(index//columns)*height
            # Fractional generated grid boundaries retain the SAME logical cell
            # width and uniform whole-atlas camera for every frame. Direct box
            # resampling avoids alternating444/443pixel crops and implicit fits.
            native_cell=atlas.resize(size,Image.Resampling.LANCZOS,box=(x,y,x+width,y+height))
            bounds=native_cell.getchannel("A").point(lambda value:255 if value>=8 else 0).getbbox()
            if bounds is None:
                raise ValueError("Generated action contains an empty subject cell")
            delta=placements[index]["native_translation"]
            frame_offset=(offset[0]+delta[0],offset[1]+delta[1])
            placed=(bounds[0]+frame_offset[0],bounds[1]+frame_offset[1],bounds[2]+frame_offset[0],bounds[3]+frame_offset[1])
            if placed[0]<0 or placed[1]<0 or placed[2]>450 or placed[3]>400:
                raise ValueError(f"Real subject g{record['group']}f{index} clips native canvas; remeasure whole-atlas camera")
            native=Image.new("RGBA",(450,400));native.alpha_composite(native_cell,frame_offset)
            output=dest/f"g{record['group']:02}-f{index:03}.png"
            if output.exists():
                with Image.open(output) as previous:
                    if previous.mode!="RGBA" or previous.size!=native.size or previous.tobytes()!=native.tobytes():
                        raise ValueError("Preserve prior native export; use another explicit version")
            else:
                native.save(output)
            frames.append({"index":index,"source_cell":[x,y,width,height],"output":output.relative_to(project).as_posix(),
                           "sha256":sha(output),"alpha8_bbox":list(placed),"pixel_sha256":hashlib.sha256(native.tobytes()).hexdigest(),
                           "placement":placements[index]})
    result={"unit":record["unit"],"group":record["group"],"version":version,"generation_record":proof(project,generation_record),
            "camera_record":proof(project,camera_record),"actual_returned_cell":[width,height],"fixed_scale":scale,"fixed_offset":list(offset),
            "native_canvas":[450,400],"frames":frames,"source_holds":record["intentional_source_pose_holds"],
            "placement_record":proof(project,placement_path) if placement_path else None,
            "status":"source native frames only; identity/grounding/action continuity and native renderer review remain required",
            "visual_approval_granted":False,"active_assets_modified":False}
    write(folder/f"paint-action-g{record['group']:02}-native-export-v{version}{suffix}.json",result)
    return result
