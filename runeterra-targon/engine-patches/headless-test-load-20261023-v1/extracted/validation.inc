bool CVCMIServer::validatePlayers()
{
	// prevent loading or starting game where human player is not present on map
	// actual bug might be someplace else, from more likely to less likely:
	// a) RMG bug that fails to place player on map
	// b) this is saved game and player picked already eliminated player
	// c) corrupted map with invalid player
	for (const auto & [color, info] : si->playerInfos)
	{
		if (!info.isControlledByHuman())
			continue;
		const auto * ps = newGH->gameInfo().tryGetPlayerState(color);
		if (!ps || ps->checkVanquished())
		{
			logGlobal->error("Human player %s has no heroes and no towns! Aborting game start!", color.toString());
			auto str = MetaString::createFromTextID("vcmi.broadcast.failedLoadGame");
			return false;
		}
	}

	return true;
}