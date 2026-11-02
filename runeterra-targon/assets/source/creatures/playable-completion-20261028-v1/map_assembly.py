"""Technical registration of separately painted compact adventure-map actors."""
from pathlib import Path
from PIL import Image
from assemble_humanoids import HERE,atlas_cells,native_pose,png,dump,relative

PAIRS={'rakkor':['rakkorTrailguard','rakkorPassguard'],'archer':['mountainArcher','peakMarksman'],
       'lunari':['lunariAcolyte','lunariPriestess'],'forger':['solariSunforger','solariDawnforger'],
       'ibex':['crystalIbex','crestedCrystalIbex'],'sunhawk':['solariSunhawk','crownedSunhawk'],
       'stellacorn':['stellacorn','resplendentStellacorn']}

def make_map_resources(unit,root):
    family=next(k for k,v in PAIRS.items() if unit in v);row=PAIRS[family].index(unit)
    path=HERE/'maps'/(family+'-map-master-v1.png');cells,inventory=atlas_cells(path,3,2,128)
    w,h=inventory['canvas'];roots={}
    for r in [0,1]:
        b=cells[r*3]['visible_bbox'];roots[r]=((b[0]+b[2])/2,b[3])
    # One constant scale for both forms and every neutral/reaction pose. Native
    # 64px map canvas draws its bottom-right anchor tile at [32,32,64,64].
    # Choose the shared compact camera once; never resize individual attacks.
    extent=1
    for i,c in cells.items():
        r,col=divmod(i,3);b=c['bbox'];sx=roots[r][0]+col*w/3
        extent=max(extent,abs(b[0]-sx),abs(b[2]-sx))
    heights=[cells[i]['visible_bbox'][3]-cells[i]['visible_bbox'][1] for i in [0,3]]
    scale=min(35/max(heights),14/extent)
    descriptors={};images={}
    for col,name in enumerate(['hold','attackLeft','attackRight']):
        c=cells[row*3+col];source_root=(roots[row][0]+col*w/3,roots[row][1])
        image=native_pose(c,scale,source_root,(64,64),(48,60))
        info=png(root/'map'/(name+'-compact.png'),image);images[name]=image;descriptors[name]=info
    hold=descriptors.pop('hold');hold['frame']=0
    record={'status':'authored configuration','master':relative(path),'source_map':inventory,
            'cohort_scale':scale,'pair':PAIRS[family],'canvas':[64,64],'root':[48,60],
            'anchor_tile':[32,32,64,64],'mask':['VV','VA'],'map_holding_frames':1,
            'native_height':max(image.getbbox()[3]-image.getbbox()[1] for image in images.values()),
            'camera':'Independent near-frontal compact adventure camera; upright weapons and folded wings are genuinely painted, not shortened by code',
            'holding':'One real neutral map frame; encounter reactions are separately painted left/right braced poses',
            'native_execution':False,'art_acceptance':False}
    dump(root/'map/compact-assembly.json',record)
    return [hold],descriptors,record,[path,HERE/'maps/effective-prompts-v1.json',Path(__file__)]
