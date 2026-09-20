# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""Pruebas de regresión: una por cada error real encontrado en la auditoría."""

import os
import sys
import tempfile
import threading
import unittest
import urllib.request
import types
from unittest.mock import MagicMock

for mod in ["wx", "gui", "globalPluginHandler", "logHandler", "globalCommands", "ui",
            "scriptHandler", "addonHandler"]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

import scriptHandler
if not hasattr(scriptHandler, "script"):
    scriptHandler.script = lambda *a, **k: (lambda f: f)

import globalPluginHandler
if not hasattr(globalPluginHandler, "GlobalPlugin"):
    globalPluginHandler.GlobalPlugin = object

import addonHandler
if not hasattr(addonHandler, "initTranslation"):
    addonHandler.initTranslation = lambda: None

if "config" not in sys.modules:
    sys.modules["config"] = types.ModuleType("config")
    sys.modules["config"].conf = {"audioEqualizer": {}}

import wx
if not hasattr(wx, "CallAfter"):
    wx.CallAfter = lambda fn, *args, **kwargs: fn(*args, **kwargs)
if not hasattr(wx, "CallLater"):
    wx.CallLater = lambda ms, fn, *args, **kwargs: types.SimpleNamespace(Stop=lambda: None)

if not hasattr(wx, "Dialog"):
    class _DialogoDeMentira:
        def __init__(self, *args, **kwargs):
            pass

        def Show(self):
            pass

        def Raise(self):
            pass

        def SetFocus(self):
            pass

        def Destroy(self):
            pass

        def Restore(self):
            pass

        def IsIconized(self):
            return False

        def IsShown(self):
            return True
    wx.Dialog = _DialogoDeMentira

import logHandler
if not hasattr(logHandler, "log"):
    logHandler.log = MagicMock()

import ui
if not hasattr(ui, "message"):
    ui.message = MagicMock()

pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
parent_dir = os.path.abspath(os.path.join(pkg_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from audioEqualizer.constants import NUM_BANDS
from audioEqualizer.equalizer import EqualizerController
from audioEqualizer.dummy_backend import DummyBackend


class DescargaDelInstaladorDeEqualizerApo(unittest.TestCase):
    """_download_worker tiene que conectarse de verdad y escribir lo descargado."""

    class _RespuestaFalsa:
        def __init__(self, datos):
            self._restante = datos
            self.headers = {"Content-Length": str(len(datos))}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, n=-1):
            trozo, self._restante = self._restante[:n], self._restante[n:]
            return trozo

    def test_descarga_escribe_los_datos_recibidos_en_el_archivo_destino(self):
        from audioEqualizer.downloader import DownloadProgressDialog

        contenido_falso = b"X" * 100
        original_urlopen = urllib.request.urlopen
        urllib.request.urlopen = lambda req, timeout=30: self._RespuestaFalsa(contenido_falso)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                destino = os.path.join(tmpdir, "instalador.exe")
                dlg = DownloadProgressDialog.__new__(DownloadProgressDialog)
                dlg._info = {"url": "https://ejemplo.invalido/instalador.exe", "min_expected_bytes": 10}
                dlg._target_path = destino
                dlg._tmp_path = destino + ".tmp"
                dlg._is_cancelled = False
                dlg._update_progress = lambda *a, **k: None
                dlg._close_with_result = lambda *a, **k: None

                dlg._download_worker()

                self.assertTrue(os.path.exists(destino))
                with open(destino, "rb") as f:
                    self.assertEqual(f.read(), contenido_falso)
        finally:
            urllib.request.urlopen = original_urlopen


class SobrescrituraDestructivaDeConfigTxt(unittest.TestCase):
    """_ensure_include_directive no debe borrar el resto del config.txt existente."""

    def test_agrega_la_directiva_sin_borrar_lo_que_ya_habia(self):
        from audioEqualizer.apo_backend import ApoBackend

        backend = ApoBackend()
        with tempfile.TemporaryDirectory() as tmpdir:
            ruta = os.path.join(tmpdir, "config.txt")
            contenido_de_otro_programa = (
                "# Configuracion de otro dispositivo\n"
                "Device: MiTarjetaDeSonido\n"
                "Preamp: -3 dB\n"
            )
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido_de_otro_programa)
            backend._main_config = ruta

            backend._ensure_include_directive()

            with open(ruta, "r", encoding="utf-8") as f:
                resultado = f.read()

            self.assertIn("Device: MiTarjetaDeSonido", resultado)
            self.assertIn("Preamp: -3 dB", resultado)
            self.assertIn(backend._include_directive, resultado)


