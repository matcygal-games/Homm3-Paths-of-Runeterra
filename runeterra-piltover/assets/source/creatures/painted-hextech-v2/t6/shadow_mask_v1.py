"""Technical grayscale cast shadow from exact own painted alpha, no actor art."""
from PIL import Image,ImageFilter
def projected_shadow(actor,ground_y):
 alpha=actor.getchannel('A');ground=float(ground_y);shear=.5;vertical=.35
 mask=alpha.transform(actor.size,Image.Transform.AFFINE,(1,-shear/vertical,shear/vertical*ground,0,1/vertical,-(1-vertical)/vertical*ground),Image.Resampling.BILINEAR)
 mask=mask.point(lambda a:round(a*96/255)).filter(ImageFilter.GaussianBlur(.55))
 result=Image.new('RGBA',actor.size);result.putalpha(mask);return result
def embedded_shadow(actor,ground_y):
 shadow=projected_shadow(actor,ground_y)
 # Preserve every nonzero-alpha source body pixel byte-exact. Only previously
 # empty background pixels receive the derived ground shadow.
 empty=actor.getchannel('A').point(lambda a:255 if a==0 else 0)
 result=actor.copy();result.paste(shadow,(0,0),empty);return result
