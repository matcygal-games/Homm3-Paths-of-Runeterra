int CClient::sendRequest(const SaveGame & pack,PlayerColor player,bool wait) {
  if(!ownerThread) throw std::runtime_error("Request did not execute on its owner thread");
  bool racedAI=false;
  std::thread competingAI([&](){if(CGameState::mutex.try_lock_shared()){CGameState::mutex.unlock_shared();racedAI=true;}});
  competingAI.join();
  if(racedAI)throw std::runtime_error("Headless request raced AI request producers");
  CVCMIServer serverConsumer;static_cast<LobbyInfo&>(serverConsumer)=static_cast<const LobbyInfo&>(GAME->server());
  if(!serverConsumer.hasPlayerAt(player,GAME->server().logicConnection->connectionID))throw std::runtime_error("Not in actual native connection-owned set");
  requests.push_back({pack.fname,pack.notifySuccess,pack.autosaveCountLimit,player.value,wait,false});return 17;
}
int CCallback::sendRequest(const SaveGame & pack) {
  if(!ENGINE)throw std::runtime_error("Human callback has no graphical engine");
  bool racedGUI=false;
  std::thread competingGUI([&](){if(ENGINE->interfaceMutex.try_lock()){ENGINE->interfaceMutex.unlock();racedGUI=true;}});
  competingGUI.join();
  if(racedGUI)throw std::runtime_error("Human command did not serialize with the graphical interface");
  requests.push_back({pack.fname,pack.notifySuccess,pack.autosaveCountLimit,player->value,false,true});return 18;
}
void SaveGame::visitTyped(ICPackVisitor &) {}

