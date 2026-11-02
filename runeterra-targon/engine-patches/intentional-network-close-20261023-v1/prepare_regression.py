"""Compile actual pinned method bodies against explicit minimal dependency fixtures."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent


def method(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth, end = 1, brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


def main():
    records = {}
    for variant in ('upstream', 'patched'):
        base = HERE / variant
        server = (base / 'server/CVCMIServer.cpp').read_text()
        lobby = (base / 'server/NetPacksLobbyServer.cpp').read_text()
        bodies = []
        for signature in (
            'void CVCMIServer::onNewConnection(', 'std::shared_ptr<GameConnection> CVCMIServer::findConnection(',
            'void CVCMIServer::onDisconnected(', 'void CVCMIServer::handleReceivedPack(',
            'void CVCMIServer::clientDisconnected('):
            bodies.append(method(server, signature))
        if variant == 'patched':
            bodies.insert(0, method(server, 'void CVCMIServer::closeConnection('))
        for signature in ('void ClientPermissionsCheckerNetPackVisitor::visitLobbyClientDisconnected(',
                          'void ApplyOnServerNetPackVisitor::visitLobbyClientDisconnected('):
            bodies.append(method(lobby, signature))
        transport = (HERE / 'upstream/lib/network/NetworkConnection.cpp').read_text()
        for signature in ('InternalConnection::InternalConnection(', 'void InternalConnection::receivePacket(',
                          'void InternalConnection::disconnect(', 'void InternalConnection::connectTo(',
                          'void InternalConnection::sendPacket(', 'void InternalConnection::setAsyncWritesEnabled(',
                          'void InternalConnection::close('):
            bodies.append(method(transport, signature))
        declaration = (base / 'server/CVCMIServer.h').read_text()
        field = '\tstd::set<std::weak_ptr<INetworkConnection>, std::owner_less<>> requestedConnectionClosures;'
        assert (field in declaration) == (variant == 'patched')
        template = (HERE / 'consumer_fixture.cpp.in').read_text()
        source = template.replace('__CLOSURE_FIELD__', field if variant == 'patched' else '')
        source = source.replace('__CLOSE_DECLARATION__', 'void closeConnection(const std::shared_ptr<INetworkConnection> &);' if variant == 'patched' else '')
        source = source.replace('__ACTUAL_CONSUMER_METHODS__', '\n'.join(bodies))
        source = source.replace('__PATCHED__', 'true' if variant == 'patched' else 'false')
        out = HERE / 'tests-v2' / variant / 'consumer_regression.cpp'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(source, encoding='utf-8')
        records[variant] = {'consumer_bodies_sha256': hashlib.sha256('\n'.join(bodies).encode()).hexdigest(),
            'generated_cpp_sha256': hashlib.sha256(source.encode()).hexdigest(), 'actual_methods': len(bodies)}
    (HERE / 'extracted-consumers-v2.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
