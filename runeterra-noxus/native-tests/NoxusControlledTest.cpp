// Candidate 725ae80 native consumers, using the unchanged loaded Noxus dictionaries.
#include "StdInc.h"
#include "server/battles/BattleTestFixture.h"
#include "lib/GameLibrary.h"
#include "lib/entities/hero/CHero.h"
#include "lib/entities/hero/CHeroHandler.h"
#include "lib/CSkillHandler.h"
#include "lib/battle/BattleAction.h"
#include "lib/battle/BattleAttackInfo.h"
#include "lib/battle/BattleLayout.h"
#include "lib/battle/ReachabilityInfo.h"
#include "lib/bonuses/BonusList.h"
#include "lib/mapObjects/CGTownInstance.h"
#include "lib/mapObjects/army/CStackInstance.h"
#include "lib/gameState/CGameState.h"
#include "lib/CPlayerState.h"
#include "lib/networkPacks/PacksForClient.h"
#include "lib/spells/CSpell.h"
#include "server/CGameHandler.h"
#include "server/battles/BattleProcessor.h"
#include "server/battles/BattleResultProcessor.h"
#include "server/processors/NewTurnProcessor.h"

namespace
{
CreatureID creature(const std::string & id)
{
    return CreatureID(CreatureID::decode(id.find(':') == std::string::npos ? "runeterra-noxus:" + id : id));
}
HeroTypeID heroType(const std::string & id)
{
    return HeroTypeID(HeroTypeID::decode("runeterra-noxus:" + id));
}
void measured(const std::string & key, int64_t value)
{
    ::testing::Test::RecordProperty(key, std::to_string(value));
}
void note(const std::string & key, const std::string & value)
{
    ::testing::Test::RecordProperty(key, value);
}
bool includes(const battle::Units & units, const battle::Unit * unit)
{
    return std::find(units.begin(), units.end(), unit) != units.end();
}

class NoxusControlled : public BattleTestFixture
{
public:
    using Army = std::vector<std::pair<CreatureID, uint16_t>>;
    HeroTypeID requestedHero;
    Army requestedArmy;
    bool noxusTown = false;
    bool ownTown = false;

    void mapLoaded(CMap * loaded) override
    {
        TinyMapGameTest::mapLoaded(loaded);
        auto * placed = findHeroByOwner(PlayerColor(0));
        ASSERT_NE(placed, nullptr);
        placed->setHeroType(requestedHero);
        placed->clearSlots();
        int slot = 0;
        for(auto [type, count] : requestedArmy)
            placed->putStack(SlotID(slot++), std::make_unique<CStackInstance>(gameState().get(), type, count));
        if(noxusTown)
        {
            auto * town = findFirst<CGTownInstance>();
            ASSERT_NE(town, nullptr);
            town->subID = MapObjectSubID(FactionID::decode("runeterra-noxus:noxus"));
            if(ownTown)
                town->tempOwner = PlayerColor(0);
            for(int tier = 0; tier < 7; ++tier)
                town->addBuilding(BuildingID(BuildingID::DWELL_LVL_1 + tier));
        }
    }

    void setup(const std::string & hero = "riven", int level = 1, bool remove = true,
               Army army = {}, bool tokenOpponent = false)
    {
        if(gameHandler)
        {
            gameHandler.reset();
            server.gameState.reset();
            TinyMapGameTest::TearDown();
            TinyMapGameTest::SetUp();
            server.battleResults.clear();
        }
        if(army.empty())
            army = {{creature("legionRecruit"), 100}, {creature("core:pikeman"), 1}};
        requestedHero = heroType(hero);
        requestedArmy = army;
        TinyH3M::TinyH3MBuilder builder(EMapFormat::SOD);
        builder.size(36, false).name("Noxus candidate controlled lab")
            .playerActive(PlayerColor(0)).playerActive(PlayerColor(1))
            .hero({5,5,0}, HeroTypeID(0), PlayerColor(0)).heroGarrison({{creature("core:pikeman"), 1}})
            .heroExperience(static_cast<uint32_t>(LIBRARY->heroh->reqExp(level))).heroPrimary(0,0,5,10)
            .heroSecondarySkills({})
            .hero({7,7,0}, HeroTypeID(11), PlayerColor(1))
            .heroGarrison(tokenOpponent ? Army{{creature("core:pikeman"), 300}} :
                Army{{creature("core:pikeman"), 100}, {creature("core:archer"), 1}})
            .heroPrimary(0,0,5,10).heroSecondarySkills({})
            .town({12,12,0}, FactionID::CASTLE, PlayerColor(1));
        startWithMap(std::move(builder));
        ASSERT_NE(map(), nullptr);
        server.gameState = gameState();
        gameHandler = std::make_shared<CGameHandler>(server, gameState());
        gameHandler->randomizer->setSeed(seed);
        attackerSideHero = findHeroByOwner(PlayerColor(0));
        defenderSideHero = findHeroByOwner(PlayerColor(1));
        ASSERT_NE(attackerSideHero, nullptr);
        ASSERT_NE(defenderSideHero, nullptr);
        ASSERT_EQ(attackerSideHero->getHeroTypeID(), requestedHero);
        ASSERT_EQ(attackerSideHero->level, level);
        for(auto * placed : {attackerSideHero, defenderSideHero})
        {
            auto skills = placed->secSkills;
            for(auto [skill, mastery] : skills)
                placed->setSecSkillLevel(skill, 0, ChangeValueMode::ABSOLUTE);
            placed->setPrimarySkill(PrimarySkill::ATTACK, 0, ChangeValueMode::ABSOLUTE);
            placed->setPrimarySkill(PrimarySkill::DEFENSE, 0, ChangeValueMode::ABSOLUTE);
            placed->setPrimarySkill(PrimarySkill::SPELL_POWER, 5, ChangeValueMode::ABSOLUTE);
            placed->setPrimarySkill(PrimarySkill::KNOWLEDGE, 10, ChangeValueMode::ABSOLUTE);
        }
        for(const auto & bonus : defenderSideHero->getHeroType()->specialty)
            defenderSideHero->removeBonus(bonus);
        if(remove)
            for(const auto & bonus : attackerSideHero->getHeroType()->specialty)
                attackerSideHero->removeBonus(bonus);
        note("engine_scope", "candidate725ae80+a168a7b3, not selected66fa client or rendering");
        note("fixture", "H3M scaffold; MapListener binds exact loaded scoped hero/army before native CGameState initialization");
        measured("seed", seed);
    }

    void plainBattle(bool siege = false)
    {
        if(siege)
            startSiege();
        else
            startBattle();
    }

    bool send(const BattleAction & action)
    {
        return gameHandler->battles->makePlayerBattleAction(BattleID(0),
            battle()->sideToPlayer(action.side), action);
    }

