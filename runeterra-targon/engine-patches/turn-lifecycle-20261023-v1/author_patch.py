from pathlib import Path
import difflib, json, hashlib
r=Path(__file__).resolve().parent

def read(p): return (r/'upstream'/p).read_text(encoding='utf-8')
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a))
 return s.replace(a,b)
cpp='AI/Nullkiller2/AIGateway.cpp'; hdr='AI/Nullkiller2/AIGateway.h'; client='client/Client.cpp'
s=read(cpp)
s=replace(s,'''\tif(status.haveTurn())
\t{
\t\tif(pa->packType == CTypeList::getInstance().getTypeID<EndTurn>(nullptr))
\t\t{
\t\t\tif(pa->result)
\t\t\t\tstatus.madeTurn();
\t\t}
\t}''','''\tif(pa->packType == CTypeList::getInstance().getTypeID<EndTurn>(nullptr))
\t\tstatus.receivedEndTurnConfirmation(pa->requestID, pa->result);''')
s=replace(s,'void AIGateway::endTurn()\n{','void AIGateway::endTurn()\n{\n\tconst auto generation = status.getTurnGeneration();')
s=replace(s,'''	do
	{
		cc->endTurn();
	}
	while(status.haveTurn()); //for some reasons, our request may fail -> stop requesting end of turn only after we've received a confirmation that it's over''','''	// A rejected request may be retried, but a newer turn belongs to its own task.
	while(status.haveTurn(generation))
	{
		cc->endTurn();
	}''')
s=replace(s,'\t//BNLOG("I have sent request of type %s", typeid(*pack).name());','''\tif(dynamic_cast<const EndTurn *>(pack))
\t\tstatus.attemptedEndingTurn(requestID);''')
s=replace(s,'\thavingTurn = true;\n\tcv.notify_all();','\t++turnGeneration;\n\thavingTurn = true;\n\tcv.notify_all();')
s=replace(s,'''void AIStatus::madeTurn()
{
\tstd::unique_lock<std::mutex> lock(mx);
\thavingTurn = false;
\tcv.notify_all();
}''','''uint64_t AIStatus::getTurnGeneration()
{
\tstd::unique_lock<std::mutex> lock(mx);
\treturn turnGeneration;
}

bool AIStatus::haveTurn(uint64_t generation)
{
\tstd::unique_lock<std::mutex> lock(mx);
\treturn havingTurn && turnGeneration == generation;
}

void AIStatus::attemptedEndingTurn(int requestID)
{
\tstd::unique_lock<std::mutex> lock(mx);
\tendTurnRequests.emplace(requestID, turnGeneration);
}

void AIStatus::receivedEndTurnConfirmation(int requestID, bool accepted)
{
\tstd::unique_lock<std::mutex> lock(mx);
\tauto request = endTurnRequests.find(requestID);
\tif(request == endTurnRequests.end())
\t\treturn;

\tif(accepted && request->second == turnGeneration)
\t\thavingTurn = false;
\tendTurnRequests.erase(request);
\tcv.notify_all();
}''')
h=read(hdr); h=replace(h,'\tbool havingTurn;','\tbool havingTurn;\n\tuint64_t turnGeneration = 0;\n\tstd::map<int, uint64_t> endTurnRequests;')
h=replace(h,'\tvoid madeTurn();','\tuint64_t getTurnGeneration();\n\tbool haveTurn(uint64_t generation);\n\tvoid attemptedEndingTurn(int requestID);\n\tvoid receivedEndTurnConfirmation(int requestID, bool accepted);')
c=read(client); c=replace(c,'''\tGAME->server().sendGamePack(request);
\tif(vstd::contains(playerint, player))
\t\tplayerint[player]->requestSent(&request, requestID);''','''\t// Register request ownership before transport can deliver a reply or the next turn.
\tif(vstd::contains(playerint, player))
\t\tplayerint[player]->requestSent(&request, requestID);
\tGAME->server().sendGamePack(request);''')
patch=[]; records=[]
for p,t in [(cpp,s),(hdr,h),(client,c)]:
 out=r/'patched'/p; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(t,encoding='utf-8',newline='\n')
 patch.extend(difflib.unified_diff(read(p).splitlines(True),t.splitlines(True),fromfile='a/'+p,tofile='b/'+p))
 records.append({'path':p,'before_sha256':hashlib.sha256((r/'upstream'/p).read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
(r/'0001-bind-end-turn-acknowledgements-to-turn-generation.patch').write_text(''.join(patch),encoding='utf-8',newline='\n')
(r/'patch-inputs.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
