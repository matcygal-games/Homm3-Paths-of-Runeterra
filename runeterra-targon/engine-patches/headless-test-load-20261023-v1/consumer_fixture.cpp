// Isolated copied-consumer fixture. This is not a native VCMI reload.
#include <map>
#include <set>
#include <vector>
#include <string>
#include <memory>
#include <chrono>
#include <stdexcept>
#include <iostream>
#include <utility>
static int sleeps=0;
namespace std { namespace this_thread { template<class T> void sleep_for(T) { if(++sleeps>100) throw runtime_error("fixture bounded poll exceeded"); } } }
struct PlayerColor {
 int num;explicit PlayerColor(int n=0):num(n){};static constexpr int PLAYER_LIMIT_I=8;
 static const PlayerColor CANNOT_DETERMINE;
 bool isValidPlayer()const;std::string toString()const{return isValidPlayer()?std::to_string(num):"invalid";}
 bool operator<(PlayerColor o)const{return num<o.num;}bool operator!=(PlayerColor o)const{return num!=o.num;}bool operator==(PlayerColor o)const{return num==o.num;}
};
const PlayerColor PlayerColor::CANNOT_DETERMINE(-3);
#include "extracted/valid_color.inc"
enum class PlayerConnectionID:int {INVALID=-1,PLAYER_AI=0,HUMAN=1,REMOTE=2};
using GameConnectionID=int;
namespace vstd {template<class T,class K>bool contains(const T& t,const K& k){return t.find(k)!=t.end();}}
struct PlayerSettings {PlayerColor color;std::string name;std::set<PlayerConnectionID> connectedPlayerIDs;bool compOnly=false;bool isControlledByHuman()const{return !connectedPlayerIDs.empty();}};
struct StartInfo {std::map<PlayerColor,PlayerSettings> playerInfos;};
struct ClientPlayer {GameConnectionID connection;std::string name;};
struct LobbyInfo {
 std::shared_ptr<StartInfo> si=std::make_shared<StartInfo>();std::map<PlayerConnectionID,ClientPlayer> playerNames;
 PlayerColor clientFirstColor(GameConnectionID)const;bool isClientColor(GameConnectionID,const PlayerColor&)const;
};
#include "extracted/client_first.inc"
#include "extracted/is_client.inc"
struct Log {std::vector<std::string> errors;template<class... T>void info(const char*,T...){}template<class... T>void debug(const char*,T...){}template<class... T>void error(const char* format,T...){errors.emplace_back(format);}} logObject;
Log*logGlobal=&logObject;
struct Texts {std::vector<std::string>allTexts=std::vector<std::string>(469,"Computer");};
struct Library {Texts*generaltexth;};Texts textObject;Library library{&textObject};Library*LIBRARY=&library;
struct State {bool vanquished=false;int heroes=1,towns=0;bool checkVanquished()const{return vanquished;}};
struct Info {std::map<PlayerColor,State> players;const State*tryGetPlayerState(PlayerColor c)const{auto it=players.find(c);return it==players.end()?nullptr:&it->second;}};
struct FakeHandler {Info info;Info&gameInfo(){return info;}};
struct MetaString {static std::string createFromTextID(const char*x){return x;}};
struct CVCMIServer:LobbyInfo {
 std::shared_ptr<FakeHandler>newGH=std::make_shared<FakeHandler>();
 void setPlayerConnectedId(PlayerSettings&,PlayerConnectionID)const;void setPlayer(PlayerColor);bool validatePlayers();
 PlayerConnectionID getIdOfFirstUnallocatedPlayer()const{for(auto&[id,value]:playerNames){bool found=false;for(auto&[c,p]:si->playerInfos)found|=vstd::contains(p.connectedPlayerIDs,id);if(!found)return id;}return PlayerConnectionID::PLAYER_AI;}
};
#include "extracted/connected.inc"
// Exact prefix through the connection assignment; avoid executing the known
// unrelated empty-AI-set dereference in the remainder of the legacy method.
#include "extracted/server_set_prefix.inc"
#include "extracted/validation.inc"
enum class EStartMode {LOAD_GAME,NEW_GAME};enum class ESelectionScreen{loadGame,newGame};enum class EServerMode{LOCAL};enum class EResType{SAVEGAME};
struct ResourcePath {std::string value;ResourcePath(std::string s,EResType):value(s){}};
struct CMapInfo {std::string fileURI;void saveInit(ResourcePath p){fileURI=p.value;}void mapInit(std::string s){fileURI=s;}};
struct Setting {std::string key,value;Setting operator[](const char*k)const{return {k,{}};}bool Bool()const{return key=="headless";}std::string&String(){return value;}}settings;
struct CLobbyScreen{};struct Windows {template<class T>bool topWindow(){return true;}};
struct Engine {Windows value;Windows&windows(){return value;}}engine;Engine*ENGINE=&engine;
struct Logic {int connectionID=1;};struct LobbySetPlayer {PlayerColor clickedColor;};
struct CServerHandler:LobbyInfo {
 CVCMIServer&server;std::shared_ptr<CMapInfo>mi;Logic logic;Logic*logicConnection=&logic;std::vector<PlayerColor>sent;int starts=0;bool started=false;EStartMode mode=EStartMode::LOAD_GAME;
 explicit CServerHandler(CVCMIServer&s):server(s){si=s.si;playerNames=s.playerNames;}
 PlayerColor myFirstColor()const;void setPlayer(PlayerColor)const;
 void sendLobbyPack(LobbySetPlayer p)const{auto*self=const_cast<CServerHandler*>(this);self->sent.push_back(p.clickedColor);server.setPlayer(p.clickedColor);}
 void resetStateForLobby(EStartMode m,ESelectionScreen,EServerMode,std::initializer_list<int>){mode=m;}
 std::string getLocalHostname(){return "localhost";}int getLocalPort(){return 0;}void connectToServer(std::string,int){}void startLocalServerAndConnect(bool){}
 void setMapInfo(std::shared_ptr<CMapInfo>v){mi=v;}void sendStartGame(){++starts;started=server.validatePlayers();}
 void debugStartTest(std::string,bool);void debugStartTestBaseline(std::string,bool);void debugStartTestNeverClick(std::string,bool);void debugStartTestInverted(std::string,bool);
};
#include "extracted/client_my.inc"
#include "extracted/client_set.inc"
#define debugStartTest debugStartTestBaseline
#include "extracted/debug_before.inc"
#undef debugStartTest
#include "extracted/debug_after.inc"
#define debugStartTest debugStartTestNeverClick
#include "extracted/debug_never.inc"
#undef debugStartTest
#define debugStartTest debugStartTestInverted
#include "extracted/debug_inverted.inc"
#undef debugStartTest

