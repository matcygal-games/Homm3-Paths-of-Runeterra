ZAUN LORE AND ROSTER SYNTHESIS
Runeterra / Zaun - design synthesis, 20 October 2026

Status: DESIGN PROPOSAL, coordinated by the Zaun coordinator. This document
synthesises the verified lore, the authored configuration and the measured
evidence into one design basis. It is NOT a claim that the lore is fully
verified, that the roster is balanced, or that anything has been painted,
loaded or played. Where the dated evidence disagrees with this document, the
evidence wins.

Companion documents:
  RUNETERRA_ZAUN_PROJECT_PROMPT.txt     the end-to-end implementation contract
  RUNETERRA_ZAUN_CREATURE_PROMPT.txt    the fourteen unit briefs
  RUNETERRA_ZAUN_CHAMPION_PROMPT.txt     the eighteen champion briefs
  RUNETERRA_ZAUN_TOWN_PROMPT.txt         the twenty town sites, puzzle and siege
  RUNETERRA_ZAUN_IMAGE_ART_PROMPT.txt    the 373-output art umbrella
  runeterra-zaun/review/                 the dated evidence, including the deep
                                         lore review and the roster audit
  runeterra-zaun/design/                 the active ledgers

===============================================================================
1. THE THREE EVIDENCE TIERS
===============================================================================

Everything in this project is one of three things, and the difference is
never blurred:

  VERIFIED CANON
      Supported by a named primary body that was actually fetched and read.
      The deep lore review records the URLs, the authors and the coverage.
      Only a verified body may support a factual statement about a champion
      or a region.

  AUDITED DESIGN LIBRARY
      The curated lore library and the design documents under
      homm3-runterra-main/homm3-runterra-main/mod_design/ and
      runeterra-zaun/design/. These are this project's source material. They
      may be correct, they may be project fiction, and they are not evidence
      about the real world.

  PROJECT FICTION
      Everything this project invents to make a Heroes III town work: the
      chem-baron employment economy, the Shimmer Factory, The Sump, the
      Code of Progress, the recruitment pool structure, the tier-seven beast,
      the town names. Project fiction is legitimate and often good, but it
      must be labelled as fiction in the source, the tooltips and the
      biographies, and it must never be presented as a Riot claim.

A biography line that cannot be traced to the first tier is either removed or
marked as project framing. A unit description that says "canonically" is
either backed by a verified body or rewritten.

===============================================================================
2. THE SETTING BOUNDARY
===============================================================================

This project uses the LEGACY Piltover/Zaun prose continuity: the shared city
with an industrial undercity below and a wealthy mercantile city above, a
shimmer resource, a chem-baron economy, an augmentation trade, and a
culture in which the body is a site of work and of debt. That continuity is
a deliberate selection, and it is recorded as such in
runeterra-zaun/design/lore-decisions.json.

The boundary rules, and they are not negotiable inside the content:

  - The Arcane era, the Hexcore, the Primordian events and any modern rework
    chronology are NOT part of this continuity. No champion biography, unit
    description, town name or building description may import them.
  - HEXTECH IS NOT EXCLUSIVELY PILTOVER AND NOT FORBIDDEN TO ZAUN. The deep
    review read a Shuriman hextech crystal in Blitzcrank's own biography, so
    "hextech equals Piltover" is not a canon rule, and "hextech is banned in
    Zaun" is not a canon rule either. The project chooses a chemtech army
    doctrine - industrial chemistry, salvage and augmentation rather than
    crystal engineering - and that choice is labelled as a project choice, not
    as a canon prohibition. Blitzcrank's biography is the source for the
    legacy-supported reading of an autonomous, compassionate steam construct
    that rescued a miner's child; the review could not date the revision of
    that biography, so it is not reclassified as Hexcore-era material and not
    read for exclusion.
  - TECHNOLOGY IS NOT CITIZENSHIP. A Piltover-linked champion can be a Zaun
    scenario guest without becoming a Zaun citizen. A Zaun champion can work
    with Piltover without being reclassified. A champion's place in the
    Zaun roster is a recruitment or scenario role, not a nationality.
  - THE CHEM-BARON ECONOMY OF ZAUN AND THE GLASC INDUSTRIES ARE THE SAME
    CITY. Renata Glasc built Glasc Industries in Zaun, from her parents'
    alchemical research, and expanded it into Piltover. She is a Zaun
    chem-baroness with a Piltover commercial reach, not a Piltover house that
    is kept apart from the undercity. Her advertisements are not objective
    medical canon.
  - POLLUTION AND AUGMENTATION ARE NOT A MORAL VERDICT. They are ordinary
    facts of life in this setting. The faction is neutral in alignment as a
  game rule; that is not a claim of innocence, and the art must not
  caricature the city or its people as slum, feral or broken. Augmentation is
  equipment, not degradation, and it never removes a character's agency.
  - No invented geography. The exact relation between the sump, the swamp
  and the districts above it is this project's fiction and is not painted as
  a canon map.
  - No champion serves a government as a lore fact, and ordinary tavern
  availability is written as this project's skirmish hiring abstraction, not
  as a political appointment.

