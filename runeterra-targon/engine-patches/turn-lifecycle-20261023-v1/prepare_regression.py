from pathlib import Path
import json, hashlib
r=Path(__file__).resolve().parent

def extract(text, prefix):
 start=text.index(prefix); brace=text.index('{',start); depth=1; pos=brace+1
 while depth:
  if text[pos]=='{': depth+=1
  elif text[pos]=='}': depth-=1
  pos+=1
 return text[start:pos]+'\n'

pre=r'''#include <atomic>
#include <condition_variable>
#include <cstdint>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <vector>
#include <algorithm>
#define LOG_TRACE(...) do {} while(false)
#define LOG_TRACE_PARAMS(...) do {} while(false)
struct Logger { int errors=0; template<class... T> void error(T...){++errors;} template<class... T> void info(T...){} template<class... T> void debug(T...){} template<class... T> void trace(T...){} template<class... T> void warn(T...){} } logger;
auto logAi=&logger; auto logGlobal=&logger; auto logNetwork=&logger;
using ui32=uint32_t; struct CGObjectInstance; using QuestionID=int; using ObjectInstanceID=int; struct TryMoveHero{};
enum BattleState { NO_BATTLE }; struct AIGateway;
'''
post=r'''
struct CPackForServer { virtual ~CPackForServer()=default; mutable uint32_t requestID=0; mutable int player=0; };
struct EndTurn:CPackForServer{}; struct CastAdvSpell:CPackForServer{}; struct QuestionAnswer:CPackForServer{ int questionID=0; };
struct PackageApplied{int packType; bool result; uint32_t requestID; int player=0;};
struct CTypeList { static CTypeList& getInstance(){static CTypeList t;return t;} template<class T> int getTypeID(T*){ if constexpr(std::is_same_v<T,EndTurn>)return 1; if constexpr(std::is_same_v<T,CastAdvSpell>)return 2; return 3;} };
struct Player{int value=0; operator int()const{return value;} std::string toString()const{return "red";}};
enum class EPlayerStatus{INGAME,LOST}; struct Resource{std::string toString(){return "resources";}};
struct Callback { int calls=0; EPlayerStatus playerStatus=EPlayerStatus::INGAME; std::function<void()> send;
 void endTurn(){++calls;if(calls>8)throw std::runtime_error("EndTurn retry escaped its generation");send();}
 Resource getResourceAmount(){return {};} EPlayerStatus getPlayerStatus(Player){return playerStatus;} };
struct Interrupt {void reset(){}}; struct Nullkiller{Interrupt makingTurnInterruption;void invalidatePathfinderData(){}};
struct AsyncRunner{std::vector<std::function<void()>> pending; void run(std::function<void()> f){pending.push_back(f);}};
struct AIGateway { AIStatus status{this}; Player playerID; std::shared_ptr<Callback> cc=std::make_shared<Callback>(); std::unique_ptr<Nullkiller> nullkiller=std::make_unique<Nullkiller>(); std::unique_ptr<AsyncRunner> asyncTasks=std::make_unique<AsyncRunner>(); bool lastAdventureCastSucceeded=true;
 int waits=0, makes=0; std::function<void()> waitHook; void waitTillFree(){++waits;if(waitHook)waitHook();} void makeTurn(){++makes;} void answerQuestion(int,int){} void executeActionAsync(const std::string&,std::function<void()> f){f();}
 void requestRealized(PackageApplied*);void requestSent(const CPackForServer*,int);void yourTurn(QuestionID);void endTurn();};
struct ScopedThreadName{ScopedThreadName(const char*){}};
void AIStatus::attemptedAnsweringQuestion(int,int){} void AIStatus::addQuestion(QuestionID,std::string){} void AIStatus::receivedAnswerConfirmation(int,int){} void AIStatus::waitTillFree(){}
namespace vstd {template<class C,class K> bool contains(C const& c,K const& k){return c.find(k)!=c.end();} int makeUnlockSharedGuard(int&){return 0;}}
struct CGameState {static int mutex;}; int CGameState::mutex=0;
struct Waiting{std::vector<int> ids;void pushBack(int i){ids.push_back(i);}void waitWhileContains(int i){if(std::find(ids.begin(),ids.end(),i)!=ids.end())throw std::runtime_error("lost ACK");}bool tryRemovingElement(int i){auto it=std::find(ids.begin(),ids.end(),i);if(it==ids.end())return false;ids.erase(it);return true;}};
struct Server {std::function<void(const CPackForServer&)> send;void sendGamePack(const CPackForServer& p){send(p);}};
struct Game{Server s; Server& server(){return s;}} game; auto GAME=&game;
using PlayerColor=int;
struct CClient {bool observerMode=false;unsigned requestCounter=1;Waiting waitingRequest;std::map<int,AIGateway*> playerint;int sendRequest(const CPackForServer&,PlayerColor,bool);};
struct IGameEventsReceiver {void requestRealized(PackageApplied*){}};
template<class Method>void callInterfaceIfPresent(CClient&cl,int p,Method,PackageApplied*pa){if(cl.playerint.count(p))cl.playerint[p]->requestRealized(pa);}
struct ApplyClientNetPackVisitor{CClient&cl;void visitPackageApplied(PackageApplied&);};
'''
tests=r'''
int failures=0,cases=0; void check(bool b,const char* msg){++cases;if(!b){++failures;std::cout<<"FAIL "<<msg<<"\n";}else std::cout<<"PASS "<<msg<<"\n";}
void begin(AIGateway&g){g.yourTurn(10);}
void ack(AIGateway&g,int id,bool ok=true){PackageApplied pa{1,ok,static_cast<uint32_t>(id)};g.requestRealized(&pa);}
void submit(AIGateway&g,int id){EndTurn p;g.requestSent(&p,id);}
int main(){
 {AIGateway g;begin(g);submit(g,1);ack(g,1);check(!g.status.haveTurn(),"accepted current request ends current turn");}
 {AIGateway g;begin(g);submit(g,1);ack(g,1,false);check(g.status.haveTurn(),"rejected request preserves turn");}
 {AIGateway g;begin(g);submit(g,1);begin(g);ack(g,1);check(g.status.haveTurn(),"old accepted ACK cannot clear new turn");}
 {AIGateway g;begin(g);submit(g,1);ack(g,1);begin(g);ack(g,1);check(g.status.haveTurn(),"duplicate ACK cannot clear new turn");}
 {AIGateway g;begin(g);ack(g,999);check(g.status.haveTurn(),"unknown EndTurn ACK cannot clear active turn");}
 {AIGateway g;begin(g);submit(g,1);begin(g);ack(g,1,false);check(g.status.haveTurn(),"old rejected ACK leaves new turn active");}
 {AIGateway g;begin(g);submit(g,1);PackageApplied p{2,false,1};g.requestRealized(&p);check(g.status.haveTurn()&&!g.lastAdventureCastSucceeded,"spell rejection retains its separate result and turn");}
 {AIGateway g;begin(g);g.cc->send=[&]{submit(g,g.cc->calls);ack(g,g.cc->calls,g.cc->calls>1);};g.endTurn();check(g.cc->calls==2&&!g.status.haveTurn(),"rejected EndTurn retries until same generation accepted");}
 {AIGateway g;begin(g);g.cc->playerStatus=EPlayerStatus::LOST;g.cc->send=[]{};g.endTurn();check(g.cc->calls==0&&g.waits==1,"defeated player waits for battle cleanup without requesting turn end");}
 {AIGateway g;begin(g);int newTaskAt=g.makes;g.cc->send=[&]{submit(g,g.cc->calls);begin(g);ack(g,g.cc->calls);};try{g.endTurn();check(g.cc->calls==1&&g.status.haveTurn()&&g.asyncTasks->pending.size()==2&&g.makes==newTaskAt,"same-player new turn before ACK neither retries old task nor clears new task");}catch(const std::exception&e){check(false,"same-player new turn before ACK must not loop");}}
 {AIGateway g;begin(g);g.cc->send=[&]{submit(g,g.cc->calls);ack(g,g.cc->calls);begin(g);};try{g.endTurn();check(g.cc->calls==1&&g.status.haveTurn(),"ACK followed by new turn before callback returns cannot trigger old retry");}catch(const std::exception&e){check(false,"ACK then new turn must not loop");}}
 {AIGateway g;begin(g);CClient cl;cl.playerint[0]=&g;ApplyClientNetPackVisitor visitor{cl};game.s.send=[&](const CPackForServer&p){PackageApplied pa{1,true,p.requestID,p.player};visitor.visitPackageApplied(pa);};EndTurn p;cl.sendRequest(p,0,true);check(!g.status.haveTurn()&&cl.waitingRequest.ids.empty(),"immediate transport ACK sees registered request before waiting caller resumes");}
 {AIGateway g;begin(g);CClient cl;cl.playerint[0]=&g;ApplyClientNetPackVisitor visitor{cl};game.s.send=[&](const CPackForServer&p){begin(g);PackageApplied pa{1,true,p.requestID,p.player};visitor.visitPackageApplied(pa);};EndTurn p;cl.sendRequest(p,0,true);check(g.status.haveTurn()&&cl.waitingRequest.ids.empty(),"immediate new-turn transport reentry preserves new generation");}
 {AIGateway g;begin(g);CClient cl;cl.playerint[0]=&g;cl.observerMode=true;int sent=0;game.s.send=[&](const CPackForServer&){++sent;};EndTurn p;cl.sendRequest(p,0,true);check(sent==0&&cl.waitingRequest.ids.empty()&&g.status.haveTurn(),"observer path drops request without registering ownership");}
 {AIGateway g;begin(g);g.waitHook=[&]{begin(g);};g.cc->send=[&]{submit(g,g.cc->calls);ack(g,g.cc->calls);};g.endTurn();check(g.cc->calls==0&&g.status.haveTurn(),"turn replaced during cleanup wait cannot submit from the old task");}
 std::cout<<"RESULT "<<cases<<" cases "<<failures<<" failures\n";return failures?1:0;
}
'''
for variant in ['upstream','patched']:
 cpp=(r/variant/'AI/Nullkiller2/AIGateway.cpp').read_text();hdr=(r/variant/'AI/Nullkiller2/AIGateway.h').read_text();client=(r/variant/'client/Client.cpp').read_text();visitor=(r/'upstream/client/NetPacksClient.cpp').read_text()
 cls=extract(hdr,'class AIStatus')+';\n'
 methods=['AIStatus::AIStatus(', 'AIStatus::~AIStatus()', 'void AIStatus::startedTurn()', 'bool AIStatus::haveTurn()', 'void AIGateway::requestRealized(', 'void AIGateway::requestSent(', 'void AIGateway::yourTurn(', 'void AIGateway::endTurn()']
 if variant=='patched':methods+=['uint64_t AIStatus::getTurnGeneration()', 'bool AIStatus::haveTurn(uint64_t', 'void AIStatus::attemptedEndingTurn(', 'void AIStatus::receivedEndTurnConfirmation(']
 else:methods+=['void AIStatus::madeTurn()']
 content=pre+cls+post+'\n'.join(extract(cpp,m) for m in methods)+extract(client,'int CClient::sendRequest(')+extract(visitor,'void ApplyClientNetPackVisitor::visitPackageApplied(')+tests
 out=r/'tests'/variant/'consumer_regression.cpp';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(content,encoding='utf-8',newline='\n')
print('Wrote actual consumer extractions for upstream and patched variants')
