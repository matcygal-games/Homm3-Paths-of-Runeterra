import pathlib, urllib.request, hashlib, json
root=pathlib.Path('runeterra-targon/engine-patches/turn-lifecycle-20261023-v1'); commit='66fa496c6328a276c4eb14c0011b3a9d751dfac3'
records=[]
for p in ['client/Client.cpp','server/processors/TurnOrderProcessor.cpp','server/CGameHandler.cpp','server/networkPacks/ServerNetPackVisitor.cpp','lib/AsyncRunner.h','lib/network/NetworkConnection.cpp','lib/network/NetworkConnection.h','license.txt']:
 u=f'https://raw.githubusercontent.com/vcmi/vcmi/{commit}/{p}'
 try:
  b=urllib.request.urlopen(u,timeout=20).read(); out=root/'upstream'/p; out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(b)
  records.append({'path':p,'url':u,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
 except Exception as e: records.append({'path':p,'url':u,'error':str(e)})
(root/'additional-provenance.json').write_text(json.dumps(records,indent=2)+'\n'); print(json.dumps(records,indent=2))