===============================================================================
3. THE EIGHTEEN CHAMPIONS
===============================================================================

Two classes, eighteen champions, six ordinary and twelve scenario-only. The
specialty column is the authored native form from
runeterra-zaun/content/heroes.json; the scope column is the contract in
runeterra-zaun/design/champion-acceptance.json and must appear in the
tooltip exactly as written.

ORDINARY - recruitable in the Zaun tavern, a hiring abstraction:

  blitzcrank   Machinist  Salvage Escort         GENERAL_DAMAGE_REDUCTION 5
  jinx         Machinist  Overpacked Magazines   SHOTS +4, SHOOTER_ONLY
  singed       Chemist    Alchemical Bombardment Fireball scaling +5% per step
  drmundo      Machinist  Pain-Hardened Column   Armorer secondary specialty, step 5
  ekko         Chemist    Borrowed Moment         Haste fixed additive +1 at every tier
  urgot        Machinist  Dredge Fireteam         +2 ranged Attack, ONLY_DISTANCE_FIGHT

SCENARIO-ONLY - placed on the map or held in neutral prisons:

  viktor        Chemist    Augmented Formation    Stone Skin fixed additive +2
  warwick       Machinist  Blood Hunt             +2 melee Attack, ONLY_MELEE_FIGHT
  twitch        Machinist  Contaminating Volley   ENEMY_DEFENCE_REDUCTION 10, ONLY_DISTANCE_FIGHT
  zac           Machinist  Resilient Escort       MORALE +1
  ziggs         Chemist    Demolition Crew        NO_WALL_PENALTY
  zeri          Machinist  Electric Advance       SIGHT_RADIUS +1
  janna         Chemist    Sheltering Tailwind    LUCK +1
  renata        Chemist    Glasc Dividends        GENERATE_RESOURCE gold 125 per day
  caitlyn       Machinist  Measured Fire          Archery secondary specialty, step 5
  vi            Machinist  Denting Command        ENEMY_DEFENCE_REDUCTION 10, ONLY_MELEE_FIGHT
  corki         Machinist  Route Briefing         +100 land movement
  heimerdinger  Chemist    Pressure-Frame Tuning  tier-three construct upgrade specialty, step 5

Rules that constrain every biography and portrait:

  - The regional and biographical statements are the deep lore review's
    dossiers. Until a dossier exists for a champion, no birthplace, no
    species, no faction membership and no era may be written into its
    biography. Corki is a YORDLE pilot with Bandle City roots who left for
    Piltover and leads the Screaming Yipsnakes; he is never presented as a
    Noxian pilot. Renata is a ZAUN chem-baroness whose Glasc Industries
    expanded into Piltover; Caitlyn and Heimerdinger are Piltover-linked
    guests. Zeri is a Zaun community mage of the Entresol, and Janna is an
    ancient coastal wind spirit who protects modern Zaun; neither is
    reclassified as a Shuriman national.
  - Blitzcrank is a construct, Zac is a monster of the undercity and Warwick
    is a beast-man. Their portraits are what they are, not human faces on a
    human body plan, and not generic human portrait rules. Zac and Janna are
    singular: the project never recruits a mass-produced copy of either.
  - The six ordinary champions are the ones the project's hiring abstraction
    puts in a tavern. The twelve scenario champions are the ones whose
    command needs a negotiated or opposing role. That split is a project
    framing decision, not a claim about canon availability.
  - Every specialty is a native form. The scope must be exact: the Armorer
    bonus reduces melee and ranged attack damage and NOT spell damage;
    NO_WALL_PENALTY removes the wall penalty for a shot at a defender behind
    the walls and grants no catapult ability, no extra shots and no damage to
    structures; the ENEMY_DEFENSE_REDUCTION specialties are filtered by the
    native attack mode.

