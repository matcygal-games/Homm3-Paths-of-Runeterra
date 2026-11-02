/* Native VCMI consumer regression for a private, pinned source build.
 * GPL-2.0-or-later; see upstream/license.txt. */
#include "StdInc.h"
#include "../AI/Nullkiller2/AIGateway.h"
#include <gtest/gtest.h>

TEST(TurnGenerationLifecycle, AcceptedCurrentAcknowledgement)
{
 NK2AI::AIStatus status(nullptr);
 status.startedTurn();
 const auto generation = status.getTurnGeneration();
 status.attemptedEndingTurn(1);
 status.receivedEndTurnConfirmation(1, true);
 EXPECT_FALSE(status.haveTurn());
 EXPECT_FALSE(status.haveTurn(generation));
}

TEST(TurnGenerationLifecycle, RejectedAcknowledgementAllowsRetry)
{
 NK2AI::AIStatus status(nullptr);
 status.startedTurn();
 const auto generation = status.getTurnGeneration();
 status.attemptedEndingTurn(1);
 status.receivedEndTurnConfirmation(1, false);
 ASSERT_TRUE(status.haveTurn(generation));
 status.attemptedEndingTurn(2);
 status.receivedEndTurnConfirmation(2, true);
 EXPECT_FALSE(status.haveTurn(generation));
}

TEST(TurnGenerationLifecycle, OldAcknowledgementCannotEndNewTurn)
{
 NK2AI::AIStatus status(nullptr);
 status.startedTurn();
 const auto oldGeneration = status.getTurnGeneration();
 status.attemptedEndingTurn(1);
 status.startedTurn();
 const auto newGeneration = status.getTurnGeneration();
 status.receivedEndTurnConfirmation(1, true);
 EXPECT_FALSE(status.haveTurn(oldGeneration));
 EXPECT_TRUE(status.haveTurn(newGeneration));
}

TEST(TurnGenerationLifecycle, DuplicateAcknowledgementCannotEndNewTurn)
{
 NK2AI::AIStatus status(nullptr);
 status.startedTurn();
 status.attemptedEndingTurn(1);
 status.receivedEndTurnConfirmation(1, true);
 status.startedTurn();
 status.receivedEndTurnConfirmation(1, true);
 EXPECT_TRUE(status.haveTurn());
}

TEST(TurnGenerationLifecycle, UnknownAcknowledgementDoesNotEndTurn)
{
 NK2AI::AIStatus status(nullptr);
 status.startedTurn();
 status.receivedEndTurnConfirmation(999, true);
 EXPECT_TRUE(status.haveTurn());
}

TEST(TurnGenerationLifecycle, RejectedOldAcknowledgementDoesNotEndNewTurn)
{
 NK2AI::AIStatus status(nullptr);
 status.startedTurn();
 status.attemptedEndingTurn(1);
 status.startedTurn();
 status.receivedEndTurnConfirmation(1, false);
 EXPECT_TRUE(status.haveTurn());
}

TEST(TurnGenerationLifecycle, CompletedRequestOwnershipIsRemoved)
{
 NK2AI::AIStatus status(nullptr);
 status.startedTurn();
 status.attemptedEndingTurn(1);
 status.receivedEndTurnConfirmation(1, true);
 status.startedTurn();
 status.attemptedEndingTurn(1);
 status.receivedEndTurnConfirmation(1, true);
 EXPECT_FALSE(status.haveTurn());
}
