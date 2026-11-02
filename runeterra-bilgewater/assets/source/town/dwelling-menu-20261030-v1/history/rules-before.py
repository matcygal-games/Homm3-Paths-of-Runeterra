"""Bilgewater native source contracts. These checks do not execute VCMI."""
from faction_pipeline import check_graph, local_id, read_json, utility

FACTION = "bilgewater"
ROSTER = (("bilgeRat", "seaDog"), ("corsair", "pirateMarksman"),
          ("shellshotGunner", "reefBombardier"), ("krakenPriest", "tideHierophant"),
          ("cliffwing", "stormwing"), ("boardingCaptain", "fleetVeteran"),
          ("shoreLeviathan", "elderShoreLeviathan"))
GROWTH = (14, 9, 7, 4, 3, 2, 1)
CHAMPIONS = frozenset(("missFortune", "illaoi", "twistedFate", "graves", "gangplank", "fizz", "pyke", "nautilus",
                      "jack", "rafen", "nukkle", "mako", "bull", "fivePunchPablo", "perfidiousPromoter"))
SCENARIO_CHAMPIONS = frozenset()
CLASSES = frozenset(("freeCaptain", "tideSeer"))
PROJECTILE_ANGLES = [90, 45, 0, -45, -90]
# Current painted release-frame calibration; native launch observation remains pending.
# Shared native X yields the reviewed 2/3px residual; manual landmarks have 2px uncertainty.
MUZZLE_OFFSETS = {
    "corsair": {"lowerX": 32, "lowerY": -29, "middleX": 36, "middleY": -59, "upperX": 22, "upperY": -72},
    "pirateMarksman": {"lowerX": 36, "lowerY": -28, "middleX": 40, "middleY": -60, "upperX": 28, "upperY": -72},
    "shellshotGunner": {"lowerX": 32, "lowerY": -19, "middleX": 36, "middleY": -41, "upperX": 34, "upperY": -66},
    "reefBombardier": {"lowerX": 28, "lowerY": -19, "middleX": 34, "middleY": -39, "upperX": 38, "upperY": -69},
}
AURA = {"type": "MORALE", "val": 1, "propagator": "ARMY", "stacking": "runeterra.bilgewater.fleetMorale"}


