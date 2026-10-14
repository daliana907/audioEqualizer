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
import builtins
builtins._ = lambda x: x

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
            self.profile.preamp = 25.0  # Máximo es 20.0
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

    def test_surround_and_radar_attributes(self):
        self.assertFalse(self.profile.surround_3d)
        self.assertFalse(self.profile.radar_mode)
        self.profile.surround_3d = True
        self.profile.radar_mode = True
        self.assertTrue(self.profile.surround_3d)
        self.assertTrue(self.profile.radar_mode)
        
        cloned = self.profile.clone()
        self.assertTrue(cloned.surround_3d)
        self.assertTrue(cloned.radar_mode)


from audioEqualizer.dummy_backend import DummyBackend
from audioEqualizer.equalizer import EqualizerController

class TestEqualizerController(unittest.TestCase):

    def setUp(self):
        import tempfile
        self._temp_dir = tempfile.mkdtemp()
        from audioEqualizer import config as eq_config
        self._orig_get_state_file = eq_config._get_state_file
        eq_config._get_state_file = lambda: os.path.join(self._temp_dir, "state.json")
        mock_nvda_config.conf = {'audioEqualizer': {}}

        self.backend = DummyBackend()
        self.controller = EqualizerController(self.backend)

    def tearDown(self):
        import shutil
        from audioEqualizer import config as eq_config
        eq_config._get_state_file = self._orig_get_state_file
        shutil.rmtree(self._temp_dir, ignore_errors=True)
        mock_nvda_config.conf = {'audioEqualizer': {}}

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
        self.assertIn("L=1.325*L+-0.175*R", copy_line)
        self.assertIn("R=-0.175*L+1.325*R", copy_line)

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


class TestConfigParsers(unittest.TestCase):

    def test_parse_bool(self):
        from audioEqualizer.config import _parse_bool
        self.assertTrue(_parse_bool(True))
        self.assertFalse(_parse_bool(False))
        self.assertTrue(_parse_bool("true"))
        self.assertTrue(_parse_bool("1"))
        self.assertTrue(_parse_bool("YES"))
        self.assertTrue(_parse_bool("si"))
        self.assertFalse(_parse_bool("false"))
        self.assertFalse(_parse_bool("0"))
        self.assertFalse(_parse_bool("no"))
        self.assertTrue(_parse_bool(None, default=True))
        self.assertFalse(_parse_bool("invalid_string", default=False))

    def test_parse_float(self):
        from audioEqualizer.config import _parse_float
        self.assertEqual(_parse_float(3.5), 3.5)
        self.assertEqual(_parse_float(" -4.2 "), -4.2)
        self.assertEqual(_parse_float("corrupted", default=1.0), 1.0)
        self.assertEqual(_parse_float(None, default=0.0), 0.0)

    def test_parse_int(self):
        from audioEqualizer.config import _parse_int
        self.assertEqual(_parse_int(42), 42)
        self.assertEqual(_parse_int("42"), 42)
        self.assertEqual(_parse_int("42.7"), 43)
        self.assertEqual(_parse_int("invalid", default=10), 10)
        self.assertEqual(_parse_int(None, default=5), 5)

    def test_parse_gains(self):
        from audioEqualizer.config import _parse_gains
        from audioEqualizer.constants import NUM_BANDS
        # Lista normal
        gains = [1.0] * NUM_BANDS
        self.assertEqual(_parse_gains(gains), gains)

        # Cadena separada por comas (formato ConfigObj cuando no parsea como lista)
        comma_str = ", ".join(["2.5"] * NUM_BANDS)
        parsed = _parse_gains(comma_str)
        self.assertEqual(len(parsed), NUM_BANDS)
        self.assertTrue(all(g == 2.5 for g in parsed))

        # Lista corta rellenada con 0.0
        short_gains = [3.0, -2.0]
        parsed_short = _parse_gains(short_gains)
        self.assertEqual(len(parsed_short), NUM_BANDS)
        self.assertEqual(parsed_short[0], 3.0)
        self.assertEqual(parsed_short[1], -2.0)
        self.assertEqual(parsed_short[2], 0.0)

        # Clamping de límites excedidos
        out_of_bounds = [99.0] + [-99.0] + [0.0] * (NUM_BANDS - 2)
        parsed_clamped = _parse_gains(out_of_bounds)
        self.assertEqual(parsed_clamped[0], 12.0)
        self.assertEqual(parsed_clamped[1], -12.0)


