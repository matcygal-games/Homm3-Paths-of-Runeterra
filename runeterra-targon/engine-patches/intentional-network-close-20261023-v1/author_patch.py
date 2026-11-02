"""Create separate patched consumer copies and an apply-checkable official66fa diff."""
from pathlib import Path
import difflib
import hashlib
import json

HERE = Path(__file__).resolve().parent


def replace(source, before, after):
    assert source.count(before) == 1, before
    return source.replace(before, after)


def main():
    patches = []
    names = ('server/CVCMIServer.h', 'server/CVCMIServer.cpp', 'server/NetPacksLobbyServer.cpp')
    hashes = {}
    for name in names:
        raw = (HERE / 'upstream' / name).read_bytes()
        source = raw.decode()
        if name.endswith('.h'):
            source = replace(source, '#include "IGameServer.h"', '#include "IGameServer.h"\n\n#include <memory>\n#include <set>')
            source = replace(source, '\tstd::unique_ptr<INetworkServer> networkServer;',
                '\tstd::unique_ptr<INetworkServer> networkServer;\n\tstd::set<std::weak_ptr<INetworkConnection>, std::owner_less<>> requestedConnectionClosures;')
            source = replace(source, '\tvoid onDisconnected(', '\tvoid closeConnection(const std::shared_ptr<INetworkConnection> & connection);\n\tvoid onDisconnected(')
        elif name.endswith('CVCMIServer.cpp'):
            source = replace(source, '\t\tconnection->close();', '\t\tcloseConnection(connection);')
            marker = 'void CVCMIServer::onDisconnected('
            method = '''void CVCMIServer::closeConnection(const std::shared_ptr<INetworkConnection> & connection)
{
	for(auto it = requestedConnectionClosures.begin(); it != requestedConnectionClosures.end();)
	{
		if(it->expired())
			it = requestedConnectionClosures.erase(it);
		else
			++it;
	}
	requestedConnectionClosures.insert(connection);
	connection->close();
}

'''
            source = replace(source, marker, method + marker)
            source = replace(source, '\tlogNetwork->error("Network error receiving a pack. Connection has been closed");', '''	if(requestedConnectionClosures.find(connection) != requestedConnectionClosures.end())
	{
		logNetwork->debug("Connection closed after explicit local close request: %s", errorMessage);
		return;
	}

	logNetwork->error("Network error receiving a pack. Connection has been closed: %s", errorMessage);''')
        else:
            source = replace(source, '\tconnection->getConnection()->close();', '\tsrv.closeConnection(connection->getConnection());')
        target = HERE / 'patched' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_text() == source
        else:
            target.write_bytes(source.encode())
        patches.append('diff --git a/' + name + ' b/' + name + '\n' + ''.join(difflib.unified_diff(raw.decode().splitlines(True), source.splitlines(True), fromfile='a/' + name, tofile='b/' + name)))
        hashes[name] = {'upstream_sha256': hashlib.sha256(raw).hexdigest(), 'patched_sha256': hashlib.sha256(source.encode()).hexdigest()}
    output = HERE / '0001-track-explicit-server-connection-close-ownership.patch'
    content = ''.join(patches).encode()
    if output.exists():
        assert output.read_bytes() == content
    else:
        output.write_bytes(content)
    (HERE / 'patch-inputs.json').write_text(json.dumps({'files': hashes, 'patch_sha256': hashlib.sha256(content).hexdigest()}, indent=2) + '\n')
    print(json.dumps({'patch': str(output), 'sha256': hashlib.sha256(content).hexdigest()}))


if __name__ == '__main__':
    main()
