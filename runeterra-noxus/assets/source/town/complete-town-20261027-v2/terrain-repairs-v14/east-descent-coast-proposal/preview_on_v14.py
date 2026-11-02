"""Read-only rebase preview of the frozen V2 patches on approved V14 terrain."""
from prepare_inputs import *
def main():
 base=TOWN/'terrain/final-native-v14-proposal.png';assert sha(base)=='5787c1646a08f3e8cf0c115cc5b10024f7595ef96f9571511d28786ef326cec7'
 receipt=load(REPORT/'receipt-v2.json');bg=Image.open(base).convert('RGBA');im=bg.copy();allowed=Image.new('L',bg.size)
 for p in receipt['patches']:
  patch=ROOT/p['rgba_patch']['path'];assert sha(patch)==p['rgba_patch']['sha256'];im.alpha_composite(Image.open(patch).convert('RGBA'),p['native_box'][:2]);mask=ROOT/p['mask']['path'];assert sha(mask)==p['mask']['sha256'];allowed=ImageChops.lighter(allowed,Image.open(mask).convert('L'))
 output=HERE/'terrain-proposal-rebased-on-v14.png';save(output,im);dr,dg,db=ImageChops.difference(bg.convert('RGB'),im.convert('RGB')).split();changed=ImageChops.lighter(ImageChops.lighter(dr,dg),db).point(lambda a:255 if a else 0)
 assert ImageChops.multiply(changed,ImageChops.invert(allowed)).getbbox()is None
 for name in('all36-actual-body128-EXCLUSION.png','all36-full-structural-contact-EXCLUSION.png'):assert ImageChops.multiply(changed,Image.open(GUIDE/name).convert('L')).getbbox()is None
 idx=TOWN/'native-transforms-v14/states.json';assert sha(idx)=='e5101798a4336583495f9fbcb04ad780e54cca81275677b94e191ac69f233023';rows={r['state']:r for r in load(idx)['states']};s=load(TOWN/'candidate-final-v5/selection.json')
 for mode in('empty','base','full','coast'):
  view=im.copy();chosen=[]if mode=='empty'else[site['states'][0]if mode=='base'else site['top']for site in s['sites']if site['id']not in('coast','grail')]
  if mode=='coast':chosen.append('ship')
  for state in sorted(chosen,key=lambda k:rows[k]['native_z']):view.alpha_composite(Image.open(ROOT/rows[state]['frame']['path']).convert('RGBA'))
  save(REPORT/f'rebased-v14-{mode}-native.png',view)
 data={'status':'design proposal','base':ref(base),'source_index':ref(idx),'frozen_patches_receipt':ref(REPORT/'receipt-v2.json'),'patch_hashes_unchanged':True,'output':ref(output),'changed_pixels':changed.histogram()[255],'outside_masks_or_bodies_or_roots_changed':0,'script':ref(Path(__file__)),'canonical_integration_performed':False,'independent_visual_review':'Foundation reviewer reports all three V2 physical stair/landing sources positive. Exact surface traces and final consumer remain geometry/coordinator scope.','runtime_verified':False,'release_accepted':False}
 (REPORT/'rebased-v14-receipt.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data))
if __name__=='__main__':main()