    void naturalStart()
    {
        for(const auto & unit : battle()->stacks)
            gameHandler->battles->processBattleEventTriggers(*battle(), CombatEventType::BATTLE_SETUP, unit.get(), nullptr);
        battle()->tacticDistance = 1;
        battle()->tacticsSide = BattleSide::ATTACKER;
        ASSERT_TRUE(send(BattleAction::makeEndOFTacticPhase(BattleSide::ATTACKER)));
        ASSERT_NE(battle()->battleActiveUnit(), nullptr);
    }

    bool advance(const CStack * subject)
    {
        for(int steps = 0; steps < 150; ++steps)
        {
            const auto * active = battle()->battleActiveUnit();
            if(!active)
                return false;
            if(active->unitId() == subject->unitId())
                return true;
            if(!send(BattleAction::makeDefend(active)))
                return false;
        }
        ADD_FAILURE() << "Natural turn progression exceeded its bounded action budget";
        return false;
    }

    void nextRound()
    {
        int round = battle()->getRound();
        for(int steps = 0; steps < 150 && battle()->getRound() == round; ++steps)
        {
            const auto * active = battle()->battleActiveUnit();
            ASSERT_NE(active, nullptr);
            ASSERT_TRUE(send(BattleAction::makeDefend(active)));
        }
        ASSERT_GT(battle()->getRound(), round);
    }

    void position(CStack * unit, BattleHex hex)
    {
        // Fixture placement precedes measured actions and never sets activeStack.
        battle()->moveUnit(unit->unitId(), hex);
        for(auto occupied : unit->getHexes())
            ASSERT_TRUE(occupied.isAvailable());
    }

    CStack * realStack(BattleSide side, int slot = 0)
    {
        for(auto & unit : battle()->stacks)
            if(unit->unitSide() == side && unit->unitSlot() == SlotID(slot))
                return unit.get();
        return nullptr;
    }

    void snapshot(const std::string & prefix, const CStack * unit)
    {
        measured(prefix + "_id", unit->unitId());
        measured(prefix + "_front", unit->getPosition().toInt());
        measured(prefix + "_rear", unit->occupiedHex().toInt());
        measured(prefix + "_hp", unit->getAvailableHealth());
        measured(prefix + "_shots", unit->shots.available());
        measured(prefix + "_casts", unit->casts.available());
        measured(prefix + "_morale", unit->moraleVal());
        measured(prefix + "_round", battle()->getRound());
        measured(prefix + "_active", battle()->getActiveStackID());
        measured(prefix + "_status", static_cast<int>(unit->getTurnStatus()));
    }

    int64_t hit(CStack * from, CStack * target, bool ranged)
    {
        if(!advance(from))
        {
            ADD_FAILURE() << "Attacker was not naturally activated";
            return -1;
        }
        auto expected = battle()->calculateDmgRange(BattleAttackInfo(from, target, 0, ranged));
        auto hp = target->getAvailableHealth();
        bool accepted = ranged ? send(BattleAction::makeShotAttack(from, target)) :
            send(BattleAction::makeMeleeAttack(from, target, from->getPosition()));
        EXPECT_TRUE(accepted);
        auto actual = hp - target->getAvailableHealth();
        EXPECT_GE(actual, std::min<int64_t>(hp, expected.damage.min));
        EXPECT_LE(actual, std::min<int64_t>(hp, expected.damage.max));
        return actual;
    }

