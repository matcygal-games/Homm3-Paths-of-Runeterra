"""Select only existing cloth surfaces from genuine official-crest painted edit."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import hashlib,json
HERE=Path(__file__).resolve().parent
CLOTH={
 'castle_left':[(168,43),(181,44),(181,73),(174,84),(168,77)],
 'castle_right':[(249,58),(258,60),(257,85),(252,91),(249,85)],
 'civic_left':[(368,93),(378,95),(378,116),(373,124),(367,119)],
 'civic_right':[(406,96),(414,98),(413,118),(408,124),(404,118)],
 'guild':[(501,83),(510,85),(510,111),(504,120),(500,114)],
 'cannon':[(308,143),(317,145),(316,171),(312,179),(307,173)],
 'treasury_left':[(449,153),(457,155),(457,177),(453,185),(449,180)],
 'treasury_right':[(511,156),(519,157),(518,180),(514,187),(511,182)],
 'fleet':[(557,110),(566,112),(566,134),(560,145),(556,137)],
 'fleet_pennant':[(556,58),(565,61),(577,66),(578,71),(567,69),(557,64)],
 'black_market':[(9,249),(27,252),(25,282),(18,294),(9,286)],
 'tavern':[(540,196),(557,198),(554,233),(547,248),(539,238)],
 'middle_street':[(372,170),(382,173),(382,205),(376,218),(371,207)],
 'market_pennant':[(435,233),(446,236),(445,254),(440,264),(435,258)]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    base=Image.open(HERE/'complete-town-native-v2.png').convert('RGB')
    raw=Image.open(HERE/'crest-cloth-native-raw-v3.png').convert('RGB')
    mask=Image.new('L',base.size);d=ImageDraw.Draw(mask)
    for poly in CLOTH.values():d.polygon(poly,fill=255)
    mask.save(HERE/'crest-cloth-mask-v3.png')
    selected=Image.composite(raw,base,mask);selected.save(HERE/'complete-town-native-v3.png')
    outside=ImageChops.multiply(ImageChops.difference(selected,base).convert('L'),ImageChops.invert(mask))
    assert not outside.getbbox()
    detail=Image.new('RGB',(400,240),(25,25,25))
    for i,box in enumerate([(7,245,30,299),(537,192,560,251),(165,40,184,87),(498,81,513,122)]):
        crop=selected.crop(box);crop.thumbnail((95,232));crop=crop.resize((crop.width*4,crop.height*4),Image.Resampling.NEAREST)
        detail.paste(crop,(i*100,0))
    detail.save(HERE/'crest-inspection-v3.png')
    ref=Path('.tools/lore-reference-cache/bilgewater-heraldry-20261028')
    data={'status':'authored configuration','provider':'OpenAI built-in image_gen','model':'not exposed by built-in tool',
       'prompt':'assets/source/town/complete-town-20261028-v1/crest-cloth-prompt-v3.txt','prompt_sha256':sha(HERE/'crest-cloth-prompt-v3.txt'),
       'raw_master':'assets/source/town/complete-town-20261028-v1/crest-cloth-master-v3.png','raw_master_sha256':sha(HERE/'crest-cloth-master-v3.png'),
       'raw_native':'assets/source/town/complete-town-20261028-v1/crest-cloth-native-raw-v3.png','raw_native_sha256':sha(HERE/'crest-cloth-native-raw-v3.png'),
       'base_native_sha256':sha(HERE/'complete-town-native-v2.png'),
       'selected_native':'assets/source/town/complete-town-20261028-v1/complete-town-native-v3.png','selected_native_sha256':sha(HERE/'complete-town-native-v3.png'),
       'cloth_mask':'assets/source/town/complete-town-20261028-v1/crest-cloth-mask-v3.png','cloth_mask_sha256':sha(HERE/'crest-cloth-mask-v3.png'),
       'cloth_polygons':CLOTH,'outside_mask_pixels_changed':0,
       'official_private_controls_ids_and_hashes_only':{n:sha(ref/n) for n in ['official-universe-crest.png','official-lor-region-icon.png']},
       'method':'Genuine whole-scene cloth-only painted edit using inspected official regional controls. Technical protected selection of existing cloth; no symbol stamping/vector/code artwork.',
       'native_verified':False,'release_accepted':False}
    (HERE/'generation-v3.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'selected_native_sha256':data['selected_native_sha256'],'cloth_regions':len(CLOTH),'outside_mask_pixels_changed':0}))
if __name__=='__main__':main()
