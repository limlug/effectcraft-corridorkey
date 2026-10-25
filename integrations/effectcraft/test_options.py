import tempfile
from pathlib import Path
import unittest
from options import validate, frame_range


class OptionsTests(unittest.TestCase):
    def test_frame_ranges_are_end_exclusive_and_preview_is_bounded(self):
        self.assertEqual(frame_range(24,240,1,2),(24,48))
        self.assertEqual(frame_range(24000/1001,240,1,2),(23,48))
        self.assertEqual(frame_range(24,240,1,None,True,2),(24,72))
        self.assertEqual(frame_range(24,30,1,None,True,2),(24,30))
        for a,b in [(10,None),(1,1),(3,2)]:
            with self.assertRaises(ValueError): frame_range(24,100,a,b)

    def test_validation_rejects_conflicting_hints_and_bad_matte(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'movie.mp4';source.touch()
            image=Path(tmp)/'matte.png';image.touch()
            self.assertEqual(validate({'input':str(source)})['matte_white'],1)
            for invalid in [dict(matte_black=.8,matte_white=.2),dict(matte_expand=1.5),dict(preview='true'),
                            dict(hint=str(image),hint_video=str(source)),dict(range_start=3,range_end=2),
                            dict(preview_scale=float('nan')),dict(context={'command':'unsafe'})]:
                with self.assertRaises(ValueError):validate(dict(input=str(source),**invalid))

    def test_picker_returns_selection_and_cancellation_without_blocking_ui(self):
        import time
        from unittest.mock import patch
        from types import SimpleNamespace
        from picker import Picker
        p=Picker()
        with patch("picker.shutil.which",return_value="zenity"), patch("picker.subprocess.run",return_value=SimpleNamespace(returncode=0,stdout="/tmp/matte.png\n")):
            result=p.start('image')
            deadline=time.monotonic()+1
            while p.status(result['id'])['state']=='pending' and time.monotonic()<deadline:time.sleep(.01)
            self.assertEqual(p.status(result['id'])['path'],'/tmp/matte.png')
        with patch("picker.shutil.which",return_value="zenity"), patch("picker.subprocess.run",return_value=SimpleNamespace(returncode=1,stdout="")):
            result=p.start('video')
            deadline=time.monotonic()+1
            while p.status(result['id'])['state']=='pending' and time.monotonic()<deadline:time.sleep(.01)
            self.assertEqual(p.status(result['id'])['state'],'cancelled')

    def test_picker_only_accepts_supported_kinds(self):
        from picker import Picker
        p=Picker()
        with self.assertRaises(ValueError): p.start('command')
        with self.assertRaises(ValueError): p.status('unknown')

if __name__=='__main__':unittest.main()