def validate_creatures(creatures, pipeline):
    errors, pools = [], []
    if set(creatures) != {key for pair in ROSTER for key in pair}:
        errors.append("Bilgewater requires exactly fourteen selected own creatures; no retired aliases")
    for tier, pair in enumerate(ROSTER, 1):
        for variant, identifier in enumerate(pair):
            creature = creatures.get(identifier, {})
            if not local_id(creature.get("faction"), {FACTION}, pipeline) or creature.get("level") != tier:
                errors.append(f"{identifier}: own faction and selected tier required")
            if creature.get("growth") != GROWTH[tier - 1] or creature.get("doubleWide", False) != (tier in (5, 7)):
                errors.append(f"{identifier}: selected shared growth and footprint required")
            links = creature.get("upgrades", [])
            if [key.split(":")[-1] for key in links] != ([pair[1]] if not variant else []) or any(not local_id(key, creatures, pipeline) for key in links):
                errors.append(f"{identifier}: only the selected forward own upgrade link permitted")
            for field in ("hitPoints", "attack", "defense", "speed", "fightValue", "aiValue"):
                if type(creature.get(field)) is not int or creature[field] <= 0:
                    errors.append(f"{identifier}: positive integer {field} required")
            damage = creature.get("damage", {})
            if damage.get("min", 0) <= 0 or damage.get("max", 0) < damage.get("min", 0):
                errors.append(f"{identifier}: invalid damage interval")
            abilities = list(creature.get("abilities", {}).values())
            by_type = {bonus.get("type"): bonus for bonus in abilities}
            expected = {1: {"ENEMY_DEFENCE_REDUCTION"} if variant else set(),
                2: {"SHOOTER", "NO_MELEE_PENALTY"} if variant else {"SHOOTER"},
                3: {"SHOOTER"}, 4: {"SPELLCASTER", "CASTS", "SPECIFIC_SPELL_POWER"},
                5: {"FLYING"}, 6: {"MORALE"} if variant else set(),
                7: {"GENERAL_DAMAGE_REDUCTION", "KING"}}[tier]
            if set(by_type) != expected or len(by_type) != len(abilities):
                errors.append(f"{identifier}: selected native action/ability set violated")
            if any(bonus.get("propagator") for bonus in abilities) and not (identifier == "fleetVeteran" and abilities == [AURA]):
                errors.append(f"{identifier}: only the selected strongest-only fleet army aura propagates")
            if identifier == "seaDog" and by_type.get("ENEMY_DEFENCE_REDUCTION") != {"type": "ENEMY_DEFENCE_REDUCTION", "val": 10}:
                errors.append("seaDog: exactly ten percent enemy Defense reduction required")
            if tier == 4:
                contract = {"SPELLCASTER": {"type": "SPELLCASTER", "subtype": "core:cure", "val": variant + 1},
                    "CASTS": {"type": "CASTS", "val": 1},
                    "SPECIFIC_SPELL_POWER": {"type": "SPECIFIC_SPELL_POWER", "subtype": "core:cure", "val": (10, 15)[variant]}}
                if by_type != contract:
                    errors.append(f"{identifier}: one action-cost Basic/Advanced Cure, ten/fifteen HP per current priest required")
            if identifier == "fleetVeteran" and by_type.get("MORALE") != AURA:
                errors.append("fleetVeteran: one shared strongest-only army-membership morale bonus required")
            if tier == 7 and (by_type.get("GENERAL_DAMAGE_REDUCTION") != {"type": "GENERAL_DAMAGE_REDUCTION", "subtype": "damageTypeAll", "val": (15, 20)[variant]}
                    or by_type.get("KING") != {"type": "KING", "val": 2}):
                errors.append(f"{identifier}: bounded physical reduction and explicit Slayer eligibility required")
            shots = ((8, 16) if tier == 2 else (12, 16))[variant] if tier in (2, 3) else 0
            if creature.get("shots", 0) != shots:
                errors.append(f"{identifier}: selected finite physical ammunition required")
            graphics = creature.get("graphics", {})
            for field, filename in utility("identity").UNIT_GRAPHICS.items():
                if graphics.get(field) != pipeline.prefix + f"creatures/{identifier}/{filename}":
                    errors.append(f"{identifier}: own canonical {field} resource required")
            if "animationPreview" in graphics:
                errors.append(f"{identifier}: unimplemented optional preview extension prohibited")
            missile = graphics.get("missile", {})
            if tier in (2, 3):
                if missile.get("projectile") != pipeline.prefix + f"projectiles/{identifier}.json" or missile.get("frameAngles") != PROJECTILE_ANGLES or missile.get("attackClimaxFrame") != 4:
                    errors.append(f"{identifier}: own five-angle physical missile and release frame four required")
                if missile.get("offset") != MUZZLE_OFFSETS[identifier]:
                    errors.append(f"{identifier}: current painted release-frame muzzle offsets required")
            elif missile:
                errors.append(f"{identifier}: melee line must not register a missile")
        base, upgrade = (creatures.get(key, {}) for key in pair)
        prices = [creature.get("cost", {}) for creature in (base, upgrade)]
        charges = {resource: prices[1].get(resource, 0) - prices[0].get(resource, 0) for resource in set(prices[0]) | set(prices[1])}
        if any(amount < 0 for amount in charges.values()):
            errors.append(f"Tier {tier}: upgrade full recruitment price must not decrease")
        pools.append({"tier": tier, "creatures": list(pair), "growth": GROWTH[tier - 1], "upgrade_charge": charges})
    return errors, pools


def native_reference_errors(content, core_skills, core_spells):
    """Resolve real registries and nonempty generic specialty targets."""
    errors = []
    def registered(reference, registry, location):
        if not isinstance(reference, str) or not reference.startswith("core:") or reference[5:] not in registry:
            errors.append(f"{location}: unregistered native reference {reference!r}")
            return None
        return registry[reference[5:]]
    for identifier, hero_class in content.get("heroClasses", {}).items():
        for reference in hero_class.get("secondarySkills", {}):
            registered(reference, core_skills, identifier + ".secondarySkills")
    for identifier, hero in content.get("heroes", {}).items():
        for reference in hero.get("spellbook", []):
            registered(reference, core_spells, identifier + ".spellbook")
        for skill in hero.get("skills", []):
            registered(skill.get("skill"), core_skills, identifier + ".skills")
        specialty = hero.get("specialty", {})
        if "secondary" in specialty:
            skill = registered(specialty["secondary"], core_skills, identifier + ".specialty")
            if skill is not None:
                basic = utility("common").merge(skill.get("base", {}), skill.get("basic", {}))
                targets = skill.get("specialty", [])
                if not targets or any(not basic.get("effects", {}).get(target, {}).get("type") for target in targets):
                    errors.append(f"{identifier}: secondary specialty has no executable native target")
    for identifier, faction in content.get("factions", {}).items():
        for reference in faction.get("town", {}).get("guildSpells", {}):
            registered(reference, core_spells, identifier + ".guildSpells")
    for identifier, creature in content.get("creatures", {}).items():
        for ability in creature.get("abilities", {}).values():
            if ability.get("type") in ("SPELLCASTER", "SPECIFIC_SPELL_POWER"):
                registered(ability.get("subtype"), core_spells, identifier + ".abilities")
    return errors


