import unittest
from unittest.mock import MagicMock, patch
import sys
import types

# Asegurar módulos requeridos para el test
for mod in ["wx", "gui", "globalPluginHandler", "logHandler", "globalCommands"]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

import globalPluginHandler
if not hasattr(globalPluginHandler, "runningPlugins"):
    globalPluginHandler.runningPlugins = set()

import logHandler
if not hasattr(logHandler, "log"):
    logHandler.log = MagicMock()
for method in ["debug", "info", "warning", "error"]:
    if not hasattr(logHandler.log, method):
        setattr(logHandler.log, method, MagicMock())

import gui
if not hasattr(gui, "messageBox"):
    gui.messageBox = MagicMock()

import wx
if not hasattr(wx, "OK"):
    wx.OK = 4
    wx.ICON_INFORMATION = 1
    wx.ICON_WARNING = 2

import globalCommands
if not hasattr(globalCommands, "commands"):
    globalCommands.commands = MagicMock()
    globalCommands.commands._gestureMap = {}

from audioEqualizer.conflicts import format_gesture_name, audit_conflicts


class DummyScript:
    def __init__(self, name, desc):
        self.__name__ = name
        self.description = desc


class DummyPlugin:
    def __init__(self, name="dummyPlugin"):
        self.__module__ = f"globalPlugins.{name}"
        self._gestureMap = {}


class TestConflicts(unittest.TestCase):
    def test_format_gesture_name(self):
        self.assertEqual(format_gesture_name("kb:nvda+shift+e"), "NVDA + Shift + E")
        self.assertEqual(format_gesture_name("kb:control+shift+e"), "Control + Shift + E")
        self.assertEqual(format_gesture_name("kb:nvda+e"), "NVDA + E")
        self.assertEqual(format_gesture_name("kb:alt+f4"), "Alt + F4")

    def test_no_conflicts_when_no_other_plugins(self):
        plugin = DummyPlugin("audioEqualizer")
        plugin._gestureMap = {
            "kb:nvda+e": DummyScript("script_open", "Abrir ecualizador"),
            "kb:nvda+shift+e": DummyScript("script_toggle", "Alternar ecualizador"),
        }
        with patch.object(globalPluginHandler, "runningPlugins", {plugin}):
            conflicts, warnings = audit_conflicts(plugin)
            self.assertEqual(len(conflicts), 0)

    def test_detects_conflict_with_other_plugin(self):
        our_plugin = DummyPlugin("audioEqualizer")
        our_plugin._gestureMap = {
            "kb:nvda+shift+e": DummyScript("script_toggle", "Alternar ecualizador"),
        }

        other_plugin = DummyPlugin("monitorSistema")
        other_plugin._gestureMap = {
            "kb:nvda+shift+e": DummyScript("script_summary", "Resumen de recursos"),
        }

        with patch.object(globalPluginHandler, "runningPlugins", {our_plugin, other_plugin}):
            conflicts, warnings = audit_conflicts(our_plugin)
            self.assertEqual(len(conflicts), 1)
            self.assertIn("NVDA + Shift + E", conflicts[0])
            self.assertIn("monitorSistema", conflicts[0])

    def test_detects_dynamically_changed_gesture(self):
        our_plugin = DummyPlugin("audioEqualizer")
        other_plugin = DummyPlugin("otroPlugin")
        
        # El otro plugin usa NVDA+Alt+X
        other_plugin._gestureMap = {
            "kb:nvda+alt+x": DummyScript("script_x", "Accion de otro plugin"),
        }

        with patch.object(globalPluginHandler, "runningPlugins", {our_plugin, other_plugin}):
            # Inicialmente nuestro plugin usa NVDA+E (sin conflicto)
            our_plugin._gestureMap = {
                "kb:nvda+e": DummyScript("script_open", "Abrir ecualizador"),
            }
            conflicts, _ = audit_conflicts(our_plugin)
            self.assertEqual(len(conflicts), 0)

            # El usuario personaliza el atajo en Gestos de entrada a NVDA+Alt+X
            our_plugin._gestureMap = {
                "kb:nvda+alt+x": DummyScript("script_open", "Abrir ecualizador"),
            }
            conflicts, _ = audit_conflicts(our_plugin)
            # Debe detectar el nuevo atajo inmediatamente
            self.assertEqual(len(conflicts), 1)
            self.assertIn("NVDA + Alt + X", conflicts[0])

    def test_detects_conflict_with_nvda_core_commands(self):
        our_plugin = DummyPlugin("audioEqualizer")
        our_plugin._gestureMap = {
            "kb:nvda+t": DummyScript("script_custom", "Comando personalizado"),
        }

        globalCommands.commands._gestureMap = {
            "kb:nvda+t": DummyScript("script_title", "Decir título de la ventana"),
        }

        with patch.object(globalPluginHandler, "runningPlugins", {our_plugin}):
            conflicts, warnings = audit_conflicts(our_plugin)
            self.assertEqual(len(conflicts), 1)
            self.assertIn("comando nativo de NVDA", conflicts[0])


if __name__ == "__main__":
    unittest.main()
