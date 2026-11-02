/* Actual server visitor/handler authority regressions. GPL-2.0-or-later. */
#include "StdInc.h"
#include "mock/TinyMapGameTest.h"
#include "mock/GameHandlerTestServer.h"
#include "server/CGameHandler.h"
#include "server/ServerNetPackVisitors.h"
#include "lib/CPlayerState.h"
#include "lib/gameState/EVictoryLossCheckResult.h"
#include "lib/mapObjects/CGHeroInstance.h"
#include "lib/networkPacks/PacksForServer.h"

namespace
{
const PlayerColor RED(0), BLUE(1);
class RecordingServer : public GameHandlerTestServer
{
public:
	using GameHandlerTestServer::GameHandlerTestServer;
	std::vector<PackageApplied> acknowledgements;
	void sendPack(CPackForClient & pack, GameConnectionID connection) override
	{
		if(const auto * applied = dynamic_cast<const PackageApplied *>(&pack))
			acknowledgements.push_back(*applied);
		GameHandlerTestServer::sendPack(pack, connection);
	}
};
class RecordingAuthorityLogger final : public vstd::CLoggerBase
{
public:
	mutable std::vector<std::pair<ELogLevel::ELogLevel, std::string>> records;
	void log(ELogLevel::ELogLevel level, const std::string & text) const override { records.emplace_back(level, text); }
	void log(ELogLevel::ELogLevel level, const boost::format & text) const override { log(level, text.str()); }
	bool isDebugEnabled() const override { return true; }
	bool isTraceEnabled() const override { return true; }
	ELogLevel::ELogLevel getEffectiveLevel() const override { return ELogLevel::TRACE; }
	size_t errors() const { return std::count_if(records.begin(), records.end(), [](const auto & r) { return r.first == ELogLevel::ERROR; }); }
	bool cancellation() const { return std::any_of(records.begin(), records.end(), [](const auto & r) { return r.first == ELogLevel::INFO && r.second.find("Cancelled queued MoveHero request 1184") != std::string::npos; }); }
};
class TerminalMoveCancellation : public TinyMapGameTest
{
protected:
	CGHeroInstance * hero = nullptr;
	RecordingAuthorityLogger logger;
	vstd::CLoggerBase * previousLogger = nullptr;
	vstd::CLoggerBase * previousNetworkLogger = nullptr;
	std::unique_ptr<RecordingServer> server;
	std::unique_ptr<CGameHandler> handler;
	void start(EPlayerStatus status)
	{
		TinyH3M::TinyH3MBuilder builder(EMapFormat::SOD);
		builder.size(36, false).playerActive(RED).playerActive(BLUE)
			.hero({5, 5, 0}, HeroTypeID(0), RED).hero({15, 15, 0}, HeroTypeID(16), BLUE)
			.garrison({10, 10, 0}, RED, {{CreatureID(0), 1}}, true);
		startWithMap(std::move(builder));
		hero = findHeroByOwner(RED); ASSERT_NE(hero, nullptr);
		hero->setMovementPoints(2000);
		gameState()->actingPlayers.insert(RED);
		if(status == EPlayerStatus::WINNER || status == EPlayerStatus::LOSER)
		{
			PlayerEndsGame ended;
			ended.player = RED;
			ended.victoryLossCheckResult = status == EPlayerStatus::WINNER
				? EVictoryLossCheckResult::victory({}, {}) : EVictoryLossCheckResult::defeat({}, {});
			gameState()->apply(ended); // Actual authoritative terminal consumer removes acting player.
			ASSERT_EQ(gameState()->getPlayerState(RED)->status, status);
			ASSERT_EQ(gameState()->actingPlayers.count(RED), 0);
		}
		else
			gameState()->actingPlayers.erase(RED);
		server = std::make_unique<RecordingServer>(gameState(), RED);
		handler = std::make_unique<CGameHandler>(*server, gameState());
		previousLogger = logGlobal; previousNetworkLogger = logNetwork;
		logGlobal = &logger; logNetwork = &logger;
	}
	MoveHero request()
	{
		MoveHero pack({hero->pos + int3(1, 0, 0)}, EPathfindingLayer::LAND, hero->id, false);
		pack.player = RED; pack.requestID = 1184;
		return pack;
	}
	void TearDown() override
	{
		handler.reset(); server.reset();
		if(previousLogger) logGlobal = previousLogger;
		if(previousNetworkLogger) logNetwork = previousNetworkLogger;
		TinyMapGameTest::TearDown();
	}
};
}

