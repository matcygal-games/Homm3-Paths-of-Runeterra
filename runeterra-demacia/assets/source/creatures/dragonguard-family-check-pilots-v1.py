"""Check actual partial pilot pixels/provenance without granting acceptance."""
from pathlib import Path
import hashlib
import json
import sys

from PIL import Image

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / "scripts"))
from identity import canonical_action_groups


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bound_file(record):
    path = (PROJECT / record["path"]).resolve()
    assert path.is_relative_to(PROJECT), path
    assert path.is_file() and sha(path) == record["sha256"], path
    return path


family = json.loads((PROJECT / "assets/source/creatures/dragonguard-painted-pilots-v1.json").read_text())
creatures = json.loads((PROJECT / "content/creatures.json").read_text())
checks = []
for unit in family["units"]:
    folder = PROJECT / "assets/source/creatures" / unit["id"] / "dragonguard-rig-v3"
    bound_file(unit["blend"])
    bound_file(unit["raw_pose_metadata"])
    recipe_path = bound_file(unit["candidate_recipe"])
    recipe = json.loads(recipe_path.read_text())
    assert recipe["canvas"] == [450, 400] and recipe["pivot"] == {"x": 197, "y": 266}
    registered = {group["group"]: group["frames"] for group in recipe["groups"]}
    assert {group: len(frames) for group, frames in registered.items()} == {0: 6, 2: 1, 12: 6}
    padding = json.loads((folder / "painted-pilot-padding-v1.json").read_text())
    assert len(padding["conversions"]) == 16
    conversions = {item["output"]: item for item in padding["conversions"]}
    final_checks = []
    for action in unit["actions"]:
        for key in ("generation", "camera", "placement", "native_export", "contact"):
            bound_file(action[key])
        export = json.loads((PROJECT / action["native_export"]["path"]).read_text())
        for frame in export["frames"]:
            source = PROJECT / frame["output"]
            assert sha(source) == frame["sha256"], source
        for frame in sorted((folder / "native-pilot-final-v1" / f'g{action["group"]:02}').glob("*.png")):
            relative = frame.relative_to(PROJECT).as_posix()
            proof = conversions[relative]
            assert sha(frame) == proof["sha256"]
            assert proof["retained_rgba_pixels_identical"] and proof["maximum_discarded_alpha"] < 8
            original = PROJECT / proof["source"]
            assert sha(original) == proof["source_sha256"]
            with Image.open(frame) as image, Image.open(original) as before:
                assert image.mode == "RGBA" and image.size == (450, 400)
                bbox = image.getchannel("A").getbbox()
                assert bbox and min(bbox[0], bbox[1], 450 - bbox[2], 400 - bbox[3]) > 0
                rectangle = tuple(proof["retained_rectangle"])
                assert image.crop(rectangle).tobytes() == before.crop(rectangle).tobytes()
                assert image.getchannel("A").point(lambda a: 255 if a >= 8 else 0).getbbox() == tuple(proof["alpha8_bounds"])
                final_checks.append({"path": relative, "sha256": sha(frame), "size": list(image.size), "any_alpha_bounds": list(bbox)})
    assert len(final_checks) == 16
    for frames in registered.values():
        for frame in frames:
            assert sha(PROJECT / frame["source"]) == frame["sha256"]
    idle = registered[2][0]["sha256"]
    assert all(frame["sha256"] != idle for group in (0, 12) for frame in registered[group])
    required = canonical_action_groups(recipe, creatures)
    missing = sorted(set(required) - set(registered))
    assert missing, "A partial three-group pilot must never imply complete canonical actions"
    checks.append({"id": unit["id"], "source_cells_checked": len(final_checks), "registered_entries_checked": sum(map(len, registered.values())),
        "groups": {str(group): len(frames) for group, frames in registered.items()}, "still_missing_canonical_groups": missing,
        "additional_corpse_group22": "Still missing painted death/corpse; raw source only", "frames": final_checks})

output = {"status": "Partial source pixel/provenance checks passed; not complete animation or native acceptance",
    "units": checks, "total_actual_native_source_frames_checked": sum(unit["source_cells_checked"] for unit in checks),
    "registered_partial_entries_checked": sum(unit["registered_entries_checked"] for unit in checks),
    "checks": ["All source/recipe/generation/camera/placement/export/contact hashes current", "All actual source PNGs RGBA450x400 and nonclipping",
        "All retained RGBA identical to original native export; discarded padding alpha below8 only", "Every registered entry bound to actual checked PNG; walk/thrust are not idle copies",
        "Missing canonical actions remain explicitly reported; no finality inferred"],
    "visual_approval_granted": False, "native_runtime_tested": False, "active_assets_modified": False}
target = PROJECT / "assets/source/creatures/dragonguard-painted-pilot-checks-v1.json"
target.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
print(f'Checked{output["total_actual_native_source_frames_checked"]} genuine native partial-source frames, {output["registered_partial_entries_checked"]} registered entries; full canonical requirements remain unmet.')
