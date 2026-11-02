from prepare_inputs import *
old=Image.open(ROOT/load(HERE/'input-pins.json')['approved_silo_override']['frame']['path']).convert('RGBA')
new=Image.open(TOWN/'native-transforms-v14/resourceSilo/layer.png').convert('RGBA')
diff=ImageChops.difference(old,new);a=ImageChops.difference(old.getchannel('A'),new.getchannel('A'));rgb=ImageChops.difference(old.convert('RGB'),new.convert('RGB'));r,g,b=rgb.split();m=ImageChops.lighter(ImageChops.lighter(r,g),b).point(lambda a:255 if a else 0);vis=ImageChops.multiply(m,ImageChops.lighter(old.getchannel('A'),new.getchannel('A')).point(lambda a:255 if a else 0))
print(json.dumps({'alpha_difference_bbox':a.getbbox(),'all_rgb_difference_bbox':rgb.getbbox(),'visible_difference_bbox':vis.getbbox(),'visible_different_pixels':vis.histogram()[255]}))
