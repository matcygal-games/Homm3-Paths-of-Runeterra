/* Native consumer regressions for local request/turn ownership. GPL-2.0-or-later. */
#include "StdInc.h"
#include "nullkiller2/NullkillerTest.h"
#include "lib/callback/CCallback.h"
#include "lib/callback/IClient.h"
#include "lib/networkPacks/PacksForClient.h"
#include "lib/networkPacks/PacksForServer.h"
#include "lib/serializer/CTypeList.h"
#include "lib/callback/Calendar.h"
#include "lib/UnlockGuard.h"

namespace
{
const PlayerColor PLAYER(0);
class EndTurnClient : public IClient
{
public:
	NK2AI::AIGateway * gateway = nullptr;
	int requests = 0;
	bool startNextTurnBeforeFirstAck = false;
	bool rejectFirst = false;
	std::optional<BattleAction> makeSurrenderRetreatDecision(PlayerColor, const BattleID &, const BattleStateInfoForRetreat &) override { return std::nullopt; }
	int sendRequest(const CPackForServer & pack, PlayerColor player, bool) override
	{
		if(!dynamic_cast<const EndTurn *>(&pack))
			return 0;
		const int id = ++requests;
		gateway->requestSent(&pack, id); // Real CClient registration callback.
		if(id == 1 && startNextTurnBeforeFirstAck)
			gateway->status.startedTurn(); // The yourTurn consumer starts the next generation.
		PackageApplied applied(player, id, CTypeList::getInstance().getTypeID<EndTurn>(nullptr), !(id == 1 && rejectFirst));
		gateway->requestRealized(&applied); // Real acknowledgement consumer.
		return id;
	}
};

class PlanningActionNullkiller : public NK2AI::Nullkiller
{
public:
	std::function<void()> action;
	void makeTurn() override { action(); }
};

class Nullkiller2_TurnLifecycle : public NullkillerTest
{
protected:
	std::unique_ptr<NK2AI::AIGateway> start(EndTurnClient & client)
	{
		TinyH3M::TinyH3MBuilder builder(EMapFormat::SOD);
		builder.size(36, false).playerActive(PLAYER).hero({5, 5, 0}, HeroTypeID(0), PLAYER);
		startWithMap(std::move(builder));
		auto gateway = makeGateway(PLAYER, &client);
		client.gateway = gateway.get();
		gateway->status.startedTurn();
		return gateway;
	}
	void planningAction(NK2AI::AIGateway & gateway, std::function<void()> action)
	{
		auto planner = std::make_unique<PlanningActionNullkiller>();
		planner->init(gateway.cc, &gateway);
		planner->action = std::move(action);
		gateway.nullkiller = std::move(planner);
	}
	void applyNextDay(NK2AI::AIGateway & gateway, bool deliverStartedTurn)
	{
		// Model CClient's exact boundary: unique GS apply, then callback outside GS.
		auto unlock = vstd::makeUnlockSharedGuard(CGameState::mutex);
		{
			std::unique_lock writer(CGameState::mutex);
			NewTurn nextDay;
			nextDay.day = gateway.cc->getCalendar().getCurrentDay() + 1;
			gameState()->apply(nextDay);
			PlayerStartsTurn started;
			started.player = PLAYER;
			gameState()->apply(started);
		}
		if(deliverStartedTurn)
			gateway.status.startedTurn();
	}
	void sent(NK2AI::AIGateway & gateway, int id)
	{
		EndTurn request;
		gateway.requestSent(&request, id);
	}
	void ack(NK2AI::AIGateway & gateway, int id, bool success = true)
	{
		PackageApplied applied(PLAYER, id, CTypeList::getInstance().getTypeID<EndTurn>(nullptr), success);
		gateway.requestRealized(&applied);
	}
};
}

TEST_F(Nullkiller2_TurnLifecycle, matchingAcknowledgementFinishesOnlyItsTurn)
{
	EndTurnClient client; auto gateway = start(client);
	sent(*gateway, 41); ack(*gateway, 41);
	EXPECT_FALSE(gateway->status.haveTurn());
}