def validate_heroes(content, pipeline):
    errors = []
    heroes, classes, creatures = (content.get(key, {}) for key in ("heroes", "heroClasses", "creatures"))
    if set(heroes) != CHAMPIONS or set(classes) != CLASSES:
        errors.append("Bilgewater requires fifteen selected unique heroes and two own classes")
    if {key for key, hero in heroes.items() if hero.get("special", False)} != SCENARIO_CHAMPIONS:
        errors.append("All fifteen selected Bilgewater heroes must be ordinary skirmish eligible")
    for identifier, hero in heroes.items():
        if not local_id(hero.get("class"), classes, pipeline):
            errors.append(f"{identifier}: own hero class required")
        skills = hero.get("skills", [])
        if len(skills) != 2 or len({skill.get("skill") for skill in skills}) != 2 or any(skill.get("level") != "basic" for skill in skills):
            errors.append(f"{identifier}: two different Basic starting skills required")
        army = hero.get("army", [])
        if not army or len(army) > 7:
            errors.append(f"{identifier}: nonempty legal starting army required")
        for stack in army:
            reference = stack.get("creature")
            if not local_id(reference, creatures, pipeline) or creatures[reference.split(":")[-1]].get("level", 99) > 3:
                errors.append(f"{identifier}: starting army must contain only own tiers one to three")
            if stack.get("min", 0) <= 0 or stack.get("max", 0) < stack.get("min", 0):
                errors.append(f"{identifier}: invalid starting stack range")
        specialty = hero.get("specialty", {})
        if "creature" in specialty and not local_id(specialty["creature"], creatures, pipeline):
            errors.append(f"{identifier}: creature specialty must resolve own roster")
        for field in ("large", "small", "specialtyLarge", "specialtySmall"):
            if hero.get("images", {}).get(field) != pipeline.prefix + f"heroes/{identifier}/{field}.png":
                errors.append(f"{identifier}: own canonical {field} image required")
    for identifier, hero_class in classes.items():
        if not local_id(hero_class.get("faction"), {FACTION}, pipeline):
            errors.append(f"{identifier}: own class faction required")
        for field in ("lowLevelChance", "highLevelChance"):
            values = hero_class.get(field, {})
            if set(values) != {"attack", "defence", "spellpower", "knowledge"} or sum(values.values()) != 100:
                errors.append(f"{identifier}: complete hundred-percent {field} distribution required")
        if hero_class.get("tavern", {}).get(FACTION, 0) <= 0:
            errors.append(f"{identifier}: positive own tavern recruitment weight required")
    return errors


