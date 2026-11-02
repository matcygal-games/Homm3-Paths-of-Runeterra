void CVCMIServer::setPlayerConnectedId(PlayerSettings & pset, PlayerConnectionID player) const
{
	if(vstd::contains(playerNames, player))
		pset.name = playerNames.find(player)->second.name;
	else
		pset.name = LIBRARY->generaltexth->allTexts[468]; //Computer

	logGlobal->debug("Player color %d will be controlled from connection %d", pset.color, static_cast<int>(player));
	pset.connectedPlayerIDs.clear();
	if(player != PlayerConnectionID::PLAYER_AI)
		pset.connectedPlayerIDs.insert(player);
}