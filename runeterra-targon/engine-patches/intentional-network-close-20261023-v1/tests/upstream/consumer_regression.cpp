// Dependency fixtures surround unmodified extracted official consumer method bodies.
// This is not a native VCMI executable or a full engine build.
#include <algorithm>
#include <cassert>
#include <cstddef>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>
#include <stdexcept>

struct Logger
{
    std::vector<std::string> errors, debugs;
    template<class... T> void error(const std::string & text, const T &... args) { errors.push_back(text + join(args...)); }
    template<class... T> void debug(const std::string & text, const T &... args) { debugs.push_back(text + join(args...)); }
    template<class... T> void info(const std::string &, const T &...) {}
    template<class... T> void trace(const std::string &, const T &...) {}
    static std::string join() { return {}; }
    template<class T, class... U> static std::string join(const T & value, const U &... rest) { return std::string(value) + join(rest...); }
};
Logger logger;
Logger * logNetwork = &logger;
Logger * logGlobal = &logger;
namespace vstd {
template<class C, class T> bool contains(const C & c, const T & t) { return std::find(c.begin(),c.end(),t)!=c.end(); }
template<class C, class T> void erase(C & c, const T & t) { c.erase(std::remove(c.begin(),c.end(),t),c.end()); }
}
using PlayerConnectionID=int;
struct MetaString { void appendTextID(const char *) {} void replaceRawString(const std::string &) {} };
struct INetworkConnection : std::enable_shared_from_this<INetworkConnection>
{
    virtual ~INetworkConnection()=default;
    virtual void close()=0;
};
struct INetworkConnectionListener {
    virtual void onDisconnected(const std::shared_ptr<INetworkConnection> &, const std::string &)=0;
    virtual void onPacketReceived(const std::shared_ptr<INetworkConnection> &, const std::vector<std::byte> &) {}
};
struct NetworkContext {
    std::vector<std::function<void()>> queue;
    void drain() { for(int count=0; !queue.empty(); ++count) { assert(count<30); auto f=queue.front();queue.erase(queue.begin());f(); } }
};
namespace boost { namespace asio {
template<class F> void post(NetworkContext & context, F f) { context.queue.push_back(f); }
}}
struct IInternalConnection : INetworkConnection {
    virtual void receivePacket(const std::vector<std::byte> &)=0;
    virtual void disconnect()=0;
};
struct InternalConnection : IInternalConnection {
    NetworkContext & context; INetworkConnectionListener & listener;
    std::weak_ptr<IInternalConnection> otherSideWeak; bool connectionActive=false;
    InternalConnection(INetworkConnectionListener &, NetworkContext &);
    void receivePacket(const std::vector<std::byte> &) override;
    void disconnect() override;
    void connectTo(std::shared_ptr<IInternalConnection>);
    void sendPacket(const std::vector<std::byte> &);
    void setAsyncWritesEnabled(bool);
    void close() override;
};
struct TestConnection : INetworkConnection {
    int closes=0; std::function<void()> callback;
    void close() override { ++closes; auto current=callback; if(current) current(); }
};
struct GameConnection {
    int connectionID=0; std::shared_ptr<INetworkConnection> network;
    explicit GameConnection(std::shared_ptr<INetworkConnection> c):network(std::move(c)){}
    std::shared_ptr<INetworkConnection> getConnection() {return network;}
    bool isMyConnection(const std::shared_ptr<INetworkConnection> & c) {return c==network;}
    void enterLobbyConnectionMode() {}
};
enum class EServerState { LOBBY, GAMEPLAY, SHUTDOWN };
struct CVCMIServer;
struct LobbyClientDisconnected;
struct Visitor { virtual void visitLobbyClientDisconnected(LobbyClientDisconnected &)=0; virtual ~Visitor()=default; };
struct CPackForLobby { virtual void visit(Visitor &)=0; virtual ~CPackForLobby()=default; };
struct LobbyClientDisconnected : CPackForLobby {
    int clientId=0; bool shutdownServer=false;
    void visit(Visitor & v) override {v.visitLobbyClientDisconnected(*this);}
};
struct PlayerEntry {std::string name;int connection;};
struct PlayerSettings {std::set<int> connectedPlayerIDs;};
struct StartInfo {std::map<int,PlayerSettings> playerInfos;};
struct GameHandler {
    int cleanupCalls=0;std::vector<int> disconnected;
    void handleClientDisconnection(int, const std::vector<int> & ids) {++cleanupCalls;disconnected=ids;}
};
struct CVCMIServer : INetworkConnectionListener {
    