TEST_F(TerminalMoveCancellation, winnerQueuedMoveIsCancelledWithFalseAcknowledgementAndNoMutation)
{
	start(EPlayerStatus::WINNER); auto pack = request();
	const auto position = hero->pos; const auto movement = hero->movementPointsRemaining();
	handler->handleReceivedPack(GameConnectionID::FIRST_CONNECTION, pack);
	ASSERT_EQ(server->acknowledgements.size(), 1);
	EXPECT_FALSE(server->acknowledgements[0].result);
	EXPECT_EQ(server->acknowledgements[0].requestID, 1184);
	EXPECT_EQ(hero->pos, position); EXPECT_EQ(hero->movementPointsRemaining(), movement);
	EXPECT_EQ(gameState()->getHero(hero->id), hero);
	EXPECT_EQ(logger.errors(), 0); EXPECT_TRUE(logger.cancellation());
}

TEST_F(TerminalMoveCancellation, loserQueuedMoveIsCancelledOnlyAfterOwnerAuthentication)
{
	start(EPlayerStatus::LOSER); auto pack = request();
	const auto position = hero->pos; const auto movement = hero->movementPointsRemaining();
	ApplyGhNetPackVisitor visitor(*handler, GameConnectionID::FIRST_CONNECTION);
	pack.visit(visitor);
	EXPECT_FALSE(visitor.getResult());
	EXPECT_EQ(hero->pos, position); EXPECT_EQ(hero->movementPointsRemaining(), movement);
}

TEST_F(TerminalMoveCancellation, inactiveIngameMoveRetainsAuthorityRejection)
{
	start(EPlayerStatus::INGAME); auto pack = request();
	ApplyGhNetPackVisitor visitor(*handler, GameConnectionID::FIRST_CONNECTION);
	EXPECT_THROW(pack.visit(visitor), ExceptionNotAllowedAction);
	EXPECT_GT(logger.errors(), 0); EXPECT_FALSE(logger.cancellation());
}

TEST_F(TerminalMoveCancellation, activeIngameMoveStillExecutesNormally)
{
	start(EPlayerStatus::INGAME); auto pack = request();
	gameState()->actingPlayers.insert(RED);
	const auto position = hero->pos;
	ApplyGhNetPackVisitor visitor(*handler, GameConnectionID::FIRST_CONNECTION);
	pack.visit(visitor);
	EXPECT_TRUE(visitor.getResult());
	EXPECT_NE(hero->pos, position);
}

TEST_F(TerminalMoveCancellation, terminalPlayerCannotCancelSpoofedForeignHeroRequest)
{
	start(EPlayerStatus::WINNER); auto pack = request();
	pack.hid = findHeroByOwner(BLUE)->id;
	ApplyGhNetPackVisitor visitor(*handler, GameConnectionID::FIRST_CONNECTION);
	EXPECT_THROW(pack.visit(visitor), ExceptionNotAllowedAction);
	EXPECT_GT(logger.errors(), 0); EXPECT_FALSE(logger.cancellation());
}

TEST_F(TerminalMoveCancellation, unknownConnectionCannotCancelTerminalRequest)
{
	start(EPlayerStatus::WINNER); auto pack = request();
	ApplyGhNetPackVisitor visitor(*handler, GameConnectionID(999));
	EXPECT_THROW(pack.visit(visitor), ExceptionNotAllowedAction);
	EXPECT_GT(logger.errors(), 0); EXPECT_FALSE(logger.cancellation());
}

TEST_F(TerminalMoveCancellation, unknownHeroCannotUseTerminalCancellation)
{
	start(EPlayerStatus::LOSER); auto pack = request();
	pack.hid = ObjectInstanceID(99999);
	ApplyGhNetPackVisitor visitor(*handler, GameConnectionID::FIRST_CONNECTION);
	EXPECT_THROW(pack.visit(visitor), ExceptionNotAllowedAction);
	EXPECT_GT(logger.errors(), 0); EXPECT_FALSE(logger.cancellation());
}

TEST_F(TerminalMoveCancellation, ownedNonHeroCannotUseTerminalCancellation)
{
	start(EPlayerStatus::WINNER); auto pack = request();
	auto * object = findObjectAt(int3(10, 10, 0)); ASSERT_NE(object, nullptr);
	pack.hid = object->id;
	ApplyGhNetPackVisitor visitor(*handler, GameConnectionID::FIRST_CONNECTION);
	EXPECT_THROW(pack.visit(visitor), ExceptionNotAllowedAction);
	EXPECT_GT(logger.errors(), 0); EXPECT_FALSE(logger.cancellation());
}

TEST_F(TerminalMoveCancellation, actualRemovedHeroCannotUseTerminalCancellation)
{
	start(EPlayerStatus::LOSER); auto pack = request();
	RemoveObject remove(hero->id, PlayerColor::NEUTRAL);
	gameState()->apply(remove);
	ASSERT_EQ(gameState()->getHero(pack.hid), nullptr);
	ApplyGhNetPackVisitor visitor(*handler, GameConnectionID::FIRST_CONNECTION);
	EXPECT_THROW(pack.visit(visitor), ExceptionNotAllowedAction);
	EXPECT_GT(logger.errors(), 0); EXPECT_FALSE(logger.cancellation());
}
