import unittest
from datetime import date,time
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import os
from PIL import Image
from overlay import draw_overlay,load_photo,export_image,calculate_overlay_geometry,validate_assets

class OverlayTests(unittest.TestCase):
    def test_sizes_and_exports(self):
        for size in [(1600,1200),(1920,1080),(1280,720),(1080,1920),(1000,1000),(2048,1536),(4000,3000),(320,320),(4000,320),(320,4000)]:
            with self.subTest(size=size):
                im=Image.new('RGB',size,'#8a9299')
                before=im.tobytes()
                out=draw_overlay(im,date(2026,9,25),time(10,49))
                self.assertEqual(out.size,size)
                self.assertEqual(im.tobytes(),before)
                g=calculate_overlay_geometry(*size)
                self.assertGreaterEqual(g.x,0); self.assertGreaterEqual(g.y,0)
                self.assertLessEqual(g.x+g.width,size[0]); self.assertLessEqual(g.y+g.height,size[1])
                for fmt in ['JPEG','PNG']:
                    decoded=Image.open(BytesIO(export_image(out,fmt)))
                    self.assertEqual(decoded.size,size)
                    self.assertEqual(len(decoded.getexif()),0)
    def test_long_fields_and_changes(self):
        im=Image.new('RGB',(1600,1200),'gray')
        base=draw_overlay(im,date(2026,9,25),time(10,49))
        long=draw_overlay(im,date(2026,9,25),time(10,49),location='A very long location name in Gujarat India with multiple additional place names',address='An unusually long street address with many descriptive building names and landmarks, '+ 'district street Gujarat India '*5)
        token=draw_overlay(im,date(2026,9,25),time(10,49),address='A'*180)
        self.assertNotEqual(base.tobytes(),long.tobytes())
        self.assertNotEqual(base.tobytes(),token.tobytes())
        for day,clock in [(date(2026,9,26),time(10,49)),(date(2026,9,25),time(23,59))]:
            self.assertNotEqual(base.tobytes(),draw_overlay(im,day,clock).tobytes())
        with self.assertRaises(ValueError):
            draw_overlay(im,date.today(),time(),address='A'*10000)
    def test_invalid_and_orientation(self):
        for data in [b'',b'not an image']:
            with self.assertRaises(ValueError): load_photo(data)
        b=BytesIO(); Image.new('RGB',(100,100)).save(b,format='PNG')
        with self.assertRaises(ValueError): load_photo(b.getvalue())
        b=BytesIO(); Image.new('RGB',(600,400)).save(b,format='JPEG',exif=Image.Exif())
        self.assertEqual(load_photo(b.getvalue()).size,(600,400))
        e=Image.Exif(); e[274]=6
        b=BytesIO(); Image.new('RGB',(600,400)).save(b,format='JPEG',exif=e)
        self.assertEqual(load_photo(b.getvalue()).size,(400,600))
        self.assertEqual(Image.open(BytesIO(b.getvalue())).getexif()[274],6)
    def test_assets_from_other_directory(self):
        old=os.getcwd()
        try:
            with TemporaryDirectory() as td:
                os.chdir(td); validate_assets()
        finally: os.chdir(old)

if __name__=='__main__': unittest.main()
