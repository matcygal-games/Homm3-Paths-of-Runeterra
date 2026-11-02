import urllib.request, pathlib, json, hashlib, datetime
root=pathlib.Path('runeterra-targon/engine-patches/turn-lifecycle-20261023-v1'); commit='66fa496c6328a276c4eb14c0011b3a9d751dfac3'
paths=['AI/Nullkiller2/AIGateway.cpp','AI/Nullkiller2/AIGateway.h','lib/callback/CCallback.cpp','client/NetPacksClient.cpp','server/CVCMIServer.cpp','server/CVCMIServer.h','server/TurnOrderProcessor.cpp','lib/networkPacks/PacksForClient.h','client/CClient.cpp']
records=[]
for path in paths:
 url=f'https://raw.githubusercontent.com/vcmi/vcmi/{commit}/{path}'
 try:
  with urllib.request.urlopen(url,timeout=25) as r: body=r.read(); status=r.status
 except Exception as e: records.append({'path':path,'url':url,'error':str(e)}); continue
 out=root/'upstream'/path; out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(body)
 local=pathlib.Path('vcmi-develop/vcmi-develop')/path
 records.append({'path':path,'url':url,'status':status,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'local_sha256':hashlib.sha256(local.read_bytes()).hexdigest() if local.exists() else None})
try:
 url=f'https://api.github.com/repos/vcmi/vcmi/commits/{commit}'
 req=urllib.request.Request(url,headers={'User-Agent':'Runeterra-Targon-source-provenance'})
 body=urllib.request.urlopen(req,timeout=25).read(); (root/'official-commit.json').write_bytes(body)
 meta={'url':url,'sha256':hashlib.sha256(body).hexdigest(),'returned_sha':json.loads(body)['sha']}
except Exception as e: meta={'error':str(e)}
(root/'provenance.json').write_text(json.dumps({'commit':commit,'access_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'metadata':meta,'sources':records},indent=2)+'\n')
print(json.dumps({'metadata':meta,'sources':records},indent=2))
