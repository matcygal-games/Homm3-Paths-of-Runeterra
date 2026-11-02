"""Native traced public pavement ownership, independent of path solver.

These masks remove only the surrounding paved frontage aprons. Building roofs,
walls, pen floors, fenced arenas and attached entrance steps remain state-owned.
The complete scene is unchanged: removed public pavement belongs to background.
"""
from PIL import Image,ImageDraw,ImageChops
SIZE=(800,374)
def polygon(points):
 m=Image.new('L',SIZE);ImageDraw.Draw(m).polygon(points,fill=255);return m
def clip_to_boundary(image,points):
 # An upper clipping region retains everything above the hand traced lower edge.
 keep=polygon([(0,0),(799,0)]+list(reversed(points)))
 result=image.copy();result.putalpha(ImageChops.multiply(image.getchannel('A'),keep));return result
def apply(state,image):
 points=None
 if state in ('special4','dwellingLvl7','dwellingUpLvl7'):
  points=[(0,286),(728,286),(738,289),(776,291),(787,284),(799,283)]
 elif state in ('dwellingLvl3','dwellingUpLvl3'):
  points=[(0,238),(270,238),(277,242),(286,243),(293,239),(799,239)]
 elif state=='dwellingUpLvl1':
  points=[(0,238),(190,238),(198,243),(208,243),(216,239),(227,239),(228,247),(240,247),(242,239),(799,239)]
 elif state in ('dwellingLvl2','dwellingUpLvl2'):
  points=[(0,236),(579,236),(585,239),(596,239),(603,236),(799,236)]
 elif state=='tavern':
  points=[(0,331),(30,328),(49,337),(79,333),(111,329),(127,335),(160,334),(174,321),(799,321)]
 elif state=='marketplace':
  points=[(0,329),(176,329),(187,333),(226,332),(257,335),(300,335),(324,329),(349,324),(799,324)]
 return clip_to_boundary(image,points)if points else image
