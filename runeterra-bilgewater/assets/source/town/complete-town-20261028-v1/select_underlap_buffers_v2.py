"""Recover bounded hidden architecture from genuine whole-scene absence paintings.

Outside each declared source-space patch the original full source RGB remains
byte-identical. This is technical protected compositing, never synthesized art.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib
HERE=Path(__file__).resolve().parent
OUT=HERE/'underlap-buffers-v2'
SPECS={
 'dwellingUpLvl5':{'base':'complete-town-native-v3.png','reveal':'revealed-architecture-native-raw-v1.png','delta':[0,0],
   'patches':[[(603,116),(616,118),(630,125),(638,136),(635,144),(625,146),(611,143),(600,136)],
              [(680,124),(691,125),(700,131),(701,139),(696,145),(684,145),(678,139)]],
   'reason':'Foreground independent Buhru serpent heads cover two lower Roost corners. Genuine Temple-absent painted source exposes actual timber/post/deck and terrain; matte must retain only owned architecture.'},
 'dwellingUpLvl4':{'base':'complete-town-native-v3.png','reveal':'buhru-underlap-max-native-v1.png','delta':[0,0],
   'patches':[[(596,191),(606,196),(619,203),(629,211),(635,219),(632,227),(617,229),(603,224),(595,216)]],
   'reason':'Independent Tavern roof obscures lower-left Buhru wall/steps. Genuine Tavern-absent source recovers the same selected temple state without foreign roof pixels.'},
 'citadel':{'base':'intermediate-town-native-raw-v1.png','reveal':'citadel-underlap-native-v1.png','delta':[0,3],
   'patches':[[(127,84),(138,82),(149,86),(158,92),(163,99),(158,104),(142,105),(129,100),(124,92)]],
   'reason':'Foreground independent Leviathan head arc obscures lower Citadel contact/context. Genuine basin-absent source reveals the correct wall/terrace, leaving all other source RGB exact.'}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(exist_ok=True);records={}
    for state,spec in SPECS.items():
        old=Image.open(HERE/spec['base']).convert('RGB');revealed=Image.open(HERE/spec['reveal']).convert('RGB')
        mask=Image.new('L',old.size);draw=ImageDraw.Draw(mask)
        for poly in spec['patches']:draw.polygon(poly,fill=255)
        buffer=Image.composite(revealed,old,mask)
        assert not ImageChops.multiply(ImageChops.difference(buffer,old).convert('L'),ImageChops.invert(mask)).getbbox()
        buffer.save(OUT/(state+'-source.png'));mask.save(OUT/(state+'-underlap-mask.png'))
        records[state]={'source':'assets/source/town/complete-town-20261028-v1/underlap-buffers-v2/'+state+'-source.png',
          'source_sha256':sha(OUT/(state+'-source.png')),'delta':spec['delta'],
          'base_source':'assets/source/town/complete-town-20261028-v1/'+spec['base'],'base_source_sha256':sha(HERE/spec['base']),
          'genuine_reveal_source':'assets/source/town/complete-town-20261028-v1/'+spec['reveal'],'genuine_reveal_source_sha256':sha(HERE/spec['reveal']),
          'mask':'assets/source/town/complete-town-20261028-v1/underlap-buffers-v2/'+state+'-underlap-mask.png','mask_sha256':sha(OUT/(state+'-underlap-mask.png')),
          'patches_in_source_space':spec['patches'],'outside_patch_changed_pixels':0,'reason':spec['reason'],
          'matte_status':'Pending exact-source technical silhouette proposals; these full RGB buffers are not alpha frames or acceptance.'}
    index={'status':'authored configuration','records':records,'native_verified':False,'release_accepted':False}
    (OUT/'source-index.json').write_text(json.dumps(index,indent=2)+'\n')
    print(json.dumps({'source_index_sha256':sha(OUT/'source-index.json'),'records':records},indent=2))
if __name__=='__main__':main()