static int controls=0;
void require(bool condition,const char*message){if(!condition)throw std::runtime_error(message);}
CVCMIServer setup(bool human,int color=0,bool remote=false) {
 CVCMIServer s;s.playerNames[PlayerConnectionID::HUMAN]={1,"Local"};if(remote)s.playerNames[PlayerConnectionID::REMOTE]={2,"Remote"};
 PlayerSettings seat;seat.color=PlayerColor(color);seat.name="Saved player";if(human)seat.connectedPlayerIDs.insert(remote?PlayerConnectionID::REMOTE:PlayerConnectionID::HUMAN);
 s.si->playerInfos.emplace(PlayerColor(color),seat);s.newGH->info.players.emplace(PlayerColor(color),State{});return s;
}
using Route=void(CServerHandler::*)(std::string,bool);
bool repairedCase(Route route,bool human,bool save,int color=0,bool remote=false) {
 sleeps=0;logObject.errors.clear();auto server=setup(human,color,remote);CServerHandler client(server);const auto originalState=server.newGH->info.players.at(PlayerColor(color));
 try{(client.*route)(save?"Saves/authentic":"Maps/typical",save);}catch(...){return false;}
 const bool ownHuman=human&&!remote;
 return client.started&&client.starts==1&&server.si->playerInfos.size()==1&&!server.si->playerInfos.count(PlayerColor::CANNOT_DETERMINE)&&client.sent.size()==(ownHuman?1u:0u)&&(!ownHuman||client.sent.front()==PlayerColor(color))&&server.si->playerInfos.at(PlayerColor(color)).isControlledByHuman()==(human&&remote)&&logObject.errors.empty()&&server.newGH->info.players.at(PlayerColor(color)).heroes==originalState.heroes&&server.newGH->info.players.at(PlayerColor(color)).towns==originalState.towns&&client.mode==(save?EStartMode::LOAD_GAME:EStartMode::NEW_GAME);
}
int main(){try{
 // Execute the original invalid request through the copied receiver prefix and
 // unchanged real startup rejection: the phantom human seat reproduces failure.
 {sleeps=0;logObject.errors.clear();auto server=setup(false);CServerHandler client(server);client.debugStartTestBaseline("Saves/authentic",true);require(client.sent.size()==1&&client.sent[0]==PlayerColor::CANNOT_DETERMINE,"baseline missing invalid request");require(server.si->playerInfos.count(PlayerColor::CANNOT_DETERMINE)&&server.si->playerInfos.at(PlayerColor::CANNOT_DETERMINE).isControlledByHuman(),"baseline missing phantom human");require(!client.started&&logObject.errors.size()==1&&logObject.errors[0].find("Human player %s has no heroes and no towns!")!=std::string::npos,"baseline must retain actual rejection");++controls;}
 require(repairedCase(&CServerHandler::debugStartTest,false,true),"all-AI load failed");++controls;
 require(repairedCase(&CServerHandler::debugStartTest,false,true,7),"spectator/no-owned-seat load failed");++controls;
 require(repairedCase(&CServerHandler::debugStartTest,true,true),"human load unseat changed");++controls;
 require(repairedCase(&CServerHandler::debugStartTest,true,false),"human new-game unseat changed");++controls;
 require(repairedCase(&CServerHandler::debugStartTest,false,false),"all-AI new-game failed");++controls;
 for(int color=0;color<8;++color)require(repairedCase(&CServerHandler::debugStartTest,true,true,color),"valid color unseat changed");++controls;
 require(repairedCase(&CServerHandler::debugStartTest,true,true,0,true),"remote human ownership changed");++controls;
 {logObject.errors.clear();auto s=setup(true);require(s.validatePlayers()&&s.si->playerInfos.at(PlayerColor(0)).isControlledByHuman(),"ordinary human load changed");++controls;}
 {logObject.errors.clear();auto s=setup(true);s.newGH->info.players.at(PlayerColor(0)).vanquished=true;require(!s.validatePlayers()&&!logObject.errors.empty(),"eliminated human rejection waived");++controls;}
 {logObject.errors.clear();auto s=setup(false);PlayerSettings bad;bad.connectedPlayerIDs.insert(PlayerConnectionID::HUMAN);s.si->playerInfos.emplace(PlayerColor::CANNOT_DETERMINE,bad);require(!s.validatePlayers()&&!logObject.errors.empty(),"existing invalid human rejection waived");++controls;}
 // Mutants must be detected by externally visible startup/wire outcomes.
 require(!repairedCase(&CServerHandler::debugStartTestBaseline,false,true),"always-click mutant survived");++controls;
 require(!repairedCase(&CServerHandler::debugStartTestNeverClick,true,true),"never-click mutant survived");++controls;
 require(!repairedCase(&CServerHandler::debugStartTestInverted,false,true)&&!repairedCase(&CServerHandler::debugStartTestInverted,true,true),"inverted guard mutant survived");++controls;
 // Valid AI-seat selection remains supported by the unchanged receiver prefix.
 {auto s=setup(false);s.setPlayer(PlayerColor(0));require(s.si->playerInfos.size()==1&&s.si->playerInfos.at(PlayerColor(0)).isControlledByHuman(),"valid AI click changed");++controls;}
 std::cout<<"PASS "<<controls<<" copied-consumer controls; baseline invalid-seat rejection reproduced; 3 mutants killed; no native reload executed\n";return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL after "<<controls<<" controls: "<<e.what()<<"\n";return 2;}}
