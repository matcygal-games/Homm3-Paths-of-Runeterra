#include "../../../tests/fixture.hpp"
struct DLL_LINKAGE SaveGame : public CPackForServer
{
	SaveGame() = default;
	SaveGame(std::string Fname, bool NotifySuccess, int AutosaveCountLimit = 0)
		: fname(std::move(Fname))
		, notifySuccess(NotifySuccess)
		, autosaveCountLimit(AutosaveCountLimit)
	{
	}
	std::string fname;
	bool notifySuccess = false;
	int autosaveCountLimit = 0;

	void visitTyped(ICPackVisitor & visitor) override;

	template <typename Handler> void serialize(Handler & h)
	{
		h & static_cast<CPackForServer &>(*this);
		h & notifySuccess;
		h & fname;
		h & autosaveCountLimit;
	}
}
;
void CCallback::save(const std::string & fname, bool notifySuccess)
{
	SaveGame save_game(fname, notifySuccess);
	sendRequest(save_game);
}
void ClientCommandManager::handleSaveCommand(std::istringstream & singleWordBuffer)
{
	std::string saveFilename;
	std::string extraArgument;
	if(!(singleWordBuffer >> saveFilename) || (singleWordBuffer >> extraArgument))
	{
		printCommandMessage("Usage: save <relative save filename>");
		return;
	}

	// Resource names may contain directories, but must remain relative to the local filesystem.
	if(saveFilename.front() == '/' || saveFilename.front() == '\\'
		|| saveFilename.find(':') != std::string::npos
		|| saveFilename.find_first_of("\"<>|?*") != std::string::npos
		|| std::any_of(saveFilename.begin(), saveFilename.end(), [](unsigned char value) { return value < ' ' || value == 127; }))
	{
		printCommandMessage("Invalid relative save filename");
		return;
	}
	std::string component;
	std::istringstream pathComponents(boost::replace_all_copy(saveFilename, "\\", "/"));
	while(std::getline(pathComponents, component, '/'))
	{
		if(component.empty() || component == "." || component == "..")
		{
			printCommandMessage("Invalid relative save filename");
			return;
		}
	}
	if(saveFilename.back() == '/' || saveFilename.back() == '\\')
	{
		printCommandMessage("Invalid relative save filename");
		return;
	}

	if(!GAME)
	{
		printCommandMessage("Game is not in playing state");
		return;
	}

	// Reacquire all state on its owner thread. The queued task retains no interface/client pointer.
	const auto submitSave = [saveFilename, fromIngameConsole = currentCallFromIngameConsole]()
	{
		ClientCommandManager output;
		output.currentCallFromIngameConsole = fromIngameConsole;
		if(!GAME || GAME->server().getState() != EClientState::GAMEPLAY
			|| !GAME->server().client || !GAME->server().logicConnection)
		{
			output.printCommandMessage("Game is not in playing state");
			return;
		}
		auto & server = GAME->server();
		auto & client = *server.client;
		if(false || !client.gameStatePtr())
		{
			output.printCommandMessage("Cannot save an observer or replay session");
			return;
		}

		if(auto * interface = GAME->interface())
		{
			const auto player = interface->cb ? interface->cb->getPlayerID() : std::nullopt;
			const auto registered = player ? client.playerint.find(*player) : client.playerint.end();
			if(!player || !player->isValidPlayer() || !server.isMyColor(*player)
				|| registered == client.playerint.end() || registered->second.get() != interface)
			{
				output.printCommandMessage("No owned player interface can save this game");
				return;
			}
			// Preserve the normal human callback and native SaveGame protocol.
			interface->cb->save(saveFilename, false);
			output.printCommandMessage("Save request submitted: " + saveFilename);
			return;
		}

		if(!settings["session"]["headless"].Bool())
		{
			output.printCommandMessage("No owned player interface can save this game");
			return;
		}

		// A headless client owns adventure AI interfaces instead of CPlayerInterface.
		// Keep the server's activity/ownership checks; never impersonate a foreign or neutral player.
		// AI request producers hold a shared game-state lock and release it while awaiting replies.
		// Serialize this new producer without waiting for a response on the network thread.
		std::unique_lock stateLock(CGameState::mutex);
		for(const auto & entry : client.playerint)
		{
			const auto & player = entry.first;
			if(!player.isValidPlayer() || !entry.second || !server.isMyColor(player))
				continue;
			const auto state = client.gameState().players.find(player);
			if(state == client.gameState().players.end() || state->second.status != EPlayerStatus::INGAME)
				continue;
			SaveGame request(saveFilename, false);
			if(client.sendRequest(request, player, false) > 0)
				output.printCommandMessage("Save request submitted: " + saveFilename);
			return;
		}
		output.printCommandMessage("No owned player interface can save this game");
	};

	if(ENGINE)
		ENGINE->dispatchMainThread(submitSave); // GUI tasks already execute under interfaceMutex.
	else
		boost::asio::post(GAME->server().getNetworkHandler().getContext(), submitSave);
}

int CClient::sendRequest(const SaveGame & pack,PlayerColor player,bool wait) {
  if(!ownerThread) throw std::runtime_error("Request did not execute on its owner thread");
  bool racedAI=false;
  std::thread competingAI([&](){if(CGameState::mutex.try_lock_shared()){CGameState::mutex.unlock_shared();racedAI=true;}});
  competingAI.join();
  if(racedAI)throw std::runtime_error("Headless request raced AI request producers");
  requests.push_back({pack.fname,pack.notifySuccess,pack.autosaveCountLimit,player.value,wait,false});return 17;
}
int CCallback::sendRequest(const SaveGame & pack) {
  if(!ownerThread) throw std::runtime_error("Human callback did not execute on GUI owner thread");
  requests.push_back({pack.fname,pack.notifySuccess,pack.autosaveCountLimit,player->value,false,true});return 18;
}
void SaveGame::visitTyped(ICPackVisitor &) {}

