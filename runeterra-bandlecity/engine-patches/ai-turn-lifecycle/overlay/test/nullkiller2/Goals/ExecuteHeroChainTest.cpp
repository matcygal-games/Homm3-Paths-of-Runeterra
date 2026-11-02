/*
 * ExecuteHeroChainTest.cpp, part of VCMI engine
 *
 * Authors: listed in file AUTHORS in main folder
 *
 * License: GNU General Public License v2.0 or later
 * Full text of license available in license.txt file, in main folder
 */
#include "StdInc.h"

#include "AI/Nullkiller2/AIGateway.h"
#include "AI/Nullkiller2/Goals/ExecuteHeroChain.h"
#include "AI/Nullkiller2/Pathfinding/Actions/BattleAction.h"

#include "mock/GameHandlerTestClient.h"
#include "mock/TinyH3MBuilder.h"
#include "nullkiller2/NullkillerTest.h"
#include "nullkiller2/ScriptedMovementClient.h"

#include "lib/gameState/CGameState.h"
#include "lib/mapObjects/CGHeroInstance.h"
#include "lib/mapObjects/MiscObjects.h"
#include "lib/networkPacks/PacksForServer.h"
#include "lib/serializer/CMemorySerializer.h"

namespace
{
const PlayerColor PLAYER(0);
const PlayerColor ENEMY(1);
const int3 HERO_ANCHOR_POS(6, 5, 0);
const int3 HERO_POS(5, 5, 0);
const int3 SCROLL_POS(6, 5, 0);
const int3 BEYOND_SCROLL_POS(7, 5, 0);

class MoveCountingClient : public GameHandlerTestClient
{
public:
	using GameHandlerTestClient::GameHandlerTestClient;

	int sendRequest(const CPackForServer & request, PlayerColor player, bool waitTillRealize) override
	{
		if(dynamic_cast<const MoveHero *>(&request))
			++movementRequests;

		return GameHandlerTestClient::sendRequest(request, player, waitTillRealize);
	}

	int movementRequests = 0;
};

class ExecuteHeroChainMovementTest : public NullkillerTest
{
protected:
	void startGame(bool withScroll = true)
	{
		TinyH3M::TinyH3MBuilder builder(EMapFormat::SOD);
		builder
			.size(36, false)
			.playerActive(PLAYER)
			.hero(HERO_ANCHOR_POS, HeroTypeID(0), PLAYER)
			.heroGarrison({{CreatureID(0), 1}});
		if(withScroll)
			builder.scroll(SCROLL_POS, SpellID(0));
		builder
			.playerActive(ENEMY)
			.hero({30, 30, 0}, HeroTypeID(1), ENEMY);

		startWithMap(std::move(builder));
	}
};

class RecordingAiLogger : public vstd::CLoggerBase
{
	vstd::CLoggerBase * previous = logAi;
public:
	RecordingAiLogger() { logAi = this; }
	~RecordingAiLogger() override { logAi = previous; }
	mutable std::vector<std::string> errors;
	void log(ELogLevel::ELogLevel level, const std::string & text) const override
	{
		if(level == ELogLevel::ERROR)
			errors.push_back(text);
	}
	void log(ELogLevel::ELogLevel level, const boost::format & text) const override { log(level, text.str()); }
	bool isDebugEnabled() const override { return true; }
	bool isTraceEnabled() const override { return true; }
	ELogLevel::ELogLevel getEffectiveLevel() const override { return ELogLevel::TRACE; }
};

class MeetingServer : public GameHandlerTestServer
{
public:
	using GameHandlerTestServer::GameHandlerTestServer;
	std::optional<QuestionID> exchangeQuestion;
	int meetings = 0;
	void applyPack(CPackForClient & pack) override
	{
		if(const auto * exchange = dynamic_cast<const ExchangeDialog *>(&pack))
		{
			exchangeQuestion = exchange->questionID;
			++meetings;
		}
		GameHandlerTestServer::applyPack(pack);
	}
};

class MeetingClient : public IClient
{
public:
	MeetingServer server;
private:
	CGameHandler handler;
	int requestID = 0;
public:
	int movementRequests = 0;
	MeetingClient(const std::shared_ptr<CGameState> & state)
		: server(state, PLAYER), handler(server, state)
	{
		state->actingPlayers.insert(PLAYER);
	}
	std::optional<BattleAction> makeSurrenderRetreatDecision(PlayerColor, const BattleID &, const BattleStateInfoForRetreat &) override
	{
		return std::nullopt;
	}
	int sendRequest(const CPackForServer & request, PlayerColor player, bool) override
	{
		request.player = player;
		request.requestID = ++requestID;
		if(dynamic_cast<const MoveHero *>(&request))
			++movementRequests;
		auto copy = CMemorySerializer::deepCopy(request);
		handler.handleReceivedPack(GameConnectionID::FIRST_CONNECTION, *copy);
		if(server.exchangeQuestion)
		{
			QuestionAnswer reply;
			reply.player = player;
			reply.requestID = ++requestID;
			reply.questionID = *server.exchangeQuestion;
			reply.reply = 0;
			server.exchangeQuestion.reset();
			handler.handleReceivedPack(GameConnectionID::FIRST_CONNECTION, reply);
		}
		return requestID;
	}
};
}

