// Dependency fixtures for copied actual consumers; not a VCMI runtime.
#pragma once
#include <algorithm>
#include <atomic>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <shared_mutex>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <vector>
#include <stdexcept>
#include <utility>
#include <thread>
#include <future>
#include <chrono>
#define DLL_LINKAGE
struct ICPackVisitor {};
struct CPackForServer { virtual ~CPackForServer()=default; virtual void visitTyped(ICPackVisitor&)=0; };
struct PlayerColor {
  int value=0;
  bool isValidPlayer() const { return value>=0 && value<8; }
  bool operator<(PlayerColor other) const { return value<other.value; }
  bool operator==(PlayerColor other) const { return value==other.value; }
};
enum class EPlayerStatus { INGAME, LOSER, WINNER };
enum class EClientState { NONE, GAMEPLAY, DISCONNECTING };
struct CGameInterface { virtual ~CGameInterface()=default; };
struct PlayerState { EPlayerStatus status=EPlayerStatus::INGAME; };
struct CGameState { inline static std::shared_mutex mutex; std::map<PlayerColor,PlayerState> players; };
struct CCallback;
struct CPlayerInterface : CGameInterface { std::shared_ptr<CCallback> cb; };
struct Queue {
  std::vector<std::function<void()>> pending;
  void post(std::function<void()> fn) { pending.push_back(std::move(fn)); }
  void drain() { auto copy=std::move(pending); pending.clear(); for(auto & fn:copy) fn(); }
};
namespace boost {
  inline std::string replace_all_copy(std::string text,const std::string & before,const std::string & after) {
    size_t pos=0; while((pos=text.find(before,pos))!=std::string::npos){text.replace(pos,before.size(),after);pos+=after.size();} return text;
  }
  namespace asio { inline void post(Queue & queue,std::function<void()> fn){ queue.post(std::move(fn)); } }
}
struct Request { std::string filename; bool notify=false; int autosaves=0; int player=-1; bool wait=false; bool human=false; };
inline std::vector<Request> requests;
inline std::vector<std::string> messages;
inline bool ownerThread=false;
struct CClient {
  std::atomic<bool> observerMode=false;
  std::map<PlayerColor,std::shared_ptr<CGameInterface>> playerint;
  std::shared_ptr<CGameState> state=std::make_shared<CGameState>();
  std::shared_ptr<CGameState> gameStatePtr() {return state;}
  CGameState & gameState(){return *state;}
  int sendRequest(const struct SaveGame &,PlayerColor,bool);
};
struct CCallback {
  std::optional<PlayerColor> player=PlayerColor{0};
  std::optional<PlayerColor> getPlayerID() const{return player;}
  int sendRequest(const struct SaveGame &);
  void save(const std::string &,bool);
};
struct Server {
  EClientState state=EClientState::GAMEPLAY;
  std::unique_ptr<CClient> client=std::make_unique<CClient>();
  std::shared_ptr<int> logicConnection=std::make_shared<int>(1);
  std::set<PlayerColor> owned={PlayerColor{0}};
  Queue network;
  bool replay=false;
  EClientState getState() const{return state;}
  bool isMyColor(PlayerColor p) const{return owned.count(p)!=0;}
  bool isReplayActive() const{return replay;}
  Server & getNetworkHandler(){return *this;}
  Queue & getContext(){return network;}
};
struct GameInstance {
  Server currentServer;
  std::shared_ptr<CPlayerInterface> human;
  Server & server(){return currentServer;}
  CPlayerInterface * interface(){return human.get();}
};
struct Engine {
  Queue queue;
  std::mutex interfaceMutex;
  void dispatchMainThread(std::function<void()> fn){queue.post(std::move(fn));}
  void drain(){std::scoped_lock lock(interfaceMutex);ownerThread=true;queue.drain();ownerThread=false;}
};
inline std::unique_ptr<GameInstance> GAME;
inline std::unique_ptr<Engine> ENGINE;
struct Setting {
  bool headless=true;
  Setting & operator[](const char*){return *this;}
  bool Bool() const{return headless;}
};
inline Setting settings;
class ClientCommandManager {
public:
  bool currentCallFromIngameConsole=false;
  void handleSaveCommand(std::istringstream &);
  void printCommandMessage(const std::string & text){messages.push_back(text);}
};