TEST_F(Nullkiller2_TurnLifecycle, nextTurnBeforeOldAcknowledgementRemainsActive)
{
	EndTurnClient client; auto gateway = start(client);
	sent(*gateway, 41); gateway->status.startedTurn(); ack(*gateway, 41);
	EXPECT_TRUE(gateway->status.haveTurn());
}

TEST_F(Nullkiller2_TurnLifecycle, duplicateOldAcknowledgementCannotFinishNewPendingTurn)
{
	EndTurnClient client; auto gateway = start(client);
	sent(*gateway, 41); ack(*gateway, 41); gateway->status.startedTurn(); sent(*gateway, 42);
	ack(*gateway, 41); EXPECT_TRUE(gateway->status.haveTurn());
	ack(*gateway, 42); EXPECT_FALSE(gateway->status.haveTurn());
}

TEST_F(Nullkiller2_TurnLifecycle, unknownAcknowledgementCannotFinishCurrentTurn)
{
	EndTurnClient client; auto gateway = start(client);
	ack(*gateway, 999); EXPECT_TRUE(gateway->status.haveTurn());
}

TEST_F(Nullkiller2_TurnLifecycle, failedAndDuplicateAcknowledgementsCannotFinishCurrentTurn)
{
	EndTurnClient client; auto gateway = start(client);
	sent(*gateway, 41); ack(*gateway, 41, false); ack(*gateway, 41);
	EXPECT_TRUE(gateway->status.haveTurn());
	sent(*gateway, 42); ack(*gateway, 42); EXPECT_FALSE(gateway->status.haveTurn());
}

TEST_F(Nullkiller2_TurnLifecycle, acknowledgementAfterMultipleGenerationsCannotFinishLatest)
{
	EndTurnClient client; auto gateway = start(client);
	sent(*gateway, 41); gateway->status.startedTurn(); gateway->status.startedTurn(); ack(*gateway, 41);
	EXPECT_TRUE(gateway->status.haveTurn());
}

TEST_F(Nullkiller2_TurnLifecycle, staleEndTurnInvocationNeverRetriesAgainstTheNextTurn)
{
	EndTurnClient client; auto gateway = start(client);
	client.startNextTurnBeforeFirstAck = true;
	std::shared_lock gameStateLock(CGameState::mutex);
	gateway->endTurn();
	EXPECT_EQ(client.requests, 1);
	EXPECT_TRUE(gateway->status.haveTurn());
}

TEST_F(Nullkiller2_TurnLifecycle, currentTurnRetriesOneRejectedRequestThenFinishes)
{
	EndTurnClient client; auto gateway = start(client);
	client.rejectFirst = true;
	std::shared_lock gameStateLock(CGameState::mutex);
	gateway->endTurn();
	EXPECT_EQ(client.requests, 2);
	EXPECT_FALSE(gateway->status.haveTurn());
}

TEST_F(Nullkiller2_TurnLifecycle, appliedNextDayWithDelayedStartedTurnCannotSubmitOldTaskEndTurn)
{
	EndTurnClient client; auto gateway = start(client);
	planningAction(*gateway, [this, &gateway]() { applyNextDay(*gateway, false); });
	gateway->makeTurn(); // Real consumer resumes after its wait with an old invocation origin.
	EXPECT_EQ(client.requests, 0) << "a stale task must not even enter IClient EndTurn submission";
	EXPECT_TRUE(gateway->status.haveTurn());
}

TEST_F(Nullkiller2_TurnLifecycle, nextDayCallbackBeforeSubmissionCannotEndTheNewTurn)
{
	EndTurnClient client; auto gateway = start(client);
	planningAction(*gateway, [this, &gateway]() { applyNextDay(*gateway, true); });
	gateway->makeTurn();
	EXPECT_EQ(client.requests, 0) << "registration is too late to cancel an already sent EndTurn";
	EXPECT_TRUE(gateway->status.haveTurn());
}

TEST_F(Nullkiller2_TurnLifecycle, unchangedDayMakeTurnStillSubmitsOneValidEndTurn)
{
	EndTurnClient client; auto gateway = start(client);
	planningAction(*gateway, []() {});
	gateway->makeTurn();
	EXPECT_EQ(client.requests, 1);
	EXPECT_FALSE(gateway->status.haveTurn());
}
