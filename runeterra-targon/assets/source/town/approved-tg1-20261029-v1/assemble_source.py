"""Portable technical decomposition of approved full-town painting; candidate only."""
from candidate_support import *
def mask(poly):
 im=Image.new('L',(800,374));ImageDraw.Draw(im).polygon([tuple(v)for v in poly],fill=255)
 # Capture antialiased roof tips, banner poles and small contact props. This
 # explicit margin belongs to the removal/source budget, not the click mask.
 return im.filter(ImageFilter.MaxFilter(11))
def ref(out,p):return {'path':p.relative_to(out).as_posix(),'sha256':sha(p)}
def icon(frame,size):
 body=frame.getchannel('A');piece=frame.crop(body.getbbox());piece.thumbnail((size[0]-4,size[1]-4),Image.Resampling.LANCZOS)
 im=Image.new('RGBA',size);im.alpha_composite(piece,((size[0]-piece.width)//2,size[1]-piece.height-2));return im
def row_source(slug,state):
 if state in ('villageHall','fort','mageGuild1') or state.startswith('dwellingLvl'):return 'early'
 if state in ('townHall','citadel','mageGuild2')or(slug=='shurima'and state in('special2','special4')):return 'middle'
 if state=='cityHall'or(slug=='targon'and state=='mageGuild3'):return 'late'
 return 'approved'
def state_mask(site,state,tag):
 m=mask(site['whole_form_polygon'])
 if tag=='early'and site.get('early_min_y')is not None:
  y=site['early_min_y'];ImageDraw.Draw(m).rectangle((0,0,799,y-1),fill=0)
 if state=='ship':
  m=mask([(708,328),(714,323),(719,317),(721,301),(723,301),(724,321),(741,319),(757,310),(773,309),(777,314),(775,331),(784,337),(784,346),(775,352),(751,351),(728,345),(716,341)])
 elif state=='shipyard':
  m=ImageChops.subtract(mask(site['whole_form_polygon']),state_mask(site,'ship','approved'))
 return m

def assemble(slug):
 out=source(slug);plan=read(out/'site-plan-v1.json');full=Image.open(out/'approved-full-native.png').convert('RGBA')
 paints={'approved':full}
 for tag in ('early','middle','late'):
  dest=out/(tag+'-states-raw.png')
  if not dest.is_file():raise ValueError('Missing own painted state master: '+dest.name)
  im=Image.open(dest).convert('RGBA').resize((800,374),Image.Resampling.LANCZOS);save(out/(tag+'-states-native.png'),im);paints[tag]=im
 union=Image.new('L',(800,374));states={};rows=[]
 for site in plan['sites']:
  union=ImageChops.lighter(union,mask(site['whole_form_polygon']))
  for state in site['states']:
   tag=row_source(slug,state);m=state_mask(site,state,tag)
   layer=paints[tag].copy();layer.putalpha(m)
   frame=out/'frames'/(state+'.png');save(frame,layer)
   save(out/'masks'/(state+'-body.png'),m)
   # Visible source body is truly opaque; exposed terrain never shines through.
   area=Image.new('RGBA',(800,374),(0,0,0,0));area.putalpha(m);save(out/'derived'/(state+'_area.png'),area)
   border=Image.new('RGBA',(800,374),(245,210,85,0));border.putalpha(ImageChops.subtract(m.filter(ImageFilter.MaxFilter(3)),m));save(out/'derived'/(state+'_border.png'),border)
   save(out/'derived'/(state+'_campaign.png'),icon(layer,(58,64)))
   save(out/'construction'/(state+'.png'),icon(layer,(150,70)))
   states[state]={'site':site['id'],'source_tag':tag,'frame':ref(out,frame),'body':ref(out,out/'masks'/(state+'-body.png')),
    'bbox':list(m.getbbox()),'entrance':site['entrance'],'z':site['z'],'body_alpha_values':[0,255],
    'semantic_limit':'Full form includes own contact court/steps, not only opaque wall pixels; exposed click body needs final inspection.'}
 # Restrict recovery to authored removal budget. Surrounding approved pixels are
 # byte-identical; fully-built replay replaces these recovered pixels exactly.
 # Feather only INSIDE the explicit opaque source budget. This is technical
 # inpaint compositing, never painted architecture or a translucent building.
 # Outside the budget the approved surroundings remain byte-identical.
 recovery_mix=ImageChops.multiply(union,union.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.25)))
 bg=Image.composite(Image.open(out/'empty-recovery-native.png').convert('RGBA'),full,recovery_mix)
 save(out/'background-native.png',bg);save(out/'whole-removal-budget.png',union)
 complete=[]
 for site in sorted(plan['sites'],key=lambda s:s['z']):
  complete.extend(site['states']if site['id']=='coast'else[site['states'][-1]])
 # Site's fully-built key differs from raw ordering when intermediary specials
 # were inserted in the preserved source; current plan maps that order honestly.
 scene=bg.copy()
 for state in complete:scene.alpha_composite(Image.open(out/states[state]['frame']['path']).convert('RGBA'))
 save(out/'fully-built-replayed.png',scene)
 delta=ImageChops.difference(scene.convert('RGB'),full.convert('RGB'));save(out/'fully-built-difference.png',delta)
 early=bg.copy();early_keys=[]
 for site in sorted(plan['sites'],key=lambda s:s['z']):
  key=site['states'][0];early_keys.append(key);early.alpha_composite(Image.open(out/states[key]['frame']['path']).convert('RGBA'))
 save(out/'earliest-all-sites.png',early)
 dump(out/'candidate-frames.json',{'status':'authored configuration','candidate_only':True,'region':slug,'canvas':[800,374],
  'approved_full':ref(out,out/'approved-full-native.png'),'background':ref(out,out/'background-native.png'),
  'fully_built_replayed':ref(out,out/'fully-built-replayed.png'),'fully_built_pixel_difference_bbox':delta.getbbox(),
  'complete_scene_states':complete,'early_scene_states':early_keys,'states':states,
  'missing_work':['Fine roof/body click-mask review','Every-state mixed occlusion/support/path validation','Painted recovery seam review','Actual native compiler twice and construction atlas','Independent source/art review; no staging or game acceptance']})
 print(json.dumps({'region':slug,'frames':len(states),'full_difference_bbox':delta.getbbox()}))

if __name__=='__main__':
 for slug in CONFIG:assemble(slug)
