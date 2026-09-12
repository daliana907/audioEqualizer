# -*- coding: utf-8 -*-
import unittest
import sys
import os
import types

pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
parent_dir = os.path.abspath(os.path.join(pkg_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

mock_nvda_config = types.ModuleType('config')
mock_nvda_config.conf = {'audioEqualizer': {}}
sys.modules['config'] = mock_nvda_config

mock_log = types.ModuleType('logHandler')
mock_log.log = types.SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None, debug=lambda *a, **k: None)
sys.modules['logHandler'] = mock_log

mock_gph = types.ModuleType('globalPluginHandler')
mock_gph.GlobalPlugin = object
sys.modules['globalPluginHandler'] = mock_gph

mock_sh = types.ModuleType('scriptHandler')
mock_sh.script = lambda *a, **k: (lambda f: f)
sys.modules['scriptHandler'] = mock_sh

mock_ah = types.ModuleType('addonHandler')
mock_ah.initTranslation = lambda *a, **k: None
sys.modules['addonHandler'] = mock_ah

for mod_name in ['ui', 'speech', 'gui']:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = types.ModuleType(mod_name)
sys.modules['ui'].message = lambda *a, **k: None

from unittest.mock import patch, MagicMock
from audioEqualizer import downloader

class TestDownloader(unittest.TestCase):
    def test_get_system_arch(self):
        arch = downloader.get_system_arch()
        self.assertIn(arch, ("32", "64"))

    def test_get_apo_download_info_64(self):
        with patch.dict(os.environ, {"PROCESSOR_ARCHITECTURE": "AMD64"}):
            info = downloader.get_apo_download_info()
            self.assertEqual(info["arch"], "64")
            self.assertEqual(info["filename"], "EqualizerAPO64-1.3.exe")
            self.assertTrue(info["url"].endswith("EqualizerAPO64-1.3.exe"))

    def test_get_apo_download_info_32(self):
        with patch.dict(os.environ, {"PROCESSOR_ARCHITECTURE": "x86"}, clear=True), \
             patch("platform.machine", return_value="x86"):
            info = downloader.get_apo_download_info()
            self.assertEqual(info["arch"], "32")
            self.assertEqual(info["filename"], "EqualizerAPO32-1.3.exe")
            self.assertTrue(info["url"].endswith("EqualizerAPO32-1.3.exe"))

    def test_get_downloads_dir(self):
        d = downloader.get_downloads_dir()
        self.assertTrue(os.path.isabs(d))
        self.assertTrue(os.path.exists(d))

if __name__ == "__main__":
    unittest.main()
