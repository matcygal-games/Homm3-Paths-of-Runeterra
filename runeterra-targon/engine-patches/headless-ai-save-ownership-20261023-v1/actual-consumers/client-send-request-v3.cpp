int CClient::sendRequest(const CPackForServer & request, PlayerColor player, bool waitTillRealize)
{
	if(observerMode)
	{
		logNetwork->trace("Dropped request \"%s\" - a replay is in progress", typeid(request).name());
		return 0;
	}

	ui32 requestID = requestCounter++;
	logNetwork->trace("Sending a request \"%s\". It'll have an ID=%d.", typeid(request).name(), requestID);

	waitingRequest.pushBack(requestID);
	request.requestID = requestID;
	request.player = player;
	// Register request ownership before transport can deliver a reply or the next turn.
	if(vstd::contains(playerint, player))
		playerint[player]->requestSent(&request, requestID);
	GAME->server().sendGamePack(request);

	if(waitTillRealize)
	{
		logGlobal->trace("We'll wait till request %d is answered.\n", requestID);
		auto gsUnlocker = vstd::makeUnlockSharedGuard(CGameState::mutex);
		waitingRequest.waitWhileContains(requestID);
	}

	return requestID;
}
