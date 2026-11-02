"""Targon's exact portable producer/test closure and external native read set.

Standard library plus the included shared inventory helper only. No import falls
back to an earlier workspace. Private artwork/reference pixels are never inputs
to this source exporter. The minimal MIT decoder source retains its LICENSE.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import faction_source_prerequisites as shared

FACTION = "targon"
MOD_ID = "runeterra-targon"
NATIVE_ROOT = "vcmi-develop/vcmi-develop"
ARCHIVE_METADATA = MOD_ID + "/SOURCE-PREREQUISITES.json"
FORMAT_VERSION = shared.FORMAT_VERSION
MAX_EXTERNAL_BYTES = 20 * 1024 * 1024
SCHEMAS = tuple(("artifact battlefield biome bonus bonusInstance campaignRegion creature faction "
    "flaggable gameSettings hero heroClass highscoreCreatures mapHeader mapLayer market mmaiSettings mod "
    "object objectTemplate objectType obstacle resources rewardable river road saveMetadata script "
    "settings skill spell spellSchool template terrain townBuilding townSiege townStructure").split())
TOWNS = tuple("castle rampart tower inferno necropolis dungeon stronghold fortress conflux".split())
CATALOGS = {"config/schemas": SCHEMAS,
    "config/factions": (*TOWNS, "neutral", "random"),
    "config/creatures": (*TOWNS, "neutral", "special"),
    "config/heroes": (*TOWNS, "special", "portraits", "portraitsChronicles"),
    "config/spells": tuple("ability adventure moats offensive other timed vcmiAbility".split())}
REGISTRY_DIRECTORIES = {k.removeprefix("config/"): v for k, v in CATALOGS.items() if k != "config/schemas"}
CONFIG_FILES = ("config/heroClasses.json", "config/artifacts.json", "config/skills.json",
    "config/buildingsLibrary.json", "config/roads.json", "config/gameConfig.json", "config/terrains.json",
    "config/objects/moddables.json", "config/objects/magicWell.json", "config/objects/rewardableBonusing.json",
    "config/scriptsCombat.json", "config/scriptsSpells.json")
CELESTIAL_CONSUMERS = (
    "config/schemas/script.json", "lib/CCreatureHandler.cpp", "lib/battle/BattleInfo.cpp",
    "lib/bonuses/BonusList.cpp", "lib/callback/Calendar.cpp", "lib/json/JsonBonus.cpp",
    "lib/scripting/ScriptHandler.cpp", "luascript/LuaCombatEventScript.cpp",
    "luascript/LuaContext.cpp", "luascript/LuaContext.h", "luascript/api/adventure/Calendar.cpp",
    "luascript/api/battle/Unit.cpp", "luascript/api/callback/IGameInfoCallback.cpp",
    "luascript/api/callback/ServerCallback.cpp", "luascript/api/library/Bonus.cpp",
    "luascript/api/library/BonusBearerBindings.h", "luascript/api/library/BonusDescriptor.cpp",
    "luascript/api/library/BonusDescriptor.h", "luascript/api/library/EntityBindings.h",
    "scripts/combat/ballistaDamage.lua", "scripts/combat/combatScript.lua",
    "scripts/spells/clone.lua", "server/battles/BattleFlowProcessor.cpp",
    "luascript/api/Enums.cpp", "lib/bonuses/BonusEnum.h", "lib/constants/StringConstants.h",
    "lib/modding/IdentifierStorage.cpp", "lib/bonuses/BonusCustomTypes.cpp",
    "luascript/LuaScriptFactory.cpp", "luascript/LuaScriptInstance.cpp",
    "server/battles/BattleProcessor.cpp", "lib/bonuses/Bonus.h", "lib/bonuses/BonusEnum.cpp")
NATIVE_CONSUMERS = (
    "lib/VCMIDirs.cpp", "lib/VCMIDirs.h",
    "lib/entities/hero/CHeroHandler.cpp", "lib/entities/hero/CHeroClassHandler.cpp",
    "lib/CSkillHandler.cpp", "lib/BasicTypes.cpp", "lib/bonuses/BonusCache.cpp", "lib/bonuses/Limiters.cpp",
    "lib/mapObjects/CGHeroInstance.cpp", "lib/mapObjects/CGTownInstance.cpp", "lib/mapObjects/ObjectTemplate.cpp",
    "lib/mapObjects/TownBuildingInstance.cpp", "lib/mapObjects/TownBuildingInstance.h",
    "lib/battle/CUnitState.cpp", "lib/battle/actions/ShootAction.cpp", "lib/battle/actions/SpellCastActions.cpp",
    "lib/spells/CSpell.cpp", "lib/spells/ISpellMechanics.cpp", "scripts/damage/damageCalculator.lua",
    "scripts/spells/damage.lua", "scripts/spells/timed.lua", "scripts/spells/unitEffect.lua",
    "scripts/spells/heal.lua", "scripts/battleLog.lua", "lib/mapping/MapFormatJson.cpp", "lib/mapping/CMap.h",
    "lib/mapping/CDrawRoadsOperation.cpp", "server/processors/HeroPoolProcessor.cpp",
    "lib/gameState/TavernHeroesPool.cpp", "lib/callback/MapInfoCallback.cpp", "AI/BattleAI/BattleEvaluator.cpp",
    *CELESTIAL_CONSUMERS)
OWN_REQUIRED = ("mod.json", "assets/manifest.json", "assets/rights.json", "README.md", "STATUS.md", "CREDITS.md",
    *("content/" + n + ".json" for n in ("factions", "creatures", "heroClasses", "heroes", "spells", "artifacts", "scripts")),
    "scripts/vcmi/celestialAlignment.lua", "design/celestial-cycle.json", "assets/production/source-export.json",
    "requirements.txt", "requirements.lock.txt", "requirements-test.txt",
    "local-paths.example.json", ".gitignore", "scripts/production.py", "scripts/source_tests.py",
    "scripts/source_dependencies.py", "scripts/rules.py", "scripts/references.py",
    "scripts/targon_animal_art.py", "scripts/targon_humanoid_art.py",
    "scripts/targon_town_art.py", "scripts/targon_hero_art.py",
    "design/creature-art-policy.json", "scripts/creature_art_policy.py", "tests/test_creature_art_policy.py",
    "docs/ENGINE_BUILD.md", "docs/engine/0001-fix-portable-prepare-command-variable.patch",
    "docs/REFERENCE_SPEC.md", "docs/TOWN_ART_SPEC.md",
    "docs/CORRECTED_SPEC.md", "docs/FACTION_SEPARATION.md")
SHARED_REQUIRED = ("AGENTS.md", "RUNETERRA_DEMACIA_PROJECT_PROMPT.txt", "RUNETERRA_TARGON_PROJECT_PROMPT.txt",
    "RUNETERRA_CREATURE_ART_POLICY.txt", "RUNETERRA_REGIONAL_HERALDRY_POLICY.txt",
    "scripts/runeterra.py", "scripts/runeterra.ps1", "scripts/faction_pipeline.py",
    "scripts/faction_production.py", "scripts/faction_art_compile.py", "scripts/faction_artifacts.py",
    "scripts/faction_asset_manifest.py", "scripts/faction_source_prerequisites.py",
    "scripts/faction_sdk_profile.py",
    "scripts/targon_asset_manifest.py", "scripts/targon_schema_check.py", "scripts/targon_maps.py",
    "scripts/shurima_maps.py")
PURE_HELPERS = tuple(("animation combat_preview common development discovery identity live_preview maps "
    "normal_startup prepare_town_layers preview_freshness raster runtime validation references").split())
DECODER = "tools/homm3data-main/homm3data-main/"
DECODER_FILES = ("LICENSE", "homm3data/__init__.py", "homm3data/deffile.py", "homm3data/lodfile.py",
                 "homm3data/pakfile.py", "homm3data/pcxfile.py")
PROMPTS = ("sources.json", "champion-eligibility.json", "LORE_REVIEW.md", "ROSTER_REVIEW.md",
           "unit-identity.json", "README.md")
NATIVE_LITERAL = re.compile(r"^(?:vcmi-develop/vcmi-develop/)?((?:lib|config|client|clientsdl2|server|scripts|luascript|AI)/[^: ]+\.(?:json|lua|cpp|h))(?::.*)?$")
PRIVATE_LOCATION = re.compile(r'''(?:^/(?!\s)|(?:^|[\s"'=])(?:[A-Za-z]:[\\/]|\\\\|/[A-Za-z0-9_.-]+/|~[\\/]|file://))''', re.IGNORECASE)
SCENE_EXPORT_LEDGER = "assets/production/source-export.json"
WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", "CLOCK$", "CONIN$", "CONOUT$"} | {
    prefix + str(n) for prefix in ("COM", "LPT") for n in range(1, 10)}


def _layout(root, workspace):
    return shared.owned_root(root, workspace, MOD_ID)


def required_paths(root, workspace):
    """Verified actual non-native source inputs, including current art producers."""
    root, workspace = _layout(root, workspace)
    names = set(SHARED_REQUIRED)
    names.update(MOD_ID + "/" + n for n in OWN_REQUIRED)
    names.update("prompts/targon/" + n for n in PROMPTS)
    names.update("runeterra-demacia/scripts/" + n + ".py" for n in PURE_HELPERS)
    names.update(DECODER + n for n in DECODER_FILES)
    names.update("runeterra-demacia/" + n for n in ("requirements.txt", "requirements.lock.txt", "requirements-test.txt"))
    for folder in (root / "scripts", root / "tests"):
        if not folder.is_dir() or folder.resolve() != folder.absolute():
            raise FileNotFoundError("Missing or redirected Targon executable source directory: " + str(folder))
        names.update(p.relative_to(workspace).as_posix() for p in folder.rglob("*.py") if "__pycache__" not in p.parts)
    names.update(p.relative_to(workspace).as_posix() for p in (root / "docs").rglob("*.md"))
    # These are exported source text only, never private reference pixels/caches.
    paths = tuple(shared.direct_file(workspace, n) for n in sorted(names))
    if any(p.is_relative_to(root / "references") or p.is_relative_to(workspace / NATIVE_ROOT) for p in paths):
        raise ValueError("Private or external-native source entered Targon authored closure")
    return paths


def _native_literals(root):
    """Pin native consumers named by current own producers, tests and ledgers."""
    names = set(NATIVE_CONSUMERS)
    def consume(value):
        if isinstance(value, dict):
            for item in value.values(): consume(item)
        elif isinstance(value, list):
            for item in value: consume(item)
        elif isinstance(value, str):
            # This is the explicitly owned runtime Lua source directory, not
            # VCMI's scripts/combat or scripts/spells source tree. Its mandatory
            # payload is checked independently by required_paths.
            if value.startswith("scripts/vcmi/"): return
            match = NATIVE_LITERAL.fullmatch(value)
            if match: names.add(match.group(1))
    for path in sorted((root / "design").glob("*.json")):
        if path.resolve() != path.absolute(): raise ValueError("Redirected Targon design source: " + str(path))
        consume(json.loads(path.read_text(encoding="utf-8")))
    python_inputs = [*(root / "tests").glob("test_*.py"), *(root / "scripts").rglob("*.py")]
    for path in sorted(python_inputs):
        if path.resolve() != path.absolute(): raise ValueError("Redirected Targon executable source: " + str(path))
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        dictionaries = {}
        for assignment in ast.walk(tree):
            if isinstance(assignment, ast.Assign) and isinstance(assignment.value, ast.Dict):
                for target in assignment.targets:
                    if isinstance(target, ast.Name): dictionaries[target.id] = assignment.value
        protected_dynamic = set()
        for node in ast.walk(tree):
            # Test fixtures also contain native-looking names such as config/test.json.
            # Only actual protected-root joins or full workspace-native literals
            # establish a consumed external file; arbitrary strings do not.
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                names_in_base = {n.id for n in ast.walk(node.left) if isinstance(n, ast.Name)}
                if "VCMI" in names_in_base and isinstance(node.right, ast.Name):
                    protected_dynamic.add(node.right.id)
                if isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
                    if ("VCMI" in names_in_base or ({"WORKSPACE", "ROOT"} & names_in_base
                            and node.right.value.startswith(NATIVE_ROOT + "/"))):
                        consume(node.right.value)
        # Native contracts commonly read ``VCMI / relative`` while iterating a
        # literal checks mapping. Resolve only those protected-root loop keys,
        # never every native-looking string in arbitrary fixture payloads.
        for node in ast.walk(tree):
            if not isinstance(node, ast.For): continue
            targets = {n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)}
            call = node.iter
            if (not targets & protected_dynamic or not isinstance(call, ast.Call)
                    or not isinstance(call.func, ast.Attribute) or call.func.attr != "items"
                    or not isinstance(call.func.value, ast.Name)): continue
            mapping = dictionaries.get(call.func.value.id)
            if mapping is not None:
                for key in mapping.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str): consume(key.value)
    return names


def dependency_paths(root, workspace):
    root, workspace = _layout(root, workspace)
    native = workspace / NATIVE_ROOT
    for name in ("heroClasses", "artifacts"):
        if (native / "config" / name).exists():
            raise ValueError("Targon native registry layout changed: " + name)
    return shared.inventory(workspace, NATIVE_ROOT, CATALOGS,
                            set(CONFIG_FILES) | _native_literals(root), MAX_EXTERNAL_BYTES)


def source_prerequisites(root, workspace):
    errors = source_metadata_errors(root, workspace)
    if errors:
        raise ValueError("Nonportable Targon source metadata: " + "; ".join(errors))
    return shared.manifest(workspace, FACTION, NATIVE_ROOT, dependency_paths(root, workspace))


def source_metadata_errors(root, workspace):
    """Reject machine-local locations in exportable authored art metadata.

    Original receipts remain preserved outside these source/export directories.
    Remote URLs and portable relative sources/hashes are valid provenance.
    No historical record, source, recipe, selection or approval is rewritten here.
    """
    root, workspace = _layout(root, workspace)
    errors = []
    for directory in ("assets/source", "assets/recipes", "assets/production"):
        for path in sorted((root / directory).rglob("*")):
            if not path.is_file() or path.suffix.casefold() not in (".json", ".txt", ".md"):
                continue
            name = path.relative_to(workspace).as_posix()
            shared.direct_file(workspace, name)
            text = path.read_text(encoding="utf-8-sig")
            if path.suffix.casefold() == ".json":
                def strings(value, parents=(), blender=False):
                    if isinstance(value, str): yield value, blender
                    elif isinstance(value, dict):
                        for key, item in value.items():
                            yield str(key), False
                            relative_field = (key in ("render_path", "file_browser_directories")
                                or (key == "path" and (
                                    (value.get("field") == "filepath" and value.get("structure") in ("Image", "ImagePackedFile"))
                                    or (value.get("field") == "name" and value.get("structure") == "Image")))
                                or (parents and parents[-1] == "image_paths"))
                            yield from strings(item, (*parents, key), relative_field)
                    elif isinstance(value, list):
                        for item in value: yield from strings(item, parents)
                values = strings(json.loads(text))
            else:
                values = ((line, False) for line in text.splitlines())
            def private(value, blender):
                # Blender's // denotes scene-relative data, not a filesystem root.
                # Admit only explicit Blender fields resolving inside this project.
                if blender and value.startswith("//"):
                    target = (path.parent / value[2:].replace("\\", "/")).resolve()
                    return not target.is_relative_to(root)
                return PRIVATE_LOCATION.search(value) is not None
            if any(private(value, blender) for value, blender in values):
                # Do not echo private machine paths into a distributable diagnostic.
                errors.append(name + " contains a machine-local path")
    return errors


def _export_input(root, workspace, name, prefix, suffix):
    """Own direct inputs only, including Windows reparse and hardlink refusal."""
    shared.safe_name(name)
    if (not name.startswith(prefix) or Path(name).suffix.casefold() != suffix
            or any(part.split(".", 1)[0].upper() in WINDOWS_RESERVED for part in name.split("/"))):
        raise ValueError("Foreign or unsupported selected source input: " + repr(name))
    path = shared.direct_file(workspace, MOD_ID + "/" + name)
    for part in (path, *path.parents):
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Selected source input traverses a reparse point: " + name)
        if part == root:
            break
    if path.stat().st_nlink != 1:
        raise ValueError("Selected source input is hardlinked: " + name)
    return path


def _unique_json(path):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError("Duplicate JSON declaration in " + path.name + ": " + key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=pairs)


def _selected_painted_creature_exports(root, workspace, ledger):
    """Validate the explicitly selected painted-2D source closure.

    Existing town/siege editable-scene semantics remain unchanged. Creature
    replacements use genuine masters and deterministic image assemblies;
    renamed geometry declarations or missing inputs cannot pass this route.
    """
    selected = ledger.get("painted_creature_sources")
    if selected is None:
        return {}
    creatures_path = _export_input(root, workspace, "content/creatures.json", "content/", ".json")
    creatures = _unique_json(creatures_path)
    if not isinstance(selected, dict) or set(selected) != set(creatures):
        raise ValueError("Painted creature source selection must cover every actual variant exactly")
    # Derive concrete presentation obligations from current registered content,
    # then bind those exact outputs to the currently selected manifest recipes.
    # A nonempty subset, matching count, or arbitrary extra recipe is not closure.
    factions_path = _export_input(root, workspace, "content/factions.json", "content/", ".json")
    factions = _unique_json(factions_path)
    faction = factions.get(FACTION)
    if not isinstance(faction, dict):
        raise ValueError("Actual faction definition missing for painted creature source selection")
    manifest_path = _export_input(root, workspace, "assets/manifest.json", "assets/", ".json")
    manifest = _unique_json(manifest_path)
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise ValueError("Actual selected asset manifest is missing")
    output_entries = {}
    for entry in assets:
        if not isinstance(entry, dict):
            raise ValueError("Invalid actual selected manifest entry")
        output = entry.get("output_path")
        if output in output_entries:
            raise ValueError("Duplicate actual selected output: " + str(output))
        output_entries[output] = entry
    roles = {
        "animation": "creature-battle-animation",
        "map": "creature-adventure-animation",
        "iconLarge": "creature-large",
        "iconSmall": "creature-small",
        "mapAttackFromLeft": "creature-adventure-attack-left",
        "mapAttackFromRight": "creature-adventure-attack-right",
    }
    obligations = {unit: {} for unit in creatures}
    def require(unit, resource, role):
        if not isinstance(resource, str) or not resource.startswith("runeterra/" + FACTION + "/"):
            raise ValueError("Missing or foreign registered painted creature resource: " + unit + " " + role)
        output = "Content/Sprites/" + resource
        entry = output_entries.get(output)
        if not isinstance(entry, dict) or entry.get("role") != role:
            raise ValueError("Selected output missing or wrong actual role: " + output)
        source = entry.get("source", {})
        recipe = source.get("recipe")
        if not isinstance(recipe, str) or not recipe.startswith("assets/recipes/"):
            raise ValueError("Actual selected resource has no canonical recipe: " + output)
        if recipe in obligations[unit] or any(recipe in values for key, values in obligations.items() if key != unit):
            raise ValueError("Duplicate canonical recipe binding for actual painted creature role: " + recipe)
        obligations[unit][recipe] = {"output": output, "role": role, "sha256": source.get("recipe_sha256")}
    for unit, creature in sorted(creatures.items()):
        graphics = creature.get("graphics", {})
        for field, role in roles.items():
            require(unit, graphics.get(field), role)
        missile = graphics.get("missile")
        if missile is not None:
            if not isinstance(missile, dict):
                raise ValueError("Invalid actual missile configuration: " + unit)
            require(unit, missile.get("projectile"), "projectile-animation")
    siege = faction.get("town", {}).get("siege", {})
    shooter = siege.get("shooter")
    if not isinstance(shooter, str) or shooter.split(":")[-1] not in creatures:
        raise ValueError("Actual tower shooter is not a registered painted creature")
    shooter = shooter.split(":")[-1]
    require(shooter, siege.get("towerIconLarge"), "siege-image")
    require(shooter, siege.get("towerIconSmall"), "siege-image")
    exports = {}
    for unit, binding in sorted(selected.items()):
        if not isinstance(binding, dict):
            raise ValueError("Invalid painted creature source binding: " + unit)
        name = binding.get("source_generation_ledger")
        path = _export_input(root, workspace, name, "assets/source/", ".json")
        if shared.digest(path) != binding.get("source_generation_ledger_sha256"):
            raise ValueError("Painted creature source ledger changed: " + unit)
        origin = _unique_json(path)
        if (origin.get("workflow") != "image-based-painted-2d"
                or origin.get("derived_from_blender") is not False
                or origin.get("user_rejected") is not False):
            raise ValueError("Selected creature origin is not current unrejected painted2D: " + unit)
        files = origin.get("files_sha256")
        if not isinstance(files, dict) or not files or not isinstance(origin.get("origins"), list) or not origin["origins"]:
            raise ValueError("Painted creature origin has no concrete source closure: " + unit)
        for record in origin["origins"]:
            if (not isinstance(record, dict) or record.get("kind") not in ("painted-2d-master", "image-generation")
                    or files.get(record.get("path")) != record.get("sha256")):
                raise ValueError("Unbound painted creature origin: " + unit)
        exports[MOD_ID + "/" + name] = path
        for source, pin in sorted(files.items()):
            suffix = Path(source).suffix.casefold()
            if suffix not in (".png", ".json", ".py", ".txt"):
                raise ValueError("Unsupported painted creature input: " + source)
            source_path = _export_input(root, workspace, source, "assets/source/", suffix)
            if not isinstance(pin, str) or not re.fullmatch(r"[0-9a-f]{64}", pin) or shared.digest(source_path) != pin:
                raise ValueError("Painted creature source missing or changed: " + source)
            if suffix == ".py" and re.search(r"\b(?:import\s+bpy|from\s+bpy\b)", source_path.read_text(encoding="utf-8")):
                raise ValueError("Geometry producer cannot be selected as painted creature source: " + source)
            exports[MOD_ID + "/" + source] = source_path
        recipes = binding.get("canonical_recipes")
        if not isinstance(recipes, dict) or set(recipes) != set(obligations[unit]):
            raise ValueError("Painted creature canonical recipe binding does not exactly cover its registered roles: " + unit)
        for recipe_name, pin in sorted(recipes.items()):
            recipe_path = _export_input(root, workspace, recipe_name, "assets/recipes/", ".json")
            if shared.digest(recipe_path) != pin:
                raise ValueError("Painted creature canonical recipe changed: " + recipe_name)
            recipe = _unique_json(recipe_path)
            expected = obligations[unit][recipe_name]
            if expected["sha256"] != pin or recipe.get("output_path") != expected["output"]:
                raise ValueError("Canonical recipe pin/output does not match its actual selected role: " + recipe_name)
            generation = recipe.get("generation", {})
            if (recipe.get("unit") != unit or generation.get("workflow") != "image-based-painted-2d"
                    or generation.get("source_generation_ledger") != name
                    or generation.get("source_generation_ledger_sha256") != binding["source_generation_ledger_sha256"]):
                raise ValueError("Canonical recipe is not bound to its selected painted creature: " + recipe_name)
            exports[MOD_ID + "/" + recipe_name] = recipe_path
    return dict(sorted(exports.items()))


def _selected_painted_town_exports(root, workspace, ledger):
    """Exact typed closure for Targon's selected complete painted town cohort.

    Does not retire or waive any creature, hero or siege source requirements.
    The caller unions this set with the unchanged selected-scene/creature set.
    """
    binding = ledger.get("painted_town_sources")
    if binding is None:
        for path in sorted((root / "assets/recipes/town/structures").glob("*.json")):
            recipe = _unique_json(path)
            generation = recipe.get("generation", {})
            if generation.get("workflow") == "image-based-painted-2d" and isinstance(generation.get("source_generation_ledger"), str) and generation["source_generation_ledger"].startswith("assets/source/town/"):
                raise ValueError("Active painted town recipes require their explicit source export binding")
        return {}
    if not isinstance(binding, dict) or set(binding) != {"source_generation_ledger", "source_generation_ledger_sha256", "assembly_script", "canonical_recipes"}:
        raise ValueError("Painted town source binding requires the exact supported typed schema")
    factions_path = _export_input(root, workspace, "content/factions.json", "content/", ".json")
    factions = _unique_json(factions_path)
    states = set(factions["targon"]["town"]["buildings"])
    native_states = {"villageHall", "townHall", "cityHall", "capitol", "fort", "citadel", "castle", "tavern", "marketplace", "blacksmith", "resourceSilo", "extraTownHall", "grail"}
    native_states.update("mageGuild" + str(i) for i in range(1, 5))
    native_states.update("special" + str(i) for i in range(1, 5))
    native_states.update(prefix + str(i) for prefix in ("dwellingLvl", "dwellingUpLvl") for i in range(1, 8))
    if states != native_states:
        raise ValueError("Painted Targon town must preserve its actual thirty-five dryland native functions")
    name = binding["source_generation_ledger"]
    origin_path = _export_input(root, workspace, name, "assets/source/town/", ".json")
    if shared.digest(origin_path) != binding["source_generation_ledger_sha256"]:
        raise ValueError("Painted town source generation ledger changed")
    origin = _unique_json(origin_path)
    if (origin.get("workflow") != "image-based-painted-2d" or origin.get("derived_from_blender") is not False
            or origin.get("user_rejected") is not False):
        raise ValueError("Selected town origin must be current unrejected genuine painted2D")
    files, origins, buildings = origin.get("files_sha256"), origin.get("origins"), origin.get("town_building_states")
    if not isinstance(files, dict) or not files or not isinstance(origins, list) or not origins or not isinstance(buildings, dict) or set(buildings) != states:
        raise ValueError("Painted town origin lacks complete native-state/source ownership")
    exports = {MOD_ID + "/" + name: origin_path}
    for source, pin in sorted(files.items()):
        suffix = Path(source).suffix.casefold()
        if suffix not in (".png", ".json", ".py", ".txt"):
            raise ValueError("Unsupported selected painted town source input")
        path = _export_input(root, workspace, source, "assets/source/town/", suffix)
        if not isinstance(pin, str) or not re.fullmatch(r"[0-9a-f]{64}", pin) or shared.digest(path) != pin:
            raise ValueError("Painted town source missing or changed: " + source)
        if suffix == ".py" and re.search(r"\b(?:import\s+bpy|from\s+bpy\b)", path.read_text(encoding="utf-8")):
            raise ValueError("Geometry artwork producer cannot be selected as painted town source")
        exports[MOD_ID + "/" + source] = path
    for record in origins:
        if (not isinstance(record, dict) or record.get("kind") not in ("painted-2d-master", "image-generation")
                or files.get(record.get("path")) != record.get("sha256")):
            raise ValueError("Painted town generation origin is not bound to real source bytes")
    origin_paths = {record["path"] for record in origins}
    for state, record in buildings.items():
        if (not isinstance(record, dict) or set(record) != {"master", "registered_frame"}
                or any(not isinstance(row, dict) or set(row) != {"path", "sha256"} or not isinstance(row.get("path"), str)
                       or not row["path"].endswith(".png") or files.get(row["path"]) != row.get("sha256") for row in record.values())):
            raise ValueError("Painted town state lacks its complete master and registered frame: " + state)
        if record["master"]["path"] not in origin_paths:
            raise ValueError("Painted town master lacks its genuine source-origin binding: " + state)
    assembly = binding["assembly_script"]
    if not isinstance(assembly, dict) or set(assembly) != {"path", "sha256"} or files.get(assembly.get("path")) != assembly.get("sha256") or Path(assembly["path"]).suffix != ".py":
        raise ValueError("Painted town assembly script is not bound to its selected closure")
    expected = {"assets/recipes/town/background.json", "assets/recipes/town/buildingIcons.json"}
    expected.update("assets/recipes/town/structures/" + state + suffix + ".json" for state in states for suffix in ("", "_area", "_border", "_campaign"))
    expected.update("assets/recipes/town/icons/" + form + "_" + status + "_" + size + ".json" for form in ("fort", "village") for status in ("normal", "built") for size in ("large", "small"))
    expected.update("assets/recipes/town/map/" + state + ".json" for state in ("village", "fort", "citadel", "castle", "capitol"))
    expected.update("assets/recipes/town/puzzle/piece" + str(i).zfill(2) + ".json" for i in range(48))
    expected.update("assets/recipes/town/ui/" + name + ".json" for name in ("creatureBackground120", "creatureBackground130", "guildWindow"))
    recipes = binding["canonical_recipes"]
    if not isinstance(recipes, dict) or set(recipes) != expected:
        raise ValueError("Painted town source binding must pin every actual native town recipe exactly")
    for recipe_name, pin in sorted(recipes.items()):
        path = _export_input(root, workspace, recipe_name, "assets/recipes/town/", ".json")
        if shared.digest(path) != pin:
            raise ValueError("Painted town canonical recipe changed: " + recipe_name)
        recipe = _unique_json(path)
        generation = recipe.get("generation", {})
        if (generation.get("workflow") != "image-based-painted-2d" or generation.get("source_generation_ledger") != name
                or generation.get("source_generation_ledger_sha256") != binding["source_generation_ledger_sha256"]):
            raise ValueError("Canonical recipe is not bound to its selected painted town origin: " + recipe_name)
        if recipe_name.startswith("assets/recipes/town/structures/") and recipe_name.removeprefix("assets/recipes/town/structures/").removesuffix(".json") in states:
            state = recipe_name.removeprefix("assets/recipes/town/structures/").removesuffix(".json")
            groups = recipe.get("groups")
            if not isinstance(groups, list) or len(groups) != 1 or groups[0].get("group") != 0 or len(groups[0].get("frames", [])) != 1:
                raise ValueError("Painted native town state requires its one complete current frame")
            frame = groups[0]["frames"][0]
            if frame.get("source") != buildings[state]["registered_frame"]["path"] or frame.get("sha256") != buildings[state]["registered_frame"]["sha256"]:
                raise ValueError("Native painted town state is not bound to its selected registered master")
        exports[MOD_ID + "/" + recipe_name] = path
    return dict(sorted(exports.items()))



def selected_scene_exports(root, workspace):
    """Return exact selected editable scene members, never guess from versions.

    Schema 1: editable_scenes maps project-relative .blend paths to SHA256.
    Optional scene_producers maps those paths to {path, sha256} own producers.
    Every active recipe/production scene dependency must be listed. An explicit
    required_for_production:false history record is not an active dependency.
    This selects source bytes only and makes no art/runtime/release approval.
    """
    root, workspace = _layout(root, workspace)
    ledger_path = _export_input(root, workspace, SCENE_EXPORT_LEDGER, "assets/production/", ".json")
    ledger = _unique_json(ledger_path)
    if (not isinstance(ledger, dict) or type(ledger.get("schema")) is not int or ledger["schema"] != 1
            or not isinstance(ledger.get("editable_scenes"), dict)):
        raise ValueError("Selected scene export ledger requires schema1 editable_scenes mapping")
    declared, exports, folded = ledger["editable_scenes"], {**_selected_painted_creature_exports(root, workspace, ledger), **_selected_painted_town_exports(root, workspace, ledger)}, set()
    for name, checksum in sorted(declared.items()):
        if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", checksum):
            raise ValueError("Invalid selected scene SHA256: " + repr(name))
        if name.casefold() in folded:
            raise ValueError("Case-aliased selected editable scene: " + name)
        folded.add(name.casefold())
        path = _export_input(root, workspace, name, "assets/source/", ".blend")
        if shared.digest(path) != checksum:
            raise ValueError("Selected editable scene hash changed: " + name)
        exports[MOD_ID + "/" + name] = path

    def producer(name, checksum=None):
        # Authored scene generators and metadata normalizers may be preserved
        # alongside their editable art. They remain exact own Python sources;
        # the same direct-file and checksum guards apply to both owned folders.
        prefix = "assets/source/" if isinstance(name, str) and name.startswith("assets/source/") else "scripts/"
        path = _export_input(root, workspace, name, prefix, ".py")
        if checksum is not None and (not isinstance(checksum, str)
                or not re.fullmatch(r"[0-9a-f]{64}", checksum) or shared.digest(path) != checksum):
            raise ValueError("Selected scene producer hash changed: " + name)

    producers = ledger.get("scene_producers", {})
    if not isinstance(producers, dict):
        raise ValueError("scene_producers must map declared scene paths to own producer records")
    for name, row in producers.items():
        if (name not in declared or not isinstance(row, dict) or set(row) != {"path", "sha256"}
                or not isinstance(row["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])):
            raise ValueError("Invalid selected scene producer ownership: " + str(name))
        producer(row["path"], row["sha256"])

    def dependency(name, checksum, owner):
        _export_input(root, workspace, name, "assets/source/", ".blend")
        if name not in declared:
            raise ValueError("Active scene dependency missing from source export selection: " + name + " in " + owner)
        if checksum is not None and checksum != declared[name]:
            raise ValueError("Active scene dependency pin differs from export selection: " + name + " in " + owner)

    def walk(value, owner):
        if isinstance(value, dict):
            if value.get("required_for_production") is False:
                return
            if isinstance(value.get("producer"), str) and value["producer"].endswith(".py"):
                if ("producer_sha256" in value and (not isinstance(value["producer_sha256"], str)
                        or not re.fullmatch(r"[0-9a-f]{64}", value["producer_sha256"]))):
                    raise ValueError("Invalid active source producer hash: " + value["producer"])
                producer(value["producer"], value.get("producer_sha256"))
            for key, item in value.items():
                if isinstance(key, str) and re.search(r"\.blend(?:\d+|~)?$", key, re.IGNORECASE):
                    dependency(key, item if isinstance(item, str) else None, owner)
                if isinstance(item, str) and re.search(r"\.blend(?:\d+|~)?$", item, re.IGNORECASE):
                    if key == "geometry_source":
                        # Frame records carry both a PNG sha256 and a separate
                        # editable geometry pin. Never substitute the PNG hash
                        # or waive a missing typed geometry declaration.
                        checksum = value.get("geometry_sha256")
                        if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", checksum):
                            raise ValueError("Missing or invalid active geometry_sha256: " + item + " in " + owner)
                    else:
                        checksum = value.get(key + "_sha256", value.get("sha256"))
                    dependency(item, checksum, owner)
                else:
                    walk(item, owner)
        elif isinstance(value, list):
            for item in value:
                walk(item, owner)
        elif isinstance(value, str) and re.search(r"\.blend(?:\d+|~)?$", value, re.IGNORECASE):
            dependency(value, None, owner)

    for directory in ("assets/recipes", "assets/production"):
        for path in sorted((root / directory).rglob("*.json")):
            if path == ledger_path:
                continue
            own_name = path.relative_to(root).as_posix()
            _export_input(root, workspace, own_name, directory + "/", ".json")
            walk(_unique_json(path), own_name)
    return dict(sorted(exports.items()))


def verify_prerequisites(root, workspace, manifest):
    try:
        _layout(root, workspace)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    return shared.verify(workspace, FACTION, NATIVE_ROOT, manifest,
                         lambda: dependency_paths(root, workspace))
