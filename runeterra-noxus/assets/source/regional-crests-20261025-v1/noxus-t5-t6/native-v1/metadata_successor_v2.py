"""Truthful model-exposure metadata successor; all V1 painted pixels retained."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

SELF = Path(__file__).resolve()
N = SELF.parent
S = N.parent
W = next(parent for parent in SELF.parents if (parent / "AGENTS.md").is_file())
P = W / "runeterra-noxus"


def pin(path):
    return {"path": path.relative_to(P).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def write(path, value):
    assert path.resolve().is_relative_to(S / "recipes-v1/provenance-v2") or path in (
        N / "metadata-successor-v2.json", S / "candidate-selection-v2.json")
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError("Immutable metadata successor differs: " + str(path))
    path.write_bytes(data)


def main():
    selected_path = S / "candidate-selection-v1.json"
    selected = json.loads(selected_path.read_text(encoding="utf-8"))
    recipes = [P / record["path"] for info in selected["units"].values() for record in info["recipes"]]
    assert len(recipes) == 12
    inputs = {}
    for path in recipes:
        for record in json.loads(path.read_text(encoding="utf-8"))["dependencies"]:
            assert pin(P / record["path"])["sha256"] == record["sha256"]
            inputs[record["path"]] = record["sha256"]
    for path in (*recipes, selected_path, SELF):
        record = pin(path)
        inputs[record["path"]] = record["sha256"]
    metadata = {"status": "authored configuration", "candidate_only": True, "successor_of": pin(selected_path),
        "metadata_producer": pin(SELF), "art_producer": selected["producer"],
        "change": "generation.model_id_exposed=false; builtin image generation did not expose its concrete model identifier",
        "all_native_pixels_unchanged": True,
        "direct_live_dependencies": [{"path": name, "sha256": digest} for name, digest in sorted(inputs.items())]}
    metadata_path = N / "metadata-successor-v2.json"
    write(metadata_path, metadata)
    dependencies = metadata["direct_live_dependencies"] + [pin(metadata_path)]
    successor = deepcopy(selected)
    successor.update(metadata_producer=pin(SELF), metadata_successor=pin(metadata_path), predecessor=pin(selected_path),
                     generation_model_id_exposed=False)
    for info in successor["units"].values():
        next_recipes = []
        for original in info["recipes"]:
            path = P / original["path"]
            recipe = json.loads(path.read_text(encoding="utf-8"))
            recipe["generation"]["model_id_exposed"] = False
            recipe["generation"]["metadata_producer"] = pin(SELF)
            recipe["metadata_successor"] = pin(metadata_path)
            recipe["dependencies"] = dependencies
            candidate = S / "recipes-v1/provenance-v2" / path.name
            write(candidate, recipe)
            next_recipes.append(pin(candidate))
        info["recipes"] = next_recipes
    write(S / "candidate-selection-v2.json", successor)
    print(json.dumps({"selection": pin(S / "candidate-selection-v2.json"), "metadata": pin(metadata_path),
                      "direct_live_dependencies_per_recipe": len(dependencies)}, indent=2))


if __name__ == "__main__":
    main()