static void setup(bool human=false) {
  requests.clear();messages.clear();ownerThread=false;settings.headless=!human;
  GAME=std::make_unique<GameInstance>();ENGINE.reset();
  auto & client=*GAME->server().client;
  auto & server=GAME->server();server.transport=std::make_shared<INetworkConnection>();server.logicConnection->networkConnection=server.transport;server.logicConnection->connectionID=GameConnectionID::FIRST_CONNECTION;server.hostClientId=GameConnectionID::FIRST_CONNECTION;server.si->playerInfos[{0}]={};
  if(human){server.si->playerInfos[{0}].connectedPlayerIDs={PlayerConnectionID::FIRST_HUMAN};server.playerNames[PlayerConnectionID::FIRST_HUMAN].connection=GameConnectionID::FIRST_CONNECTION;}
  client.state->players[{0}]={};
  if(human) {
    ENGINE=std::make_unique<Engine>();GAME->human=std::make_shared<CPlayerInterface>();
    GAME->human->cb=std::make_shared<CCallback>();client.playerint[{0}]=GAME->human;
  } else client.playerint[{0}]=std::make_shared<CGameInterface>();
}
static void command(const std::string & name) {std::istringstream input(name);ClientCommandManager manager;manager.handleSaveCommand(input);}
static void drain() {
  if(ENGINE) ENGINE->drain();
  else if(GAME) { ownerThread=true;GAME->server().network.drain();ownerThread=false; }
}
static void check(bool condition,const char * message) { if(!condition)throw std::runtime_error(message); }
static void noFalseSuccess() {for(const auto & message:messages)check(message.find("Game saved as:")==std::string::npos,"Claimed saved before actual serializer result");}
int main() {
  int total=0,failed=0;
  const auto run=[&](const char * name,const std::function<void()> & fn) {
    ++total;try{fn();std::cout<<"PASS|"<<name<<"\n";}catch(const std::exception &e){++failed;std::cout<<"FAIL|"<<name<<"|"<<e.what()<<"\n";}
  };
  run("headless_owned_ai_native_save_packet",[]{setup();command("Saves/checkpoint");check(requests.empty(),"Submitted inline");drain();check(requests.size()==1,"Expected one headless request");const auto &r=requests[0];check(r.filename=="Saves/checkpoint" && r.player==0 && !r.wait && !r.notify && r.autosaves==0 && !r.human,"Native packet/ownership changed");noFalseSuccess();});
  run("human_callback_preserved_under_interface_mutex",[]{setup(true);command("Saves/human");check(requests.size()==1 && requests[0].human && requests[0].filename=="Saves/human","Human callback bypassed");check(ENGINE->queue.pending.empty(),"Save adopted GUI wake queue");noFalseSuccess();});
  run("held_ai_shared_lock_delays_queued_save_without_deadlock",[]{
    setup();std::shared_lock aiRead(CGameState::mutex);command("Saves/after-ai");
    std::promise<void> started;std::exception_ptr workerError;
    std::thread network([&](){started.set_value();try{drain();}catch(...){workerError=std::current_exception();}});
    started.get_future().wait();std::this_thread::sleep_for(std::chrono::milliseconds(10));
    aiRead.unlock();network.join();if(workerError)std::rethrow_exception(workerError);
    check(requests.size()==1 && requests[0].filename=="Saves/after-ai","Queued save did not resume after AI release");
  });
  run("missing_game_rejected",[]{setup();GAME.reset();command("Saves/checkpoint");check(requests.empty(),"Saved without a game");});
  run("missing_client_at_dispatch_rejected",[]{setup();command("Saves/checkpoint");GAME->server().client.reset();drain();check(requests.empty(),"Saved absent client");});
  run("disconnected_at_dispatch_rejected",[]{setup();command("Saves/checkpoint");GAME->server().state=EClientState::DISCONNECTING;drain();check(requests.empty(),"Saved after disconnect");});
  run("missing_connection_rejected",[]{setup();GAME->server().logicConnection.reset();command("Saves/checkpoint");drain();check(requests.empty(),"Saved absent connection");});
  run("missing_gamestate_rejected",[]{setup();GAME->server().client->state.reset();command("Saves/checkpoint");drain();check(requests.empty(),"Saved absent gamestate");});
  run("replay_observer_rejected",[]{setup();GAME->server().client->observerMode=true;command("Saves/checkpoint");drain();check(requests.empty(),"Saved observer session");});
  run("active_replay_rejected",[]{setup();GAME->server().replay=true;command("Saves/checkpoint");drain();check(requests.empty(),"Saved replay session");});
  run("observer_replaced_after_enqueue_rejected",[]{setup();command("Saves/checkpoint");GAME->server().client->observerMode=true;drain();check(requests.empty(),"Stale observer check");});
  run("foreign_ai_cannot_be_impersonated",[]{setup();GAME->server().hostClientId=static_cast<GameConnectionID>(2);command("Saves/checkpoint");drain();check(requests.empty(),"Used foreign player");});
  run("neutral_ai_cannot_be_impersonated",[]{setup();auto & c=*GAME->server().client;c.playerint.clear();c.playerint[{-1}]=std::make_shared<CGameInterface>();command("Saves/checkpoint");drain();check(requests.empty(),"Used neutral player");});
  run("spectator_interface_cannot_impersonate_human",[]{setup(true);GAME->server().client->playerint.clear();GAME->server().client->playerint[{-2}]=GAME->human;command("Saves/checkpoint");drain();check(requests.empty(),"Used spectator as player");});
  run("missing_human_callback_rejected",[]{setup(true);GAME->human->cb.reset();command("Saves/checkpoint");drain();check(requests.empty(),"Used missing callback");});
  run("foreign_human_callback_rejected",[]{setup(true);GAME->human->cb->player=PlayerColor{1};command("Saves/checkpoint");drain();check(requests.empty(),"Used foreign callback");});
  run("unregistered_human_pointer_rejected",[]{setup(true);GAME->server().client->playerint[{0}]=std::make_shared<CGameInterface>();command("Saves/checkpoint");drain();check(requests.empty(),"Used stale human interface");});
  run("no_owned_ai_interface_rejected",[]{setup();GAME->server().client->playerint[{0}].reset();command("Saves/checkpoint");drain();check(requests.empty(),"Used null AI interface");});
  run("eliminated_ai_skipped_for_live_owned_player",[]{setup();auto & c=*GAME->server().client;c.state->players[{0}].status=EPlayerStatus::LOSER;c.state->players[{1}]={};c.playerint[{1}]=std::make_shared<CGameInterface>();GAME->server().si->playerInfos[{1}]={};command("Saves/checkpoint");drain();check(requests.size()==1 && requests[0].player==1,"Did not use living owned player");});
  run("all_ai_eliminated_rejected",[]{setup();GAME->server().client->state->players[{0}].status=EPlayerStatus::LOSER;command("Saves/checkpoint");drain();check(requests.empty(),"Used eliminated player");});
  run("nonheadless_no_interface_rejected",[]{setup();settings.headless=false;command("Saves/checkpoint");drain();check(requests.empty(),"Broadened nonheadless route");});
  run("empty_filename_rejected",[]{setup();command("");drain();check(requests.empty(),"Accepted empty filename");});
  run("embedded_nul_filename_rejected",[]{setup();command(std::string("Saves/ab\0cd",11));drain();check(requests.empty(),"Accepted embedded NUL filename");});
  run("extra_arguments_rejected",[]{setup();command("Saves/name trailing");drain();check(requests.empty(),"Accepted extra arguments");});
  run("invalid_resource_paths_rejected",[]{for(const auto & name:{"../outside","/absolute","C:/absolute","Saves/../outside","Saves//empty","Saves/","Saves/name?"}){setup();command(name);drain();check(requests.empty(),"Accepted invalid filename");}});
  run("relative_backslash_unicode_filename_preserved",[]{setup();command("Saves\\checkpoint-\xC3\xA9");drain();check(requests.size()==1 && requests[0].filename=="Saves\\checkpoint-\xC3\xA9","Changed valid filename bytes");});
  run("actual_lobby_host_ai_is_not_human_color",[]{setup();auto&s=GAME->server();check(!s.isMyColor({0}),"AI incorrectly has human connection IDs");check(s.getAllClientPlayers(s.logicConnection->connectionID).count({0})==1,"Host AI missing from actual native ownership");});
  run("guest_cannot_adopt_host_ai",[]{setup();GAME->server().hostClientId=static_cast<GameConnectionID>(2);command("Saves/guest");drain();check(requests.empty(),"Guest adopted host AI");});
  run("guest_connected_color_remains_owned",[]{setup();auto&s=GAME->server();s.hostClientId=static_cast<GameConnectionID>(2);s.si->playerInfos[{0}].connectedPlayerIDs={PlayerConnectionID::FIRST_HUMAN};s.playerNames[PlayerConnectionID::FIRST_HUMAN].connection=GameConnectionID::FIRST_CONNECTION;command("Saves/guest-own");drain();check(requests.size()==1&&requests[0].player==0,"Guest direct ownership lost");});
  run("invalid_connection_and_invalid_host_rejected",[]{setup();auto&s=GAME->server();s.logicConnection->connectionID=GameConnectionID::INVALID;s.hostClientId=GameConnectionID::INVALID;command("Saves/invalid");drain();check(requests.empty(),"Default invalid IDs impersonated host");});
  run("queued_host_ownership_revoked",[]{setup();command("Saves/stale");GAME->server().hostClientId=static_cast<GameConnectionID>(2);drain();check(requests.empty(),"Used stale host ownership");});
  run("queued_connection_identity_changed",[]{setup();command("Saves/stale");GAME->server().logicConnection->connectionID=static_cast<GameConnectionID>(2);drain();check(requests.empty(),"Used stale connection ownership");});
  run("connected_human_on_other_connection_not_owned",[]{setup();auto&s=GAME->server();s.hostClientId=static_cast<GameConnectionID>(2);s.si->playerInfos[{0}].connectedPlayerIDs={PlayerConnectionID::FIRST_HUMAN};s.playerNames[PlayerConnectionID::FIRST_HUMAN].connection=static_cast<GameConnectionID>(2);command("Saves/foreign");drain();check(requests.empty(),"Foreign connected human adopted");});
  run("host_missing_direct_color_can_use_next_ai",[]{setup();auto&s=GAME->server();auto&c=*s.client;c.playerint[{0}].reset();c.playerint[{1}]=std::make_shared<CGameInterface>();c.state->players[{1}]={};s.si->playerInfos[{1}]={};command("Saves/next");drain();check(requests.size()==1&&requests[0].player==1,"No host-owned live next AI");});
  run("missing_transport_rejected",[]{setup();GAME->server().transport.reset();command("Saves/no-transport");drain();check(requests.empty(),"Expired weak transport adopted");});
  run("transport_removed_after_enqueue_rejected",[]{setup();command("Saves/lost-transport");GAME->server().transport.reset();drain();check(requests.empty(),"Stale queued transport adopted");});
  std::cout<<"TOTAL|"<<total<<"|"<<failed<<"\n";return failed?1:0;
}