    bool heroCast(CGHeroInstance * hero, SpellID spell, CStack * target)
    {
        const auto side = hero == attackerSideHero ? BattleSide::ATTACKER : BattleSide::DEFENDER;
        CStack * allied = realStack(side);
        if(!allied || !advance(allied))
            return false;
        battle::Target aim;
        aim.emplace_back(target);
        return send(BattleAction::makeHeroSpellcast(side, aim, spell));
    }
};

TEST_F(NoxusControlled, ExactLoadedDictionaryRoster)
{
    for(auto id : {"legionRecruit", "legionVeteran", "drakeHound", "armoredDrakeHound", "axeReckoner",
         "veteranAxeReckoner", "roseSpellblade", "roseInfiltrator", "crimsonDisciple", "crimsonAdept",
         "minotaurReckoner", "veteranMinotaur", "ruinBringer", "greaterRuinBringer"})
    {
        SCOPED_TRACE(id);
        ASSERT_GE(creature(id).getNum(), 0);
        EXPECT_NE(creature(id).toCreature(), nullptr);
    }
    for(auto id : {"darius", "draven", "swain", "leblanc", "vladimir", "katarina", "talon", "cassiopeia",
         "samira", "kled", "riven", "rell", "briar", "ambessa", "annie", "sion", "mordekaiser", "alistar"})
        EXPECT_GE(heroType(id).getNum(), 0) << id;
}

class NoxusMobility : public NoxusControlled, public ::testing::WithParamInterface<std::string> {};

TEST_P(NoxusMobility, BattleObstacleLegalityAndNaturalTurnCost)
{
    setup("riven", 1, true, {{creature(GetParam()), 20}, {creature("core:pikeman"), 1}});
    plainBattle();
    auto * subject = realStack(BattleSide::ATTACKER);
    ASSERT_NE(subject, nullptr);
    position(subject, BattleHex(4,5));
    for(int y = 0; y < GameConstants::BFIELD_HEIGHT; ++y)
        addForceField(BattleHex(6,y));
    auto * blocker = addStack(BattleSide::DEFENDER, creature("core:pikeman"), BattleHex(10,5), 1000);
    auto * ground = addStack(BattleSide::ATTACKER, creature("armoredDrakeHound"), BattleHex(4,8), 20);
    naturalStart();
    ASSERT_TRUE(advance(subject));
    const BattleHex destination(9,5);
    EXPECT_TRUE(battle()->battleGetAvailableHexes(subject, true).contains(destination));
    EXPECT_FALSE(battle()->battleGetAvailableHexes(ground, true).contains(BattleHex(9,8)));
    snapshot("before", subject);
    ASSERT_TRUE(send(BattleAction::makeMove(subject, destination)));
    EXPECT_EQ(subject->getPosition(), destination);
    EXPECT_TRUE(subject->moved());
    EXPECT_FALSE(send(BattleAction::makeMove(subject, BattleHex(8,5))));
    snapshot("after", subject);
    ASSERT_TRUE(advance(subject));
    EXPECT_FALSE(send(BattleAction::makeMove(subject, blocker->getPosition())));
    ASSERT_TRUE(advance(subject));
    EXPECT_FALSE(send(BattleAction::makeMove(subject, BattleHex(0,5))));
    ASSERT_TRUE(advance(ground));
    EXPECT_FALSE(battle()->battleGetAllObstaclesOnPos(BattleHex(6,8)).empty());
    EXPECT_FALSE(send(BattleAction::makeMove(ground, BattleHex(9,8))));
    EXPECT_EQ(ground->getPosition(), BattleHex(4,8));
    snapshot("ground_barrier_rejection", ground);
    // Each rejected action may advance this engine's scheduler. Landing probes
    // therefore reacquire the subject naturally and never assert a free retry.
}

TEST_P(NoxusMobility, IntactFortWallCrossingAndOccupiedLanding)
{
    setup("riven", 1, true, {{creature(GetParam()), 20}, {creature("core:pikeman"), 1}});
    plainBattle(true);
    auto * subject = realStack(BattleSide::ATTACKER);
    ASSERT_NE(subject, nullptr);
    position(subject, BattleHex(7,5));
    auto * target = addStack(BattleSide::DEFENDER, creature("core:pikeman"), BattleHex(14,5), 1000);
    auto * ground = addStack(BattleSide::ATTACKER, creature("armoredDrakeHound"), BattleHex(7,8), 20);
    const BattleHex landing(13,5);
    ASSERT_NE(battle()->getDefendedTown(), nullptr);
    measured("gate_state", static_cast<int>(battle()->getGateState()));
    naturalStart();
    ASSERT_TRUE(advance(subject));
    EXPECT_EQ(battle()->getGateState(), EGateState::CLOSED);
    snapshot("before", subject);
    ASSERT_TRUE(send(BattleAction::makeMove(subject, landing)));
    EXPECT_TRUE(battle()->battleIsInsideWalls(subject->getPosition()));
    EXPECT_EQ(subject->getPosition(), landing);
    EXPECT_TRUE(subject->moved());
    snapshot("after", subject);
    ASSERT_TRUE(advance(subject));
    EXPECT_FALSE(send(BattleAction::makeMove(subject, target->getPosition())));
    ASSERT_TRUE(advance(ground));
    EXPECT_LE(BattleHex::getDistance(ground->getPosition(), BattleHex(13,8)), ground->getMovementRange());
    EXPECT_FALSE(battle()->battleGetAvailableHexes(ground, true).contains(BattleHex(13,8)));
    EXPECT_FALSE(send(BattleAction::makeMove(ground, BattleHex(13,8))));
    EXPECT_EQ(ground->getPosition(), BattleHex(7,8));
    snapshot("ground_wall_rejection", ground);
}

TEST_P(NoxusMobility, OutOfRangeAndTwoHexRearObstacleRejections)
{
    setup("riven", 1, true, {{creature(GetParam()), 20}, {creature("core:pikeman"), 1}});
    plainBattle();
    auto * subject = realStack(BattleSide::ATTACKER);
    position(subject, BattleHex(2,1));
    naturalStart();
    ASSERT_TRUE(advance(subject));
    snapshot("before_out_of_range", subject);
    EXPECT_FALSE(battle()->battleGetAvailableHexes(subject, true).contains(BattleHex(15,9)));
    EXPECT_FALSE(send(BattleAction::makeMove(subject, BattleHex(15,9))));
    EXPECT_EQ(subject->getPosition(), BattleHex(2,1));
    setup("riven", 1, true, {{creature(GetParam()), 20}, {creature("core:pikeman"), 1}});
    plainBattle();
    subject = realStack(BattleSide::ATTACKER);
    position(subject, BattleHex(4,5));
    addForceField(BattleHex(6,5));
    if(subject->doubleWide())
        addForceField(BattleHex(8,5));
    naturalStart();
    ASSERT_TRUE(advance(subject));
    const BattleHex landing(subject->doubleWide() ? 7 : 6, 5);
    note("landing_control", "Both possible two-hex head/tail orientations around the clicked cell are blocked; native single-rear-block auto-shift is not falsely called illegal");
    EXPECT_FALSE(battle()->battleGetAvailableHexes(subject, true).contains(landing));
    EXPECT_FALSE(send(BattleAction::makeMove(subject, landing)));
    EXPECT_EQ(subject->getPosition(), BattleHex(4,5));
    snapshot("after_rear_or_front_obstacle_rejection", subject);
}

INSTANTIATE_TEST_SUITE_P(Subjects, NoxusMobility, ::testing::Values(
    "roseSpellblade", "roseInfiltrator", "ruinBringer", "greaterRuinBringer"),
    [](const auto & info) { return info.param; });

class NoxusRanged : public NoxusControlled, public ::testing::WithParamInterface<std::string> {};

TEST_P(NoxusRanged, FiniteAmmoActualShotsAndExhaustion)
{
    setup();
    plainBattle();
    auto * subject = addStack(BattleSide::ATTACKER, creature(GetParam()), BattleHex(4,5), 10);
    auto * target = addStack(BattleSide::DEFENDER, creature("core:pikeman"), BattleHex(9,5), 10000);
    naturalStart();
    int shots = GetParam() == "crimsonDisciple" ? 8 : GetParam() == "crimsonAdept" ? 10 : 12;
    EXPECT_EQ(subject->shots.available(), shots);
    EXPECT_TRUE(subject->shots.isLimited());
    snapshot("before", subject);
    for(int index = 0; index < shots; ++index)
    {
        SCOPED_TRACE(index);
        ASSERT_TRUE(advance(subject));
        int before = subject->shots.available();
        EXPECT_GT(hit(subject, target, true), 0);
        EXPECT_EQ(subject->shots.available(), before - 1);
    }
    ASSERT_TRUE(advance(subject));
    EXPECT_FALSE(battle()->battleCanShoot(subject, target->getPosition()));
    EXPECT_FALSE(send(BattleAction::makeShotAttack(subject, target)));
    EXPECT_EQ(subject->casts.available(), GetParam() == "crimsonAdept" ? 1 : 0);
    snapshot("after", subject);
}

TEST_P(NoxusRanged, AmmoCartPreventsDepletion)
{
    setup();
    giveArtifact(attackerSideHero, ArtifactID::AMMO_CART, ArtifactPosition::MACH2);
    plainBattle();
    auto * subject = addStack(BattleSide::ATTACKER, creature(GetParam()), BattleHex(4,5), 10);
    auto * target = addStack(BattleSide::DEFENDER, creature("core:pikeman"), BattleHex(9,5), 10000);
    naturalStart();
    EXPECT_FALSE(subject->shots.isLimited());
    int before = subject->shots.available();
    for(int index = 0; index < 14; ++index)
        EXPECT_GT(hit(subject, target, true), 0);
    EXPECT_EQ(subject->shots.available(), before);
    snapshot("after_cart", subject);
}

TEST_P(NoxusRanged, NativeDistanceWallBlockingAndMeleeConsumers)
{
    for(bool siege : {false, true})
    {
        SCOPED_TRACE(siege);
        setup();
        plainBattle(siege);
        auto * subject = addStack(BattleSide::ATTACKER, creature(GetParam()), BattleHex(2,5), 10);
        auto * target = addStack(BattleSide::DEFENDER, creature("core:pikeman"), BattleHex(siege ? 14 : 15,5), 10000);
        EXPECT_TRUE(battle()->battleHasDistancePenalty(subject, subject->getPosition(), target->getPosition()));
        if(siege)
            EXPECT_TRUE(battle()->battleHasWallPenalty(subject, subject->getPosition(), target->getPosition()));
        naturalStart();
        auto far = hit(subject, target, true);
        measured(siege ? "wall_ranged_damage" : "far_ranged_damage", far);
    }
    setup();
    plainBattle();
    auto * subject = addStack(BattleSide::ATTACKER, creature(GetParam()), BattleHex(7,5), 100);
    auto * target = addStack(BattleSide::DEFENDER, creature("core:pikeman"), BattleHex(8,5), 1000);
    EXPECT_TRUE(battle()->battleIsUnitBlocked(subject));
    EXPECT_FALSE(battle()->battleCanShoot(subject, target->getPosition()));
    bool fullMelee = GetParam() == "veteranAxeReckoner";
    EXPECT_EQ(subject->hasBonusOfType(BonusType::NO_MELEE_PENALTY), fullMelee);
    naturalStart();
    ASSERT_TRUE(advance(subject));
    EXPECT_FALSE(send(BattleAction::makeShotAttack(subject, target)));
    measured("melee_actual_damage", hit(subject, target, false));
}

TEST_P(NoxusRanged, IndependentMatchedNumericalPenaltyConsumers)
{
    auto measure = [&](bool siege, int fromX, int toX, bool ranged)
    {
        setup();
        plainBattle(siege);
        auto * subject = addStack(BattleSide::ATTACKER, creature(GetParam()), BattleHex(fromX,5), 100);
        // A slower, durable resistant target never defends before these shooters.
        auto * target = addStack(BattleSide::DEFENDER, creature("core:dwarf"), BattleHex(toX,5), 10000);
        forceMaximumDamage(subject);
        naturalStart();
        if(!advance(subject))
        {
            ADD_FAILURE() << "Penalty subject did not become naturally active";
            return std::tuple<int64_t,int,int>{-1,0,0};
        }
        if(ranged)
        {
            EXPECT_EQ(battle()->battleHasDistancePenalty(subject, subject->getPosition(), target->getPosition()), toX - fromX > 10);
            EXPECT_EQ(battle()->battleHasWallPenalty(subject, subject->getPosition(), target->getPosition()), siege);
        }
        int attack = subject->getAttack(ranged);
        int defense = target->getDefense(ranged);
        auto before = target->getAvailableHealth();
        EXPECT_TRUE(send(ranged ? BattleAction::makeShotAttack(subject, target) :
            BattleAction::makeMeleeAttack(subject, target, subject->getPosition())));
        return std::tuple<int64_t,int,int>{before - target->getAvailableHealth(), attack, defense};
    };
    auto [near, nearAttack, nearDefense] = measure(false, 4, 9, true);
    auto [far, farAttack, farDefense] = measure(false, 4, 15, true);
    auto [open, openAttack, openDefense] = measure(false, 8, 13, true);
    auto [wall, wallAttack, wallDefense] = measure(true, 8, 13, true);
    auto [melee, meleeAttack, meleeDefense] = measure(false, 7, 8, false);
    EXPECT_GT(near, 0);
    EXPECT_LT(far, near);
    EXPECT_LT(wall, open);
    EXPECT_LE(std::abs(near - 2 * far), 1);
    EXPECT_LE(std::abs(open - 2 * wall), 1);
    EXPECT_EQ(nearAttack, farAttack);
    EXPECT_EQ(openAttack, wallAttack);
    EXPECT_EQ(nearAttack, meleeAttack);
    EXPECT_EQ(nearDefense, farDefense);
    EXPECT_EQ(openDefense, wallDefense);
    EXPECT_EQ(nearDefense, meleeDefense);
    if(GetParam() == "veteranAxeReckoner")
        EXPECT_EQ(melee, near);
    else
        EXPECT_LE(std::abs(near - 2 * melee), 1);
    measured("matched_near_actual_damage", near);
    measured("matched_far_actual_damage", far);
    measured("matched_no_wall_actual_damage", open);
    measured("matched_intact_wall_actual_damage", wall);
    measured("matched_melee_actual_damage", melee);
    note("numeric_oracle", "Independent 1/2 penalty ratios with integer rounding; actual HP deltas, no calculateDmgRange expected value");
}

INSTANTIATE_TEST_SUITE_P(Subjects, NoxusRanged, ::testing::Values(
    "axeReckoner", "veteranAxeReckoner", "crimsonDisciple", "crimsonAdept"),
    [](const auto & info) { return info.param; });

TEST_F(NoxusControlled, BasicCurseChargeTimerExpiryAndTurnCost)
{
    setup();
    plainBattle();
    auto * caster = addStack(BattleSide::ATTACKER, creature("crimsonAdept"), BattleHex(5,5), 10);
    auto * split = addStack(BattleSide::ATTACKER, creature("crimsonAdept"), BattleHex(5,7), 10);
    auto * target = addStack(BattleSide::DEFENDER, creature("legionVeteran"), BattleHex(12,5), 1000);
    auto * immune = addStack(BattleSide::DEFENDER, creature("core:blackDragon"), BattleHex(14,8), 10);
    naturalStart();
    ASSERT_TRUE(advance(caster));
    battle::Target aim;
    aim.emplace_back(target);
    snapshot("before", caster);
    ASSERT_TRUE(send(BattleAction::makeCreatureSpellcast(caster, aim, SpellID::CURSE)));
    EXPECT_EQ(caster->casts.available(), 0);
    EXPECT_EQ(split->casts.available(), 1);
    EXPECT_TRUE(caster->moved());
    EXPECT_FALSE(send(BattleAction::makeCreatureSpellcast(caster, aim, SpellID::CURSE)));
    auto selector = Selector::source(BonusSource::SPELL_EFFECT, BonusSourceID(SpellID(SpellID::CURSE)));
    auto effects = target->getBonuses(selector);
    ASSERT_FALSE(effects->empty());
    EXPECT_EQ(effects->front()->turnsRemain, 3);
    measured("curse_initial_turns", effects->front()->turnsRemain);
    auto * victim = addStack(BattleSide::ATTACKER, creature("ruinBringer"), BattleHex(11,5), 20);
    ASSERT_TRUE(advance(target));
    auto cursed = battle()->calculateDmgRange(BattleAttackInfo(target, victim, 0, false));
    EXPECT_EQ(cursed.damage.min, cursed.damage.max);
    auto curseDamage = hit(target, victim, false);
    EXPECT_EQ(curseDamage, cursed.damage.min);
    measured("curse_actual_minimum_damage", curseDamage);
    for(int left : {2,1,0})
    {
        nextRound();
        effects = target->getBonuses(selector);
        if(left)
        {
            ASSERT_FALSE(effects->empty());
            EXPECT_EQ(effects->front()->turnsRemain, left);
        }
        else
            EXPECT_TRUE(effects->empty());
    }
    EXPECT_EQ(caster->casts.available(), 0);
    ASSERT_TRUE(advance(caster));
    EXPECT_FALSE(send(BattleAction::makeCreatureSpellcast(caster, aim, SpellID::CURSE)));
    ASSERT_TRUE(advance(split));
    aim.clear();
    aim.emplace_back(immune);
    EXPECT_FALSE(send(BattleAction::makeCreatureSpellcast(split, aim, SpellID::CURSE)));
    EXPECT_EQ(split->casts.available(), 1);
    snapshot("after", caster);
}

class NoxusCleave : public NoxusControlled, public ::testing::WithParamInterface<std::tuple<std::string, bool>> {};

TEST_P(NoxusCleave, ActualRearHexFriendlyFireAndNormalRetaliation)
{
    auto [id, friendly] = GetParam();
    setup();
    plainBattle();
    auto * subject = addStack(BattleSide::ATTACKER, creature(id), BattleHex(7,5), 10);
    auto * target = addStack(BattleSide::DEFENDER, creature("core:pikeman"), BattleHex(8,5), 200);
    auto * rear = addStack(friendly ? BattleSide::ATTACKER : BattleSide::DEFENDER,
        creature("core:pikeman"), BattleHex(9,5), 1000);
    auto * bystander = addStack(BattleSide::DEFENDER, creature("core:pikeman"), BattleHex(8,7), 1000);
    bool cleave = id == "veteranMinotaur";
    EXPECT_EQ(subject->doubleWide(), true);
    auto targets = battle()->getAttackedBattleUnits(subject, target, target->getPosition(), false);
    EXPECT_EQ(includes(targets, rear), cleave);
    naturalStart();
    auto ownHP = subject->getAvailableHealth();
    auto rearHP = rear->getAvailableHealth();
    auto otherHP = bystander->getAvailableHealth();
    EXPECT_GT(hit(subject, target, false), 0);
    EXPECT_LT(subject->getAvailableHealth(), ownHP);
    EXPECT_EQ(rear->getAvailableHealth() < rearHP, cleave);
    EXPECT_EQ(bystander->getAvailableHealth(), otherHP);
    measured("retaliation_damage", ownHP - subject->getAvailableHealth());
    measured("rear_damage", rearHP - rear->getAvailableHealth());
    measured("bystander_damage", otherHP - bystander->getAvailableHealth());
}

INSTANTIATE_TEST_SUITE_P(Subjects, NoxusCleave, ::testing::Combine(
    ::testing::Values(std::string("minotaurReckoner"), std::string("veteranMinotaur")), ::testing::Bool()),
    [](const auto & info) { return std::get<0>(info.param) + (std::get<1>(info.param) ? "_friendly" : "_enemy"); });

TEST_F(NoxusControlled, CleaveTwoHexTargetsBothSidesNativeAffectedSetAndDamage)
{
    for(auto id : {"minotaurReckoner", "veteranMinotaur"})
        for(auto side : {BattleSide::ATTACKER, BattleSide::DEFENDER})
        for(bool oblique : {false,true})
        {
            setup();
            plainBattle();
            bool attacker = side == BattleSide::ATTACKER;
            const BattleHex origin = oblique ? BattleHex(attacker ? 7 : 8,4) : BattleHex(attacker ? 7 : 10,5);
            const BattleHex primary = oblique ? BattleHex(8,5) : BattleHex(attacker ? 8 : 9,5);
            const BattleHex secondary = oblique ? BattleHex(attacker ? 8 : 7,6) : BattleHex(attacker ? 10 : 7,5);
            auto * subject = addStack(side, creature(id), origin, 10);
            auto * main = addStack(battle()->otherSide(side), creature("core:cavalier"), primary, 200);
            ASSERT_FALSE(main->getHexes().contains(secondary));
            auto * rear = addStack(side, creature("core:pikeman"), secondary, 1000);
            auto affected = battle()->getAttackedBattleUnits(subject, main, main->getPosition(), false);
            // Collinear contact spends breath's second hex inside the wide primary.
            bool rearExpected = oblique && std::string(id) == "veteranMinotaur";
            EXPECT_EQ(includes(affected, rear), rearExpected);
            auto rearHP = rear->getAvailableHealth();
            naturalStart();
            EXPECT_GT(hit(subject, main, false), 0);
            EXPECT_EQ(rear->getAvailableHealth() < rearHP, rearExpected);
            auto prefix = std::string(id) + (attacker ? "_attacker" : "_defender") + (oblique ? "_oblique" : "_collinear");
            measured(prefix + "_main_front", main->getPosition().toInt());
            measured(prefix + "_main_rear", main->occupiedHex().toInt());
            measured(prefix + "_breath_second_hex", secondary.toInt());
            measured(prefix + "_secondary_target_expected", rearExpected);
            measured(prefix + "_secondary_actual_damage", rearHP - rear->getAvailableHealth());
        }
}

TEST_F(NoxusControlled, NonLivingBothMoraleSignsAndDamagingSpellConsumer)
{
    for(auto id : {"ruinBringer", "greaterRuinBringer"})
    {
        setup();
        plainBattle();
        auto * subject = addStack(BattleSide::ATTACKER, creature(id), BattleHex(7,5), 10);
        auto * living = addStack(BattleSide::ATTACKER, creature("legionRecruit"), BattleHex(7,7), 100);
        EXPECT_FALSE(subject->isLiving());
        EXPECT_FALSE(subject->hasBonusOfType(BonusType::UNDEAD));
        for(int sign : {-1,1})
        {
            auto bonus = std::make_shared<Bonus>(BonusDuration::PERMANENT, BonusType::MORALE,
                BonusSource::OTHER, sign * 20, BonusSourceID());
            subject->addNewBonus(bonus);
            living->addNewBonus(bonus);
            EXPECT_EQ(subject->moraleVal(), 0);
            EXPECT_EQ(living->moraleVal(), sign * 3);
            measured(std::string(id) + (sign > 0 ? "_positive_morale" : "_negative_morale"), subject->moraleVal());
            subject->removeBonus(bonus);
            living->removeBonus(bonus);
        }
        teachSpell(defenderSideHero, SpellID::MAGIC_ARROW);
        naturalStart();
        auto hp = subject->getAvailableHealth();
        ASSERT_TRUE(heroCast(defenderSideHero, SpellID::MAGIC_ARROW, subject));
        EXPECT_LT(subject->getAvailableHealth(), hp);
        measured(std::string(id) + "_spell_damage", hp - subject->getAvailableHealth());
        teachSpell(attackerSideHero, SpellID::RESURRECTION);
        teachSpell(attackerSideHero, SpellID::ANIMATE_DEAD);
        EXPECT_FALSE(heroCast(attackerSideHero, SpellID::RESURRECTION, subject));
        EXPECT_FALSE(heroCast(attackerSideHero, SpellID::ANIMATE_DEAD, subject));
        nextRound();
        ASSERT_TRUE(heroCast(defenderSideHero, SpellID::MAGIC_ARROW, living));
        auto livingHP = living->getAvailableHealth();
        ASSERT_TRUE(heroCast(attackerSideHero, SpellID::RESURRECTION, living));
        EXPECT_GT(living->getAvailableHealth(), livingHP);
    }
}

TEST_F(NoxusControlled, DreadOppositionStackingSplitCapsAndObservedDeathMembership)
{
    setup("riven", 1, true, {{creature("greaterRuinBringer"), 1}, {creature("legionRecruit"), 100},
        {creature("greaterRuinBringer"), 1}});
    plainBattle();
    auto * source = realStack(BattleSide::ATTACKER);
    auto * own = realStack(BattleSide::ATTACKER, 1);
    auto * enemy = realStack(BattleSide::DEFENDER);
    ASSERT_NE(source, nullptr);
    int enemyWith = enemy->moraleVal();
    int ownWith = own->moraleVal();
    EXPECT_EQ(enemyWith, 0);
    EXPECT_EQ(ownWith, 1);
    for(int sign : {-1,1})
    {
        auto cap = std::make_shared<Bonus>(BonusDuration::PERMANENT, BonusType::MORALE,
            BonusSource::OTHER, sign * 20, BonusSourceID());
        enemy->addNewBonus(cap);
        EXPECT_EQ(enemy->moraleVal(), sign * 3);
        measured(sign > 0 ? "enemy_positive_morale_cap" : "enemy_negative_morale_cap", enemy->moraleVal());
        enemy->removeBonus(cap);
    }
    auto * second = realStack(BattleSide::ATTACKER, 2);
    ASSERT_NE(second, nullptr);
    EXPECT_EQ(enemy->moraleVal(), enemyWith);
    EXPECT_EQ(own->moraleVal(), ownWith);
    battle()->removeUnit(second->unitId());
    EXPECT_EQ(source->moraleVal(), 0);
    teachSpell(defenderSideHero, SpellID::MAGIC_ARROW);
    defenderSideHero->setPrimarySkill(PrimarySkill::SPELL_POWER, 100, ChangeValueMode::ABSOLUTE);
    naturalStart();
    ASSERT_TRUE(heroCast(defenderSideHero, SpellID::MAGIC_ARROW, source));
    ASSERT_FALSE(source->alive());
    measured("enemy_live_source", enemyWith);
    measured("enemy_dead_attached_source", enemy->moraleVal());
    note("lifecycle_scope", "Measured native death and explicit detach; no advertised alive-only aura rule presumed");
    battle()->removeUnit(source->unitId());
    measured("enemy_detached_source", enemy->moraleVal());
    EXPECT_GE(enemy->moraleVal(), enemyWith);
}

TEST_F(NoxusControlled, GrailNativeGrowthInfoAddsOnlyOneFiftyPercentAndIncome5000)
{
    noxusTown = true;
    setup();
    auto * town = findFirst<CGTownInstance>();
    ASSERT_NE(town, nullptr);
    ASSERT_EQ(town->getFactionID(), FactionID(FactionID::decode("runeterra-noxus:noxus")));
    std::vector<int> before;
    for(int tier = 0; tier < 7; ++tier)
        before.push_back(town->getGrowthInfo(tier).totalGrowth());
    auto income = town->dailyIncome()[EGameResID::GOLD];
    NewStructures grail;
    grail.tid = town->id;
    grail.bid.insert(BuildingID::GRAIL);
    gameHandler->sendAndApply(grail);
    for(int tier = 0; tier < 7; ++tier)
    {
        int actual = town->getGrowthInfo(tier).totalGrowth();
        EXPECT_GT(before[tier], 0);
        EXPECT_EQ(actual, before[tier] + before[tier] / 2);
        measured("tier_" + std::to_string(tier+1) + "_base_growth", before[tier]);
        measured("tier_" + std::to_string(tier+1) + "_grail_growth", actual);
    }
    EXPECT_EQ(town->dailyIncome()[EGameResID::GOLD] - income, 5000);
}

TEST_F(NoxusControlled, SwainActualAcademyVisitAndWeeklyTrainingDoNotDoubleSight)
{
    noxusTown = true;
    ownTown = true;
    for(int level : {1,10,20})
        for(bool removed : {false,true})
        {
            setup("swain", level, removed);
            auto * town = findFirst<CGTownInstance>();
            ASSERT_NE(town, nullptr);
            NewStructures academy;
            academy.tid = town->id;
            academy.bid.insert(BuildingID::SPECIAL_1);
            gameHandler->sendAndApply(academy);
            SetHeroesInTown visit;
            visit.tid = town->id;
            visit.visiting = attackerSideHero->id;
            visit.garrison = ObjectInstanceID::NONE;
            gameHandler->sendAndApply(visit);
            int before = attackerSideHero->getSightRadius();
            EXPECT_TRUE(gameHandler->visitTownBuilding(town->id, BuildingID::SPECIAL_1));
            int after = attackerSideHero->getSightRadius();
            EXPECT_EQ(after, removed ? before + 1 : before);
            EXPECT_EQ(after, 6);
            for(int day = 0; day < 7; ++day)
                gameHandler->newTurnProcessor->onNewTurn();
            EXPECT_TRUE(gameHandler->visitTownBuilding(town->id, BuildingID::SPECIAL_1));
            EXPECT_EQ(attackerSideHero->getSightRadius(), after);
            auto prefix = std::string(removed ? "control" : "specialist") + "_L" + std::to_string(level);
            measured(prefix + "_before", before);
            measured(prefix + "_after_training", after);
            measured(prefix + "_after_weekly_revisit", attackerSideHero->getSightRadius());
        }
}

struct HeroCase { std::string id; int level; };
std::vector<HeroCase> heroCases()
{
    std::vector<HeroCase> result;
    for(auto id : {"darius", "draven", "swain", "leblanc", "vladimir", "katarina", "talon", "cassiopeia",
         "samira", "kled", "riven", "rell", "briar", "ambessa", "annie", "sion", "mordekaiser", "alistar"})
        for(int level : {1,10,20})
            result.push_back({id, level});
    return result;
}

class NoxusSpecialty : public NoxusControlled, public ::testing::WithParamInterface<HeroCase>
{
public:
    struct Result
    {
        int attack = 0, rangedAttack = 0, defense = 0, speed = 0, value = 0, mana = 0, tier = 0, revealed = 0, extraStep = -1;
        int64_t damage = 0, rangedDamage = 0, spellDamage = 0, otherSpellDamage = 0;
    };

