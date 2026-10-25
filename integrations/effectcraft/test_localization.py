"""Catalog, installer and Unicode contracts; no GPU or network needed."""
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from build_panel import HERE, LANGUAGES, build_panel, catalogs
from install import install
from picker import Picker


class LocalizationTests(unittest.TestCase):
    def test_all_effectcraft_languages_have_complete_catalogs_and_placeholders(self):
        rows=catalogs()
        self.assertEqual(len(rows),12)
        for code, catalog in rows.items():
            for key, value in catalog.items():
                with self.subTest(language=code,key=key):
                    self.assertIsInstance(value,str)
                    self.assertTrue(value.strip())
                    self.assertNotIn('\ufffd',value)
                    self.assertEqual(sorted(re.findall(r'\{[a-zA-Z]+\}',key)),sorted(re.findall(r'\{[a-zA-Z]+\}',value)))

    def test_every_literal_translation_key_exists(self):
        source=(HERE/'CorridorKey.jsx').read_text(encoding='utf-8')
        source+=(HERE/'i18n.js').read_text(encoding='utf-8')
        keys=re.findall(r'\bt\(("(?:\\.|[^"\\])*")',source)
        for key in keys:self.assertIn(json.loads(key),catalogs()['en'])
        # German text no longer appears directly in the UI implementation.
        self.assertNotRegex((HERE/'CorridorKey.jsx').read_text(encoding='utf-8'),r'[äöüÄÖÜß]')

    def test_installed_panel_contains_all_catalogs_and_no_machine_paths_in_build(self):
        content=build_panel()
        self.assertNotIn(str(Path.home()),content)
        self.assertIn('createCorridorKeyI18n',content)
        with tempfile.TemporaryDirectory(prefix='panel_日本語_') as folder:
            target=install(folder)
            installed=target.read_text(encoding='utf-8')
            self.assertIn('CORRIDORKEY_CATALOGS',installed)
            for language in LANGUAGES:self.assertIn(json.dumps(language),installed)
            self.assertIn(json.dumps(str(Path(folder).resolve()/'corridorkey-connection.json')),installed)

    def test_picker_titles_follow_panel_language(self):
        from threading import Event
        for code in LANGUAGES:
            with self.subTest(language=code):
                picker=Picker()
                picker.requests['sample']={'state':'pending'}
                with patch('picker.shutil.which',return_value='zenity'),patch('picker.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='')) as run:
                    picker._run('sample','image',code)
                    title=next(arg for arg in run.call_args.args[0] if arg.startswith('--title='))
                    self.assertIn(catalogs()[code]['Choose mask…'],title)
                    self.assertEqual(picker.status('sample')['state'],'cancelled')

    def test_picker_rejects_untrusted_locale_paths(self):
        with self.assertRaises(ValueError):Picker().start('image','../../secrets')


if __name__=='__main__':unittest.main()
