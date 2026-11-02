"""V9 metadata successor: builtin image generation did not expose a model ID.

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
R = P / "build/reports/regional-crests-20261025-v1/noxus-t2-art/metadata-closure-v9"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return {"path": path.relative_to(P).as_posix(), "sha256": sha(path)}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    assert path.resolve().is_relative_to(R) or path.resolve().is_relative_to(S / "recipes-v9") or path in (
        S / "candidate-selection-v9.json", S / "metadata-closure-v9.json")
    data = value if isinstance(value, bytes) else (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError("Immutable V9 output differs; version successor: " + str(path))
    path.write_bytes(data)


def main():
    v7_selection_path = S / "candidate-selection-v7.json"
    selection = load(v7_selection_path)
    source_recipes = sorted((S / "recipes-v7").glob("*.json"))
    assert len(source_recipes) == 12
    inputs = {}
    for path in source_recipes:
        for record in load(path)["dependencies"]:
            assert sha(P / record["path"]) == record["sha256"]
            assert record["path"] not in inputs or inputs[record["path"]] == record["sha256"]
            inputs[record["path"]] = record["sha256"]
    for path in source_recipes:
        record = pin(path)
        inputs[record["path"]] = record["sha256"]
    for record in (pin(SELF), pin(v7_selection_path)):
        inputs[record["path"]] = record["sha256"]
    frozen = {str(P / name): checksum for name, checksum in inputs.items()}
    frozen.update({str(P / "scripts/art_compile.py"): sha(P / "scripts/art_compile.py"),
                   str(P / "scripts/production.py"): sha(P / "scripts/production.py")})
    metadata = {"status": "authored configuration", "candidate_only": True, "revision": "metadata-closure-v9",
        "scope": "Metadata truth correction only; no generated pixel, action, scale or gameplay change",
        "successor_of": pin(v7_selection_path), "metadata_producer": pin(SELF),
        "art_producer": pin(S / "assemble_candidate_v6.py"),
        "generation_truth": {"model_id_exposed": False,
            "reason": "The builtin image generation tool did not expose its concrete model identifier. Existing not-exposed model text is retained."},
        "live_inputs": [{"path": name, "sha256": digest} for name, digest in sorted(inputs.items())],
        "visual_approval_granted": False, "runtime_verified": False, "release_accepted": False}
    metadata_path = S / "metadata-closure-v9.json"
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
        candidate = S / "recipes-v9" / path.name
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
    successor_selection.update(metadata_revision="metadata-closure-v9", metadata_closure=pin(metadata_path),
                               metadata_producer=pin(SELF), successor_of=pin(v7_selection_path),
                               generation_model_id_exposed=False)
    for unit, info in successor_selection["units"].items():
        info["recipes"] = [pin(S / "recipes-v9" / Path(rec["path"]).name) for rec in selection["units"][unit]["recipes"]]
        assert info["entries"] == selection["units"][unit]["entries"]
        assert info["generation"] == selection["units"][unit]["generation"]
    selection_path = S / "candidate-selection-v9.json"
    write(selection_path, successor_selection)
    write(R / "recipe-metadata-delta.json", deltas)
    spec = importlib.util.spec_from_file_location("_noxus_t2_v9_actual_compiler", P / "scripts/art_compile.py")
    compiler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compiler)
    expected = load(P / "build/reports/regional-crests-20261025-v1/noxus-t2-art/metadata-closure-v7/runtime-output-inventory.json")
    inventories, plans = [], []
    for passname in ("pass-a", "pass-b"):
        inventory = {}
        for path in sorted((S / "recipes-v9").glob("*.json")):
            outputs, receipt = compiler.plan(P, path)
            plans.append({"pass": passname, **receipt})
            for name, data in outputs.items():
                assert name not in inventory
                inventory[name] = hashlib.sha256(data).hexdigest()
                write(R / passname / name, data)
        assert inventory == expected and len(inventory) == 128
        inventories.append(inventory)
    assert inventories[0] == inventories[1]
    # Execute the unchanged scanner with all12V9 candidates first. A separate
    # one-recipe negative fixture has their identical shared direct closure.
    spec = importlib.util.spec_from_file_location("_noxus_t2_v9_production", P / "scripts/production.py")
    production = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(production)
    import sys
    sys.path.insert(0, str(W / "scripts"))
    import faction_pipeline as fp
    all_fixture = R / "production-inputs-all12-fixture"
    one_fixture = R / "production-inputs-negative-fixture"
    for fixture in (all_fixture, one_fixture):
        for record in dependencies:
            write(fixture / record["path"], (P / record["path"]).read_bytes())
    all_paths = sorted((S / "recipes-v9").glob("*.json"))
    for index, path in enumerate(all_paths):
        for fixture in ((all_fixture, one_fixture) if index == 0 else (all_fixture,)):
            recipe = load(path)
            for _, value in fp.walk(recipe):
                if isinstance(value, str) and value.startswith("assets/source/") and (P / value).is_file():
                    write(fixture / value, (P / value).read_bytes())
            write(fixture / "assets/recipes/creatures" / path.name, path.read_bytes())
    all_pipeline = fp.Pipeline(all_fixture, "runeterra-noxus", "noxus")
    all_inputs = production.production_inputs(all_pipeline)
    assert all(all_inputs[str(all_fixture / rec["path"])] == rec["sha256"] for rec in dependencies)
    write(R / "actual-production-inputs-all12.json", all_inputs)
    one_pipeline = fp.Pipeline(one_fixture, "runeterra-noxus", "noxus")
    baseline = production.production_inputs(one_pipeline)
    baseline_signature = production.signature(baseline)
    templates = [rec for rec in dependencies if "/before-recipes/" in rec["path"] or "/recipes-v7/" in rec["path"]]
    assert len(templates) == 24
    negatives = []
    for record in templates:
        target = one_fixture / record["path"]
        original = target.read_bytes()
        target.unlink()
        absent = production.production_inputs(one_pipeline)
        absent_signature = production.signature(absent)
        assert str(target) in absent and absent[str(target)] is None and absent_signature != baseline_signature
        negatives.append({"case": "missing-template", "path": record["path"], "actual_hash": None,
            "actual_signature": absent_signature, "signature_changed": True,
            "consumer": "unchanged production_inputs/signature", "diagnostic": "Missing path retained with null hash; signature changes"})
        target.write_bytes(original + b"\n ")
        stale = production.production_inputs(one_pipeline)
        stale_signature = production.signature(stale)
        assert stale[str(target)] == hashlib.sha256(original + b"\n ").hexdigest()
        assert stale[str(target)] != record["sha256"] and stale_signature != baseline_signature
        negatives.append({"case": "stale-template", "path": record["path"], "actual_hash": stale[str(target)],
            "actual_signature": stale_signature, "signature_changed": True,
            "consumer": "unchanged production_inputs/signature", "diagnostic": "Changed byte hash read; signature changes"})
        target.write_bytes(original)
    assert production.production_inputs(one_pipeline) == baseline
    write(R / "actual-consumer-negative-controls.json", negatives)
    write(R / "template-closure-proof.json", {"all12_candidates_scanned": True,
        "all12_share_same_direct_dependency_closure": True, "negative_fixture": "one selected candidate with identical closure",
        "v7_recipe_template_count": 12, "original_before_template_count": 12,
        "missing_stale_cases": len(negatives), "baseline_signature": baseline_signature,
        "template_pins": templates})
    assert all(sha(Path(name)) == digest for name, digest in frozen.items())
    write(R / "actual-own-compiler-plans.json", plans)
    write(R / "runtime-output-inventory.json", inventories[0])
    write(R / "frozen-inputs-before-after.json", {"unchanged": True, "pins": frozen})
    receipt = {"ok": True, "SOURCE_SAFE": True, "status": "authored configuration", "metadata_only": True,
        "selection": pin(selection_path), "metadata_closure": pin(metadata_path), "metadata_producer": pin(SELF),
        "recipes": recipes, "recipe_count": 12, "two_actual_own_compiler_passes": True, "physical_outputs": 128,
        "all_runtime_bytes_exact_v7_v6": True, "all_generation_model_id_exposed_false": True,
        "all_v7_live_inputs_preserved_and_directly_pinned": True,
        "all12_consumed_v7_recipe_templates_directly_pinned": True,
        "actual_scanner_all12_baseline_passed": True, "missing_stale_template_signature_controls": len(negatives), "direct_live_inputs_per_recipe": len(dependencies),
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
