void CServerHandler::debugStartTest(std::string filename, bool save)
{
	logGlobal->info("Starting debug test with file: %s", filename);
	auto mapInfo = std::make_shared<CMapInfo>();
	if(save)
	{
		resetStateForLobby(EStartMode::LOAD_GAME, ESelectionScreen::loadGame, EServerMode::LOCAL, {});
		mapInfo->saveInit(ResourcePath(filename, EResType::SAVEGAME));
	}
	else
	{
		resetStateForLobby(EStartMode::NEW_GAME, ESelectionScreen::newGame, EServerMode::LOCAL, {});
		mapInfo->mapInit(filename);
	}
	if(settings["session"]["donotstartserver"].Bool())
		connectToServer(getLocalHostname(), getLocalPort());
	else
		startLocalServerAndConnect(false);

	std::this_thread::sleep_for(std::chrono::milliseconds(100));

	while(!settings["session"]["headless"].Bool() && !ENGINE->windows().topWindow<CLobbyScreen>())
		std::this_thread::sleep_for(std::chrono::milliseconds(50));

	while(!mi || mapInfo->fileURI != mi->fileURI)
	{
		setMapInfo(mapInfo);
		std::this_thread::sleep_for(std::chrono::milliseconds(50));
	}
	// "Click" on our color only when a seat is assigned. An all-AI save
	// already has no local human player to remove.
	const auto playerColor = myFirstColor();
	if(false)
		setPlayer(playerColor);
	while(myFirstColor() != PlayerColor::CANNOT_DETERMINE)
		std::this_thread::sleep_for(std::chrono::milliseconds(50));

	while(true)
	{
		try
		{
			sendStartGame();
			break;
		}
		catch(...)
		{

		}
		std::this_thread::sleep_for(std::chrono::milliseconds(50));
	}
}