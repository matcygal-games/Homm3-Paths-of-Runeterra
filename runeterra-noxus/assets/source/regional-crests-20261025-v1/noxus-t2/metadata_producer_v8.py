"""V8 metadata successor: builtin image generation did not expose a model ID.

Keeps V6 art and V7 inputs exact; authoring and checks write only new candidates
and their own report directory. No production conversion/staging is invoked.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

SELF = Path(__file__).resolve()
S = SELF.parent
W = next(parent for parent in SELF.parents if (parent / "AGENTS.md").is_file())
P = W / "runeterra-noxus"
R = P / "build/reports/regional-crests-20261025-v1/noxus-t2-art/metadata-closure-v8"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return {"path": path.relative_to(P).as_posix(), "sha256": sha(path)}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    assert path.resolve().is_relative_to(R) or path.resolve().is_relative_to(S / "recipes-v8") or path in (
        S / "candidate-selection-v8.json", S / "metadata-closure-v8.json")
    data = value if isinstance(value, bytes) else (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError("Immutable V8 output differs; version successor: " + str(path))
    path.write_bytes(data)


def main():
    v7_selection_path = S / "candidate-selection-v7.json"
    selection = load(v7_selection_path)
    source_recipes = sorted((S / "recipes-v7").glob("*.json"))
    assert len(source_recipes) == 12
    frozen = {str(path): sha(path) for path in S.rglob("*") if path.is_file() and
        "recipes-v8" not in path.parts and path.name not in ("candidate-selection-v8.json", "metadata-closure-v8.json")}
    frozen.update({str(P / "scripts/art_compile.py"): sha(P / "scripts/art_compile.py"),
                   str(P / "scripts/production.py"): sha(P / "scripts/production.py")})
    inputs = {}
    for path in source_recipes:
        for record in load(path)["dependencies"]:
            assert sha(P / record["path"]) == record["sha256"]
            assert record["path"] not in inputs or inputs[record["path"]] == record["sha256"]
            inputs[record["path"]] = record["sha256"]
    for record in (pin(SELF), pin(v7_selection_path)):
        inputs[record["path"]] = record["sha256"]
    metadata = {"status": "authored configuration", "candidate_only": True, "revision": "metadata-closure-v8",
        "scope": "Metadata truth correction only; no generated pixel, action, scale or gameplay change",
        "successor_of": pin(v7_selection_path), "metadata_producer": pin(SELF),
        "art_producer": pin(S / "assemble_candidate_v6.py"),
        "generation_truth": {"model_id_exposed": False,
            "reason": "The builtin image generation tool did not expose its concrete model identifier. Existing not-exposed model text is retained."},
        "live_inputs": [{"path": name, "sha256": digest} for name, digest in sorted(inputs.items())],
        "visual_approval_granted": False, "runtime_verified": False, "release_accepted": False}
    metadata_path = S / "metadata-closure-v8.json"
    write(metadata_path, metadata)
    dependencies = metadata["live_inputs"] + [pin(metadata_path)]
    recipes = []
    deltas = []
    for path in source_recipes:
        original = load(path)
        successor = deepcopy(original)
        successor["generation"]["model_id_exposed"] = False
        successor["generation"]["metadata_producer"] = pin(SELF)
        successor["metadata_closure"] = pin(metadata_path)
        successor["dependencies"] = dependencies
        candidate = S / "recipes-v8" / path.name
        write(candidate, successor)
        recipes.append(pin(candidate))
        old_generation = deepcopy(original["generation"])
        new_generation = deepcopy(successor["generation"])
        new_generation.pop("model_id_exposed")
        new_generation.pop("metadata_producer")
        assert old_generation == new_generation
        assert {k: v for k, v in original.items() if k not in ("generation", "dependencies", "metadata_closure")} == {
            k: v for k, v in successor.items() if k not in ("generation", "dependencies", "metadata_closure")}
        deltas.append({"v7": pin(path), "v8": pin(candidate), "changed_fields": ["generation/model_id_exposed", "generation/metadata_producer", "metadata_closure", "dependencies"]})
    successor_selection = deepcopy(selection)
    successor_selection.update(metadata_revision="metadata-closure-v8", metadata_closure=pin(metadata_path),
                               metadata_producer=pin(SELF), successor_of=pin(v7_selection_path),
                               generation_model_id_exposed=False)
    for unit, info in successor_selection["units"].items():
        info["recipes"] = [pin(S / "recipes-v8" / Path(rec["path"]).name) for rec in selection["units"][unit]["recipes"]]
        assert info["entries"] == selection["units"][unit]["entries"]
        assert info["generation"] == selection["units"][unit]["generation"]
    selection_path = S / "candidate-selection-v8.json"
    write(selection_path, successor_selection)
    write(R / "recipe-metadata-delta.json", deltas)
    spec = importlib.util.spec_from_file_location("_noxus_t2_v8_actual_compiler", P / "scripts/art_compile.py")
    compiler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compiler)
    expected = load(P / "build/reports/regional-crests-20261025-v1/noxus-t2-art/metadata-closure-v7/runtime-output-inventory.json")
    inventories, plans = [], []
    for passname in ("pass-a", "pass-b"):
        inventory = {}
        for path in sorted((S / "recipes-v8").glob("*.json")):
            outputs, receipt = compiler.plan(P, path)
            plans.append({"pass": passname, **receipt})
            for name, data in outputs.items():
                assert name not in inventory
                inventory[name] = hashlib.sha256(data).hexdigest()
                write(R / passname / name, data)
        assert inventory == expected and len(inventory) == 128
        inventories.append(inventory)
    assert inventories[0] == inventories[1]
    assert all(sha(Path(name)) == digest for name, digest in frozen.items())
    write(R / "actual-own-compiler-plans.json", plans)
    write(R / "runtime-output-inventory.json", inventories[0])
    write(R / "frozen-inputs-before-after.json", {"unchanged": True, "pins": frozen})
    receipt = {"ok": True, "SOURCE_SAFE": True, "status": "authored configuration", "metadata_only": True,
        "selection": pin(selection_path), "metadata_closure": pin(metadata_path), "metadata_producer": pin(SELF),
        "recipes": recipes, "recipe_count": 12, "two_actual_own_compiler_passes": True, "physical_outputs": 128,
        "all_runtime_bytes_exact_v7_v6": True, "all_generation_model_id_exposed_false": True,
        "all_v7_live_inputs_preserved_and_directly_pinned": True, "direct_live_inputs_per_recipe": len(dependencies),
        "actual_compiler": pin(P / "scripts/art_compile.py"), "frozen_source_inputs_unchanged": True,
        "active_files_backend_manifest_or_stage_modified": False, "runtime_executed": False,
        "visual_approval_granted": False, "release_accepted": False}
    write(R / "SOURCE_SAFE.json", receipt)
    write(R / "output-pins.json", {path.relative_to(R).as_posix(): sha(path) for path in sorted(R.rglob("*"))
        if path.is_file() and path.name != "output-pins.json"})
    print(json.dumps({"SOURCE_SAFE": True, "selection": receipt["selection"], "metadata_closure": receipt["metadata_closure"],
        "metadata_producer": receipt["metadata_producer"], "receipt_sha256": sha(R / "SOURCE_SAFE.json"),
        "output_pins_sha256": sha(R / "output-pins.json"), "physical_outputs": 128}, indent=2))


if __name__ == "__main__":
    main()