===============================================================================
4. THE FOURTEEN UNITS
===============================================================================

Seven pairs. The stats, prices, growth and native abilities below are the
authored configuration in runeterra-zaun/content/creatures.json; the prose is
the identity contract in runeterra-zaun/design/unit-identity.json and the
full briefs are in RUNETERRA_ZAUN_CREATURE_PROMPT.txt.

  T1  Zaun Thug             6/3/2  1-3  spd5  35g   growth 14  no ability
     Chem-Punk              8/4/3  2-4  spd6  50g   growth 14  no ability
  T2  Chem Ravager         15/6/3  2-4  spd5 100g   growth 9   HP_REGENERATION 2
     Mutant Berserker      20/8/5  3-5  spd6 140g   growth 9   HP_REGENERATION 3
  T3  Chemtech Construct   28/7/6  4-8  spd4 250g   growth 7   MECHANICAL, SHOOTER 8 shots
     Reinforced Construct  38/9/8  6-11 spd5 350g   growth 7   MECHANICAL, SHOOTER 12 shots
  T4  Chem-Baron Enforcer  40/11/10 6-9  spd5 350g  growth 4   no ability
     Cybernetic Guard      50/12/11 7-11 spd6 500g  growth 4   THREE_HEADED_ATTACK
  T5  Chem-Baron Agent     65/14/11 12-18 spd6 600g growth 3   SPELLCASTER core:weakness 1,
                                                        CASTS 1, CREATURE_ENCHANT_POWER 3
     Master Alchemist      70/15/13 13-20 spd6 700g growth 3  SPELLCASTER core:weakness 2,
                                                        CASTS 1, CREATURE_ENCHANT_POWER 3
  T6  Augmentation Veteran 95/16/14 16-24 spd6 1150g growth 2  LONG_WEAPON
     Chemtech Vanguard    105/17/16 18-26 spd7 1500g growth 2  LONG_WEAPON
  T7  Apex Predator       240/27/24 40-60 spd7 3200g +1 sulfur growth 1
                                                        HP_REGENERATION 10, KING 2, two hexes
     Perfect Mutation     290/29/26 45-60 spd8 4320g +2 sulfur growth 1
                                                        HP_REGENERATION 15, KING 2, two hexes,
                                                        ATTACKS_ALL_ADJACENT on the upgrade

The stat line is HP/Attack/Defense, then damage, then Speed, then price and
growth. All fourteen values are the authored configuration in
runeterra-zaun/content/creatures.json. Twelve of the fourteen were re-derived
on 20 October 2026 from the distinctiveness review and were not copied from
it; the tier-one and tier-three pairs keep their audited values unchanged.

