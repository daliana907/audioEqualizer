import unittest
import sys
import os
import types
import importlib.util

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

mock_wx = types.ModuleType('wx')
mock_wx.Dialog = object
sys.modules['wx'] = mock_wx

for mod_name in ['ui', 'speech', 'gui']:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = types.ModuleType(mod_name)
sys.modules['ui'].message = lambda *a, **k: None

from audioEqualizer.constants import DEFAULT_ENABLED, DEFAULT_PREAMP, DEFAULT_GAINS, NUM_BANDS
from audioEqualizer.config import EqualizerProfile

class TestEqualizerProfile(unittest.TestCase):

    def setUp(self):
        self.profile = EqualizerProfile(enabled=DEFAULT_ENABLED, preamp=DEFAULT_PREAMP, gains=list(DEFAULT_GAINS))

    def test_default_initialization(self):
        self.assertEqual(self.profile.enabled, False)
        self.assertEqual(self.profile.preamp, 0.0)
        self.assertEqual(len(self.profile.gains), NUM_BANDS)
        self.assertTrue(all(g == 0.0 for g in self.profile.gains))

    def test_invalid_enabled_type(self):
        with self.assertRaises(TypeError):
            self.profile.enabled = "True"

    def test_invalid_preamp_type(self):
        with self.assertRaises(TypeError):
            self.profile.preamp = "foo"

    def test_preamp_out_of_bounds(self):
        with self.assertRaises(ValueError):
            self.profile.preamp = 5.0  # Máximo es 0.0
        with self.assertRaises(ValueError):
            self.profile.preamp = -25.0  # Mínimo es -20.0

    def test_gains_wrong_length(self):
        with self.assertRaises(ValueError):
            self.profile.gains = [0.0] * (NUM_BANDS - 1)
        with self.assertRaises(ValueError):
            self.profile.gains = [0.0] * (NUM_BANDS + 1)

    def test_gains_invalid_type(self):
        with self.assertRaises(TypeError):
            self.profile.gains = "invalid string"
            
        with self.assertRaises(TypeError):
            self.profile.gains = [0.0] * 30 + ["foo"]

    def test_gains_out_of_bounds(self):
        bad_gains = list(DEFAULT_GAINS)
        bad_gains[0] = 15.0 # Límite es 12.0
        with self.assertRaises(ValueError):
            self.profile.gains = bad_gains

        bad_gains[0] = -15.0 # Mínimo es -12.0
        with self.assertRaises(ValueError):
            self.profile.gains = bad_gains

    def test_clone(self):
        self.profile.preamp = -5.0
        self.profile.enabled = True
        
        cloned = self.profile.clone()
        self.assertEqual(cloned.enabled, True)
        self.assertEqual(cloned.preamp, -5.0)
        self.assertEqual(cloned.gains, self.profile.gains)
        
        # Verificar que es copia profunda
        self.assertIsNot(cloned, self.profile)
        self.assertIsNot(cloned.gains, self.profile.gains)


from audioEqualizer.dummy_backend import DummyBackend
from audioEqualizer.equalizer import EqualizerController

class TestEqualizerController(unittest.TestCase):

    def setUp(self):
        self.backend = DummyBackend()
        self.controller = EqualizerController(self.backend)

    def test_toggle_equalizer(self):
        init_state = self.controller._current_profile.enabled
        self.controller.toggle_equalizer()
        self.assertEqual(self.controller._current_profile.enabled, not init_state)
        self.assertEqual(self.backend.get_enabled(), not init_state)

    def test_cycle_profiles(self):
        self.controller.next_profile()
        self.assertEqual(self.controller._current_profile.profile_index, 1)
        self.controller.previous_profile()
        self.assertEqual(self.controller._current_profile.profile_index, 0)

    def test_adjust_tone(self):
        self.controller.adjust_tone_bass(1.0)
        self.assertAlmostEqual(self.controller._current_profile.tone_bass, 1.0)
        self.controller.adjust_tone_treble(-2.0)
        self.assertAlmostEqual(self.controller._current_profile.tone_treble, -2.0)


class TestStereoWidthApoFormatting(unittest.TestCase):

    def test_stereo_width_greater_than_100_has_valid_plus_separator(self):
        from audioEqualizer.apo_backend import ApoBackend
        backend = ApoBackend()
        backend._enabled = True
        backend._stereo_width = 150
        lines = backend._build_config_lines()
        copy_line = next((l for l in lines if l.startswith("Copy: L=")), None)
        self.assertIsNotNone(copy_line)
        # Debe contener el separador '+' antes del coeficiente negativo de R para que Equalizer APO lo parsee
        self.assertIn("*L+", copy_line)
        self.assertIn("L=1.25*L+-0.25*R", copy_line)
        self.assertIn("R=-0.25*L+1.25*R", copy_line)

    def test_stereo_width_less_than_100_has_valid_plus_separator(self):
        from audioEqualizer.apo_backend import ApoBackend
        backend = ApoBackend()
        backend._enabled = True
        backend._stereo_width = 50
        lines = backend._build_config_lines()
        copy_line = next((l for l in lines if l.startswith("Copy: L=")), None)
        self.assertIsNotNone(copy_line)
        self.assertIn("L=0.75*L+0.25*R", copy_line)
        self.assertIn("R=0.25*L+0.75*R", copy_line)


if __name__ == "__main__":
    unittest.main()