static void setup(bool human=false) {
  requests.clear();messages.clear();ownerThread=false;settings.headless=!human;
  GAME=std::make_unique<GameInstance>();ENGINE.reset();
  auto & client=*GAME->server().client;
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
int main(int argc,char ** argv) {
  int total=0,failed=0;
  const auto run=[&](const char * name,const std::function<void()> & fn) {
    ++total;try{fn();std::cout<<"PASS|"<<name<<"\n";}catch(const std::exception &e){++failed;std::cout<<"FAIL|"<<name<<"|"<<e.what()<<"\n";}
  };
  // The upstream baseline is exercised without dereferencing a null pointer: a human
  // control exposes immediate wrong-thread submission and false completion reporting.
  if(argc>1 && std::string(argv[1])=="upstream") {
    run("baseline_human_submission_is_not_scheduled",[]{ setup(true);command("Saves/control");check(requests.empty(),"Submitted inline instead of scheduling");});
    std::cout<<"TOTAL|"<<total<<"|"<<failed<<"\n";return failed?1:0;
  }
  run("headless_owned_ai_native_save_packet",[]{setup();command("Saves/checkpoint");check(requests.empty(),"Submitted inline");drain();check(requests.size()==1,"Expected one headless request");const auto &r=requests[0];check(r.filename=="Saves/checkpoint" && r.player==0 && !r.wait && !r.notify && r.autosaves==0 && !r.human,"Native packet/ownership changed");noFalseSuccess();});
  run("human_callback_preserved_on_gui_owner_thread",[]{setup(true);command("Saves/human");check(requests.empty(),"Submitted inline");drain();check(requests.size()==1 && requests[0].human && requests[0].filename=="Saves/human","Human callback bypassed");noFalseSuccess();});
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
  run("observer_replaced_after_enqueue_rejected",[]{setup(true);command("Saves/checkpoint");GAME->server().client->observerMode=true;drain();check(requests.empty(),"Stale observer check");});
  run("foreign_ai_cannot_be_impersonated",[]{setup();GAME->server().owned={{1}};command("Saves/checkpoint");drain();check(requests.empty(),"Used foreign player");});
  run("neutral_ai_cannot_be_impersonated",[]{setup();auto & c=*GAME->server().client;c.playerint.clear();c.playerint[{-1}]=std::make_shared<CGameInterface>();GAME->server().owned={{-1}};command("Saves/checkpoint");drain();check(requests.empty(),"Used neutral player");});
  run("spectator_interface_cannot_impersonate_human",[]{setup(true);GAME->server().client->playerint.clear();GAME->server().client->playerint[{-2}]=GAME->human;command("Saves/checkpoint");drain();check(requests.empty(),"Used spectator as player");});
  run("missing_human_callback_rejected",[]{setup(true);GAME->human->cb.reset();command("Saves/checkpoint");drain();check(requests.empty(),"Used missing callback");});
  run("foreign_human_callback_rejected",[]{setup(true);GAME->human->cb->player=PlayerColor{1};command("Saves/checkpoint");drain();check(requests.empty(),"Used foreign callback");});
  run("unregistered_human_pointer_rejected",[]{setup(true);GAME->server().client->playerint[{0}]=std::make_shared<CGameInterface>();command("Saves/checkpoint");drain();check(requests.empty(),"Used stale human interface");});
  run("no_owned_ai_interface_rejected",[]{setup();GAME->server().client->playerint[{0}].reset();command("Saves/checkpoint");drain();check(requests.empty(),"Used null AI interface");});
  run("eliminated_ai_skipped_for_live_owned_player",[]{setup();auto & c=*GAME->server().client;c.state->players[{0}].status=EPlayerStatus::LOSER;c.state->players[{1}]={};c.playerint[{1}]=std::make_shared<CGameInterface>();GAME->server().owned.insert({1});command("Saves/checkpoint");drain();check(requests.size()==1 && requests[0].player==1,"Did not use living owned player");});
  run("all_ai_eliminated_rejected",[]{setup();GAME->server().client->state->players[{0}].status=EPlayerStatus::LOSER;command("Saves/checkpoint");drain();check(requests.empty(),"Used eliminated player");});
  run("nonheadless_no_interface_rejected",[]{setup();settings.headless=false;command("Saves/checkpoint");drain();check(requests.empty(),"Broadened nonheadless route");});
  run("empty_filename_rejected",[]{setup();command("");drain();check(requests.empty(),"Accepted empty filename");});
  run("embedded_nul_filename_rejected",[]{setup();command(std::string("Saves/ab\0cd",11));drain();check(requests.empty(),"Accepted embedded NUL filename");});
  run("extra_arguments_rejected",[]{setup();command("Saves/name trailing");drain();check(requests.empty(),"Accepted extra arguments");});
  run("invalid_resource_paths_rejected",[]{for(const auto & name:{"../outside","/absolute","C:/absolute","Saves/../outside","Saves//empty","Saves/","Saves/name?"}){setup();command(name);drain();check(requests.empty(),"Accepted invalid filename");}});
  run("relative_backslash_unicode_filename_preserved",[]{setup();command("Saves\\checkpoint-\xC3\xA9");drain();check(requests.size()==1 && requests[0].filename=="Saves\\checkpoint-\xC3\xA9","Changed valid filename bytes");});
  std::cout<<"TOTAL|"<<total<<"|"<<failed<<"\n";return failed?1:0;
}