    std::vector<std::shared_ptr<GameConnection>> activeConnections;
    EServerState state=EServerState::LOBBY;
    int hostClientId=1000, announcements=0; bool runByClient=true;
    std::map<int,PlayerEntry> playerNames;
    std::shared_ptr<StartInfo> si=std::make_shared<StartInfo>();
    std::shared_ptr<GameHandler> gh=std::make_shared<GameHandler>();
    EServerState getState() const {return state;} void setState(EServerState s) {state=s;}
    bool wasStartedByClient() const {return runByClient;}
    void announceTxt(const MetaString &) {} void announcePack(CPackForLobby &) {++announcements;}
    
    void onNewConnection(const std::shared_ptr<INetworkConnection> &);
    std::shared_ptr<GameConnection> findConnection(const std::shared_ptr<INetworkConnection> &);
    void onDisconnected(const std::shared_ptr<INetworkConnection> &, const std::string &) override;
    void handleReceivedPack(std::shared_ptr<GameConnection>, CPackForLobby &);
    void clientDisconnected(std::shared_ptr<GameConnection>);
};
struct ClientPermissionsCheckerNetPackVisitor : Visitor {
    CVCMIServer & srv;std::shared_ptr<GameConnection> connection;bool result=false;
    ClientPermissionsCheckerNetPackVisitor(CVCMIServer & s,std::shared_ptr<GameConnection> c):srv(s),connection(c){}
    bool getResult() const {return result;}
    void visitLobbyClientDisconnected(LobbyClientDisconnected &) override;
};
struct ApplyOnServerNetPackVisitor : Visitor {
    CVCMIServer & srv;std::shared_ptr<GameConnection> connection;bool result=false;
    ApplyOnServerNetPackVisitor(CVCMIServer & s,std::shared_ptr<GameConnection> c):srv(s),connection(c){}
    bool getResult() const {return result;}
    void visitLobbyClientDisconnected(LobbyClientDisconnected &) override;
};

void CVCMIServer::onNewConnection(const std::shared_ptr<INetworkConnection> & connection)
{
	if(getState() == EServerState::LOBBY)
	{
		activeConnections.push_back(std::make_shared<GameConnection>(connection));
		activeConnections.back()->enterLobbyConnectionMode();
	}
	else
	{
		// TODO: reconnection support
		connection->close();
	}
}

std::shared_ptr<GameConnection> CVCMIServer::findConnection(const std::shared_ptr<INetworkConnection> & netConnection)
{
	for(const auto & gameConnection : activeConnections)
	{
		if (gameConnection->isMyConnection(netConnection))
			return gameConnection;
	}

	return nullptr;
}

void CVCMIServer::onDisconnected(const std::shared_ptr<INetworkConnection> & connection, const std::string & errorMessage)
{
	logNetwork->error("Network error receiving a pack. Connection has been closed");

	std::shared_ptr<GameConnection> c = findConnection(connection);

	// player may have already disconnected via clientDisconnected call
	if (c)
	{
		LobbyClientDisconnected lcd;
		lcd.clientId = c->connectionID;
		handleReceivedPack(c, lcd);
	}
}

void CVCMIServer::handleReceivedPack(std::shared_ptr<GameConnection> connection, CPackForLobby & pack)
{
	ClientPermissionsCheckerNetPackVisitor checker(*this, connection);
	pack.visit(checker);

	if(checker.getResult())
	{
		ApplyOnServerNetPackVisitor applier(*this, connection);
		pack.visit(applier);
		if (applier.getResult())
			announcePack(pack);
	}
}

void CVCMIServer::clientDisconnected(std::shared_ptr<GameConnection> connection)
{
	assert(vstd::contains(activeConnections, connection));
	logGlobal->trace("Received disconnection request");
	vstd::erase(activeConnections, connection);

	std::vector<PlayerConnectionID> disconnectedPlayerIds;
	for(const auto & playerEntry : playerNames)
	{
		if(playerEntry.second.connection != connection->connectionID)
			continue;

		disconnectedPlayerIds.push_back(playerEntry.first);
		logNetwork->info("Player disconnected from lobby: name='%s', connectionId=%d", playerEntry.second.name, static_cast<int>(connection->connectionID));
		MetaString disconnectMessage;
		disconnectMessage.appendTextID("vcmi.lobby.system.playerDisconnected");
		disconnectMessage.replaceRawString(playerEntry.second.name);
		announceTxt(disconnectMessage);
	}

	if(disconnectedPlayerIds.empty())
		logNetwork->info("Connection %d disconnected from lobby with no mapped player names", static_cast<int>(connection->connectionID));

	if(activeConnections.empty() || hostClientId == connection->connectionID)
	{
		setState(EServerState::SHUTDOWN);
		return;
	}

	if(gh && getState() == EServerState::GAMEPLAY)
	{
		gh->handleClientDisconnection(connection->connectionID, disconnectedPlayerIds);
	}

	for(const auto & playerId : disconnectedPlayerIds)
		playerNames.erase(playerId);

	for(auto & playerInfoEntry : si->playerInfos)
	{
		auto & connectedPlayerIDs = playerInfoEntry.second.connectedPlayerIDs;
		for(const auto & playerId : disconnectedPlayerIds)
			connectedPlayerIDs.erase(playerId);
	}
}

