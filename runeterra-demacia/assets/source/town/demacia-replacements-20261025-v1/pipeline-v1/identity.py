"""Prevent faction patches, foreign recruitment and original resource shadowing.

These are configuration boundaries. Distinct silhouettes and tactical identity
also require the recorded design review and actual native-size visual review.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import re

from common import COLLECTIONS, MOD_ID, VCMI, read_json, sha256

FACTION = "demacia"
RESOURCE_ROOT = "runeterra/demacia/"
UNIT_GRAPHICS = {"animation":"battle.json", "map":"map.json", "iconLarge":"large.png", "iconSmall":"small.png",
                 "mapAttackFromLeft":"attackLeft.png", "mapAttackFromRight":"attackRight.png"}
BASE_ACTION_GROUPS = {0: 2, 1: 2, 2: 1, 3: 2, 4: 1, 5: 3, 7: 1, 8: 1, 11: 2, 12: 2, 13: 2}


def safe_relative_name(value) -> bool:
    if not isinstance(value, str) or not value:
        return False
    value = value.replace("\\", "/")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts:
        return False
    for part in path.parts:
        if part.endswith((".", " ")) or any(ord(c) < 32 or ord(c) == 127 or c in '<>:"|?*' for c in part):
            return False
        if re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", part.split(".")[0]):
            return False
    return True


def local_id(identifier, registry) -> bool:
    if not isinstance(identifier, str):
        return False
    parts = identifier.split(":")
    return (len(parts) == 1 or len(parts) == 2 and parts[0] == MOD_ID) and parts[-1] in registry


def namespaced_path(value, prefix=RESOURCE_ROOT) -> bool:
    if not safe_relative_name(value):
        return False
    value = value.replace("\\", "/")
    return value.startswith(prefix)


def unit_asset_contract(entry: dict) -> tuple[str, str] | None:
    output = entry.get("output_path")
    # Production uses output_path; resource-only entries are isolated tool inputs.
    resource = output.removeprefix("Content/Sprites/") if isinstance(output, str) else entry.get("resource", "")
    parts = resource.replace("\\", "/").split("/")
    roles = {"battle.json":"creature-battle-animation", "map.json":"creature-adventure-animation",
             "large.png":"creature-large", "small.png":"creature-small"}
    if len(parts) == 5 and parts[:3] == ["runeterra", "demacia", "creatures"] and parts[4] in roles:
        return parts[3], roles[parts[4]]
    return None


def canonical_action_groups(entry: dict, creatures: dict | None = None) -> dict[int, int]:
    contract = unit_asset_contract(entry)
    if not contract:
        return {}
    unit, role = contract
    if role == "creature-adventure-animation":
        return {0: 1}
    if role != "creature-battle-animation":
        return {}
    groups = dict(BASE_ACTION_GROUPS)
    if creatures is None:
        from common import PROJECT
        path = PROJECT / "content/creatures.json"
        creatures = read_json(path) if path.is_file() else {}
    bonuses = {b.get("type") for b in creatures.get(unit, {}).get("abilities", {}).values()}
    if "SHOOTER" in bonuses or unit in {"demacianRanger", "veteranRanger"}:
        groups.update({14: 2, 15: 2, 16: 2})
    if "SPELLCASTER" in bonuses:
        groups.update({30: 2, 31: 2, 32: 2})
    return groups


def animation_groups(definition: dict, complete: bool = False) -> dict[int, list[str]]:
    """Read native group/frame addressing; final unit groups are contiguous."""
    if not isinstance(definition, dict):
        raise ValueError("Animation must be a JSON object")
    sequences, images = definition.get("sequences", []), definition.get("images", [])
    if sequences and images:
        raise ValueError("Mixed sequences/images overlays are not supported by this standalone-asset pipeline")
    groups = {}
    for sequence in sequences:
        group, frames = sequence.get("group"), sequence.get("frames")
        if type(group) is not int or group < 0 or group in groups:
            raise ValueError("Duplicate or invalid animation group")
        if not isinstance(frames, list) or any(not isinstance(f, str) or not f for f in frames):
            raise ValueError("Native sequence frames must be filename strings")
        groups[group] = frames
    indexed = {}
    for image in images:
        group, frame, filename = image.get("group", 0), image.get("frame"), image.get("file")
        if type(group) is not int or group < 0 or type(frame) is not int or frame < 0:
            raise ValueError("Native images require non-negative integer group/frame indices")
        if not isinstance(filename, str) or not filename:
            raise ValueError("Native image file must be a filename string")
        frames = indexed.setdefault(group, {})
        if frame in frames:
            raise ValueError(f"Duplicate image frame {frame} in group {group}")
        frames[frame] = filename
    for group, frames in indexed.items():
        if complete and sorted(frames) != list(range(len(frames))):
            raise ValueError(f"Standalone creature group {group} must use contiguous frames starting at zero")
        groups[group] = [frames[index] for index in sorted(frames)]
    return groups


def animation_frame_hashes(mod_root: Path, output: str) -> dict[str, str]:
    if not safe_relative_name(output):
        raise ValueError("Invalid animation output path")
    path = (mod_root / output).resolve()
    if not path.is_relative_to(mod_root.resolve()):
        raise ValueError("Animation leaves mod staging")
    definition = read_json(path)
    contract = unit_asset_contract({"output_path":output})
    frame_prefix = RESOURCE_ROOT + f"creatures/{contract[0]}/" if contract else RESOURCE_ROOT
    frames = [name for names in animation_groups(definition, complete=bool(contract)).values() for name in names]
    if not frames:
        raise ValueError("Animation has no referenced PNG frames")
    result = {}
    for frame in frames:
        if not isinstance(frame, str):
            raise ValueError("Animation frame must be a filename string")
        resource = (definition.get("basepath", "") + frame).replace("\\", "/")
        if not namespaced_path(resource, frame_prefix) or PurePosixPath(resource).suffix.lower() != ".png":
            raise ValueError(f"Animation frame is not an own-mod PNG: {resource!r}")
        name = "Content/Sprites/" + resource
        target = (mod_root / name).resolve()
        if not target.is_relative_to(mod_root.resolve()) or not target.is_file():
            raise ValueError(f"Animation frame missing or outside staging: {name}")
        result[name] = sha256(target)
        # These files are loaded implicitly by RenderHandler and can change a
        # reviewed sprite without changing its animation JSON or main PNG.
        for suffix in ("-OVERLAY", "-SHADOW"):
            sidecar = target.with_name(target.stem + suffix + target.suffix)
            if sidecar.is_file():
                if not sidecar.resolve().is_relative_to(mod_root.resolve()):
                    raise ValueError(f"Animation sidecar outside staging: {sidecar}")
                result[sidecar.relative_to(mod_root).as_posix()] = sha256(sidecar)
    return result


def core_registry(vcmi: Path = VCMI) -> dict:
    result = {}
    for collection in COLLECTIONS:
        directory = vcmi / "config" / collection
        paths = sorted(directory.glob("*.json")) if directory.is_dir() else [directory.with_suffix(".json")]
        result[collection] = {key for path in paths if path.is_file() for key in read_json(path)}
    return result


def protected_core_files(vcmi: Path = VCMI) -> dict[str, str]:
    paths = set((vcmi / "config").rglob("*.json")) | set((vcmi / "scripts").rglob("*.lua"))
    essential = vcmi / "Mods/vcmi"
    if essential.is_dir():
        paths.update(p for p in essential.rglob("*") if p.is_file())
    return {p.relative_to(vcmi).as_posix(): sha256(p) for p in sorted(paths) if p.is_file()}


def core_changes(before: dict, after: dict) -> list[str]:
    return sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))


def check_separation(content: dict, original_ids: dict | None = None) -> list[str]:
    errors = []
    original_ids = core_registry() if original_ids is None else original_ids
    for collection, entries in content.items():
        for identifier, entity in entries.items():
            if ":" in identifier or identifier in original_ids.get(collection, set()):
                errors.append(f"{collection}/{identifier}: original/foreign entity key is forbidden in an additional faction")
            if "index" in entity:
                errors.append(f"{collection}/{identifier}: numeric original entity index is forbidden")
    if set(content.get("factions", {})) != {FACTION}:
        errors.append("factions: this delivery must add only runeterra-demacia:demacia and preserve all original towns")
        return errors
    creatures = content.get("creatures", {})
    classes = content.get("heroClasses", {})
    faction = content["factions"][FACTION]
    town = faction.get("town", {})
    recruited = []
    for tier, pair in enumerate(town.get("creatures", []), 1):
        for identifier in pair:
            if not local_id(identifier, creatures):
                errors.append(f"demacia/recruitment/tier{tier}: must recruit an own-mod creature, got {identifier!r}")
            else:
                recruited.append(identifier.split(":")[-1])
    if len(recruited) != 14 or len(set(recruited)) != 14 or set(recruited) != set(creatures):
        errors.append("demacia/recruitment: fourteen distinct own-mod variants must occupy the seven dwelling pairs")
    if not local_id(town.get("siege", {}).get("shooter"), creatures):
        errors.append("demacia/siege/shooter: must use an own-mod unit")
    for identifier, creature in creatures.items():
        if not local_id(creature.get("faction"), {FACTION}):
            errors.append(f"creatures/{identifier}/faction: must belong to runeterra-demacia:demacia")
        for upgrade in creature.get("upgrades", []):
            if not local_id(upgrade, creatures):
                errors.append(f"creatures/{identifier}/upgrades: foreign upgrade {upgrade!r}")
        graphics = creature.get("graphics", {})
        for field, filename in UNIT_GRAPHICS.items():
            expected = RESOURCE_ROOT + f"creatures/{identifier}/{filename}"
            value = graphics.get(field)
            if not namespaced_path(value) or value.replace("\\", "/") != expected:
                errors.append(f"creatures/{identifier}/graphics/{field}: own distinct namespaced art required; original troop art may only be a reference")
        projectile = graphics.get("missile", {}).get("projectile")
        if projectile and not namespaced_path(projectile):
            errors.append(f"creatures/{identifier}/graphics/missile: projectile must use the Demacia namespace")
    for identifier, hero_class in classes.items():
        if not local_id(hero_class.get("faction"), {FACTION}):
            errors.append(f"heroClasses/{identifier}/faction: foreign faction membership")
    for identifier, hero in content.get("heroes", {}).items():
        if not local_id(hero.get("class"), classes):
            errors.append(f"heroes/{identifier}/class: must use an own-mod class")
        for stack in hero.get("army", []):
            if not local_id(stack.get("creature"), creatures):
                errors.append(f"heroes/{identifier}/army: must start with own-mod troops")
    return errors


def check_asset_namespace(manifest: dict) -> list[str]:
    errors, outputs = [], set()
    allowed = tuple(f"Content/{kind}/{RESOURCE_ROOT}" for kind in ("Sprites", "Music", "Sounds"))
    for entry in manifest.get("assets", []):
        output = entry.get("output_path", "")
        if not any(namespaced_path(output, prefix) for prefix in allowed):
            errors.append(f"asset/{entry.get('id', '?')}: output may shadow original game resources: {output!r}")
        if output.casefold() in outputs:
            errors.append(f"asset/{entry.get('id', '?')}: duplicate case-insensitive output {output!r}")
        outputs.add(output.casefold())
    return errors


def check_visual_identity(project: Path, entry: dict, mod_root: Path | None = None) -> list[str]:
    """Require evidence of review; this function cannot judge sprite originality."""
    contract = unit_asset_contract(entry)
    if not contract:
        return []
    unit, role = contract
    context = f"asset/{entry['id']}/identity"
    name = entry.get("identity_review")
    if not safe_relative_name(name):
        return [f"{context}: a separate native-size identity review is required"]
    root = (project / "assets/reviews").resolve()
    path = (project / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        return [f"{context}: identity review must exist under assets/reviews"]
    try:
        review = read_json(path)
        errors = []
        if (review.get("status") != "passed"
                or any(not isinstance(review.get(key), str) or not review[key].strip() for key in ("reviewer", "notes"))):
            errors.append(f"{context}: completed reviewer and distinctiveness findings are required")
        if not entry.get("sha256") or review.get("asset_sha256") != entry["sha256"]:
            errors.append(f"{context}: approval belongs to a different asset checksum")
        if review.get("unit") != unit:
            errors.append(f"{context}: approval belongs to a different unit")
        references = review.get("original_unit_references")
        if not isinstance(references, list) or not references or any(not isinstance(ref, str) or not ref.startswith("core:") for ref in references):
            errors.append(f"{context}: original unit comparisons must be identified")
        for check in ("native_scale", "distinct_silhouette", "distinct_equipment", "not_recolored_original", "upgrade_readability"):
            if review.get("checks", {}).get(check) is not True:
                errors.append(f"{context}: visual check {check} has not passed")
        sheet_name = review.get("comparison_sheet")
        sheet = (project / sheet_name).resolve() if safe_relative_name(sheet_name) else root
        if not sheet.is_relative_to(root) or not sheet.is_file() or not review.get("comparison_sha256"):
            errors.append(f"{context}: native-size comparison sheet and checksum are required")
        elif sha256(sheet) != review["comparison_sha256"]:
            errors.append(f"{context}: comparison sheet changed after review")
        else:
            from PIL import Image
            with Image.open(sheet) as picture:
                picture.verify()
        if role in {"creature-battle-animation", "creature-adventure-animation"}:
            stage = mod_root if mod_root is not None else project / "build/Mods" / MOD_ID
            output = entry.get("output_path", "Content/Sprites/" + entry.get("resource", ""))
            frames = animation_frame_hashes(stage, output)
            if review.get("frame_sha256") != frames:
                errors.append(f"{context}: referenced PNG frame hashes differ from the reviewed animation")
        return errors
    except (OSError, ValueError, TypeError, ImportError) as error:
        return [f"{context}: invalid identity review: {error}"]