Five ability statements must appear in the tooltips in this exact sense, and
each of them is a correction of an earlier over-statement:

  - HP_REGENERATION (tiers two and seven) restores the missing hit points of
    the TOP surviving creature of the stack, capped by that creature's missing
    health, and never revives a dead creature. It is not per-model
    regeneration and it is not resurrection. Source: BattleFlowProcessor.cpp,
    GameStatePackVisitor.cpp, CUnitState.cpp CHealth::heal.
  - THREE_HEADED_ATTACK (tier four upgrade) adds the hexes immediately to the
    left and right of the target to the strike, so one swing can hit three
    enemies. It adds no extra attack, no spell damage and no defence
    penetration. Source: CBattleInfoCallback.cpp getPotentiallyAttackableHexes.
  - LONG_WEAPON (tier six) lets the unit strike over exactly one empty hex,
    and that long attack is not answered by retaliation. It is not a ranged
    shot and it cannot strike through another stack. Source: BonusEnum.h and
    CBattleInfoCallback.cpp fromWhichHexAttack.
  - ATTACKS_ALL_ADJACENT (tier seven upgrade) adds every hex around the
    attacker to the strike, so the grab tears at all enemies standing next to
    it. Only hostile stacks are hit, so it carries no friendly fire. Source:
    CBattleInfoCallback.cpp getPotentiallyAttackableHexes.
  - KING 2 (tier seven) is a native counterplay marker: a slayer effect only
    reaches the stack when its mastery meets that value, so a basic slayer
    spell does not grant its additional Attack against this stack. It is not
    immunity to damage: the stack still takes ordinary damage. Source:
    scripts/damage/damageCalculator.lua getAttackFromSlayer and
    config/spells/timed.json Slayer mastery parameters.

The tier-seven pair is a DECLARED PROJECT FICTION. The official material does
not describe a canonical Zaun apex predator, and the unit is never presented
as a Riot claim.

===============================================================================
5. THE COMPOSITION, AND WHAT IS DELIBERATELY MISSING
===============================================================================

Zaun's army is a narrow industrial ground army, and the narrowness is the
identity:

  - One shooter line, at tier three. Zaun has NO ranged answer below the
    third dwelling.
  - One line that casts, at tier five, and it is a MELEE unit that trades its
    action for a single charge.
  - One two-hex line, at tier seven.
  - NO flyers. NO cavalry. NO undead. No second mechanical line.
  - Everything except the tier-three construct is living, and augmentation is
    never a non-living classification.

The absent abilities are as much a part of the design as the present ones.
Demacia has a non-living petricite colossus with spell-damage reduction and
a KING slayer marker, a petricite-staff disruptor that raises the enemy
hero's battle spell cost, and a petricite spellcaster; Noxus has a
teleport-style covert flanker, a flying two-hex bound demon with a KING
marker and a morale aura, and a ranged crimson adept that casts a curse.
Zaun has a repairman, a workshop machine, a fanning heavy, a reach tool, a
chemist and a lab beast. The town fights with chemistry and salvage, and
loses the mobility and the air that the other two factions own.

The first-volley and siege weakness is a real cost and is kept deliberately.
It is an open balance item, not a settled one: see
runeterra-zaun/design/creature-balance.json#/openFindings.

===============================================================================
6. CROSS-FACTION DIVERSITY, MEASURED FROM THE CONTENT DICTIONARIES
===============================================================================

This section compares the three Runeterra factions directly, by reading
runeterra-demacia/content/creatures.json and
runeterra-noxus/content/creatures.json against the Zaun dictionary. The
ranked audit lives in
runeterra-zaun/review/zaun-roster-distinctiveness-20261020.md and is the
authority; this section is the coordinator's own reading of the same data.