    Result observe(const HeroCase & c, bool removed, int mastery = 3, const std::string & troop = "legionRecruit")
    {
        setup(c.id, c.level, removed, {{creature(troop), 100}, {creature("core:pikeman"), 1}});
        Result r;
        bool offence = c.id == "darius" || c.id == "katarina" || c.id == "briar";
        bool archery = c.id == "draven" || c.id == "samira";
        if(offence || archery || c.id == "mordekaiser")
            attackerSideHero->setSecSkillLevel(skillByName(offence ? "core:offence" : archery ? "core:archery" : "core:necromancy"), mastery, ChangeValueMode::ABSOLUTE);
        if(c.id == "vladimir")
        {
            attackerSideHero->mana = 0;
            gameHandler->newTurnProcessor->onNewTurn();
            r.mana = attackerSideHero->mana;
            attackerSideHero->mana = attackerSideHero->manaLimit();
            gameHandler->newTurnProcessor->onNewTurn();
            EXPECT_EQ(attackerSideHero->mana, attackerSideHero->manaLimit());
            measured("daily_mana_cap", attackerSideHero->mana);
            note("consumer", "actual NewTurnProcessor::onNewTurn mana packet");
            return r;
        }
        if(c.id == "swain")
        {
            r.value = attackerSideHero->getSightRadius();
            setMapVisibility(PlayerColor(0), false);
            gameHandler->changeSecSkill(attackerSideHero, skillByName("core:scouting"), 0, ChangeValueMode::ABSOLUTE);
            const auto * team = gameState()->getPlayerTeam(PlayerColor(0));
            for(int x = 0; x < map()->width; ++x)
                for(int y = 0; y < map()->height; ++y)
                    r.revealed += team->fogOfWarMap[int3(x,y,0)] ? 1 : 0;
            note("consumer", "native changeSecSkill fog-refresh consumer; actual revealed tiles measured; separate native Academy visit case");
            return r;
        }
        if(c.id == "mordekaiser")
        {
            BattleResult result;
            result.winner = BattleSide::ATTACKER;
            result.casualties[BattleSide::DEFENDER][creature("core:pikeman")] = 300;
            auto raised = attackerSideHero->calculateNecromancy(result);
            r.value = raised.getCount();
            r.tier = raised.getId().getNum();
            // A real BattleActivity is required for native result/casualty settlement.
            setup(c.id, c.level, removed, {{creature("legionRecruit"), 5000}, {creature("core:pikeman"), 1}}, true);
            attackerSideHero->setSecSkillLevel(skillByName("core:necromancy"), mastery, ChangeValueMode::ABSOLUTE);
            attackerSideHero->addNewBonus(std::make_shared<Bonus>(BonusDuration::PERMANENT,
                BonusType::HERO_EXPERIENCE_GAIN_PERCENT, BonusSource::OTHER,
                -attackerSideHero->valOfBonuses(BonusType::HERO_EXPERIENCE_GAIN_PERCENT), BonusSourceID()));
            gameHandler->battles->startBattle(attackerSideHero, defenderSideHero);
            auto * striker = realStack(BattleSide::ATTACKER);
            auto * victim = realStack(BattleSide::DEFENDER);
            EXPECT_NE(striker, nullptr);
            EXPECT_NE(victim, nullptr);
            position(striker, BattleHex(7,5));
            position(victim, BattleHex(8,5));
            EXPECT_TRUE(advance(striker));
            EXPECT_TRUE(send(BattleAction::makeMeleeAttack(striker, victim, striker->getPosition())));
            EXPECT_FALSE(server.battleResults.empty());
            EXPECT_EQ(gameState()->getBattle(BattleID(0)), nullptr);
            int settled = 0;
            for(const auto & [slot, stack] : attackerSideHero->Slots())
                if(stack->getCreatureID() == creature("core:skeleton"))
                    settled += attackerSideHero->getStackCount(slot);
            EXPECT_EQ(settled, r.value);
            r.value = settled;
            note("consumer", "actual legal lethal melee, native BattleActivity result and postbattle skeleton army settlement");
            return r;
        }
        plainBattle();
        auto * commanded = realStack(BattleSide::ATTACKER);
        if(!commanded)
        {
            ADD_FAILURE() << "Missing actual commanded army stack";
            return r;
        }
        r.attack = commanded->getAttack(false);
        r.rangedAttack = commanded->getAttack(true);
        r.defense = commanded->getDefense(false);
        r.speed = commanded->getMovementRange();
        if(offence || archery)
            r.value = commanded->valOfBonuses(BonusType::PERCENTAGE_DAMAGE_BOOST,
                BonusSubtypeID(archery ? BonusCustomSubtype::damageTypeRanged : BonusCustomSubtype::damageTypeMelee));
        bool incoming = c.id == "ambessa" || c.id == "alistar";
        bool weak = c.id == "leblanc" || c.id == "cassiopeia";
        auto * melee = addStack(BattleSide::ATTACKER, creature("legionRecruit"), BattleHex(7,5), incoming ? 10000 : 100);
        auto * target = addStack(BattleSide::DEFENDER, creature(weak ? "core:swordsman" : "core:pikeman"), BattleHex(8,5), incoming ? 100 : 10000);
        auto * shooter = addStack(BattleSide::ATTACKER, creature("axeReckoner"), BattleHex(3,8), 100);
        auto * distant = addStack(BattleSide::DEFENDER, creature("core:pikeman"), BattleHex(8,8), 10000);
        auto * incomingShooter = incoming ? addStack(BattleSide::DEFENDER, creature("core:archer"), BattleHex(12,9), 100) : nullptr;
        auto * incomingTarget = incoming ? addStack(BattleSide::ATTACKER, creature("legionRecruit"), BattleHex(6,9), 10000) : nullptr;
        bool fire = c.id == "annie";
        if(weak || fire)
        {
            auto spell = weak ? SpellID::WEAKNESS : SpellID::FIREBALL;
            teachSpell(attackerSideHero, spell);
            setMagicMastery(attackerSideHero, mastery);
            auto * friendly = addStack(BattleSide::ATTACKER, creature("core:pikeman"), BattleHex(9,5), 10000);
            naturalStart();
            int mana = attackerSideHero->mana;
            auto hp = target->getAvailableHealth();
            auto friendlyHP = friendly->getAvailableHealth();
            int attackBefore = target->getAttack(false);
            EXPECT_TRUE(heroCast(attackerSideHero, spell, target));
            r.mana = mana - attackerSideHero->mana;
            r.spellDamage = hp - target->getAvailableHealth();
            r.value = target->getAttack(false) - attackBefore;
            if(fire)
                EXPECT_LT(friendly->getAvailableHealth(), friendlyHP);
            battle::Target aim;
            aim.emplace_back(target);
            EXPECT_FALSE(send(BattleAction::makeHeroSpellcast(BattleSide::ATTACKER, aim, spell)));
            EXPECT_GT(r.mana, 0);
            nextRound();
            teachSpell(attackerSideHero, SpellID::MAGIC_ARROW);
            auto controlHP = distant->getAvailableHealth();
            EXPECT_TRUE(heroCast(attackerSideHero, SpellID::MAGIC_ARROW, distant));
            r.otherSpellDamage = controlHP - distant->getAvailableHealth();
            note("consumer", "server-validated paid hero spell action and affected native stack state");
            return r;
        }
        for(auto * damageSource : {melee, target, shooter})
            forceMaximumDamage(damageSource);
        if(incomingShooter)
            forceMaximumDamage(incomingShooter);
        note("damage_control", "Matched ALWAYS_MAXIMUM_DAMAGE environmental bonus on action sources; loaded mod definitions unchanged");
        if(c.id == "kled")
            position(commanded, BattleHex(2,2));
        naturalStart();
        if(c.id == "kled")
        {
            bool affected = troop == "legionRecruit" || troop == "legionVeteran";
            const BattleHex extraStep(2 + r.speed - (affected && !removed ? 1 : 0) + 1, 2);
            if(!advance(commanded))
            {
                ADD_FAILURE() << "Kled's commanded stack was not naturally activated";
                return r;
            }
            bool accepted = send(BattleAction::makeMove(commanded, extraStep));
            EXPECT_EQ(accepted, affected && !removed);
            r.extraStep = accepted;
        }
        if(c.id == "ambessa" || c.id == "alistar")
        {
            r.damage = hit(target, melee, false);
            r.rangedDamage = hit(incomingShooter, incomingTarget, true);
            note("consumer", "actual incoming melee and ranged server actions plus damaging-spell negative control");
        }
        else
        {
            r.damage = hit(melee, target, false);
            r.rangedDamage = hit(shooter, distant, true);
            note("consumer", "actual matched melee and ranged server actions");
        }
        auto * caster = incoming ? defenderSideHero : attackerSideHero;
        auto * magicTarget = incoming ? incomingTarget : distant;
        teachSpell(caster, SpellID::MAGIC_ARROW);
        auto magicHP = magicTarget->getAvailableHealth();
        EXPECT_TRUE(heroCast(caster, SpellID::MAGIC_ARROW, magicTarget));
        r.spellDamage = magicHP - magicTarget->getAvailableHealth();
        return r;
    }

};

TEST_P(NoxusSpecialty, MatchedSpecialtyRemovedControlAtAuthoredLevel)
{
    auto c = GetParam();
    note("hero", c.id);
    measured("level", c.level);
    auto with = observe(c, false);
    auto without = observe(c, true);
    measured("specialist_damage", with.damage);
    measured("control_damage", without.damage);
    measured("specialist_ranged_damage", with.rangedDamage);
    measured("control_ranged_damage", without.rangedDamage);
    measured("specialist_value", with.value);
    measured("control_value", without.value);
    measured("specialist_mana", with.mana);
    measured("control_mana", without.mana);
    measured("specialist_spell_damage", with.spellDamage);
    measured("control_spell_damage", without.spellDamage);
    measured("specialist_melee_attack", with.attack);
    measured("control_melee_attack", without.attack);
    measured("specialist_ranged_attack", with.rangedAttack);
    measured("control_ranged_attack", without.rangedAttack);
    measured("specialist_defense", with.defense);
    measured("control_defense", without.defense);
    measured("specialist_speed", with.speed);
    measured("control_speed", without.speed);
    measured("specialist_extra_step_accepted", with.extraStep);
    measured("control_extra_step_accepted", without.extraStep);
    measured("specialist_unrelated_spell_damage", with.otherSpellDamage);
    measured("control_unrelated_spell_damage", without.otherSpellDamage);
    measured("specialist_revealed_tiles", with.revealed);
    measured("control_revealed_tiles", without.revealed);
    if(c.id == "darius" || c.id == "katarina" || c.id == "briar" || c.id == "draven" || c.id == "samira")
    {
        int expected = without.value * (100 + 5 * c.level) / 100;
        EXPECT_EQ(with.value, expected);
        bool archery = c.id == "draven" || c.id == "samira";
        EXPECT_GT(archery ? with.rangedDamage : with.damage, archery ? without.rangedDamage : without.damage);
        EXPECT_EQ(archery ? with.damage : with.rangedDamage, archery ? without.damage : without.rangedDamage);
    }
    else if(c.id == "talon" || c.id == "sion")
    {
        EXPECT_EQ(with.attack, without.attack + 2);
        EXPECT_EQ(with.rangedAttack, without.rangedAttack);
        EXPECT_GT(with.damage, without.damage);
        EXPECT_EQ(with.rangedDamage, without.rangedDamage);
    }
    else if(c.id == "riven")
    {
        EXPECT_EQ(with.attack, without.attack + 1);
        EXPECT_EQ(with.rangedAttack, without.rangedAttack + 1);
        EXPECT_GT(with.damage, without.damage);
        EXPECT_GT(with.rangedDamage, without.rangedDamage);
    }
    else if(c.id == "ambessa")
    {
        EXPECT_EQ(with.defense, without.defense + 1);
        EXPECT_LT(with.damage, without.damage);
        EXPECT_LT(with.rangedDamage, without.rangedDamage);
    }
    else if(c.id == "rell")
    {
        EXPECT_GT(with.damage, without.damage);
        EXPECT_GT(with.rangedDamage, without.rangedDamage);
        EXPECT_EQ(with.attack, without.attack);
    }
    else if(c.id == "alistar")
    {
        EXPECT_LT(with.damage, without.damage);
        EXPECT_LT(with.rangedDamage, without.rangedDamage);
    }
    else if(c.id == "kled")
    {
        EXPECT_EQ(with.speed, without.speed + 1);
        EXPECT_EQ(with.attack, (without.attack * (100 + 5 * c.level) + 99) / 100);
        EXPECT_EQ(with.defense, (without.defense * (100 + 5 * c.level) + 99) / 100);
        for(auto troop : {"legionVeteran", "drakeHound"})
        {
            auto a = observe(c, false, 3, troop);
            auto b = observe(c, true, 3, troop);
            EXPECT_EQ(a.speed - b.speed, std::string(troop) == "legionVeteran" ? 1 : 0);
            measured(std::string(troop) + "_specialist_speed", a.speed);
            measured(std::string(troop) + "_control_speed", b.speed);
            measured(std::string(troop) + "_specialist_extra_step_accepted", a.extraStep);
            measured(std::string(troop) + "_control_extra_step_accepted", b.extraStep);
        }
    }
    else if(c.id == "swain")
    {
        EXPECT_EQ(with.value, without.value + 1);
        EXPECT_GT(with.revealed, without.revealed);
    }
    else if(c.id == "vladimir")
        EXPECT_EQ(with.mana, without.mana + 2);
    else if(c.id == "leblanc" || c.id == "cassiopeia")
    {
        EXPECT_EQ(with.value, without.value - 1);
        EXPECT_EQ(with.mana, without.mana);
    }
    else if(c.id == "annie")
    {
        EXPECT_EQ(with.spellDamage, without.spellDamage * (100 + 5 * c.level) / 100);
        EXPECT_EQ(with.mana, without.mana);
    }
    else if(c.id == "mordekaiser")
    {
        EXPECT_GT(with.value, without.value);
        EXPECT_EQ(with.tier, creature("core:skeleton").getNum());
    }
    else
        FAIL() << "Missing specialty contract for loaded hero " << c.id;
    if(c.id != "annie" && c.id != "leblanc" && c.id != "cassiopeia")
        EXPECT_EQ(with.spellDamage, without.spellDamage);
    EXPECT_EQ(with.otherSpellDamage, without.otherSpellDamage);
}

INSTANTIATE_TEST_SUITE_P(Heroes, NoxusSpecialty, ::testing::ValuesIn(heroCases()),
    [](const auto & info) { return info.param.id + "_L" + std::to_string(info.param.level); });
}