void ClientPermissionsCheckerNetPackVisitor::visitLobbyClientDisconnected(LobbyClientDisconnected & pack)
{
	if(pack.clientId != connection->connectionID)
	{
		result = false;
		return;
	}

	if(pack.shutdownServer)
	{
		if(!srv.wasStartedByClient())
		{
			result = false;
			return;
		}

		if(connection->connectionID != srv.hostClientId)
		{
			result = false;
			return;
		}
	}

	result = true;
}

void ApplyOnServerNetPackVisitor::visitLobbyClientDisconnected(LobbyClientDisconnected & pack)
{
	connection->getConnection()->close();
	srv.clientDisconnected(connection);
	result = true;
}

InternalConnection::InternalConnection(INetworkConnectionListener & listener, NetworkContext & context)
	: context(context)
	, listener(listener)
{
}

void InternalConnection::receivePacket(const std::vector<std::byte> & message)
{
	boost::asio::post(context, [self = std::static_pointer_cast<InternalConnection>(shared_from_this()), message](){
		if (self->connectionActive)
			self->listener.onPacketReceived(self, message);
	});
}

void InternalConnection::disconnect()
{
	boost::asio::post(context, [self = std::static_pointer_cast<InternalConnection>(shared_from_this())](){
		self->listener.onDisconnected(self, "Internal connection has been terminated");
		self->otherSideWeak.reset();
		self->connectionActive = false;
	});
}

void InternalConnection::connectTo(std::shared_ptr<IInternalConnection> connection)
{
	otherSideWeak = connection;
	connectionActive = true;
}

void InternalConnection::sendPacket(const std::vector<std::byte> & message)
{
	auto otherSide = otherSideWeak.lock();

	if (otherSide)
		otherSide->receivePacket(message);
}

void InternalConnection::setAsyncWritesEnabled(bool on)
{
	// no-op
}

void InternalConnection::close()
{
	auto otherSide = otherSideWeak.lock();

	if (otherSide)
		otherSide->disconnect();

	otherSideWeak.reset();
	connectionActive = false;
}


