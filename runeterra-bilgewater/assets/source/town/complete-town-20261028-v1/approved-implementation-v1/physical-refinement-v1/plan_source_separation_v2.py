"""Actual construction/public-terrace ownership, authored before geometry.

The plans identify permanent city retaining fascia, paved/wooden courts and
public stairs. They never read a support mask or a desired consumer result.
Actual columns, functional sculpture, individual entry steps and stilt shoes
are retained separately; a boundary is not a floor-support approval.
"""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
OUT = HERE / 'ownership-separation-v2'
OUT.mkdir(exist_ok=False)
def row(boundary,retains=(),entry=None,note='Permanent city terrace/quay fascia below the construction seam stays scenery; the actual building, its entry and bearing components remain constructible.'):
    return {'boundary':boundary,'retain_polygons':list(retains),'own_entry_region':entry,'source_interpretation':note}
def box(x0,y0,x1,y1):
    return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
states = {
 'blacksmith':row([[158,289],[175,295],[198,298],[219,299],[244,298],[268,293]], [box(216,285,238,305),box(231,281,260,301)], [216,291,239,306], 'Preserve the workshop, complete furnace/firebox and actual entry steps. The lower common court curb/fascia is permanent public ground, not the workshop foundation.'),
 'castle':row([[108,83],[133,87],[159,91],[184,94],[209,96],[229,99],[244,101],[260,99],[270,94]], [box(243,83,260,107)], [243,94,261,108]),
 'fort':row([[112,82],[139,87],[163,91],[188,93],[213,95],[245,93]], [box(179,81,204,101)], [179,90,205,102]),
 'citadel':row([[105,82],[130,87],[155,90],[181,92],[207,95],[231,96],[248,92]], [box(193,82,220,104)], [193,91,221,105]),
 'capitol':row([[309,110],[333,116],[353,120],[378,123],[397,123],[422,116],[425,113]], [box(381,117,398,128),box(368,120,377,126),box(398,119,405,126)], [381,121,399,129]),
 'cityHall':row([[309,111],[334,117],[360,122],[383,124],[405,123],[427,120]], [box(381,117,401,129)], [381,121,402,130]),
 'townHall':row([[310,120],[335,123],[358,125],[383,126],[404,125],[426,122]], [box(380,116,402,129)], [380,122,403,130]),
 'villageHall':row([[335,120],[356,124],[382,125],[404,125],[426,123]], [box(383,116,401,129)], [383,121,402,130]),
 'mageGuild1':row([[470,122],[482,126],[498,128],[513,128],[531,125]], [box(496,119,510,132),box(477,122,483,129),box(519,120,525,130)], [496,124,511,133]),
 'mageGuild2':row([[471,123],[486,127],[503,129],[519,128],[528,124]], [box(495,119,511,133),box(478,123,485,130),box(517,122,523,130)], [495,125,512,134]),
 'mageGuild3':row([[485,122],[495,126],[507,127],[519,120]], [box(496,117,508,131),box(486,121,491,127),box(513,118,519,127)], [496,123,509,132]),
 'dwellingLvl1':row([[70,243],[86,246],[109,249],[128,248],[144,243]], [box(128,231,145,251)], [128,239,146,252]),
 'dwellingUpLvl1':row([[70,243],[87,246],[110,249],[129,248],[144,243]], [box(128,231,145,251)], [128,239,146,252]),
 'dwellingLvl2':row([[249,269],[268,276],[288,280],[314,281],[336,277],[350,272]], [box(329,260,346,286)], [329,274,347,287]),
 'dwellingUpLvl2':row([[266,275],[287,280],[309,284],[333,281],[349,276]], [box(328,263,346,288)], [328,276,347,289]),
 'dwellingLvl3':row([[205,174],[228,178],[252,181],[278,181],[304,177],[315,171]], [box(208,170,226,185),box(268,166,291,186),box(304,162,316,181)], [304,171,317,183]),
 'dwellingUpLvl3':row([[195,177],[220,181],[242,184],[263,184],[286,185],[308,180],[322,175]], [box(207,168,226,187),box(268,167,293,190),box(305,164,324,184)], [305,175,325,186]),
 'special1':row([[599,198],[618,204],[638,207],[659,208],[683,205],[700,196]], [box(641,187,666,212)], [641,201,667,213]),
 'dwellingLvl4':row([[598,196],[615,202],[636,206],[659,207],[682,205],[700,194]], [box(624,181,640,211),box(672,190,686,210)], [624,199,641,212]),
 'dwellingUpLvl4':row([[599,206],[620,214],[642,217],[661,217],[683,214],[704,205]], [box(640,185,663,220),box(605,197,626,219),box(678,194,700,219)], [640,199,664,221]),
 'dwellingLvl5':{'retain_all':True,'source_interpretation':'The lower Roost masonry plinth and separate flagstaff are actual construction anatomy. No source pixels are retired as ground in this state.'},
 'dwellingUpLvl5':{'retain_all':True,'source_interpretation':'The developed Roost is a raised timber construction with5 genuine detached stilt shoes. Keep its complete beam, all stilt shafts/shoes, rigging and flags; its open air gaps are genuine.'},
 'dwellingLvl6':row([[525,135],[539,140],[556,142],[577,140],[592,135]], [box(564,128,581,149)], [564,138,582,150]),
 'dwellingUpLvl6':row([[528,137],[542,142],[556,145],[575,141],[592,135]], [box(558,130,575,152)], [558,140,576,153]),
 'special2':row([[534,139],[550,143],[578,144],[597,139]], [box(542,126,587,148)], [570,139,588,149]),
 'dwellingLvl7':row([[95,170],[116,174],[140,176],[166,176],[190,173]], [box(95,164,195,182)], [159,173,187,184], 'The functional sculpture and stone vessel/rim remain construction. Only the lower shared city retaining fascia and non-solid falling-water continuation are permanent scenery; the whole source pool is not discarded.'),
 'dwellingUpLvl7':row([[95,170],[117,174],[141,176],[166,176],[190,173]], [box(95,164,195,182)], [159,173,187,184], 'Retain the complete sculpture and actual stone vessel/rim, including isolated real pedestal contacts; the vertical lower spill/fascia continuation is scenery, not a foundation or doorway.'),
 'resourceSilo':row([[4,210],[29,215],[63,217],[94,216],[121,210]], [box(23,200,43,221),box(104,203,118,217)], [23,210,44,222]),
 'tavern':row([[515,255],[542,264],[569,271],[595,275],[635,269]], [box(604,222,640,291),box(531,244,550,271)], [612,261,637,292], 'Main inn walls and actual right annex remain construction, with their real entry. The large shared front city retaining face and outdoor public stair are permanent community circulation, not a closed building wall.'),
 'special4':row([[450,185],[466,191],[480,194],[501,192],[517,186]], [box(473,181,487,198)], [473,190,488,199]),
 'marketplace':row([[355,312],[380,317],[407,319],[432,319],[459,319],[487,318],[513,316],[542,312]], [box(398,312,402,320)], [540,309,548,320], 'All stall roofs, actual shop fronts, counter posts and their construction soles remain. The shared city quay pavement, lower retaining fascia and public pier continuations are permanent scenery, not constructible store legs.'),
 'special3':row([[4,309],[28,314],[53,316],[78,317],[103,318],[128,317],[148,315],[163,310]], [box(159,301,168,317)], [159,309,168,318], 'The shops and their actual front wall/post contacts remain constructible; the lower common quay/fascia continuation belongs to the town. The east end-aisle remains a real open frontage.'),
 'shipyard':{'retain_all':True,'source_interpretation':'Keep the entire functional coastal jetty with every painted piling, brace, rail and landing; coastal anatomy is not used as a permanent-terrain shortcut.'},
 'ship':{'retain_all':True,'source_interpretation':'The actual replacement ship state contains both jetty and moored hull; retain all source maritime anatomy, rigging and visible pier details independently of the base jetty.'},
 'grail':{'retain_all':True,'source_interpretation':'Retain the complete optional functional beacon and its pedestal.'},
}
plan = {'status':'design proposal','method':'Actual architectural/public-ground separation, manually observed at native size. Shared terrace/quay paving, permanent retaining fascia and public outdoor stairs remain town scenery. Real building walls/columns, functional sculpture, detached structural feet, individual entrance stairs, coast and optional Grail remain construction. A boundary is not a support approval.',
    'states':states,'support_or_validation_inputs_used_to_choose_boundary':False,
    'approved_full_pixel_change_permitted':False,'independent_anatomy_review_pending':True}
(OUT / 'plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print('Prepared'+str(len(states))+' independently authored ownership records; no source art modified')