class TestConfigPersistence(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.test_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.test_dir, "audioEqualizer_state.json")
        
        from audioEqualizer import config as eq_config
        self.orig_get_state_file = eq_config._get_state_file
        eq_config._get_state_file = lambda: self.state_file

        class MockConfDict(dict):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.save_called = False
            def save(self):
                self.save_called = True

        mock_nvda_config.conf = MockConfDict({'audioEqualizer': {}})

    def tearDown(self):
        import shutil
        from audioEqualizer import config as eq_config
        eq_config._get_state_file = self.orig_get_state_file
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_profile_calls_save_and_writes_state_file(self):
        from audioEqualizer import config as eq_config
        profile = eq_config.EqualizerProfile(
            enabled=True,
            preamp=-2.5,
            auto_preamp=True,
            balance=-15,
            stereo_width=130,
            surround_3d=True,
            radar_mode=False,
            gains=[1.0] * 31,
            profile_index=2,
        )
        eq_config.save_profile(profile)

        # Verifica que se llamó config.conf.save()
        self.assertTrue(mock_nvda_config.conf.save_called)
        
        # Verifica que se guardó en el diccionario de NVDA
        c = mock_nvda_config.conf["audioEqualizer"]
        self.assertTrue(c["enabled"])
        self.assertEqual(c["preamp"], -2.5)
        self.assertEqual(c["balance"], -15)
        self.assertTrue(c["surround_3d"])

        # Verifica que se escribió el archivo JSON atómico
        self.assertTrue(os.path.exists(self.state_file))
        import json
        with open(self.state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data["enabled"])
        self.assertEqual(data["preamp"], -2.5)
        self.assertEqual(data["stereo_width"], 130)

    def test_load_profile_restores_from_state_file_when_conf_is_empty(self):
        from audioEqualizer import config as eq_config
        # Escribimos un estado previo en el archivo JSON
        profile_data = {
            "enabled": True,
            "preamp": -4.0,
            "auto_preamp": True,
            "loudness": True,
            "balance": 20,
            "surround_3d": True,
            "radar_mode": True,
            "stereo_width": 140,
            "profile_index": 3,
            "gains": [2.0] * 31,
        }
        import json
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(profile_data, f)

        # Dejamos mock_nvda_config.conf["audioEqualizer"] vacío (simulando reinicio antes de flush)
        mock_nvda_config.conf["audioEqualizer"] = {}

        loaded = eq_config.load_profile()
        self.assertTrue(loaded.enabled)
        self.assertEqual(loaded.preamp, -4.0)
        self.assertTrue(loaded.auto_preamp)
        self.assertTrue(loaded.loudness)
        self.assertEqual(loaded.balance, 20)
        self.assertTrue(loaded.surround_3d)
        self.assertTrue(loaded.radar_mode)
        self.assertEqual(loaded.stereo_width, 140)
        self.assertEqual(loaded.profile_index, 3)
        self.assertEqual(loaded.gains[0], 2.0)

    def test_load_profile_with_aggregated_section_like_nvda(self):
        """Simula AggregatedSection de NVDA (que solo itera claves, no pares clave-valor)."""
        from audioEqualizer import config as eq_config

        class MockAggregatedSection:
            def __init__(self, data):
                self._data = data
            def __iter__(self):
                return iter(self._data.keys())
            def __getitem__(self, key):
                return self._data[key]
            def __contains__(self, key):
                return key in self._data

        mock_nvda_config.conf["audioEqualizer"] = MockAggregatedSection({
            "enabled": True,
            "preamp": 3.0,
            "profile_index": 5,
            "gains": [1.5] * 31,
        })

        loaded = eq_config.load_profile()
        self.assertTrue(loaded.enabled)
        self.assertEqual(loaded.preamp, 3.0)
        self.assertEqual(loaded.profile_index, 5)
        self.assertEqual(loaded.gains[0], 1.5)


if __name__ == "__main__":
    unittest.main()
