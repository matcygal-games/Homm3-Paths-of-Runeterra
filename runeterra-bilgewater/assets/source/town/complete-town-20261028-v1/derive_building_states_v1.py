"""Technical source cutouts/whole-variant registration from complete painted scenes.

No artwork is created here. Masks trace source architecture; pixel sources are
genuine painted complete-town and revealed/early-state variants. This first
cohort is reviewable and not canonical integration or release acceptance.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps,ImageChops,ImageFilter
import hashlib,json,copy,importlib.util
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/derived-v1'
OUT=HERE/'derived-v1'
spec=importlib.util.spec_from_file_location('bilge_scene_trace',HERE/'trace_complete_scene_v2.py')
trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)
SITES=copy.deepcopy(trace.SITES)
SITES['defenses']['poly']=[(91,44),(103,39),(104,28),(116,28),(117,13),(125,16),(126,25),(136,30),(145,29),(148,22),(158,20),(161,12),(168,14),(169,24),(176,29),(187,31),(190,28),(199,33),(210,33),(213,29),(223,32),(226,39),(236,42),(244,43),(248,38),(260,40),(274,35),(279,39),(269,45),(270,70),(273,91),(263,99),(249,105),(233,107),(215,103),(196,99),(179,95),(162,92),(145,91),(126,88),(112,86),(98,84),(92,73)]
SITES['sailors']['poly']=[(65,229),(70,223),(80,221),(86,215),(96,215),(104,217),(114,218),(123,216),(132,221),(139,223),(145,230),(146,240),(140,248),(130,252),(114,253),(99,252),(84,250),(71,247),(65,240)]
SITES['slaughterDocks']['poly']=[(0,129),(9,124),(23,119),(36,113),(42,114),(42,121),(34,129),(26,133),(24,142),(31,148),(38,147),(40,157),(48,158),(55,168),(68,168),(79,171),(83,163),(87,164),(87,182),(102,188),(113,191),(124,188),(127,193),(121,199),(124,211),(116,219),(99,223),(80,221),(57,223),(39,220),(18,220),(0,216)]

MAX_EXTRA={
 'defenses': [[(193,6),(196,7),(196,12),(205,12),(220,20),(209,19),(197,17),(197,34),(193,34)]],
 'civic': [[(374,0),(379,3),(379,10),(389,11),(399,15),(413,24),(401,21),(391,18),(379,17),(378,43),(374,43)]],
 'cliffwing': [[(653,28),(656,29),(656,49),(653,49)],[(644,30),(645,31),(645,48),(643,48)]]}

# Outline, source and whole-body offsets were calibrated from the actual painted
# variant's level footing, not a generated square slot. Entrances may differ.
VARIANTS={
 'villageHall':{'site':'civic','source':'village-hall-native-raw-v1.png','delta':[0,3], 'entrance':[389,122],
   'poly':[(330,99),(337,94),(345,91),(351,87),(360,83),(368,79),(377,75),(386,72),(395,76),(402,82),(410,84),(417,90),(425,93),(431,94),(434,99),(428,103),(427,117),(432,121),(425,125),(410,127),(392,127),(374,126),(357,124),(341,121),(333,117)],
   'extra':[[(394,52),(397,53),(398,59),(405,60),(412,65),(410,74),(403,77),(398,76),(397,91),(394,91)]]},
 'townHall':{'site':'civic','source':'base-town-native-raw-v1.png','delta':[0,30],'entrance':[385,119],
   'poly':[(306,61),(314,56),(323,50),(334,44),(345,43),(356,37),(366,36),(377,41),(391,42),(405,44),(421,39),(429,40),(427,48),(420,54),(422,80),(428,88),(423,96),(410,100),(391,100),(371,99),(350,98),(329,96),(311,91),(306,82)],
   'extra':[[(362,9),(365,10),(365,19),(374,19),(386,28),(377,27),(366,25),(366,44),(362,43)]]},
 'cityHall':{'site':'civic','source':'intermediate-town-native-raw-v1.png','delta':[0,3],'entrance':[384,121],
   'poly':[(302,71),(310,66),(312,55),(319,52),(325,42),(336,42),(343,35),(355,34),(360,29),(367,24),(374,28),(378,37),(387,38),(396,41),(407,43),(416,41),(422,47),(426,59),(425,81),(429,103),(428,117),(418,123),(400,126),(380,128),(360,124),(340,121),(322,116),(307,108),(303,94)],
   'extra':[[(364,3),(368,5),(368,16),(377,16),(389,21),(398,26),(386,24),(377,22),(369,22),(368,42),(364,41)]]},
 'fort':{'site':'defenses','source':'base-town-native-raw-v1.png','delta':[0,8],'entrance':[186,89],
   'poly':[(108,44),(116,39),(125,39),(127,32),(133,33),(134,39),(144,39),(146,36),(153,38),(153,43),(161,42),(165,38),(174,40),(178,46),(186,47),(189,42),(193,44),(193,52),(201,52),(202,45),(210,47),(213,54),(224,54),(228,50),(236,52),(242,59),(249,59),(251,71),(250,85),(241,91),(221,96),(201,97),(184,96),(164,95),(145,91),(127,90),(113,86),(108,72)],
   'extra':[[(158,15),(161,16),(160,45),(157,45)],[(189,16),(193,13),(206,17),(216,22),(208,22),(194,19),(193,43),(189,42)]]},
 'citadel':{'site':'defenses','source':'intermediate-town-native-raw-v1.png','delta':[0,3],'entrance':[199,90],
   'poly':[(102,43),(113,39),(116,34),(124,35),(128,31),(134,34),(136,38),(147,38),(151,29),(153,21),(158,15),(165,20),(170,30),(173,39),(181,40),(189,41),(196,37),(203,39),(205,42),(215,41),(218,35),(224,32),(233,34),(239,39),(245,38),(250,46),(250,67),(252,91),(242,99),(221,103),(201,102),(179,100),(159,97),(137,94),(116,88),(105,81)],
   'extra':[[(190,5),(194,6),(194,11),(205,12),(220,21),(209,18),(196,16),(194,37),(190,36)]]},
 'mageGuild1':{'site':'guild','source':'guild-one-native-raw-v1.png','delta':[-7,0],'entrance':[502,125],
   'poly':[(475,102),(483,98),(491,95),(496,91),(504,88),(507,81),(511,78),(515,83),(515,90),(523,95),(533,99),(539,100),(541,104),(536,108),(535,123),(538,127),(530,132),(515,133),(501,133),(486,131),(478,126)]},
 'mageGuild2':{'site':'guild','source':'intermediate-town-native-raw-v1.png','delta':[0,12],'entrance':[502,123],
   'poly':[(466,66),(473,60),(476,55),(483,53),(484,44),(490,36),(495,34),(501,38),(507,43),(509,51),(515,54),(520,58),(526,63),(524,70),(522,74),(523,104),(529,111),(525,119),(512,122),(497,122),(482,119),(470,114),(467,102)]},
 'dwellingLvl1':{'site':'sailors','source':'base-town-native-raw-v1.png','delta':[0,1],'entrance':[112,246],
   'poly':[(65,229),(74,224),(80,219),(89,217),(99,220),(109,218),(120,220),(130,224),(140,226),(147,233),(144,245),(136,250),(120,252),(102,251),(86,249),(71,246),(65,240)]},
 'dwellingLvl2':{'site':'corsair','source':'base-town-native-raw-v1.png','delta':[0,0],'entrance':[319,280],
   'poly':[(243,244),(251,237),(263,234),(273,231),(280,226),(288,221),(296,219),(299,209),(303,207),(304,224),(313,226),(324,232),(337,236),(351,235),(354,242),(348,248),(351,274),(349,283),(337,290),(321,293),(303,292),(284,288),(268,282),(252,277),(244,267)]},
 'dwellingLvl3':{'site':'cannon','source':'base-town-native-raw-v1.png','delta':[0,11],'entrance':[282,174],
   'poly':[(204,141),(213,135),(220,132),(231,128),(241,125),(250,129),(263,130),(277,126),(285,124),(293,129),(305,128),(314,133),(316,142),(312,151),(314,164),(307,174),(290,178),(271,178),(253,178),(235,175),(219,174),(206,167)]},
 'dwellingLvl5':{'site':'cliffwing','source':'base-town-native-raw-v1.png','delta':[0,21],'entrance':[655,134],
   'poly':[(587,88),(593,81),(601,77),(607,72),(615,73),(622,71),(630,68),(636,65),(642,62),(644,55),(646,45),(653,40),(663,39),(671,43),(676,49),(684,52),(689,58),(693,67),(701,69),(708,68),(712,72),(709,84),(707,104),(699,112),(682,115),(663,114),(645,113),(626,110),(608,111),(593,105)],
   'extra':[[(627,39),(636,31),(645,35),(651,34),(658,31),(666,32),(675,40),(688,43),(691,46),(679,45),(668,40),(659,42),(649,45),(638,43)]]},
 'dwellingLvl7':{'site':'leviathan','source':'base-town-native-raw-v1.png','delta':[0,17],'entrance':[168,180],
   'poly':[(94,130),(100,123),(106,118),(112,115),(119,113),(123,108),(129,108),(136,116),(137,130),(146,132),(150,127),(157,127),(159,134),(166,137),(170,137),(176,128),(182,126),(188,133),(191,145),(187,151),(193,159),(191,168),(179,172),(162,174),(143,173),(125,172),(107,170),(96,165)],
   'extra':[]},
 'special1':{'site':'buhru','source':'base-town-native-raw-v1.png','delta':[0,23],'entrance':[651,202],
   'poly':[(595,162),(603,154),(610,150),(615,148),(620,142),(623,136),(624,128),(630,124),(637,126),(643,134),(642,140),(639,145),(642,151),(648,152),(655,151),(661,147),(669,147),(674,151),(681,151),(685,159),(693,163),(700,162),(703,169),(697,175),(692,183),(676,189),(656,190),(635,189),(615,186),(600,181)]},
 'dwellingLvl4':{'site':'buhru','source':'intermediate-town-native-raw-v1.png','delta':[0,8],'entrance':[651,202],
   'poly':[(592,168),(600,161),(604,154),(610,151),(615,147),(620,148),(625,151),(632,151),(635,147),(644,146),(647,141),(655,138),(660,141),(664,148),(672,150),(681,151),(685,157),(692,160),(699,157),(705,164),(702,172),(699,188),(692,197),(675,204),(654,205),(634,203),(615,199),(601,193),(593,181)]},
 'special2':{'site':'captains','source':'intermediate-town-native-raw-v1.png','delta':[0,17],'entrance':[553,143],
   'poly':[(532,115),(539,110),(544,104),(548,98),(552,96),(555,91),(555,85),(561,78),(569,75),(576,79),(580,85),(581,100),(585,109),(593,115),(600,118),(600,126),(588,131),(574,132),(558,131),(543,129),(532,123)],
   'extra':[[(551,48),(555,47),(555,57),(564,57),(576,63),(583,72),(574,70),(565,65),(555,64),(555,96),(552,96)]]},
 'dwellingLvl6':{'site':'captains','source':'base-town-native-raw-v1.png','delta':[0,17],'entrance':[550,141],
   'poly':[(520,97),(529,93),(538,88),(545,84),(549,77),(548,72),(553,68),(558,64),(565,67),(568,73),(566,81),(572,86),(583,90),(595,94),(602,96),(602,101),(596,105),(596,122),(589,129),(574,132),(558,132),(540,129),(526,125),(521,115)],
   'extra':[[(552,59),(555,59),(555,64),(565,65),(573,69),(573,72),(563,69),(555,67),(555,80),(552,80)]]}
}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()

def cut(source, polygons, delta=(0,0),scale=1,root=None,target=None):
    image=Image.open(HERE/source).convert('RGBA');mask=Image.new('L',(800,374));d=ImageDraw.Draw(mask)
    for p in polygons:d.polygon(p,fill=255)
    image.putalpha(mask)
    if scale!=1:
        box=mask.getbbox();cropped=image.crop(box)
        size=(round(cropped.width*scale),round(cropped.height*scale))
        cropped=cropped.resize(size,Image.Resampling.LANCZOS)
        canvas=Image.new('RGBA',(800,374))
        x=round(target[0]-(root[0]-box[0])*scale);y=round(target[1]-(root[1]-box[1])*scale)
        canvas.alpha_composite(cropped,(x,y));return canvas
    canvas=Image.new('RGBA',(800,374));canvas.alpha_composite(image,tuple(delta));return canvas

def overlay_mask(layer):return layer.getchannel('A').point(lambda x:255 if x>=8 else 0)

def masks(layer):
    alpha=overlay_mask(layer);area=Image.new('RGBA',layer.size);area.putalpha(alpha)
    edge=ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(3)),alpha.filter(ImageFilter.MinFilter(3)))
    border=Image.new('RGBA',layer.size,(255,235,80,0));border.putalpha(edge)
    return area,border

def icon(layer,size):
    box=layer.getchannel('A').getbbox();cropped=layer.crop(box)
    cropped.thumbnail((size[0]-4,size[1]-4),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',size);out.alpha_composite(cropped,((size[0]-cropped.width)//2,(size[1]-cropped.height)//2));return out

def main():
    OUT.mkdir(exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
    frames={};records={};by_state={state:site for site,v in SITES.items() for state in v['keys']}
    for site,entry in SITES.items():
        source='complete-town-native-v3.png'
        if site in ('defenses','corsair','tavern'):source='revealed-architecture-native-raw-v1.png'
        state=entry['top'];polys=[entry['poly']]+MAX_EXTRA.get(site,[])
        frames[state]=cut(source,polys)
        records[state]={'site':site,'source':source,'source_sha256':sha(HERE/source),'polygons':polys,'delta':[0,0],'entrance':entry['door'],'z':entry['z']}
    for state,entry in VARIANTS.items():
        polys=[entry['poly']]+entry.get('extra',[]);delta=entry['delta']
        frames[state]=cut(entry['source'],polys,delta)
        records[state]={'site':entry['site'],'source':entry['source'],'source_sha256':sha(HERE/entry['source']),
            'polygons':polys,'delta':delta,'entrance':entry['entrance'],'z':SITES[entry['site']]['z']}
    # Separate optional native replacement: one genuinely painted dock-only
    # source and a combined full dock+boat source. The public quay stays in BG.
    dock_poly=[(634,300),(645,301),(659,305),(676,307),(695,307),(712,308),(730,308),(751,305),(771,305),(778,311),(778,323),(764,330),(747,333),(730,337),(709,340),(687,342),(667,339),(650,333),(638,325)]
    ship_poly=[(622,326),(634,318),(647,315),(660,305),(670,293),(684,277),(699,255),(710,247),(711,254),(705,267),(703,289),(704,304),(717,316),(728,326),(731,343),(723,355),(708,363),(690,365),(670,364),(651,358),(636,348)]
    shipyard=cut('empty-terrain-native-raw-v1.png',[dock_poly]);frames['shipyard']=shipyard
    boat=cut('complete-town-native-v3.png',[ship_poly,dock_poly]);frames['ship']=boat
    for state,source,polys in [('shipyard','empty-terrain-native-raw-v1.png',[dock_poly]),('ship','complete-town-native-v3.png',[ship_poly,dock_poly])]:
        records[state]={'site':'coast','source':source,'source_sha256':sha(HERE/source),'polygons':polys,'delta':[0,0],'entrance':[641,315],'z':370,'intentional_water':True,'native_replacement':'ship contains dock+boat; inherited ship.upgrades=shipyard'}
    grail_poly=[(742,226),(743,220),(747,215),(748,210),(752,214),(756,217),(757,224),(761,229),(759,236),(751,240),(743,237)]
    frames['grail']=cut('complete-town-native-v3.png',[grail_poly],scale=.75,root=[751,238],target=[315,319])
    records['grail']={'site':'grail','source':'complete-town-native-v3.png','source_sha256':sha(HERE/'complete-town-native-v3.png'),'polygons':[grail_poly],'uniform_scale':.75,'source_root':[751,238],'target_root':[315,319],'entrance':[315,319],'z':335,'reason':'Same genuinely painted small beacon relocated from inaccessible cliff rock to connected level public quay.'}
    assert set(frames)==set(json.loads((PROJECT/'content/factions.json').read_text())['bilgewater']['town']['buildings'])
    for state,layer in frames.items():
        folder=OUT/'states'/state;folder.mkdir(parents=True,exist_ok=True)
        layer.save(folder/'layer.png');area,border=masks(layer);area.save(folder/'area.png');border.save(folder/'border.png')
        icon(layer,(58,64)).save(folder/'campaign.png');icon(layer,(150,70)).save(folder/'construction.png')
        records[state].update({'frame':rel(folder/'layer.png'),'frame_sha256':sha(folder/'layer.png'),
           'alpha_bounds':list(layer.getchannel('A').getbbox()),'visible_pixels':overlay_mask(layer).histogram()[255],
           'area':rel(folder/'area.png'),'area_sha256':sha(folder/'area.png'),'border':rel(folder/'border.png'),'border_sha256':sha(folder/'border.png'),
           'campaign':rel(folder/'campaign.png'),'campaign_sha256':sha(folder/'campaign.png'),'construction':rel(folder/'construction.png'),'construction_sha256':sha(folder/'construction.png')})
    background=HERE/'empty-terrain-selected-v4.png'
    top=[e['top'] for e in SITES.values()]
    base=[next(k for k in e['keys'] if k in ('villageHall','fort','mageGuild1','special1','special2') or k.startswith('dwellingLvl')) if len(e['keys'])>1 else e['top'] for e in SITES.values()]
    def scene(name,states):
        image=Image.open(background).convert('RGBA')
        for state in sorted(states,key=lambda k:records[k]['z']):image=Image.alpha_composite(image,frames[state])
        image.convert('RGB').save(REPORT/(name+'.png'));return image
    scene('full-native',top);scene('base-native',base);scene('coast-native',top+['ship','grail'])
    scene('early-native',['villageHall','fort','tavern','dwellingLvl1']);scene('shipyard-native',top+['shipyard'])
    for name,states in [('fort-family',['fort','citadel','castle']),('hall-family',['villageHall','townHall','cityHall','capitol']),('guild-family',['mageGuild1','mageGuild2','mageGuild3'])]:
        board=Image.new('RGB',(800,len(states)*374))
        for i,state in enumerate(states):board.paste(scene(name+'-'+state,[state]).convert('RGB'),(0,i*374))
        board.save(REPORT/(name+'-comparison.png'))
    index={'status':'authored configuration','cohort':'derived-v1-provisional-not-frozen','background':rel(background),'background_sha256':sha(background),'canvas':[800,374],
       'ordinary_land_sites':16,'optional_coast':1,'grail':1,'state_count':len(frames),'states':records,
       'full_scene_states':sorted(top,key=lambda k:records[k]['z']),'base_scene_states':sorted(base,key=lambda k:records[k]['z']),
       'source_method':'Complete whole-town first, genuine whole-state variants/revealed surfaces, technical source-silhouette extraction/whole-variant translation/uniform small-Grail registration. No 3D/code artwork.',
       'native_verified':False,'release_accepted':False}
    (OUT/'states.json').write_text(json.dumps(index,indent=2)+'\n')
    print(json.dumps({'states':len(frames),'background_sha256':index['background_sha256'],'index_sha256':sha(OUT/'states.json'),'report':str(REPORT)}))

if __name__=='__main__':main()
