# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import types

# Ensure required mock modules
for mod in ["wx", "gui", "globalPluginHandler", "logHandler", "globalCommands", "ui"]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

import wx
if not hasattr(wx, "CallAfter"):
    wx.CallAfter = lambda fn, *args, **kwargs: fn(*args, **kwargs)
if not hasattr(wx, "Dialog"):
    class FakeWxDialog:
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
    wx.Dialog = FakeWxDialog

import gui
if not hasattr(gui, "mainFrame"):
    gui.mainFrame = types.SimpleNamespace(
        prePopup=MagicMock(),
        postPopup=MagicMock(),
    )

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

from audioEqualizer.equalizer import EqualizerController
from audioEqualizer.apo_backend import ApoBackend
from audioEqualizer.dummy_backend import DummyBackend
from audioEqualizer.dialog import EqualizerDialog
from audioEqualizer.config import EqualizerProfile


class TestGuiResilience(unittest.TestCase):

    def setUp(self):
        self.backend = DummyBackend()
        self.controller = EqualizerController(self.backend)

    def test_is_dialog_active_when_none(self):
        self.controller._dialog_instance = None
        self.assertFalse(self.controller._is_dialog_active())

    def test_is_dialog_active_when_valid(self):
        mock_dlg = MagicMock()
        mock_dlg.__bool__.return_value = True
        self.controller._dialog_instance = mock_dlg
        self.assertTrue(self.controller._is_dialog_active())

    def test_is_dialog_active_when_dead_object(self):
        mock_dlg = MagicMock()
        mock_dlg.__bool__.side_effect = RuntimeError("wrapped C/C++ object has been deleted")
        self.controller._dialog_instance = mock_dlg
        self.assertFalse(self.controller._is_dialog_active())
        self.assertIsNone(self.controller._dialog_instance)

    def test_show_gui_restores_and_raises_existing_dialog(self):
        mock_dlg = MagicMock()
        mock_dlg.IsIconized.return_value = True
        mock_dlg.IsShown.return_value = False
        self.controller._dialog_instance = mock_dlg
        
        self.controller.show_gui()
        
        mock_dlg.Restore.assert_called_once()
        mock_dlg.Show.assert_called_once()
        mock_dlg.Raise.assert_called_once()
        mock_dlg.SetFocus.assert_called_once()

    @patch("audioEqualizer.equalizer.EqualizerDialog")
    def test_show_gui_recovers_gracefully_from_dead_existing_dialog(self, mock_eq_dlg_cls):
        mock_new_dlg = MagicMock()
        mock_eq_dlg_cls.return_value = mock_new_dlg
        
        mock_dead_dlg = MagicMock()
        mock_dead_dlg.Raise.side_effect = RuntimeError("dead object")
        self.controller._dialog_instance = mock_dead_dlg
        
        self.controller.show_gui()
        
        # Debe haberse recreado un nuevo diálogo sin lanzar excepción
        self.assertEqual(self.controller._dialog_instance, mock_new_dlg)
        mock_new_dlg.Show.assert_called_once()
        mock_new_dlg.Raise.assert_called_once()

    def test_terminate_destroys_dialog_safely(self):
        mock_dlg = MagicMock()
        self.controller._dialog_instance = mock_dlg
        
        self.controller.terminate()
        
        mock_dlg.Destroy.assert_called_once()
        self.assertIsNone(self.controller._dialog_instance)

    def test_dialog_cleanup_clears_controller_ref_and_calls_post_popup(self):
        dlg = EqualizerDialog.__new__(EqualizerDialog)
        dlg._controller = self.controller
        dlg._cleaned_up = False
        self.controller._dialog_instance = dlg
        
        with patch("gui.mainFrame.postPopup") as mock_post_popup:
            dlg.Destroy = MagicMock()
            dlg._cleanup()
            
            self.assertIsNone(self.controller._dialog_instance)
            mock_post_popup.assert_called_once()
            dlg.Destroy.assert_called_once()

    def test_apo_backend_is_available_detection(self):
        apo = ApoBackend()
        # Verificamos que _detect_and_init_paths corre sin error
        apo._detect_and_init_paths()
        self.assertTrue(hasattr(apo, "_config_dir"))
        self.assertTrue(hasattr(apo, "_main_config"))
        self.assertTrue(hasattr(apo, "_addon_config_path"))


if __name__ == '__main__':
    unittest.main()