TEST_F(ExecuteHeroChainMovementTest, blockingVisitOnRouteStopsChainForReplanning)
{
	startGame();
	revealMap(PLAYER);

	auto * hero = findHeroByOwner(PLAYER);
	auto * scroll = findFirst<CGArtifact>();
	ASSERT_NE(hero, nullptr);
	ASSERT_NE(scroll, nullptr);
	ASSERT_EQ(hero->visitablePos(), HERO_POS);
	ASSERT_EQ(scroll->visitablePos(), SCROLL_POS);
	const auto scrollID = scroll->id;
	hero->setMovementPoints(2000);

	MoveCountingClient client(gameState(), PLAYER);
	auto gateway = makeGateway(PLAYER, &client);

	NK2AI::AIPath path;
	path.targetHero = hero;
	path.heroArmy = hero;
	path.chainMask = 1;
	path.nodes.push_back(pathNode(*hero, BEYOND_SCROLL_POS));
	path.nodes.push_back(pathNode(*hero, SCROLL_POS));
	path.nodes.push_back(pathNode(*hero, HERO_POS));

	std::shared_lock gameStateLock(CGameState::mutex);
	EXPECT_NO_THROW(NK2AI::Goals::ExecuteHeroChain(path).accept(gateway.get()));
	EXPECT_EQ(gameState()->getObjInstance(scrollID), nullptr) << "the hero must pick up the scroll";
	EXPECT_EQ(hero->visitablePos(), HERO_POS) << "picking up a scroll does not move the hero";
	EXPECT_EQ(client.movementRequests, 1) << "the chain must stop after the pickup instead of following the stale route";
}

TEST_F(ExecuteHeroChainMovementTest, repeatedIdleChainFailsForReplanning)
{
	startGame();

	auto * hero = findHeroByOwner(PLAYER);
	ASSERT_NE(hero, nullptr);
	hero->setMovementPoints(2000);

	MoveCountingClient client(gameState(), PLAYER);
	auto gateway = makeGateway(PLAYER, &client);

	NK2AI::AIPath path;
	path.targetHero = hero;
	path.heroArmy = hero;
	path.chainMask = 1;
	path.nodes.push_back(pathNode(*hero, HERO_POS));

	std::shared_lock gameStateLock(CGameState::mutex);
	EXPECT_NO_THROW(NK2AI::Goals::ExecuteHeroChain(path).accept(gateway.get()));
	EXPECT_THROW(NK2AI::Goals::ExecuteHeroChain(path).accept(gateway.get()), NK2AI::cannotFulfillGoalException)
		<< "an idle chain counted as success would be selected again on every pass";
	EXPECT_EQ(client.movementRequests, 0);
}

TEST_F(ExecuteHeroChainMovementTest, multiTurnNodeLocksHeroWithoutMovementPoints)
{
	startGame();
	revealMap(PLAYER);

	auto * hero = findHeroByOwner(PLAYER);
	ASSERT_NE(hero, nullptr);
	hero->setMovementPoints(10); // not enough for a single step

	MoveCountingClient client(gameState(), PLAYER);
	auto gateway = makeGateway(PLAYER, &client);

	auto node = pathNode(*hero, int3(20, 5, 0));
	node.turns = 1;

	NK2AI::AIPath path;
	path.targetHero = hero;
	path.heroArmy = hero;
	path.chainMask = 1;
	path.nodes.push_back(node);

	std::shared_lock gameStateLock(CGameState::mutex);
	EXPECT_NO_THROW(NK2AI::Goals::ExecuteHeroChain(path).accept(gateway.get()));
	EXPECT_TRUE(gateway->nullkiller->isHeroLocked(hero)) << "the hero must wait for the next turn instead of failing the route";
	EXPECT_EQ(client.movementRequests, 0);
}