def validate_town(faction, creatures, pipeline):
    errors, order, effective = check_graph(faction)
    town, buildings = faction.get("town", {}), faction.get("town", {}).get("buildings", {})
    if faction.get("disabled") or faction.get("special"):
        errors.append("Bilgewater must remain an additional selectable faction")
    if faction.get("nativeTerrain") != ["sand"] or faction.get("alignment") != "neutral" or town.get("primaryResource") != "crystal" or town.get("mageGuild") != 3:
        errors.append("Selected sand, neutral compatibility, crystal and level-three guild required")
    if len(buildings) != 35 or set(buildings) != set(effective) or set(buildings) != set(town.get("structures", {})):
        errors.append("Exactly thirty-five canonical states with complete matching structure definitions required")
    groups = [group for row in town.get("hallSlots", []) for group in row]
    if len(groups) != 18 or sorted(key for group in groups for key in group) != sorted(set(buildings) - {"ship"}):
        errors.append("Sixteen land HALL sites plus coast and Grail must cover every non-ship state once")
    for tier, pair in enumerate(ROSTER, 1):
        pools = town.get("creatures", [])
        if tier > len(pools) or tuple(key.split(":")[-1] for key in pools[tier - 1]) != pair or any(not local_id(key, creatures, pipeline) for key in pools[tier - 1]):
            errors.append(f"Tier {tier}: selected own base and upgrade must share one recruitment pool")
        base, upgrade = f"dwellingLvl{tier}", f"dwellingUpLvl{tier}"
        if buildings.get(upgrade, {}).get("upgrades") != base or not any(base in group and upgrade in group for group in groups):
            errors.append(f"Tier {tier}: dwelling upgrade must replace its base in one site")
    if len(town.get("creatures", [])) != 7 or town.get("horde") != [-1, -1]:
        errors.append("Exactly seven shared recruitment pools and no additional horde required")
    for service, tier, bonus in (("special1", 4, {"type": "MORALE", "val": 1}), ("special2", 6, {"type": "LUCK", "val": 1})):
        base, upgrade = f"dwellingLvl{tier}", f"dwellingUpLvl{tier}"
        if buildings.get(service, {}).get("bonuses") != [bonus] or buildings.get(base, {}).get("upgrades") != service or not any(service in group and base in group and upgrade in group for group in groups):
            errors.append(f"{service}: one native defending bonus retained in its single dwelling site required")
        if any(buildings.get(key, {}).get("upgradeReplacesBonuses", False) or buildings.get(key, {}).get("bonuses") for key in (base, upgrade)):
            errors.append(f"{service}: dwelling states must retain rather than duplicate the ancestor bonus")
    merchant = buildings.get("special3", {})
    if merchant.get("type") or merchant.get("marketModes") != ["resource-artifact", "artifact-resource"]:
        errors.append("Black Market must use native artifact merchant marketModes exactly once, without an unsupported building type")
    if sum("resource-artifact" in value.get("marketModes", []) for value in buildings.values()) != 1:
        errors.append("Artifact merchant must not be duplicated across slots")
    if buildings.get("resourceSilo", {}).get("produce") != {"crystal": 1} or buildings.get("resourceSilo", {}).get("bonuses"):
        errors.append("Slaughter Docks occupy the sole silo and produce exactly one crystal daily")
    if buildings.get("special4", {}).get("produce") != {"gold": 150} or buildings.get("special4", {}).get("bonuses"):
        errors.append("Treasure Vault produces exactly one hundred fifty gold daily")
    for key in buildings:
        if key not in ("ship", "shipyard") and "shipyard" in utility("validation").condition_names(buildings[key].get("requires")):
            errors.append(f"{key}: ordinary land construction must not depend on optional coast")
    if buildings.get("grail", {}).get("bonuses") or buildings.get("grail", {}).get("produce"):
        errors.append("Grail must inherit native income/growth once without a duplicate explicit bonus")
    for key, structure in town.get("structures", {}).items():
        for field, suffix in (("animation", ".json"), ("area", "_area.png"), ("border", "_border.png"), ("campaignBonus", "_campaign.png")):
            if structure.get(field) != pipeline.prefix + f"town/structures/{key}{suffix}":
                errors.append(f"{key}: own canonical {field} structure resource required")
    pieces = faction.get("puzzleMap", {}).get("pieces", [])
    if len(pieces) != 48 or sorted(piece.get("index", -1) for piece in pieces) != list(range(1, 49)):
        errors.append("Puzzle requires forty-eight unique native reveal indices")
    if town.get("siege", {}).get("shooter") != "corsair":
        errors.append("Tower shooter must remain the selected base Corsair pistol troop")
    return errors, order


def validate(content, pipeline):
    if (pipeline.faction, pipeline.mod_id) != (FACTION, "runeterra-bilgewater"):
        return {"errors": ["Bilgewater semantics refuse foreign faction identity"]}
    errors, pools = validate_creatures(content.get("creatures", {}), pipeline)
    errors.extend(validate_heroes(content, pipeline))
    if content.get("spells") or content.get("artifacts"):
        errors.append("Bilgewater adds no custom spell or artifact collection")
    core = pipeline.root.parent / "vcmi-develop/vcmi-develop/config"
    skills = read_json(core / "skills.json")
    spells = {key: value for path in (core / "spells").glob("*.json") for key, value in read_json(path).items()}
    errors.extend(native_reference_errors(content, skills, spells))
    faction = content.get("factions", {}).get(FACTION)
    if not faction:
        return {"errors": errors + ["Missing own Bilgewater faction"]}
    town_errors, order = validate_town(faction, content.get("creatures", {}), pipeline)
    errors.extend(town_errors)
    return {"errors": errors, "pools": pools, "construction_order": order,
        "semantic_scope": "Own source registries, finite native action contracts, availability, recruitment and acyclic town sites; no gameplay or art acceptance",
        "status": "authored configuration", "runtime_verified": False, "release_accepted": False}
