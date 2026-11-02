"""Actual masonry/beam/post sole annotations for every native state.

Contours are authored against the actor-only magenta native atlas. Terrain
support is deliberately not loaded by this writer. Existing sources are never
cropped to a green mask. Detached step/post soles remain separate components.
"""
from pathlib import Path
import hashlib
import json
import importlib.util
from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
OUT = HERE / 'structural-contacts-v1'
OUT.mkdir(exist_ok=False)
spec = importlib.util.spec_from_file_location('binder',HERE / 'bind_contract.py')
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)
source = HERE / 'semantic-candidate-v6/annotations.json'
annotation = json.loads(source.read_text())
index_path = HERE / 'lower-roost-registration-v1/states.json'
index = json.loads(index_path.read_text())
contours = {
 'blacksmith': [[[158,292],[176,298],[197,302],[218,305],[244,305],[267,300]],[[220,305],[237,305]]],
 'castle': [[[108,83],[132,87],[155,91],[180,95],[204,100],[228,103],[245,104],[260,100],[270,94]],[[249,105],[257,104]]],
 'fort': [[[112,88],[132,93],[153,96],[178,100],[207,101],[230,98],[245,94]],[[193,101],[205,101]]],
 'citadel': [[[107,86],[129,92],[154,97],[181,100],[209,103],[231,100],[248,95]],[[205,102],[218,102]]],
 'capitol': [[[310,109],[330,116],[352,122],[374,126],[393,128],[413,123],[424,118]],[[386,128],[396,128]]],
 'cityHall': [[[309,111],[333,119],[361,125],[389,129],[412,127],[427,122]],[[388,129],[399,129]]],
 'townHall': [[[310,121],[334,125],[357,128],[388,129],[415,128],[426,124]],[[387,129],[399,129]]],
 'villageHall': [[[335,121],[356,126],[382,129],[405,129],[426,125]],[[387,129],[398,129]]],
 'mageGuild1': [[[470,126],[482,131],[493,133],[507,133],[520,132],[531,128]],[[499,133],[508,133]]],
 'mageGuild2': [[[471,126],[486,131],[503,133],[519,132],[528,127]],[[500,133],[509,133]]],
 'mageGuild3': [[[482,125],[493,130],[505,131],[518,127],[521,123]],[[500,131],[506,131]]],
 'dwellingLvl1': [[[70,246],[82,249],[101,251],[124,252],[142,249]],[[135,251],[143,249]]],
 'dwellingUpLvl1': [[[70,246],[83,249],[101,252],[123,252],[142,249]],[[135,251],[143,249]]],
 'dwellingLvl2': [[[250,278],[266,284],[284,289],[312,289],[340,285],[349,280]],[[334,286],[344,285]]],
 'dwellingUpLvl2': [[[251,273],[266,282],[285,287],[308,291],[332,289],[348,284]],[[333,288],[344,287]]],
 'dwellingLvl3': [[[209,180],[227,184],[251,187],[278,189],[300,186],[314,181]],[[308,184],[314,183]]],
 'dwellingUpLvl3': [[[196,182],[219,187],[241,189],[263,190],[282,192],[302,189],[320,184]],[[278,192],[286,192]],[[312,185],[320,184]]],
 'special1': [[[600,202],[615,208],[637,212],[659,213],[682,210],[698,203]],[[647,213],[657,213]]],
 'dwellingLvl4': [[[598,200],[612,206],[635,211],[658,213],[681,211],[699,203]],[[626,212],[638,212]]],
 'dwellingUpLvl4': [[[600,215],[619,220],[640,224],[657,225],[678,223],[695,218],[705,208]],[[646,225],[659,225]]],
 'dwellingLvl5': [[[619,107],[635,109],[649,111],[665,112],[681,110],[694,107]],[[651,112],[661,112]]],
 'dwellingUpLvl5': [[[608,104],[627,106],[647,108],[670,108],[686,105]],[[650,110],[660,110]]],
 'dwellingLvl6': [[[525,140],[538,145],[556,148],[577,146],[590,142]],[[568,148],[577,148]]],
 'dwellingUpLvl6': [[[529,145],[541,151],[555,152],[574,148],[591,141]],[[561,152],[570,152]]],
 'special2': [[[534,143],[550,147],[577,148],[596,144]],[[573,148],[583,148]]],
 'dwellingLvl7': [[[99,178],[111,182],[127,185]],[[168,184],[181,185],[191,182]],[[135,185],[138,185]],[[149,185],[152,185]]],
 'dwellingUpLvl7': [[[101,178],[115,182],[128,184]],[[169,184],[183,185],[192,181]],[[136,184],[139,184]],[[151,184],[154,184]]],
 'resourceSilo': [[[4,216],[24,219],[48,222],[76,222],[102,220],[121,216]],[[31,222],[41,222]]],
 'tavern': [[[516,268],[538,277],[557,284],[579,289],[599,293],[621,291],[634,285]],[[619,292],[632,289]]],
 'special4': [[[450,192],[465,197],[482,201],[502,200],[517,192]],[[476,201],[485,201]]],
 'marketplace': [[[355,317],[380,323],[407,326],[432,328],[459,329],[487,329],[513,327],[537,323],[545,318]]],
 'special3': [[[4,320],[28,324],[53,324],[78,326],[103,328],[128,327],[148,325],[161,320]]],
 'grail': [[[326,311],[330,313],[334,311]]],
 'shipyard': [[[636,323],[640,321]],[[660,321],[664,321]],[[676,322],[680,322]],[[687,320],[690,320]],[[705,324],[709,324]],[[718,325],[721,325]],[[731,324],[734,324]],[[744,325],[748,325]],[[758,326],[761,326]],[[766,323],[769,323]]],
 'ship': [[[626,329],[641,341],[660,349],[681,354],[700,352],[717,344],[722,332]],[[636,323],[640,321]],[[660,321],[664,321]],[[676,322],[680,322]],[[687,320],[690,320]],[[705,324],[709,324]],[[718,325],[721,325]],[[731,324],[734,324]],[[744,325],[748,325]],[[758,326],[761,326]],[[766,323],[769,323]]],
}
assert set(contours) == set(index['states'])
records = {}
for key,parts in contours.items():
    definition = {'lines':[{'points':part,'width':1} for part in parts]}
    row = annotation['states'][key]
    row['foundation'] = definition
    row['contact_interpretation'] = 'Complete source-inspected basal masonry/beam contour, with independently retained entrance-step and detached pier/post soles where present. The actor-only native magenta atlas, not the terrain support result, defines this authored anatomy trace; transparent/foliage ambiguities remain explicitly measured for correction.'
    row['contact_reference'] = {'path':(HERE / 'contact-atlas-v1' / (key+'-native-contact.png')).relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256((HERE / 'contact-atlas-v1' / (key+'-native-contact.png')).read_bytes()).hexdigest()}
    frame = Image.open(PROJECT / index['states'][key]['frame']).convert('RGBA')
    full = frame.getchannel('A').point(lambda p:255 if p>=8 else 0)
    raw = binder.trace(definition)
    actual = ImageChops.multiply(raw,full)
    outside = ImageChops.subtract(raw,full)
    records[key] = {'components':parts,'raw_native_trace_pixels':sum(bool(v) for v in raw.get_flattened_data()),
        'actual_native_alpha8_trace_pixels':sum(bool(v) for v in actual.get_flattened_data()),
        'raw_trace_transparency_ambiguity_pixels':sum(bool(v) for v in outside.get_flattened_data()),
        'anatomy_source':row['contact_reference'],'whole_physical_admission':False}
annotation['structural_contact_ancestry'] = {'path':source.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
annotation['review_limits'] = 'Source anatomy authored for all35states; transparency ambiguities, fixed terrain support and actual full connected public network still require executed closure. No partial contour is automatically admitted by alpha clipping.'
(OUT / 'annotations.json').write_text(json.dumps(annotation,indent=2,sort_keys=True)+'\n',encoding='utf-8')
(OUT / 'plan.json').write_text(json.dumps({'status':'design proposal','all35_actual_native_contact_records':records,'terrain_loaded':False,'source_art_modified':False},indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({key:{'actual':row['actual_native_alpha8_trace_pixels'],'raw':row['raw_native_trace_pixels'],'ambiguity':row['raw_trace_transparency_ambiguity_pixels']} for key,row in records.items()},indent=2))
