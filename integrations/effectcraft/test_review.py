"""Image evidence for frame inspection, selection and the external reference workflow."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from options import validate
from runtime_cli import arguments

NUMERIC=bool(importlib.util.find_spec('cv2'))

class ReviewOptionsTests(unittest.TestCase):
    def test_new_options_validate_and_temporal_flags_use_public_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.mp4';path.touch()
            opts=validate(dict(input=str(path),temporal_window=16,despill_color='blue',core_strength=.5,reference_frame=8))
            args=arguments('/external',path,tmp,opts)
            self.assertEqual(args[args.index('--hann_chunk')+1],'16')
            self.assertEqual(args[args.index('--hann_stride')+1],'8')
            for invalid in ({'temporal_window':3},{'reference_frame':1.5},{'core_strength':2},{'despill_color':'red'}):
                with self.assertRaises(ValueError):validate(dict(input=str(path),**invalid))

    def test_gpu_query_is_optional_and_parses_multiple_devices(self):
        from review import gpu_status
        with patch('review.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='Test GPU, 16384, 1024, 15360\nSecond GPU, 8192, 4096, 4096')):
            data=gpu_status();self.assertEqual(len(data['devices']),2);self.assertEqual(data['devices'][0]['free_mb'],15360)
        with patch('review.subprocess.run',side_effect=OSError):self.assertFalse(gpu_status()['available'])

@unittest.skipUnless(NUMERIC,'NumPy/OpenCV required')
class ReviewImageTests(unittest.TestCase):
    def test_blue_green_and_off_spill_preserve_other_channels_and_alpha(self):
        import numpy as np
        from postprocess import finish_pixels
        raw=np.array([[[.9,.1,.3,.4]]],np.float32)
        options=dict(matte_black=0,matte_white=1,matte_expand=0,matte_feather=0,despill=1,despill_color='blue')
        out=finish_pixels(raw,options,False)
        np.testing.assert_allclose(out,[[[.2,.1,.3,.4]]],rtol=1e-6)
        options['despill_color']='off';np.testing.assert_array_equal(finish_pixels(raw,options,False),raw)
        options['despill_color']='green';np.testing.assert_array_equal(finish_pixels(raw,options,False),raw)

    def test_core_fills_interior_without_crushing_semitransparent_edges(self):
        import numpy as np
        from postprocess import finish_pixels
        raw=np.ones((9,9,4),np.float32)*.95;raw[:,:,3]=.95;raw[0,:,3]=.3
        o=dict(matte_black=0,matte_white=1,matte_expand=0,matte_feather=0,despill=0,core_strength=1,edge_strength=.5)
        result=finish_pixels(raw,o,False)
        self.assertAlmostEqual(result[0,4,3],.15,places=5)
        self.assertGreater(result[4,4,3],.7)
        np.testing.assert_array_equal(result[:,:,:3],raw[:,:,:3])

    def test_background_split_extremes_and_matte(self):
        import numpy as np
        from review import composite
        source=np.full((4,8,3),7,np.uint8);rgba=np.zeros((4,8,4),np.uint8);rgba[:,:,:3]=200;rgba[:,:,3]=128
        black=composite(source,rgba,'black',0,'comparison');white=composite(source,rgba,'white',0,'comparison')
        self.assertGreater(white[0,0,0],black[0,0,0])
        np.testing.assert_array_equal(composite(source,rgba,'black',1,'comparison'),source)
        self.assertTrue((composite(source,rgba,'black',0,'matte')==128).all())
        bg=np.full_like(source,33);rgba[:,:,3]=0
        np.testing.assert_array_equal(composite(source,rgba,view='checker',backdrop=bg),bg)

    def test_foreground_and_background_clicks_separate_a_synthetic_subject(self):
        import numpy as np
        from review import seeded_mask
        image=np.zeros((100,100,3),np.uint8);image[:,:,1]=180;image[30:70,35:65]=[10,10,220]
        mask=seeded_mask(image,[dict(x=.5,y=.5,keep=True),dict(x=.1,y=.1,keep=False)])
        self.assertEqual(mask[50,50],255);self.assertEqual(mask[10,10],0)
        with self.assertRaises(ValueError):seeded_mask(image,[dict(x=2,y=.5,keep=True)])
        with self.assertRaises(ValueError):seeded_mask(image,[dict(x=.1,y=.1,keep=False)])

    def test_combined_masks_subtract_regardless_of_mask_order(self):
        import cv2
        import numpy as np
        from mask_hint import rasterize_stack
        def square(a,b):return dict(vertices=[[a,a],[b,a],[b,b],[a,b]],inTangents=[[0,0]]*4,outTangents=[[0,0]]*4,width=32,height=32,inverted=False,opacity=100,feather=[0,0],expansion=0)
        stack=[dict(mode='remove',mask=square(12,20)),dict(mode='keep',mask=square(4,28))]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'mask.png';rasterize_stack(stack,path);pixels=cv2.imread(str(path),0)
            self.assertEqual(pixels[8,8],255);self.assertEqual(pixels[16,16],0);self.assertEqual(pixels[0,0],0)
            rasterize_stack(list(reversed(stack)),path);np.testing.assert_array_equal(cv2.imread(str(path),0),pixels)

@unittest.skipUnless(NUMERIC and shutil.which('ffmpeg') and shutil.which('ffprobe'),'NumPy/OpenCV and FFmpeg required')
class ReviewWorkflowTests(unittest.TestCase):
    def wait(self,tasks,job):
        end=time.monotonic()+30
        while time.monotonic()<end:
            result=tasks.status(job['id'])
            if result['state']!='running':break
            time.sleep(.02)
        self.assertEqual(result['state'],'completed',result)
        return result['result']

    def test_exact_frame_review_zoom_and_reference_overlay(self):
        import cv2
        import numpy as np
        from review import Review
        from tasks import Tasks
        import threading
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);source=folder/'source.mkv'
            subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=green:s=64x48:r=24','-frames:v','3','-c:v','ffv1',str(source)],check=True)
            sequence=folder/'sequence';sequence.mkdir()
            import os;os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
            for i in range(3):
                rgba=np.ones((48,64,4),np.float32);rgba[:,:,:3]=i*.2;rgba[:,:,3]=.5;cv2.imwrite(str(sequence/f'{i:06d}.exr'),rgba)
            job=dict(state='completed',input=str(source),output=str(sequence/'000000.exr'),sequence=True,first_frame=0,frame_count=3,native_fps=24)
            jobs=SimpleNamespace(output_root=folder,jobs={'test':job},lock=threading.RLock());tasks=Tasks();review=Review(jobs,tasks)
            try:
                result=self.wait(tasks,review.detail(dict(id='test',frame=2,zoom=2,background='white',view='checker')))
                image=cv2.imread(result['path']);self.assertEqual(image.shape[:2],(24,32));self.assertEqual(result['frame'],2)
                ref=self.wait(tasks,review.reference(dict(input=str(source),frame=1)));self.assertEqual(ref['frame'],1)
                mask=folder/'small.png';cv2.imwrite(str(mask),np.ones((2,2),np.uint8)*255)
                task=review.reference(dict(input=str(source),frame=1,hint=str(mask)))
                while tasks.status(task['id'])['state']=='running':time.sleep(.01)
                self.assertEqual(tasks.status(task['id'])['state'],'failed')
            finally:tasks.close()

    def test_bidirectional_worker_preserves_frame_order_without_patching_external_program(self):
        import cv2
        import numpy as np
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);external=folder/'external';external.mkdir();out=folder/'job';out.mkdir()
            source=folder/'source.mkv'
            for i in range(4):cv2.imwrite(str(folder/f'in_{i:03d}.png'),np.full((32,48,3),30+i*40,np.uint8))
            subprocess.run(['ffmpeg','-v','error','-y','-framerate','24','-i',str(folder/'in_%03d.png'),'-c:v','ffv1',str(source)],check=True)
            # A standalone CLI fixture exports actual decoded frames, making order observable.
            cli='''import argparse,cv2,os,numpy as np
from pathlib import Path
os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
p=argparse.ArgumentParser();p.add_argument('--input');p.add_argument('--output_dir');a,_=p.parse_known_args()
f=Path(a.output_dir)/'fixture_cutout_exr';f.mkdir(parents=True)
c=cv2.VideoCapture(a.input);i=0
while True:
 ok,bgr=c.read()
 if not ok:break
 rgba=np.concatenate([bgr.astype(np.float32)/255,np.ones((*bgr.shape[:2],1),np.float32)],axis=2)
 cv2.imwrite(str(f/f'{i:06d}.exr'),rgba);i+=1
'''
            (external/'infer.py').write_text(cli)
            options=validate(dict(input=str(source),hint=str(folder/'in_002.png'),reference_frame=2,output_format='exr',despill=0,despill_color='off'))
            spec=dict(id='fixture',folder=str(out),options=options)
            proc=subprocess.run([sys.executable,str(Path(__file__).parent/'worker.py'),'--root',str(external)],input=json.dumps(dict(spec=spec))+'\n',text=True,capture_output=True,timeout=60)
            self.assertEqual(proc.returncode,0,proc.stderr);result=json.loads(proc.stdout);self.assertTrue(result['ok'],result)
            self.assertEqual(result['model_loads'],2);self.assertEqual(result['frame_count'],4)
            values=[cv2.imread(str(p),cv2.IMREAD_UNCHANGED)[0,0,0] for p in sorted((out/'cache').glob('*.exr'))]
            np.testing.assert_allclose(values,np.array([30,70,110,150])/255,atol=.01)
            self.assertEqual((external/'infer.py').read_text(),cli)

if __name__=='__main__':unittest.main()