Tier-by-tier ability overlap AFTER the 20 October 2026 corrections:

  T1  Zaun: none            Demacia: DEFENSIVE_STANCE   Noxus: none
      ACCEPTED. Tier one is conventionally plain in Heroes III, so a plain,
      cheap tier one is shared genre grammar and not an identity claim. Zaun
      and Noxus tier-one units are both cheap human foot soldiers.

  T2  Zaun: HP_REGENERATION Demacia: SHOOTER + range   Noxus: none
      DISTINCT. Zaun's tier two is unique among the three. Its contact damage
      was cut from 3-7 and 5-10 to 2-4 and 3-5 at unchanged price, because the
      audit measured the old budget at more than twice the original same-slot
      median per gold.

  T3  Zaun: SHOOTER + MECHANICAL
      Demacia: SHOOTER (two units, tier two and tier three)
      Noxus: SHOOTER (tier three)
      ACCEPTED, RECORDED. Tier three is the shooter tier in all three
      factions and the upgrade adds a ranged mechanic in all three. Zaun's
      line is the only MECHANICAL one; the finite ammunition is the shared
      Heroes III shooter rule, not a Zaun distinction, but the slot and the
      ranged tempo are shared.

  T4  Zaun: no ability, and THREE_HEADED_ATTACK on the upgrade
      Demacia: ENEMY_DEFENCE_REDUCTION 20/30 (plus ADDITIONAL_RETALIATION on
      the upgrade)
      Noxus: FLYING / movementTeleporting
      RESOLVED. The old Zaun tier four was the same native
      ENEMY_DEFENCE_REDUCTION bonus as Demacia's tier four, in the same
      single-target armour-cutter role, on a larger and costlier body. The
      rule was removed and the line was rebuilt around the native fan strike,
      which neither peer faction uses.

  T5  Zaun: SPELLCASTER core:weakness + CASTS 1 + CREATURE_ENCHANT_POWER 3,
      a MELEE unit with no ranged attack
      Demacia: CHARGE_IMMUNITY (tier five)
      Noxus: SHOOTER, and on the upgrade SPELLCASTER core:curse + CASTS 1 +
      CREATURE_ENCHANT_POWER 3
      STILL OPEN, RECORDED. The CASTS + CREATURE_ENCHANT_POWER combination is
      a house pattern that also appears in Noxus tier five and Demacia tier
      seven. Zaun's melee debuffer and Noxus's ranged caster are different
      units and the spells differ, but the "one charge of a debuff" idea is
      not unique. The price was cut so that both variants sit inside the
      measured original tier-five envelope; the shell itself stays a
      documented open overlap rather than an invented fix.

  T6  Zaun: LONG_WEAPON on both variants
      Demacia: CHANGES_SPELL_COST_FOR_ENEMY
      Noxus: two hexes, and TWO_HEX_ATTACK_BREATH on the upgrade
      RESOLVED. The old Zaun tier six was the same native DEFENSIVE_STANCE
      bonus Demacia's tier one uses, and the stance made the unit forgo its
      attack. It was replaced with the native long-tool reach, which neither
      peer faction uses.

  T7  Zaun: HP_REGENERATION, two hexes, KING 2, and ATTACKS_ALL_ADJACENT on
      the upgrade
      Demacia: NON_LIVING, SPELL_DAMAGE_REDUCTION, a shield caster, KING
      Noxus: NON_LIVING, FLYING, KING, and on the upgrade MORALE -1
      RESOLVED. The old Zaun upgrade was the same native TWO_HEX_ATTACK_BREATH
      bonus Noxus's upgraded tier six uses, including the rear-hex friendly
      fire. It was replaced with the native all-adjacent grab. The KING 2
      marker is now shared with both peer apexes, which is a counterplay
      marker and not an identity claim.

SUMMARY OF THE OVERLAPS, after the 20 October 2026 corrections:

  1. RESOLVED - tier four ENEMY_DEFENCE_REDUCTION shared with Demacia tier
     four. Replaced by THREE_HEADED_ATTACK.
  2. RESOLVED - the two-hex upgrade TWO_HEX_ATTACK_BREATH shared with Noxus.
     Replaced by ATTACKS_ALL_ADJACENT.
  3. RESOLVED - tier six DEFENSIVE_STANCE shared with Demacia tier one.
     Replaced by LONG_WEAPON.
  4. RECORDED - tier three is the shooter tier in all three factions.
  5. RECORDED - the CASTS + CREATURE_ENCHANT_POWER one-charge debuff pattern
     is used in all three factions, in three different tiers. Zaun's tier
     five is the closest to Noxus's.
  6. RECORDED - Zaun and Noxus share a plain tier one.

Recorded overlaps are not fatal and are not a licensing problem: shared
mechanics with different subjects, equipment, statistics, silhouettes and
counters are legitimate in Heroes III. The three resolved items were changed
in the content dictionary, the ledgers, the rules, the tests and the recipes
together, and they did not take a native mechanic away from Demacia or Noxus,
which are other people's work and are not being changed here.

The replacement values are UNCALIBRATED DESIGN NUMBERS. Their gold and
statistic values were placed inside the measured original town envelopes
(tier four 250-500 gold, tier five 350-700, tier six 750-1600, tier seven
1500-5000), they are not a balance result, and the new native bonuses are
source-inspected rather than executed. The tier-seven sulfur surcharge is a
project choice with no original precedent and is outside the gold-only
comparison.

