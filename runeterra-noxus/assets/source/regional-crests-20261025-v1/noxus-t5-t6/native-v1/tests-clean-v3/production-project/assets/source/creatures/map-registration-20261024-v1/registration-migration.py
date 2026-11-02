"""One-time measured registration repair; preserves existing painted pixels.

This does not generate artwork. The production compiler consumes the resulting
versioned PNGs; this migration is not rerun by assets/build commands.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import importlib.util
import json
import shutil
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
WORKSPACE = PROJECT.parent
REPORT = HERE / "survivor-map-registration"
SOURCE = PROJECT / "assets/source/creatures/map-registration-20261024-v1"
BEFORE = PROJECT / "build/history/nx24-survivor-maps"
NEW = {"guildKnifeThrower", "masterKnifeThrower", "arachnoidSentry", "broodSentry", "boundRuinManifestation", "greaterRuinManifestation"}
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
rel = lambda path: path.relative_to(PROJECT).as_posix()

def main():
    pins = json.loads((HERE.parent / "independent/survivor-map-before-pins.json").read_text())
    for name, expected in pins["before_sha256"].items():
        path = Path(name)
        assert path.resolve().is_relative_to(PROJECT.resolve()) and path.is_file()
        assert sha(path) == expected, name
    content_before = {rel(path):sha(path) for path in (PROJECT/"content").glob("*.json")}
    creatures = json.loads((PROJECT/"content/creatures.json").read_text())
    units = set(creatures)-NEW
    assert len(units) == 8 and units == set(pins["units"])
    assert not SOURCE.exists() and not BEFORE.exists(), "Do not overwrite a completed migration"
    for folder in (SOURCE, BEFORE, REPORT):
        assert folder.resolve().is_relative_to(PROJECT.resolve())
        folder.mkdir(parents=True)
    producer = SOURCE / "registration-migration.py"
    shutil.copy2(Path(__file__), producer)
    records, selected = [], []
    for unit in sorted(units):
        recipe_path = PROJECT / f"assets/recipes/creatures/{unit}-map.json"
        recipe = json.loads(recipe_path.read_text())
        before_recipe = deepcopy(recipe)
        archive = BEFORE/unit
        archive.mkdir()
        shutil.copy2(recipe_path, archive/"recipe.json")
        frames = []
        for group in recipe["groups"]:
            assert group["group"] == 0 and len(group["frames"]) == 6
            for index, frame in enumerate(group["frames"]):
                original = PROJECT/frame["source"]
                assert sha(original) == frame["source_sha256"] == frame["sha256"]
                target = SOURCE/unit/f"g00-f{index:03d}.png"
                target.parent.mkdir(parents=True, exist_ok=True)
                with Image.open(original) as image:
                    pixels = image.convert("RGBA")
                assert pixels.size == (96,64)
                shifted = Image.new("RGBA", pixels.size)
                shifted.paste(pixels, (16,5))  # Unmasked: preserve original RGBA, not alpha_composite.
                count = 0
                for y in range(64):
                    for x in range(96):
                        rgba = pixels.getpixel((x,y))
                        if rgba[3]:
                            assert x+16 < 96 and y+5 < 64, (unit,index,x,y)
                            assert shifted.getpixel((x+16,y+5)) == rgba
                            count += 1
                shifted.save(target, compress_level=9)
                old_generated = PROJECT/f"assets/generated/Content/Sprites/runeterra/noxus/creatures/{unit}/map-frames/g00-f{index:03d}.png"
                shutil.copy2(old_generated, archive/f"g00-f{index:03d}.png")
                frames.append({"frame":index,"original":rel(original),"original_sha256":sha(original),
                               "registered":rel(target),"registered_sha256":sha(target),"preserved_nonzero_alpha_pixels":count})
                frame.update(source=rel(target),source_sha256=sha(target),sha256=sha(target))
        generation = recipe["generation"]
        # Preserve the exact prior recipe privately, at the producer, rather
        # than mutating ZIP payloads to conceal machine-local receipt fields.
        generation.pop("original_generated_path", None)
        recipe.pop("guide_definition", None)  # Unconsumed old geometry-guide locator, not a new painting input.
        recipe["pivot"] = {"x":64,"y":63}
        recipe["native_measurement"] = "Actual MapRenderer bottom-right image projection: 96x64 A-tile samples x64..95/y32..63; fixed +16,+5 registration, no pose or scale change. Native placement review remains pending."
        recipe["registration_evidence"] = "build/reports/roster-revision-20261024-v2/coordinator/survivor-map-registration/result.json"
        recipe["technical_registration"] = {"producer":rel(producer),"producer_sha256":sha(producer),
                                             "translation":[16,5],"prior_recipe_sha256":sha(archive/"recipe.json"),
                                             "method":"Unmasked whole-canvas RGBA translation; every visible source pixel preserved, no recolor/resize/painting."}
        recipe["status"] = "built-unreviewed"
        recipe["visual_approval_granted"] = False
        recipe_path.write_text(json.dumps(recipe,indent=2,sort_keys=True)+"\n")
        records.append({"unit":unit,"recipe":rel(recipe_path),"recipe_sha256":sha(recipe_path),"frames":frames})
        selected.append(rel(recipe_path))
    spec = importlib.util.spec_from_file_location("_noxus_survivor_map_compiler", PROJECT/"scripts/art_compile.py")
    compiler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compiler)
    first, second = {}, {}
    for name in selected:
        first.update(compiler.plan(PROJECT,PROJECT/name)[0])
        second.update(compiler.plan(PROJECT,PROJECT/name)[0])
    assert first == second and len(first) == 56
    conversion = compiler.compile_recipes(PROJECT, selected, resume=True)
    assert conversion.get("ok") is True, conversion
    assert content_before == {rel(path):sha(path) for path in (PROJECT/"content").glob("*.json")}
    for name, data in first.items():
        assert (PROJECT/"assets/generated"/name).read_bytes() == data
    (REPORT/"result.json").write_text(json.dumps({"status":"authored configuration","units":records,
        "recipes":8,"frames":48,"physical_outputs":56,"actual_own_compiler_repeat_exact":True,
        "content_unchanged":True,"native_verified":False,"release_accepted":False},indent=2)+"\n")
    (REPORT/"conversion.json").write_text(json.dumps(conversion,indent=2)+"\n")
    print("8 map recipes / 48 frames registered; 56 actual compiler outputs exact; content unchanged")

if __name__ == "__main__":
    main()
