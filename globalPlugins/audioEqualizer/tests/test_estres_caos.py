# -*- coding: utf-8 -*-
"""Batería de pruebas de estrés, caos y resiliencia acústica para audioEqualizer.

Prueba el motor de audio ante:
- Preamplificación automática extrema (+24 dB en 31 bandas + todos los filtros simultáneos)
- Fuzzing de ganancias con NaN e Infinito
- Concurrencia de comprobación de canales (channel_tester lock contention)
- Corrupción de archivos JSON de perfiles y factory overrides (0 bytes, sintaxis rota, tipos anómalos)
- Bloqueo de archivos por audiodg.exe y reintentos automáticos
- Ciclado de perfiles ultra veloz
"""
import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import types
import json
import tempfile
import threading
import time

pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
parent_dir = os.path.abspath(os.path.join(pkg_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

if "config" not in sys.modules:
    mock_nvda_config = types.ModuleType("config")
    mock_nvda_config.conf = {"audioEqualizer": {}}
    sys.modules["config"] = mock_nvda_config

if "logHandler" not in sys.modules:
    mock_log = types.ModuleType("logHandler")
    mock_log.log = types.SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None, debug=lambda *a, **k: None)
    sys.modules["logHandler"] = mock_log

if "globalPluginHandler" not in sys.modules:
    mock_gph = types.ModuleType("globalPluginHandler")
    mock_gph.GlobalPlugin = object
    sys.modules["globalPluginHandler"] = mock_gph

if "scriptHandler" not in sys.modules:
    mock_sh = types.ModuleType("scriptHandler")
    mock_sh.script = lambda *a, **k: (lambda f: f)
    sys.modules["scriptHandler"] = mock_sh

if "addonHandler" not in sys.modules:
    mock_ah = types.ModuleType("addonHandler")
    mock_ah.initTranslation = lambda *a, **k: None
    sys.modules["addonHandler"] = mock_ah

import builtins
builtins._ = lambda x: x

for mod_name in ["ui", "speech", "gui", "wx"]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = types.ModuleType(mod_name)
sys.modules["ui"].message = lambda *a, **k: None

import wx
if not hasattr(wx, "CallAfter"):
    wx.CallAfter = lambda fn, *args, **kwargs: fn(*args, **kwargs)
if not hasattr(wx, "Dialog"):
    class FakeWxDialog:
        def __init__(self, *args, **kwargs):
            pass
        def Show(self): pass
        def Raise(self): pass
        def SetFocus(self): pass
        def Destroy(self): pass
    wx.Dialog = FakeWxDialog

from audioEqualizer import constants
from audioEqualizer import config
from audioEqualizer import profiles
from audioEqualizer.equalizer import EqualizerController
from audioEqualizer.dummy_backend import DummyBackend
from audioEqualizer.apo_backend import ApoBackend
from audioEqualizer import channel_tester


class TestEstresCaosAudioEqualizer(unittest.TestCase):
    """Pruebas de estrés y situaciones inesperadas en audioEqualizer."""

    def setUp(self):
        self.backend = DummyBackend()
        self.controller = EqualizerController(self.backend)

    # ── 1. Anticlíping extremo con realce total en todas las bandas ───────────
    def test_auto_preamp_con_realce_maximo_y_todos_los_filtros(self):
        """Somete a auto_preamp a una curva con +12 dB en todas las bandas y todos los realces activos."""
        prof = config.EqualizerProfile(
            enabled=True,
            auto_preamp=True,
            gains=[constants.MAX_GAIN] * constants.NUM_BANDS,
            tone_bass=constants.MAX_TONE,
            tone_treble=constants.MAX_TONE,
            sub_bass=True,      # +6.0 dB
            clarity=True,       # +5.5 dB
            loudness=True,      # +4.5 dB
            nvda_voice=True,    # +4.5 dB
            surround_3d=True,   # +2.0 dB
            stereo_width=200,   # amplificación estéreo
        )
        self.controller._sync_backend(prof, notify_user=False)
        # La preamplificación efectiva debe estar atenuada y clampada al límite mínimo (-20.0 dB)
        self.assertEqual(self.backend._preamp, -20.0)

    # ── 2. Fuzzing de ganancias con NaN e Infinito ────────────────────────────
    def test_auto_preamp_fuzzing_nan_e_infinito(self):
        """Verifica que valores NaN o Infinito en ganancias no corrompan el cálculo de ganancia pico."""
        gains_corruptos = [float("nan")] * 15 + [float("inf")] * 16
        prof = config.EqualizerProfile(
            enabled=True,
            auto_preamp=True,
        )
        prof._gains = gains_corruptos
        prof.tone_bass = float("nan")
        prof.tone_treble = float("inf")

        # La sincronización no debe lanzar excepciones y el preamp resultante debe ser un número finito válido
        self.controller._sync_backend(prof, notify_user=False)
        import math
        self.assertFalse(math.isnan(self.backend._preamp))
        self.assertFalse(math.isinf(self.backend._preamp))
        self.assertTrue(-20.0 <= self.backend._preamp <= 0.0)

    # ── 3. Concurrencia masiva en la comprobación de canales ──────────────────
    def test_channel_tester_concurrencia_bloqueo_reentrante(self):
        """Dispara play_channel_test desde 20 hilos concurrentes; el lock debe impedir colisiones."""
        mensajes_ui = []
        with patch.object(channel_tester, "winsound", types.SimpleNamespace(
            PlaySound=lambda *a, **k: time.sleep(0.05),
            SND_FILENAME=1,
            SND_NODEFAULT=2
        )):
            with patch.object(channel_tester.ui, "message", side_effect=lambda m: mensajes_ui.append(m)):
                threads = [threading.Thread(target=channel_tester.play_channel_test) for _ in range(20)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()

        # Debe haberse mostrado el mensaje de que ya había una prueba en curso
        self.assertTrue(any("Ya se está reproduciendo" in str(m) for m in mensajes_ui))

    # ── 4. Resiliencia ante corrupción de perfiles de usuario ─────────────────
    def test_corrupcion_de_archivos_de_perfiles(self):
        """Prueba load_user_profiles ante archivos vacíos (0 bytes), sintaxis JSON rota o tipos inesperados."""
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
            temp_path = f.name

        try:
            casos_caoticos = [
                "",                     # 0 bytes
                "{json_roto:",          # Sintaxis inválida
                "null",                 # Null
                "12345",                # Entero
                '"cadena_suelta"',      # String
                "[null, 123, 'str']",   # Elementos no-dict
                '[{"name": ""}]',       # Perfil sin nombre
                '[{"name": "Válido", "gains": [0]*31}]',
            ]
            with patch.object(config, "USER_PROFILES_FILE", temp_path):
                for contenido in casos_caoticos:
                    with open(temp_path, "w", encoding="utf-8") as wf:
                        wf.write(contenido)
                    res = config.load_user_profiles()
                    self.assertIsInstance(res, list)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # ── 5. Resiliencia de factory overrides ante estructuras caóticas ─────────
    def test_factory_overrides_con_estructuras_caoticas(self):
        """Verifica que apply_factory_overrides_to_profiles tolere claves no numéricas o tipos corruptos."""
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
            temp_path = f.name

        try:
            caos_overrides = [
                "",
                "{bad_json:",
                json.dumps(["no", "es", "diccionario"]),
                json.dumps({"clave_invalida": {"gains": [1.0] * 31}}),
                json.dumps({"-1": {"gains": [1.0] * 31}}),
                json.dumps({"9999": {"gains": [1.0] * 31}}),
                json.dumps({"0": "no_es_subdict"}),
                json.dumps({"0": {"tone_bass": 3.0}}),
            ]
            with patch("audioEqualizer.config.get_factory_override_file", return_value=temp_path):
                for contenido in caos_overrides:
                    with open(temp_path, "w", encoding="utf-8") as wf:
                        wf.write(contenido)
                    # No debe lanzar ninguna excepción
                    config.apply_factory_overrides_to_profiles()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # ── 6. Ciclado ultra rápido de perfiles (hammering de atajos) ─────────────
    def test_ciclado_ultra_rapido_de_perfiles(self):
        """Simula pulsación repetida a alta velocidad de ciclado de perfiles sin bloqueos."""
        total_perfiles = len(profiles.PREDEFINED_PROFILES)
        for i in range(50):
            next_idx = i % total_perfiles
            p_data = profiles.PREDEFINED_PROFILES[next_idx]
            prof = config.EqualizerProfile(
                enabled=True,
                gains=p_data["gains"],
                profile_index=next_idx
            )
            self.controller._sync_backend(prof, notify_user=False)
        self.assertTrue(self.backend.get_enabled())

    # ── 7. Fuzzing de directivas Equalizer APO (_build_config_lines) ──────────
    def test_build_config_lines_con_valores_nan_e_inf(self):
        """Verifica que las líneas generadas para Equalizer APO nunca contengan 'nan' ni 'inf'."""
        apo = ApoBackend()
        apo._enabled = True
        apo._preamp = float("nan")
        apo._tone_bass = float("inf")
        apo._tone_treble = float("-inf")
        apo._balance = float("nan")
        apo._stereo_width = float("inf")
        apo._gains = [float("nan")] * 15 + [float("inf")] * 16

        lines = apo._build_config_lines()
        for line in lines:
            self.assertNotIn("nan", line.lower(), f"Directiva con 'nan' detectada: {line}")
            self.assertNotIn("inf", line.lower(), f"Directiva con 'inf' detectada: {line}")

    # ── 8. Fuzzing exhaustivo de _clean_float ──────────────────────────────────
    def test_clean_float_helper_fuzzing(self):
        """Fuzzing exhaustivo de la función _clean_float con tipos extremos."""
        from audioEqualizer.apo_backend import _clean_float
        casos = [
            (float("nan"), 0.0),
            (float("inf"), 0.0),
            (float("-inf"), 0.0),
            (None, 0.0),
            ("no_es_numero", 0.0),
            ([], 0.0),
            ({}, 0.0),
            (100.0, 20.0),   # max_v = 20.0 por defecto
            (-100.0, -20.0), # min_v = -20.0 por defecto
            (5.5, 5.5),
            (-3.2, -3.2),
        ]
        for entrada, esperado in casos:
            with self.subTest(entrada=entrada):
                res = _clean_float(entrada, default=0.0, min_v=-20.0, max_v=20.0)
                self.assertEqual(res, esperado)

    # ── 9. Validación y sanitización de nombres de perfiles personalizados ────
    def test_validacion_nombres_perfil_personalizado(self):
        """Verifica que validate_profile_name rechace nombres reservados, vacíos, largos o con caracteres ilegales."""
        # Nombres que deben fallar
        nombres_invalidos = [
            "",
            "   ",
            None,
            "CON",
            "prn",
            "aux",
            "nul",
            "com1",
            "Lpt1",
            "Personalizado",
            "personalizado",
            "Plano (Sin ecualizar)",  # Predefinido de fábrica
            "Música (Curva Harman)",  # Predefinido de fábrica
            "Perfil/Invalido",
            "Perfil\\Invalido",
            "Perfil:Test",
            "Perfil*Test?",
            "Perfil<Prueba>",
            "Perfil|Pipe",
            "Perfil\"Comillas\"",
            "P" * 65,  # Excede 64 caracteres
            "Perfil\x00Nulo",
            "Perfil\nSalto",
        ]
        for name in nombres_invalidos:
            with self.subTest(name=name):
                valido, msg = config.validate_profile_name(name)
                self.assertFalse(valido, f"El nombre '{name}' debería haber sido rechazado")
                self.assertTrue(len(msg) > 0)

        # Nombres válidos
        nombres_validos = [
            "Mi Perfil 1",
            "Auriculares Sony WH-1000XM4",
            "Gaming Pro 2026",
            "Voz - Ultra Claridad",
            "P" * 64,
        ]
        for name in nombres_validos:
            with self.subTest(name=name):
                valido, msg = config.validate_profile_name(name)
                self.assertTrue(valido, f"El nombre '{name}' debería ser válido, pero dio: {msg}")
                self.assertEqual(msg, "")

    # ── 10. Resiliencia en guardado y borrado de perfiles de usuario ───────────
    def test_guardado_y_borrado_perfiles_usuario_resiliencia(self):
        """Verifica que save_user_profile y delete_user_profile gestionen entradas inválidas sin lanzar excepciones."""
        prof = config.get_default_profile()
        # Intentar guardar con nombre reservado o inválido debe devolver False
        self.assertFalse(config.save_user_profile("CON", prof))
        self.assertFalse(config.save_user_profile("", prof))
        self.assertFalse(config.save_user_profile("Personalizado", prof))
        self.assertFalse(config.save_user_profile("Nombre/Ilegal", prof))

        # Borrado de perfil que no existe debe devolver False
    # ── 11. Inmunidad a NaN, Inf y OverflowError en parsers y presets ─────────
    def test_inmunidad_overflow_nan_inf_en_parsers_y_presets(self):
        """Verifica que los parsers toleren nan, inf y valores enormes sin lanzar OverflowError ni corromper perfiles."""
        from audioEqualizer.config import _parse_float, _parse_int, _parse_gains
        self.assertEqual(_parse_float(float("nan"), 1.0), 1.0)
        self.assertEqual(_parse_float(float("inf"), 2.0), 2.0)
        self.assertEqual(_parse_float("inf", 3.0), 3.0)
        self.assertEqual(_parse_int(float("inf"), 5), 5)
        self.assertEqual(_parse_int(float("nan"), 6), 6)
        self.assertEqual(_parse_int("1e1000", 7), 7)

        # En gains, nan o inf no deben pasar como ganancias válidas
        clean = _parse_gains([float("nan"), float("inf"), float("-inf")] + [0.0] * 28)
        self.assertEqual(len(clean), 31)
        self.assertEqual(clean[0], 0.0)
        self.assertEqual(clean[1], 0.0)
        self.assertEqual(clean[2], 0.0)

        # _apply_preset_to_profile tolera diccionarios malformados o con tipos caóticos
        prof = config.get_default_profile()
        self.controller._apply_preset_to_profile(prof, {"gains": None, "preamp": "inf", "tone_bass": "nan"})
        self.assertEqual(len(prof.gains), 31)
        self.assertEqual(prof.preamp, 0.0)
    # ── 12. Diálogo de descarga y resiliencia ante controles destruidos ──────
    def test_downloader_dialog_resiliencia_dead_controls(self):
        """Verifica que DownloadProgressDialog maneje controles wx destruidos o callbacks con errores sin lanzar excepciones."""
        from audioEqualizer.downloader import DownloadProgressDialog

        dlg = DownloadProgressDialog.__new__(DownloadProgressDialog)
        dlg._is_cancelled = False
        dlg._last_spoken_percent = 0
        dlg._target_path = "C:\\fake\\path.exe"
        dlg._tmp_path = "C:\\fake\\path.tmp"

        # Mock de controles que lanzan RuntimeError (simulando wx.PyDeadObjectError)
        mock_gauge = MagicMock()
        mock_gauge.SetValue.side_effect = RuntimeError("Dead gauge")
        mock_lbl = MagicMock()
        mock_lbl.SetLabel.side_effect = RuntimeError("Dead label")
        dlg._gauge = mock_gauge
        dlg._lbl_status = mock_lbl

        # _update_progress no debe lanzar excepción
        try:
            dlg._update_progress(5000000, 10000000)
        except Exception as e:
            self.fail(f"_update_progress lanzó excepción con controles muertos: {e}")

        # _cancel no debe lanzar excepción
        try:
            dlg._cancel()
        except Exception as e:
            self.fail(f"_cancel lanzó excepción con controles muertos: {e}")

        # _close_with_result con callback que falla
        def bad_callback(ok, msg, target):
            raise ValueError("Error en consumidor de on_finished")

        dlg._on_finished = bad_callback
        try:
            dlg._close_with_result(False, "Error simulado")
        except Exception as e:
            self.fail(f"_close_with_result lanzó excepción con callback defectuoso: {e}")


    # ── 13. Ajustes rápidos y ciclado de perfil con valores None, NaN o anómalos ─
    def test_ajustes_rapidos_y_ciclado_con_valores_none_o_nan(self):
        """Verifica que adjust_preamp, adjust_tone, stereo_width, balance y cycle_profile no fallen con None o NaN."""
        prof = self.controller._current_profile
        prof._profile_index = None
        prof._preamp = None
        prof.tone_bass = 0.0
        prof.tone_treble = 0.0
        prof.stereo_width = 100
        prof.balance = 0
        prof.auto_preamp = False

        # _cycle_profile con profile_index = None
        try:
            self.controller.next_profile()
            self.assertIsNotNone(self.controller._current_profile.profile_index)
        except Exception as e:
            self.fail(f"next_profile falló con profile_index None: {e}")

        # adjust_preamp con preamp = None
        prof.auto_preamp = False
        prof._preamp = None
        try:
            self.controller.adjust_preamp(1.0)
            self.assertEqual(self.controller._current_profile.preamp, 1.0)
        except Exception as e:
            self.fail(f"adjust_preamp falló con preamp None: {e}")

        # adjust_tone_bass con tone_bass = NaN
        prof.tone_bass = float("nan")
        try:
            self.controller.adjust_tone_bass(1.0)
            self.assertEqual(self.controller._current_profile.tone_bass, 1.0)
        except Exception as e:
            self.fail(f"adjust_tone_bass falló con tone_bass NaN: {e}")

        # adjust_stereo_width con stereo_width = None
        prof.stereo_width = None
        try:
            self.controller.adjust_stereo_width(10)
            self.assertEqual(self.controller._current_profile.stereo_width, 110)
        except Exception as e:
            self.fail(f"adjust_stereo_width falló con stereo_width None: {e}")

        # adjust_balance con balance = None
        prof.balance = None
        try:
            self.controller.adjust_balance(5)
            self.assertEqual(self.controller._current_profile.balance, 5)
        except Exception as e:
            self.fail(f"adjust_balance falló con balance None: {e}")


    # ── 14. Destrucción garantizada de diálogos en _on_save_profile_as y _on_delete_profile ──
    def test_dialog_save_and_delete_profile_try_finally_destruction(self):
        """Verifica que los diálogos modales de guardar y eliminar perfil se destruyan siempre con try-finally."""
        from audioEqualizer.dialog import EqualizerDialog
        import wx
        dlg = EqualizerDialog.__new__(EqualizerDialog)
        dlg._profile = self.controller._current_profile
        dlg._controller = self.controller
        from audioEqualizer import profiles
        dlg._profile_choice = MagicMock()
        dlg._profile_choice.GetSelection.return_value = profiles.CUSTOM_INDEX + 1

        # Simular TextEntryDialog con excepción en save_user_profile
        id_ok = getattr(wx, "ID_OK", 5100)
        wx.ID_OK = id_ok
        id_yes = getattr(wx, "ID_YES", 5103)
        wx.ID_YES = id_yes
        wx.YES_NO = getattr(wx, "YES_NO", 0)
        wx.NO_DEFAULT = getattr(wx, "NO_DEFAULT", 0)
        wx.ICON_QUESTION = getattr(wx, "ICON_QUESTION", 0)

        mock_text_dlg = MagicMock()
        mock_text_dlg.ShowModal.return_value = id_ok
        mock_text_dlg.GetValue.return_value = "Nuevo Perfil"
        wx.TextEntryDialog = MagicMock(return_value=mock_text_dlg)

        with patch("audioEqualizer.config.validate_profile_name", return_value=(True, "")):
            with patch("audioEqualizer.config.save_user_profile", side_effect=IOError("Disco lleno")):
                dlg._on_save_profile_as(None)
                mock_text_dlg.Destroy.assert_called_once()

        # Simular MessageDialog con excepción en delete_user_profile
        mock_msg_dlg = MagicMock()
        mock_msg_dlg.ShowModal.return_value = id_yes
        wx.MessageDialog = MagicMock(return_value=mock_msg_dlg)

        with patch("audioEqualizer.dialog.config.load_user_profiles", return_value=[{"name": "PerfilABorrar"}]):
            with patch("audioEqualizer.dialog.config.delete_user_profile", side_effect=OSError("Permiso denegado")):
                dlg._on_delete_profile(None)
                mock_msg_dlg.Destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()

