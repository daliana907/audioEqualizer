# -*- coding: utf-8 -*-
import unittest
import sys
import os
import types

pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
parent_dir = os.path.abspath(os.path.join(pkg_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

mock_log = types.ModuleType('logHandler')
mock_log.log = types.SimpleNamespace(
    info=lambda *a, **k: None,
    error=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None
)
sys.modules['logHandler'] = mock_log

from audioEqualizer import logger

class TestLoggerDiagnostics(unittest.TestCase):
    def setUp(self):
        os.makedirs(os.path.dirname(logger.LOG_FILE_PATH), exist_ok=True)

    def test_log_error_formatting(self):
        try:
            raise ValueError("Prueba de valor invalido")
        except ValueError as ve:
            logger.log_error(
                "Error en prueba unitaria",
                exc=ve,
                component="TestRunner",
                context={"test_key": "test_value"}
            )
        
        self.assertTrue(os.path.isfile(logger.LOG_FILE_PATH))
        with open(logger.LOG_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("ERROR EN TESTRUNNER", content)
        self.assertIn("Prueba de valor invalido", content)
        self.assertIn("test_key: test_value", content)

    def test_write_audit_log(self):
        logger.write_audit_log(
            enabled=True,
            preamp=-2.0,
            auto_preamp=True,
            mono=False,
            swap_channels=False,
            balance=0,
            tone_bass=1.5,
            tone_treble=-1.0,
            sub_bass=True,
            anti_box=True,
            clarity=True,
            anti_sibilance=True,
            anti_fatigue=True,
            ground_hum=True,
            loudness=True,
            subsonic=True,
            nvda_voice=True,
            stereo_width=120,
            gains=[0.0] * 31,
            lines_written=["Preamp: -2.0 dB"],
            apo_config_path=r"C:\fake\nvda_equalizer.txt",
            apo_include_ok=True
        )
        with open(logger.LOG_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("ESTADO DEL ECUALIZADOR: [ACTIVADO Y PROCESANDO AUDIO]", content)
        self.assertIn("Filtro subs", content)
        self.assertIn("120% (Procesamiento matricial)", content)

if __name__ == '__main__':
    unittest.main()