struct Fixture {
    CVCMIServer server;
    std::shared_ptr<TestConnection> transport=std::make_shared<TestConnection>();
    std::shared_ptr<GameConnection> connection;
    Fixture() {logger={};server.onNewConnection(transport);connection=server.activeConnections.at(0);connection->connectionID=1;server.state=EServerState::GAMEPLAY;}
    void request(int id=1,bool shutdown=false) {LobbyClientDisconnected p;p.clientId=id;p.shutdownServer=shutdown;server.handleReceivedPack(connection,p);}
};
void require(bool value,const char * message) {if(!value)throw std::runtime_error(message);}
int main(int argc, char ** argv) {
    constexpr bool patched=false;
    int passed=0,failed=0;
    auto test=[&](const char * name, auto fn) {if(argc>1&&std::string(argv[1])!=name)return;try{fn();++passed;std::cout<<"PASS "<<name<<"\n";}catch(const std::exception & e){++failed;std::cout<<"FAIL "<<name<<": "<<e.what()<<"\n";}};
    test("authorized-request-late-and-duplicate",[]{Fixture f;f.request();f.server.onDisconnected(f.transport,"canceled");f.server.onDisconnected(f.transport,"eof");require(logger.errors.empty(),"intentional callback ERROR");require(f.transport->closes==1&&f.server.activeConnections.empty()&&f.server.state==EServerState::SHUTDOWN,"cleanup changed");});
    test("synchronous-close-before-removal",[]{Fixture f;f.transport->callback=[&]{f.transport->callback={};f.server.onDisconnected(f.transport,"immediate close");};f.request();require(logger.errors.empty(),"synchronous intentional callback ERROR");require(f.transport->closes==1&&f.server.activeConnections.empty(),"reentrant duplicate cleanup");});
    test("unexpected-active-loss-cleanup-once",[]{Fixture f;auto other=std::make_shared<TestConnection>();auto c=std::make_shared<GameConnection>(other);c->connectionID=2;f.server.activeConnections.push_back(c);f.server.playerNames[10]={"red",1};f.server.si->playerInfos[0].connectedPlayerIDs.insert(10);f.server.onDisconnected(f.transport,"reset by peer");require(logger.errors.size()==1,"lost unexpected ERROR");if(patched)require(logger.errors[0].find("reset by peer")!=std::string::npos,"lost error reason");require(f.server.gh->cleanupCalls==1&&f.server.playerNames.empty()&&f.server.si->playerInfos[0].connectedPlayerIDs.empty(),"authoritative cleanup not performed");f.server.onDisconnected(f.transport,"cancel from cleanup");require(logger.errors.size()==1,"duplicate local-close error");require(f.server.gh->cleanupCalls==1&&f.transport->closes==1,"cleanup repeated");});
    test("unknown-loss-after-shutdown-remains-error",[]{Fixture f;f.request();auto unknown=std::make_shared<TestConnection>();f.server.onDisconnected(unknown,"unknown connection failed");require(logger.errors.size()==1,"unknown ERROR hidden by global shutdown");require(unknown->closes==0,"unknown transport mutated");});
    test("rejected-wrong-client-cannot-mark",[]{Fixture f;f.request(2);require(f.transport->closes==0&&f.server.activeConnections.size()==1,"invalid command applied");f.server.onDisconnected(f.transport,"unrequested reset");require(logger.errors.size()==1,"invalid request hid failure");});
    test("rejected-nonhost-shutdown-cannot-mark",[]{Fixture f;f.server.hostClientId=2;f.request(1,true);require(f.transport->closes==0,"nonhost command applied");f.server.onDisconnected(f.transport,"unrequested reset");require(logger.errors.size()==1,"nonhost request hid failure");});
    test("rejected-dedicated-shutdown-cannot-mark",[]{Fixture f;f.server.runByClient=false;f.server.hostClientId=1;f.request(1,true);require(f.transport->closes==0,"dedicated shutdown applied");f.server.onDisconnected(f.transport,"reset");require(logger.errors.size()==1,"denied request hid failure");});
    test("one-peer-close-other-peer-failure",[]{Fixture f;auto other=std::make_shared<TestConnection>();auto c=std::make_shared<GameConnection>(other);c->connectionID=2;f.server.activeConnections.push_back(c);f.request();f.server.onDisconnected(f.transport,"requested close");require(logger.errors.empty(),"first intentional peer ERROR");f.server.onDisconnected(other,"second peer reset");require(logger.errors.size()==1&&f.server.activeConnections.empty(),"other peer failure hidden");});
    test("other-peer-failure-before-local-completion",[]{Fixture f;auto other=std::make_shared<TestConnection>();auto c=std::make_shared<GameConnection>(other);c->connectionID=2;f.server.activeConnections.push_back(c);f.request();f.server.onDisconnected(other,"second peer reset");f.server.onDisconnected(f.transport,"late first-peer completion");require(logger.errors.size()==1&&f.server.activeConnections.empty(),"completion ordering lost failure");});
    test("rejected-new-connection-owned-close",[]{Fixture f;auto rejected=std::make_shared<TestConnection>();f.server.onNewConnection(rejected);require(rejected->closes==1,"rejection did not close");f.server.onDisconnected(rejected,"rejected close");require(logger.errors.empty(),"known rejected transport ERROR");f.server.onDisconnected(f.transport,"active peer failure");require(logger.errors.size()==1,"rejection hid active loss");});
    test("weak-lifetime-and-address-reuse",[]{Fixture f;auto rejected=std::make_shared<TestConnection>();std::weak_ptr<INetworkConnection> weak=rejected;f.server.onNewConnection(rejected);rejected.reset();require(weak.expired(),"closure registry extends transport lifetime");auto unrelated=std::make_shared<TestConnection>();f.server.onDisconnected(unrelated,"new transport failure");require(logger.errors.size()==1,"new ownership incorrectly treated as closed");});
    test("actual-internal-queued-requested-completion",[]{logger={};CVCMIServer s;NetworkContext context;auto transport=std::make_shared<InternalConnection>(s,context);transport->connectTo(transport);s.onNewConnection(transport);auto c=s.activeConnections[0];c->connectionID=1;s.state=EServerState::GAMEPLAY;LobbyClientDisconnected p;p.clientId=1;s.handleReceivedPack(c,p);require(!context.queue.empty(),"actual internal completion not queued");context.drain();require(logger.errors.empty()&&s.activeConnections.empty(),"actual queued intentional close ERROR");});
    std::cout<<"RESULT "<<passed<<" passed "<<failed<<" failed\n";
    return failed?1:0;
}