class AlcanceDeCanalSinReiniciarAlEmpezar(unittest.TestCase):
    """El archivo propio del complemento debe reiniciar el alcance de canales a "todos"
    antes de aplicar sus propios filtros, sin depender de lo que haya quedado activo
    en config.txt justo antes de la línea Include que lo carga.
    """

    def test_el_archivo_empieza_reiniciando_el_alcance_a_todos_los_canales(self):
        from audioEqualizer.apo_backend import ApoBackend

        backend = ApoBackend()
        backend._enabled = True
        lineas = backend._build_config_lines()

        lineas_de_directivas = [
            l for l in lineas if l.strip() and not l.strip().startswith("#")
        ]
        self.assertTrue(lineas_de_directivas, "El archivo generado no tiene ninguna directiva.")
        self.assertEqual(lineas_de_directivas[0], "Channel: all")


class FiltroDeZumbidoElectricoConEcos(unittest.TestCase):
    """El filtro anti-zumbido debe recortar tanto la frecuencia principal (50/60 Hz)
    como sus ecos (100/120 Hz)."""

    def test_genera_los_cuatro_recortes(self):
        from audioEqualizer.apo_backend import ApoBackend

        backend = ApoBackend()
        backend._enabled = True
        backend._ground_hum = True
        lineas = backend._build_config_lines()

        for frecuencia in (50, 60, 100, 120):
            self.assertTrue(
                any(f"Fc {frecuencia} Hz" in linea for linea in lineas),
                f"Falta el recorte en {frecuencia} Hz",
            )


class ProtecciónDeVolumenAlElegirUnPerfilDeFabrica(unittest.TestCase):
    """Elegir un perfil de fábrica (que no trae su propio preamp seguro) debe activar
    el preamp automático, para no arrastrar un preamp manual que podría saturar el sonido
    con un perfil de bandas mucho más realzadas.
    """

    def setUp(self):
        self.backend = DummyBackend()
        self.controller = EqualizerController(self.backend)

    def test_ciclar_a_un_perfil_de_fabrica_activa_el_preamp_automatico(self):
        # Simula haber apagado el preamp automático a mano, como viene de fábrica.
        self.controller._current_profile.auto_preamp = False
        self.controller._current_profile.preamp = 0.0

        self.controller.next_profile()

        self.assertTrue(self.controller._current_profile.auto_preamp)

    def test_elegir_perfil_desde_la_ventana_tambien_activa_el_preamp_automatico(self):
        from audioEqualizer.dialog import EqualizerDialog

        dlg = EqualizerDialog.__new__(EqualizerDialog)
        dlg._profile = self.controller._current_profile
        dlg._profile.auto_preamp = False
        dlg._auto_preamp_cb = MagicMock()
        dlg._preamp_slider = MagicMock()
        dlg._band_sliders = []
        dlg._tone_bass_slider = MagicMock()
        dlg._tone_treble_slider = MagicMock()
        dlg._width_slider = MagicMock()
        dlg._sub_bass_cb = MagicMock()
        dlg._clarity_cb = MagicMock()
        dlg._anti_sibilance_cb = MagicMock()
        dlg._anti_fatigue_cb = MagicMock()
        dlg._subsonic_cb = MagicMock()
        dlg._nvda_voice_cb = MagicMock()
        dlg._loudness_cb = MagicMock()
        dlg._ground_hum_cb = MagicMock()
        dlg._update_tone_names = lambda: None
        dlg._update_width_name = lambda: None
        dlg._update_profile_buttons_state = lambda: None

        # Perfil 0 ("Plano") no trae su propio preamp: debe forzar el checkbox a True.
        dlg._apply_profile_to_ui(0)

        dlg._auto_preamp_cb.SetValue.assert_called_with(True)

    def test_restablecer_perfil_de_fabrica_preserva_el_preamp_automatico(self):
        """Restablecer un perfil de fábrica debe mantener el preamplificador automático activo."""
        from audioEqualizer.dialog import EqualizerDialog
        dlg = EqualizerDialog.__new__(EqualizerDialog)
        dlg._profile = self.controller._current_profile
        dlg._profile_choice = MagicMock()
        dlg._profile_choice.GetSelection.return_value = 1
        dlg._loudness_cb = MagicMock()
        dlg._mono_cb = MagicMock()
        dlg._swap_cb = MagicMock()
        dlg._balance_slider = MagicMock()
        dlg._update_balance_name = lambda: None
        dlg._width_slider = MagicMock()
        dlg._update_width_name = lambda: None
        dlg._tone_bass_slider = MagicMock()
        dlg._tone_treble_slider = MagicMock()
        dlg._update_tone_names = lambda: None
        dlg._sub_bass_cb = MagicMock()
        dlg._clarity_cb = MagicMock()
        dlg._anti_sibilance_cb = MagicMock()
        dlg._anti_fatigue_cb = MagicMock()
        dlg._ground_hum_cb = MagicMock()
        dlg._subsonic_cb = MagicMock()
        dlg._nvda_voice_cb = MagicMock()
        dlg._preamp_slider = MagicMock()
        dlg._auto_preamp_cb = MagicMock()
        dlg._band_sliders = []
        dlg._update_profile_buttons_state = lambda: None
        dlg._on_apply = MagicMock()

        dlg._on_reset(None)

        calls = dlg._auto_preamp_cb.SetValue.call_args_list
        self.assertTrue(any(c.args == (True,) for c in calls))
        self.assertFalse(any(c.args == (False,) for c in calls))


