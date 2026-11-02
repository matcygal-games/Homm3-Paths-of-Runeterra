"""Check actual authored puzzle pixels and native VCMI placement geometry.

This is an offline asset check. It does not open a game or observe obelisk UI.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys

from PIL import Image

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / "scripts"))
from common import read_json, sha256, write_json


def check() -> dict:
    root = PROJECT / "assets/source/puzzle"
    production = read_json(root / "production.json")
    faction_path = PROJECT / "content/factions.json"
    faction = read_json(faction_path)["demacia"]["puzzleMap"]
    native_path = PROJECT / production["native_source"]
    report = {
        "schema_version": 1,
        "ok": False,
        "scope": "Actual PNG reconstruction and source-loader geometry; not a running VCMI puzzle UI.",
        "native_dimensions": [592, 544],
        "viewport_origin": [8, 8],
        "engine_piece_offset": [1, 0],
        "faction_sha256": sha256(faction_path),
        "checker_sha256": sha256(Path(__file__)),
        "errors": [],
        "tiles": [],
        "release_art_accepted": False,
    }
    try:
        assert sha256(PROJECT / production["source_file"]) == production["master_sha256"], "Generated master checksum changed"
        assert sha256(native_path) == production["native_sha256"], "Preserved native master checksum changed"
        full_recipe = PROJECT / production["native_derivation_recipe"]
        assert sha256(full_recipe) == production["native_derivation_recipe_sha256"], "Native derivation recipe changed"
        assert read_json(full_recipe)["source_sha256"] == production["master_sha256"], "Master derivation no longer bound to source"
        assert faction["prefix"] == "runeterra/demacia/puzzle/piece", "Wrong puzzle resource prefix"
        assert len(faction["pieces"]) == len(production["pieces"]) == 48, "Expected exactly 48 pieces"
        assert sorted(p["index"] for p in faction["pieces"]) == list(range(1, 49)), "Reveal order must cover 1–48 once"
        with Image.open(native_path) as source:
            source.load()
            assert source.mode == "RGBA" and source.size == (592, 544), "Wrong native source canvas/mode"
            assert source.getextrema()[3] == (255, 255), "Cover master must be opaque"
            reconstructed = Image.new("RGBA", source.size)
            coverage = bytearray(592 * 544)
            for number, (config, record) in enumerate(zip(faction["pieces"], production["pieces"])):
                column, row = number % 8, number // 8
                x, y = column * 74, row * 91
                height = 91 if row < 5 else 89
                expected_crop = [x, y, x + 74, y + height]
                assert config["x"] + 1 == 8 + x and config["y"] == 8 + y, f"piece{number:02d}:native placement gap/overlap"
                assert record["number"] == number and record["reveal_order"] == config["index"], f"piece{number:02d}:wrong filename/reveal mapping"
                recipe_path = PROJECT / record["recipe"]
                recipe = read_json(recipe_path)
                assert sha256(recipe_path) == record["recipe_sha256"], f"piece{number:02d}:recipe changed"
                assert recipe["crop"] == expected_crop and recipe["size"] == [74, height], f"piece{number:02d}:wrong crop"
                assert recipe["source_sha256"] == production["native_sha256"], f"piece{number:02d}:stale native input"
                assert recipe["source"] == production["native_source"], f"piece{number:02d}:wrong crop input"
                expected_output = f"Content/Sprites/runeterra/demacia/puzzle/piece{number:02d}.png"
                assert recipe["output_path"] == record["output_path"] == expected_output, f"piece{number:02d}:wrong output path"
                tile_path = PROJECT / "assets/generated" / expected_output
                assert sha256(tile_path) == record["sha256"], f"piece{number:02d}:PNG checksum changed"
                with Image.open(tile_path) as tile:
                    tile.load()
                    assert tile.mode == "RGBA" and tile.size == (74, height), f"piece{number:02d}:wrong canvas/mode"
                    assert tile.getextrema()[3] == (255, 255), f"piece{number:02d}:unexpected transparent hole"
                    assert tile.tobytes() == source.crop(tuple(expected_crop)).tobytes(), f"piece{number:02d}:pixels differ from native master"
                    reconstructed.paste(tile, (x, y))
                for yy in range(y, y + height):
                    for xx in range(x, x + 74):
                        coverage[yy * 592 + xx] += 1
                report["tiles"].append({"number": number, "sha256": record["sha256"], "crop": expected_crop,
                                        "engine_position": [config["x"] + 1, config["y"]], "reveal_order": config["index"]})
            assert min(coverage) == max(coverage) == 1, "Gap/overlap in reconstructed viewport coverage"
            # Raw-byte equality includes RGB and alpha; an RGBA diff bbox alone can miss RGB errors under zero difference-alpha.
            assert reconstructed.tobytes() == source.tobytes(), "Reconstructed map differs from preserved native master"
            review = root / "review"
            review.mkdir(exist_ok=True)
            reconstruction_path = review / "reconstructed-native.png"
            reconstructed.save(reconstruction_path)
            report.update({"ok": True, "tiles_checked": 48, "coverage_min": min(coverage), "coverage_max": max(coverage),
                           "covered_pixels": len(coverage), "raw_pixel_sha256": hashlib.sha256(source.tobytes()).hexdigest(),
                           "native_master_sha256": sha256(native_path), "reconstruction_png_sha256": sha256(reconstruction_path),
                           "exact_reconstruction": True, "engine_bounds_exclusive": [8, 8, 600, 552],
                           "reconstruction_image": reconstruction_path.relative_to(PROJECT).as_posix()})
    except (AssertionError, OSError, KeyError, ValueError) as error:
        report["errors"].append(str(error))
    return report


if __name__ == "__main__":
    result = check()
    write_json(PROJECT / "assets/source/puzzle/assembly-check.json", result)
    write_json(PROJECT / "build/reports/puzzle-assembly.json", result)
    print(f"Puzzle pixel/geometry check: {'passed' if result['ok'] else 'FAILED'}, {len(result['tiles'])}/48tiles")
    for error in result["errors"]:
        print(error)
    raise SystemExit(0 if result["ok"] else 1)
