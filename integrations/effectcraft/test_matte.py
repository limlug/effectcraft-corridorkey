"""Independent image finishing; numerical tests need NumPy/OpenCV, not CorridorKey."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

@unittest.skipUnless(importlib.util.find_spec('cv2'),'OpenCV environment required')
class MatteTests(unittest.TestCase):
    def test_identity_threshold_grow_shrink_and_feather(self):
        import numpy as np
        from postprocess import refine_alpha
        x=np.zeros((9,9),np.float32);x[3:6,3:6]=1
        np.testing.assert_array_equal(refine_alpha(x),x)
        self.assertEqual(refine_alpha(x,expand=1).sum(),25)
        self.assertEqual(refine_alpha(x,expand=-1).sum(),1)
        y=refine_alpha(x,feather=.8)
        self.assertTrue(0<y[2,4]<1)
        values=np.array([[0,.25,.5,.75,1]],np.float32)
        np.testing.assert_allclose(refine_alpha(values,black=.25,white=.75),[[0,0,.5,1,1]])

    def test_colour_and_alpha_are_independent(self):
        import numpy as np
        from postprocess import finish_pixels
        raw=np.array([[[.1,.8,.3,.5]]],np.float32)
        options={'matte_black':.25,'matte_white':.75,'matte_expand':0,'matte_feather':0,'despill':1}
        out=finish_pixels(raw,options,False)
        np.testing.assert_allclose(out,[[[.1,.2,.3,.5]]],rtol=1e-6)
        np.testing.assert_allclose(raw,[[[.1,.8,.3,.5]]],rtol=1e-6)

@unittest.skipUnless(importlib.util.find_spec('cv2'),'OpenCV environment required')
class MaskTests(unittest.TestCase):
    def test_bezier_mask_rasterization_and_inversion(self):
        import cv2
        from mask_hint import rasterize
        mask=dict(vertices=[[4,4],[28,4],[28,28],[4,28]],inTangents=[[0,0]]*4,outTangents=[[0,0]]*4,
                  width=32,height=32,inverted=False,opacity=100,feather=[0,0],expansion=0)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'mask.png';rasterize(mask,path)
            pixels=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE)
            self.assertEqual(pixels[16,16],255);self.assertEqual(pixels[0,0],0)
            mask['inverted']=True;rasterize(mask,path)
            pixels=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE)
            self.assertEqual(pixels[16,16],0);self.assertEqual(pixels[0,0],255)

if __name__=='__main__':unittest.main()