class CondicionDeCarreraEnLaPruebaDeCanales(unittest.TestCase):
    """Una segunda llamada mientras ya hay una prueba de canales en curso no debe
    arrancar otro hilo (que escribiría el mismo archivo temporal al mismo tiempo).
    """

    def setUp(self):
        from audioEqualizer import channel_tester
        self.channel_tester = channel_tester
        self._winsound_original = channel_tester.winsound
        channel_tester.winsound = MagicMock()

    def tearDown(self):
        self.channel_tester.winsound = self._winsound_original
        if self.channel_tester._test_in_progress.locked():
            self.channel_tester._test_in_progress.release()

    def test_segunda_llamada_mientras_hay_una_en_curso_no_arranca_otro_hilo(self):
        self.channel_tester._test_in_progress.acquire()
        hilos_antes = threading.active_count()

        self.channel_tester.play_channel_test()

        self.assertEqual(threading.active_count(), hilos_antes)


class ImportFaltanteEnRestablecerAPlano(unittest.TestCase):
    """reset_to_flat() no debe perder la referencia a una ventana que sigue abierta."""

    def setUp(self):
        self.backend = DummyBackend()
        self.controller = EqualizerController(self.backend)

    def test_reset_to_flat_no_pierde_la_ventana_si_seguia_abierta(self):
        mock_dlg = MagicMock()
        mock_dlg.__bool__.return_value = True
        self.controller._dialog_instance = mock_dlg

        self.controller.reset_to_flat()

        # Antes, por el import que faltaba, esto quedaba en None aunque la
        # ventana siguiera abierta y funcionando bien.
        self.assertIsNotNone(self.controller._dialog_instance)
        mock_dlg._apply_profile_to_ui.assert_called_once()


class DesajusteDeIndicesAlCiclarPerfiles(unittest.TestCase):
    """Ciclar perfiles con el atajo de teclado debe saltar el hueco de "Personalizado",
    igual que hace la ventana, para no aplicar un perfil de usuario distinto al anunciado.
    """

    def setUp(self):
        self.backend = DummyBackend()
        self.controller = EqualizerController(self.backend)

        import audioEqualizer.config as config_mod
        self._original_load_user_profiles = config_mod.load_user_profiles
        self.perfil_usuario = {"name": "Mi perfil", "gains": [7.0] * NUM_BANDS}
        config_mod.load_user_profiles = lambda: [self.perfil_usuario]

    def tearDown(self):
        import audioEqualizer.config as config_mod
        config_mod.load_user_profiles = self._original_load_user_profiles

    def test_desde_personalizado_el_siguiente_perfil_es_el_de_usuario_correcto(self):
        from audioEqualizer import profiles

        custom_index = len(profiles.PREDEFINED_PROFILES)
        self.controller._current_profile.profile_index = custom_index

        self.controller.next_profile()

        self.assertEqual(self.controller._current_profile.profile_index, custom_index + 1)
        self.assertEqual(self.controller._current_profile.gains, self.perfil_usuario["gains"])


class SincronizacionCompletaDePerfilesEnGui(unittest.TestCase):
    """Verifica que todos los perfiles de fabrica definan sus atributos acusticos
    y que al conmutar controles o perfiles en la GUI no se pierdan o queden en blanco.
    """

    def test_todos_los_perfiles_definen_claves_acusticas_completas(self):
        from audioEqualizer import profiles
        claves_requeridas = {
            "name", "gains", "tone_bass", "tone_treble", "sub_bass", "clarity",
            "anti_sibilance", "anti_fatigue", "ground_hum", "subsonic", "nvda_voice",
            "loudness", "stereo_width"
        }
        for prof in profiles.PREDEFINED_PROFILES:
            faltantes = claves_requeridas - set(prof.keys())
            self.assertEqual(len(faltantes), 0, f"Perfil '{prof.get('name')}' carece de claves: {faltantes}")

    def test_modificar_control_acustico_marca_perfil_personalizado(self):
        from audioEqualizer.dialog import EqualizerDialog
        from audioEqualizer import profiles

        dlg = EqualizerDialog.__new__(EqualizerDialog)
        dlg._profile_choice = MagicMock()
        dlg._profile_choice.GetSelection.return_value = 1  # Harman
        dlg._update_profile_buttons_state = MagicMock()
        dlg._on_apply = MagicMock()

        dlg._on_enhancement_check(None)

        dlg._profile_choice.SetSelection.assert_called_with(profiles.CUSTOM_INDEX)


if __name__ == "__main__":
    unittest.main(verbosity=2)
