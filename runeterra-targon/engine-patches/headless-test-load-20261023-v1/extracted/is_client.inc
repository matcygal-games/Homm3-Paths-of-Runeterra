bool LobbyInfo::isClientColor(GameConnectionID clientId, const PlayerColor & color) const
{
	if(si->playerInfos.find(color) != si->playerInfos.end())
	{
		for(PlayerConnectionID id : si->playerInfos.find(color)->second.connectedPlayerIDs)
		{
			if(playerNames.find(id) != playerNames.end())
			{
				if(playerNames.find(id)->second.connection == clientId)
					return true;
			}
		}
	}
	return false;
}