===============================================================================
7. THE BALANCE BASELINE AND ITS LIMITS
===============================================================================

The arithmetic behind the prices and the growth is in
runeterra-zaun/design/creature-balance.json, anchored on the measured
installed profiles of the original towns in
runeterra-demacia/design/castle-balance-evidence.json. The weekly figures:

  T1  35 / 50 gold,   growth 14   ->  490 / 700 gold per week
  T2  100 / 140 gold, growth 9    ->  900 / 1260
  T3  250 / 350 gold, growth 7    ->  1750 / 2450
  T4  350 / 500 gold, growth 4    ->  1400 / 2000
  T5  600 / 700 gold, growth 3    ->  1800 / 2100
  T6  1150 / 1500 gold, growth 2  ->  2300 / 3000
  T7  3200 / 4320 gold, growth 1  ->  3200 / 4320, plus 1 or 2 sulfur

  Base week 11,840 gold plus 1 sulfur. Upgrade surcharge 3,990 gold plus
  1 sulfur, so an upgraded week is 15,830 gold plus 2 sulfur. For comparison
  the same arithmetic on the authored peer rosters is 11,725 gold plus 1 gem
  for Demacia and 11,190 gold plus 1 sulfur for Noxus.

The LIMITS, which are not optional wording:

  - The fightValue and aiValue fields are DESIGNER ESTIMATES. The engine
    computes its own combat valuation, and the estimator has never been
    compared against it for Zaun.
  - The three replacement lines (tier four, tier six, tier seven) carry
    UNCALIBRATED values. Their gold and statistics were placed inside the
    measured original town envelopes, not derived from a simulation, and the
    tier-seven sulfur surcharge is a project addition with no original
    precedent.
  - The three new native bonuses are SOURCE-INSPECTED, not executed. Whether
    the native AI selects a long-tool strike, how often a fan strike finds a
    second target and how the all-adjacent grab plays out in a real battle
    are all unmeasured.
  - The regeneration line was found to be weaker than the original audited
    wording implied, because the native rule repairs the top creature only.
    The earlier optimistic note is withdrawn.
  - There is NO native creature-value calibration, NO combat simulation, NO
    AI result and NO win-rate claim for Zaun. A number in this project is a
    design intent, not a measurement.
  - The 6 hit points of the tier-one unit is unusually fragile for its price
    and is the first candidate for a simulation-led adjustment.

===============================================================================
8. WHAT IS STILL OPEN
===============================================================================

  - The deep lore review is the authority for every champion dossier and for
    the regional table. Its section 8 replacement biographies and section 8.2
    creature descriptions were applied to the content on 20 October 2026; the
    dated review is not rewritten. Two earlier statements in this document
    were wrong and are corrected here: Corki is not a Noxian pilot, and the
    Glasc house is a Zaun institution, not a Piltover one.
  - The roster audit is the authority for the ranked distinctiveness verdict.
    Its tier-four, tier-five, tier-six and tier-seven corrections were applied
    to the content, the ledgers, the rules, the tests and the recipes; the
    audit file itself is preserved unedited.
  - No Zaun battle, window, load, save, AI or install evidence exists. The
    acceptance categories are not_run. The tier-one art is authored and
    converted, but it is built-unreviewed: no native visual review and no
    accepted art exist.
  - The demonstration map is a source fixture that has never been loaded by
    the client, and its footprints are unmeasured.
  - The redistribution and licence status is unresolved, which correctly
    blocks the release.

===============================================================================
9. HOW TO USE THIS DOCUMENT
===============================================================================

  - The town worker reads sections 2, 4, 5 and 6 and the town brief.
  - The creature worker reads sections 1, 2, 4, 5, 6 and 7 and the creature
    brief.
  - The champion worker reads sections 1, 2, 3 and 6 and the champion brief.
  - The coordinator reads all of it before changing a single dictionary.
  - Anyone who changes a number here changes it in the content dictionary and
    in the ledgers first, and never in this document alone.
