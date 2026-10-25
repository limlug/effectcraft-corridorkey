"""Installer contracts without network, GPU, downloads or package installation."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('setup_effectcraft',ROOT/'setup_effectcraft.py')
setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)


class SetupTests(unittest.TestCase):
    def test_plan_pins_code_and_weights_and_installs_panel_last(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'Unicode_日本語 folder'
            plan=setup.commands(root,'python','EffectCraft',False)
            commands=[c for c,_ in plan]
            self.assertIn(['git','checkout','--detach',setup.REVISION],commands)
            self.assertTrue(any(setup.MODEL_REVISION in c for c in commands))
            self.assertEqual(commands[-1][-1],'--check')
            self.assertTrue(any(str(root/'runtime/CorridorKey2.0/requirements.txt') in c for c in commands))
            self.assertTrue(any('torch==2.9.1' in c for c in commands))
            self.assertFalse(any(c[0] in ('sh','bash','cmd') for c in commands))

    def test_existing_runtime_is_not_reset_to_another_commit(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime=Path(folder);(runtime/'.git').mkdir()
            with patch.object(setup.subprocess,'check_output',return_value='unexpected-sha\n'),patch.object(setup.subprocess,'run') as run:
                with self.assertRaisesRegex(RuntimeError,'not reset'):
                    setup.execute([(['git','checkout','--detach',setup.REVISION],runtime)],runtime)
                run.assert_not_called()

    def test_new_clone_can_checkout_the_pinned_revision(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime=Path(folder);(runtime/'.git').mkdir()
            commands=[(['git','clone','--no-checkout',setup.UPSTREAM,str(runtime)],runtime),(['git','checkout','--detach',setup.REVISION],runtime)]
            with patch.object(setup.subprocess,'run') as run,patch.object(setup.subprocess,'check_output') as read:
                setup.execute(commands,runtime)
                self.assertEqual(run.call_count,2);read.assert_not_called()

    def test_setup_contains_no_patch_or_upstream_code_edits(self):
        with tempfile.TemporaryDirectory() as folder:
            plan=setup.commands(Path(folder),'python','EffectCraft')
            self.assertFalse(any('apply' in command or 'reset' in command for command,_ in plan))

    def test_modified_existing_runtime_is_refused_without_reset(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime=Path(folder);(runtime/'.git').mkdir()
            with patch.object(setup.subprocess,'check_output',side_effect=[setup.REVISION+'\n',' M corridorkey/runtime.py','']),patch.object(setup.subprocess,'run') as run:
                with self.assertRaisesRegex(RuntimeError,'not reset'):
                    setup.execute([(['git','checkout','--detach',setup.REVISION],runtime)],runtime)
                run.assert_not_called()


if __name__=='__main__':unittest.main()
