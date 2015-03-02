"""
http://stackoverflow.com/questions/10615901/trim-whitespace-using-pil
"""

from PIL import Image, ImageChops

def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)

im = Image.open("../images/test.jpg")
im.show()
im = trim(im)
im.show()