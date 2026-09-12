# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Auditoría y detección dinámica de conflictos de atajos de teclado
para Audio Equalizer con otros complementos y comandos globales de NVDA.
"""

import wx
import gui
import globalPluginHandler
import logHandler

try:
    _
except NameError:
    _ = lambda s: s


def format_gesture_name(gesture_str):
    """Convierte un identificador interno como 'kb:nvda+shift+e' en un texto amigable como 'NVDA + Shift + E'."""
    s = str(gesture_str).lower().strip()
    if s.startswith("kb:"):
        s = s[3:]
    parts = s.split("+")
    res = []
    for p in parts:
        p = p.strip()
        if p == "nvda":
            res.append("NVDA")
        elif p == "shift":
            res.append("Shift")
        elif p == "control":
            res.append("Control")
        elif p == "alt":
            res.append("Alt")
        else:
            res.append(p.upper())
    return " + ".join(res)


def audit_conflicts(plugin):
    """
    Audita los atajos actualmente configurados en Audio Equalizer comparándolos
    contra todos los complementos activos y comandos globales de NVDA.
    
    Lee dinámicamente el mapa `_gestureMap` en memoria, por lo que detecta
    inmediatamente cualquier cambio o personalización realizada por el usuario
    en 'Gestos de entrada'.
    
    Devuelve: (conflicts, warnings)
    """
    conflicts = []
    warnings = []

    logHandler.log.info("AudioEqualizer: Iniciando auditoría dinámica de atajos y conflictos...")

    # 1. Obtener atajos vigentes de este complemento (incluye modificaciones del usuario)
    our_gestures = {}
    g_map = getattr(plugin, "_gestureMap", {}) or {}
    for g_id, script_ref in g_map.items():
        norm_g = str(g_id).strip().lower().replace(" ", "")
        desc = (
            getattr(script_ref, "description", "")
            or getattr(script_ref, "__doc__", "")
            or getattr(script_ref, "__name__", str(script_ref))
        )
        our_gestures[norm_g] = (script_ref, desc)

    if not our_gestures:
        logHandler.log.debug("AudioEqualizer: No se detectaron gestos vinculados en el mapa del complemento.")

    # 2. Comprobar otros complementos activos en ejecución
    try:
        running = getattr(globalPluginHandler, "runningPlugins", set())
        for other in running:
            if other is plugin:
                continue

            other_mod = getattr(other, "__module__", str(type(other)))
            if "audioequalizer" in other_mod.lower():
                continue

            # Nombre legible del complemento
            addon_name = other_mod
            try:
                parts = other_mod.split(".")
                if len(parts) > 1 and parts[0] == "globalPlugins":
                    addon_name = parts[1]
            except Exception:
                pass

            other_map = getattr(other, "_gestureMap", {}) or {}
            if not other_map:
                other_map = getattr(other, "_ScriptableObject__gestures", {}) or {}

            for other_g, other_script in other_map.items():
                norm_other = str(other_g).strip().lower().replace(" ", "")
                if norm_other in our_gestures:
                    _, our_desc = our_gestures[norm_other]
                    other_desc = (
                        getattr(other_script, "description", "")
                        or getattr(other_script, "__doc__", "")
                        or getattr(other_script, "__name__", str(other_script))
                    )
                    friendly_key = format_gesture_name(norm_other)
                    msg = (
                        f"Atajo '{friendly_key}': asignado a '{our_desc}' (Audio Equalizer) "
                        f"y en conflicto con '{other_desc}' en el complemento '{addon_name}'."
                    )
                    conflicts.append(msg)
                    logHandler.log.warning(f"AudioEqualizer CONFLICTO DETECTADO: {msg}")
    except Exception as e:
        logHandler.log.error(f"AudioEqualizer: Error al auditar gestos de complementos activos: {e}", exc_info=True)

    # 3. Comprobar comandos globales nativos de NVDA
    try:
        import globalCommands
        cmd_obj = getattr(globalCommands, "commands", None)
        if cmd_obj:
            cmd_map = getattr(cmd_obj, "_gestureMap", {}) or {}
            for cmd_g, cmd_script in cmd_map.items():
                norm_cmd = str(cmd_g).strip().lower().replace(" ", "")
                if norm_cmd in our_gestures:
                    _, our_desc = our_gestures[norm_cmd]
                    cmd_desc = (
                        getattr(cmd_script, "description", "")
                        or getattr(cmd_script, "__name__", str(cmd_script))
                    )
                    friendly_key = format_gesture_name(norm_cmd)
                    msg = (
                        f"Atajo '{friendly_key}': asignado a '{our_desc}' (Audio Equalizer) "
                        f"y en conflicto con el comando nativo de NVDA '{cmd_desc}'."
                    )
                    conflicts.append(msg)
                    logHandler.log.warning(f"AudioEqualizer CONFLICTO CON NVDA CORE: {msg}")
    except Exception as e:
        logHandler.log.debug(f"AudioEqualizer: No se pudo verificar comandos globales nativos: {e}")

    # Resumen en log
    if not conflicts and not warnings:
        logHandler.log.info("AudioEqualizer: Auditoría de conflictos finalizada. Sin colisiones detectadas.")
    else:
        logHandler.log.warning(
            f"AudioEqualizer: Auditoría finalizada con {len(conflicts)} conflicto(s) "
            f"y {len(warnings)} advertencia(s)."
        )

    return conflicts, warnings


def show_conflict_dialog(plugin):
    """Ejecuta la auditoría y muestra un diálogo accesible con el resultado."""
    conflicts, warnings = audit_conflicts(plugin)
    
    if not conflicts and not warnings:
        gui.messageBox(
            _(
                "No se han detectado conflictos de atajos de teclado con otros complementos activos en este sistema.\n\n"
                "Todos los atajos configurados para el Ecualizador de Audio están listos para usarse sin interferencias."
            ),
            _("Auditoría de conflictos - Ecualizador de Audio"),
            wx.OK | wx.ICON_INFORMATION
        )
        return

    lines = [
        _(
            "Se han detectado posibles conflictos de atajos de teclado con otros complementos o comandos activos:\n"
        )
    ]
    if conflicts:
        for c in conflicts:
            lines.append(f"• {c}")

    if warnings:
        if conflicts:
            lines.append("")
        for w in warnings:
            lines.append(f"• {w}")

    lines.append("")
    lines.append(
        _(
            "Sugerencia: Puedes cambiar o personalizar cualquiera de estos atajos en el menú de "
            "NVDA > Preferencias > Gestos de entrada > Audio Equalizer."
        )
    )

    gui.messageBox(
        "\n".join(lines),
        _("Conflictos detectados - Ecualizador de Audio"),
        wx.OK | wx.ICON_WARNING
    )
