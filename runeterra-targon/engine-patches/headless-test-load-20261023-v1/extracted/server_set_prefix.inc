void CVCMIServer::setPlayer(PlayerColor clickedColor)
{
	struct PlayerToRestore
	{
		PlayerColor color;
		PlayerConnectionID id;
		void reset() { id = PlayerConnectionID::INVALID; color = PlayerColor::CANNOT_DETERMINE; }
		PlayerToRestore(){ reset(); }
	};

	PlayerToRestore playerToRestore;
	PlayerSettings & clicked = si->playerInfos[clickedColor];

	//identify clicked player
	PlayerConnectionID clickedNameID = PlayerConnectionID::PLAYER_AI;
	if(clicked.isControlledByHuman())
		clickedNameID = *(clicked.connectedPlayerIDs.begin()); //if not AI - set appropriate ID

	if(clickedNameID > PlayerConnectionID::PLAYER_AI && playerToRestore.id == clickedNameID) //player to restore is about to being replaced -> put him back to the old place
	{
		PlayerSettings & restPos = si->playerInfos[playerToRestore.color];
		setPlayerConnectedId(restPos, playerToRestore.id);
		playerToRestore.reset();
	}

	PlayerConnectionID newPlayer; //which player will take clicked position

	//who will be put here?
	if(clickedNameID == PlayerConnectionID::PLAYER_AI) //AI player clicked -> if possible replace computer with unallocated player
	{
		newPlayer = getIdOfFirstUnallocatedPlayer();
		if(newPlayer == PlayerConnectionID::PLAYER_AI) //no "free" player -> get just first one
			newPlayer = playerNames.begin()->first;
	}
	else //human clicked -> take next
	{
		auto i = playerNames.find(clickedNameID); //clicked one
		i++; //player AFTER clicked one

		if(i != playerNames.end())
			newPlayer = i->first;
		else
			newPlayer = PlayerConnectionID::PLAYER_AI; //AI if we scrolled through all players
	}

	setPlayerConnectedId(clicked, newPlayer); //put player

}