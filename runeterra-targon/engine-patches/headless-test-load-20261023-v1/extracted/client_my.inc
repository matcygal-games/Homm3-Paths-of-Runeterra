PlayerColor CServerHandler::myFirstColor() const
{
	return clientFirstColor(logicConnection->connectionID);
}