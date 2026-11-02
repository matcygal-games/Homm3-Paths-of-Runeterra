"""Explicit native visible gate/stair/frontage spans, rather than point guards.

Polygons protect actual entrance architecture through its stair-foot/apron.
They remain review candidates bound to each genuine selected source frame.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
OUT=HERE/'entry-spans-v1';REPORT=ROOT/'build/reports/complete-town-20261027-v2/entry-spans-v1'
POLYGONS={
 'villageHall':[(149,137),(164,137),(179,162),(157,162)],
 'townHall':[(153,136),(170,136),(186,162),(166,162)],
 'cityHall':[(147,134),(166,134),(183,162),(153,162)],
 'capitol':[(151,126),(176,126),(199,161),(157,162)],
 'fort':[(415,82),(438,82),(447,109),(447,120),(460,148),(420,148),(421,122),(413,110)],
 'citadel':[(415,79),(436,79),(445,110),(445,121),(454,148),(417,148),(420,121),(412,110)],
 'castle':[(441,73),(462,73),(470,96),(468,111),(477,148),(431,148),(436,123),(442,109)],
 'mageGuild1':[(315,136),(331,136),(343,158),(321,158)],
 'mageGuild2':[(320,132),(337,132),(351,158),(327,158)],
 'mageGuild3':[(322,131),(341,131),(355,158),(329,158)],
 'mageGuild4':[(326,127),(344,127),(359,158),(332,158)],
 'dwellingLvl1':[(628,145),(642,145),(656,175),(632,175)],
 'dwellingUpLvl1':[(619,137),(635,137),(651,172),(626,172)],
 'dwellingLvl2':[(144,207),(156,207),(162,233),(142,233)],
 'dwellingUpLvl2':[(162,204),(177,204),(187,232),(157,232)],
 'dwellingLvl3':[(49,177),(62,177),(76,201),(58,201)],
 'dwellingUpLvl3':[(45,172),(61,172),(71,201),(50,201)],
 'dwellingLvl4':[(540,168),(553,168),(558,190),(550,194),(539,193),(540,184)],
 'dwellingUpLvl4':[(501,169),(514,169),(519,188),(512,192),(502,190)],
 'dwellingLvl5':[(303,298),(318,298),(332,329),(309,329)],
 'dwellingUpLvl5':[(302,291),(319,291),(334,329),(306,329)],
 'dwellingLvl6':[(512,325),(529,325),(534,348),(508,348)],
 'dwellingUpLvl6':[(490,327),(506,327),(512,347),(485,347)],
 'special4':[(467,244),(487,244),(494,280),(462,280)],
 'dwellingLvl7':[(462,230),(484,230),(493,280),(461,280)],
 'dwellingUpLvl7':[(460,222),(485,222),(496,280),(460,280)],
 'tavern':[(176,318),(191,318),(208,345),(183,348)],
 'marketplace':[(591,235),(606,235),(614,249),(587,249)],
 'blacksmith':[(671,329),(690,329),(703,354),(664,354)],
 'resourceSilo':[(677,229),(690,229),(697,256),(680,258),(676,246)],
 'special1':[(51,101),(62,101),(76,129),(62,129)],
 'special2':[(731,131),(744,131),(753,157),(726,157)],
 'special3':[(240,201),(255,201),(259,221),(252,237),(228,231),(238,221)],
 'shipyard':[(748,169),(756,169),(759,178),(748,179)],
 'ship':[(748,169),(756,169),(759,178),(748,179)],
 'grail':[(224,140),(232,140),(233,145),(222,145)],
}
ANCHORS={'villageHall':[164,162],'townHall':[175,162],'cityHall':[168,162],'capitol':[174,161],'fort':[440,148],'citadel':[432,148],'castle':[451,148],'mageGuild1':[328,158],'mageGuild2':[335,158],'mageGuild3':[338,158],'mageGuild4':[341,158],'dwellingLvl1':[645,173],'dwellingUpLvl1':[637,171],'dwellingLvl2':[151,231],'dwellingUpLvl2':[172,231],'dwellingLvl3':[66,200],'dwellingUpLvl3':[60,199],'dwellingLvl4':[548,192],'dwellingUpLvl4':[509,190],'dwellingLvl5':[321,328],'dwellingUpLvl5':[319,328],'dwellingLvl6':[523,347],'dwellingUpLvl6':[498,347],'special4':[479,278],'dwellingLvl7':[475,279],'dwellingUpLvl7':[475,279],'tavern':[191,346],'marketplace':[601,245],'blacksmith':[682,353],'resourceSilo':[686,256],'special1':[68,128],'special2':[737,156],'special3':[245,235],'shipyard':[750,174],'ship':[750,174],'grail':[228,144]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def main():
 s=load(HERE/'candidate-final-v5/selection.json');rows=[]
 if set(POLYGONS)!={r['state']for r in s['states']}:raise ValueError('Entry span state coverage differs')
 for r in s['states']:
  state=r['state'];source=ROOT/r['native_layer'];im=Image.open(source).convert('RGBA');bb=im.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox();m=Image.new('L',(800,374));ImageDraw.Draw(m).polygon(POLYGONS[state],fill=255);bounds=Image.new('L',(800,374));ImageDraw.Draw(bounds).rectangle((bb[0],bb[1],bb[2]-1,bb[3]-1),fill=255);m=ImageChops.multiply(m,bounds);anchor=ANCHORS[state]
  if not m.getpixel(tuple(anchor)):raise ValueError('Actual anchor outside selected entry span '+state+str(anchor))
  p=OUT/(state+'.png');save(p,m);view=im.copy();color=Image.new('RGBA',(800,374),(25,210,255,0));color.putalpha(m.point(lambda a:110 if a else 0));view.alpha_composite(color);ImageDraw.Draw(view).ellipse((anchor[0]-1,anchor[1]-1,anchor[0]+1,anchor[1]+1),fill=(255,255,255,255));crop=(max(bb[0],min(p[0]for p in POLYGONS[state])-4),max(bb[1],min(p[1]for p in POLYGONS[state])-4),min(bb[2],max(p[0]for p in POLYGONS[state])+5),min(bb[3],max(p[1]for p in POLYGONS[state])+5));save(REPORT/(state+'-full-entry-6x.png'),view.crop(crop).resize(((crop[2]-crop[0])*6,(crop[3]-crop[1])*6),Image.Resampling.NEAREST));rows.append({'state':state,'source':r['native_layer'],'source_sha256':sha(source),'actual_native_gate_stair_frontage_polygon':POLYGONS[state],'entrance':anchor,'mask':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)},'mask_pixels':m.histogram()[255],'status':'authored configuration','review':'Complete visible entry span proposal, not a tiny point exemption; source-pixel review required.'})
 write(OUT/'entries.json',{'status':'authored configuration','script_sha256':sha(Path(__file__)),'states':rows});print(json.dumps({'entry_spans':len(rows),'index_sha256':sha(OUT/'entries.json')}))
if __name__=='__main__':main()
