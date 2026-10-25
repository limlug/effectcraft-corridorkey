"""Architectural boundary and subprocess cancellation checks without model imports."""
import ast
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from runtime_cli import arguments
from processes import run

HERE=Path(__file__).resolve().parent

class WrapperTests(unittest.TestCase):
    def test_no_corridorkey_imports_in_any_wrapper_module(self):
        for path in HERE.glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or ''] if isinstance(node,ast.ImportFrom) else []
                self.assertFalse(any(n=='corridorkey' or n.startswith('corridorkey.') for n in names),path.name)

    def test_only_original_cli_arguments_are_used(self):
        options=dict(hint_quality=.95,preview=False,preview_scale=.5,low_vram=True)
        args=arguments(Path('/external'),'/source_日本語.mp4',Path('/output'),options,'/mask.png','/mask.mov')
        self.assertEqual(args[1],str(Path('/external/infer.py')))
        self.assertIn('--hint_first_frame',args);self.assertIn('--hint_video',args)
        self.assertIn('--low_vram',args)
        self.assertEqual(args[args.index('--despill_strength')+1],'0')
        self.assertEqual(args[args.index('--output_format')+1],'exr')
        for arg in ('--cancel_path','--cache_dir','--matte_black'):self.assertNotIn(arg,args)

    def test_cancellation_stops_the_external_process(self):
        with tempfile.TemporaryDirectory() as folder:
            cancel=Path(folder)/'cancel';timer=threading.Timer(.2,cancel.touch);timer.start()
            started=time.monotonic()
            try:
                with self.assertRaises(InterruptedError):run([sys.executable,'-c','import time;time.sleep(30)'],cancel)
            finally:timer.join()
            self.assertLess(time.monotonic()-started,8)

    def test_external_errors_are_diagnostic_not_silent_success(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError,'original CLI failed'):
                run([sys.executable,'-c','import sys;sys.stderr.write("original CLI failed");sys.exit(2)'],Path(folder)/'cancel')

if __name__=='__main__':unittest.main()
