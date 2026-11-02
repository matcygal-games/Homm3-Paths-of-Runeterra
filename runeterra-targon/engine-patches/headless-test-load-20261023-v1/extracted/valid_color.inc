bool PlayerColor::isValidPlayer() const
{
	return num >= 0 && num < PLAYER_LIMIT_I;
}