TEST_F(ExecuteHeroChainMovementTest, battleActionExhaustionPausesBeforeLiveImmediatePathCheck)
{
	startGame(false);
	revealMap(PLAYER);
	auto * hero = findHeroByOwner(PLAYER);
	ASSERT_NE(hero, nullptr);
	hero->setMovementPoints(2000);
	ScriptedMovementClient client(gameState());
	auto gateway = makeGateway(PLAYER, &client);
	client.notify(*gateway);
	client.drainMovement(0);
	client.afterMovement = [&] { gateway->invalidatePaths(); };
	const int3 destination(15, 5, 0);
	auto node = pathNode(*hero, destination);
	node.specialAction = std::make_shared<NK2AI::AIPathfinding::BattleAction>(destination);
	NK2AI::AIPath path;
	path.targetHero = hero;
	path.heroArmy = hero;
	path.chainMask = 1;
	path.nodes.push_back(node);
	RecordingAiLogger logger;
	std::shared_lock gameStateLock(CGameState::mutex);
	EXPECT_NO_THROW(NK2AI::Goals::ExecuteHeroChain(path).accept(gateway.get()));
	EXPECT_EQ(hero->movementPointsRemaining(), 0);
	EXPECT_NE(hero->visitablePos(), destination);
	EXPECT_GT(gateway->nullkiller->getPathsInfo(hero)->getPathInfo(destination)->turns, 0);
	EXPECT_EQ(client.movementRequests, 1);
	EXPECT_TRUE(gateway->nullkiller->isHeroLocked(hero));
	EXPECT_TRUE(logger.errors.empty());
}

TEST_F(ExecuteHeroChainMovementTest, actualPlayerVictoryStopsRemainingCompositeActions)
{
	startGame(false);
	revealMap(PLAYER);
	auto * hero = findHeroByOwner(PLAYER);
	ASSERT_NE(hero, nullptr);
	hero->setMovementPoints(2000);
	ScriptedMovementClient client(gameState());
	auto gateway = makeGateway(PLAYER, &client);
	client.notify(*gateway);
	client.afterMovement = [&]
	{
		PlayerEndsGame ended;
		ended.player = PLAYER;
		ended.victoryLossCheckResult = EVictoryLossCheckResult::victory({}, {});
		gameState()->apply(ended);
	};
	auto node = pathNode(*hero, int3(15, 5, 0));
	node.specialAction = std::make_shared<NK2AI::CompositeAction>(std::vector<std::shared_ptr<const NK2AI::SpecialAction>>{
		std::make_shared<NK2AI::AIPathfinding::BattleAction>(int3(6, 5, 0)),
		std::make_shared<NK2AI::AIPathfinding::BattleAction>(int3(7, 5, 0))});
	NK2AI::AIPath path;
	path.targetHero = hero;
	path.heroArmy = hero;
	path.chainMask = 1;
	path.nodes.push_back(pathNode(*hero, int3(16, 5, 0)));
	path.nodes.push_back(node);
	RecordingAiLogger logger;
	std::shared_lock gameStateLock(CGameState::mutex);
	EXPECT_NO_THROW(NK2AI::Goals::ExecuteHeroChain(path).accept(gateway.get()));
	EXPECT_EQ(gateway->cc->getPlayerStatus(PLAYER), EPlayerStatus::WINNER);
	EXPECT_EQ(client.movementRequests, 1);
	EXPECT_EQ(hero->visitablePos(), int3(6, 5, 0));
	EXPECT_TRUE(logger.errors.empty());
}

TEST_F(ExecuteHeroChainMovementTest, activeFailedMovementStillReportsErrors)
{
	startGame(false);
	revealMap(PLAYER);
	auto * hero = findHeroByOwner(PLAYER);
	ASSERT_NE(hero, nullptr);
	hero->setMovementPoints(2000);
	ScriptedMovementClient client(gameState());
	auto gateway = makeGateway(PLAYER, &client);
	client.notify(*gateway);
	client.failMovement();
	NK2AI::AIPath path;
	path.targetHero = hero;
	path.heroArmy = hero;
	path.chainMask = 1;
	path.nodes.push_back(pathNode(*hero, int3(8, 5, 0)));
	RecordingAiLogger logger;
	std::shared_lock gameStateLock(CGameState::mutex);
	EXPECT_FALSE(NK2AI::NullkillerTestAccess::executeTask(*gateway->nullkiller, NK2AI::Goals::taskptr(NK2AI::Goals::ExecuteHeroChain(path))));
	EXPECT_EQ(gateway->cc->getPlayerStatus(PLAYER), EPlayerStatus::INGAME);
	EXPECT_EQ(client.movementRequests, 1);
	EXPECT_EQ(hero->visitablePos(), HERO_POS);
	EXPECT_GE(logger.errors.size(), 2);
	EXPECT_TRUE(std::any_of(logger.errors.begin(), logger.errors.end(), [](const auto & text)
	{
		return text.find("Failed to realize subgoal") != std::string::npos;
	}));
}

TEST_F(ExecuteHeroChainMovementTest, intentionalFriendlyMeetingCompletesOnceWithoutOccupyingTile)
{
	TinyH3M::TinyH3MBuilder builder(EMapFormat::SOD);
	builder.size(36, false).playerActive(PLAYER)
		.hero(HERO_ANCHOR_POS, HeroTypeID(0), PLAYER).heroGarrison({{CreatureID(0), 1}})
		.hero({7, 5, 0}, HeroTypeID(2), PLAYER).heroGarrison({{CreatureID(0), 1}})
		.playerActive(ENEMY).hero({30, 30, 0}, HeroTypeID(1), ENEMY);
	startWithMap(std::move(builder));
	revealMap(PLAYER);
	auto * hero = findHeroAt(HERO_ANCHOR_POS);
	auto * partner = findHeroAt(int3(7, 5, 0));
	ASSERT_NE(hero, nullptr);
	ASSERT_NE(partner, nullptr);
	hero->setMovementPoints(2000);
	MeetingClient client(gameState());
	auto gateway = makeGateway(PLAYER, &client);
	NK2AI::AIPath path;
	path.targetHero = hero;
	path.heroArmy = hero;
	path.chainMask = 1;
	path.nodes.push_back(pathNode(*hero, partner->visitablePos()));
	RecordingAiLogger logger;
	std::shared_lock gameStateLock(CGameState::mutex);
	EXPECT_TRUE(NK2AI::NullkillerTestAccess::executeTask(*gateway->nullkiller, NK2AI::Goals::taskptr(NK2AI::Goals::ExecuteHeroChain(path, partner))));
	EXPECT_EQ(client.movementRequests, 1);
	EXPECT_EQ(client.server.meetings, 1);
	EXPECT_EQ(client.server.resolvedQuestionIDs.size(), 1);
	EXPECT_EQ(hero->visitablePos(), HERO_POS);
	EXPECT_NE(hero->visitablePos(), partner->visitablePos());
	EXPECT_TRUE(logger.errors.empty());
}

// Native H3M prison -> native GiveHero/SetObjectProperty -> native friendly meeting.
// The object instance and visitable tile stay the same while type and owner change.
TEST_F(ExecuteHeroChainMovementTest, rescuedPrisonAndNewHeroExchangeAreDistinctInteractions)
{
	TinyH3M::TinyH3MBuilder builder(EMapFormat::SOD);
	builder.size(36, false).playerActive(PLAYER)
		.hero(HERO_ANCHOR_POS, HeroTypeID(0), PLAYER).heroGarrison({{CreatureID(0), 1}})
		.prison({7, 5, 0}, HeroTypeID(2))
		.playerActive(ENEMY).hero({30, 30, 0}, HeroTypeID(1), ENEMY);
	startWithMap(std::move(builder)); revealMap(PLAYER);
	auto * hero = findHeroAt(HERO_ANCHOR_POS);
	auto * partner = findHeroAt(int3(7, 5, 0));
	ASSERT_NE(hero, nullptr); ASSERT_NE(partner, nullptr);
	ASSERT_EQ(partner->ID, Obj::PRISON);
	const auto targetID = partner->id;
	const auto tile = partner->visitablePos();
	hero->setMovementPoints(2000);
	MeetingClient client(gameState()); auto gateway = makeGateway(PLAYER, &client);
	NK2AI::AIPath path;
	path.targetHero = hero; path.heroArmy = hero; path.chainMask = 1;
	path.nodes.push_back(pathNode(*hero, tile));
	RecordingAiLogger logger;
	std::shared_lock gameStateLock(CGameState::mutex);
	EXPECT_NO_THROW(NK2AI::Goals::ExecuteHeroChain(path, partner).accept(gateway.get()));
	ASSERT_EQ(partner->ID, Obj::HERO); ASSERT_EQ(partner->getOwner(), PLAYER);
	ASSERT_EQ(partner->id, targetID); ASSERT_EQ(partner->visitablePos(), tile);
	const auto positionAfterRescue = hero->visitablePos();
	ASSERT_NE(positionAfterRescue, tile);
	EXPECT_NO_THROW(NK2AI::Goals::ExecuteHeroChain(path, partner).accept(gateway.get()));
	EXPECT_EQ(hero->visitablePos(), positionAfterRescue);
	EXPECT_EQ(client.server.meetings, 1);
	EXPECT_EQ(client.server.resolvedQuestionIDs.size(), 1);
	EXPECT_TRUE(logger.errors.empty());
	// A third identical friendly interaction has no new semantic transition.
	EXPECT_THROW(NK2AI::Goals::ExecuteHeroChain(path, partner).accept(gateway.get()), NK2AI::cannotFulfillGoalException);
}
