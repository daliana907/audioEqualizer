# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Módulo de registro y auditoría de filtros para Audio Equalizer.
Permite saber con certeza qué opciones marcadas se aplicaron realmente
en Equalizer APO y cuáles no tuvieron efecto (evitando el efecto placebo).
"""

import os
import traceback
from datetime import datetime
from typing import Any, List, Dict, Optional

try:
    from logHandler import log
except ImportError:
    import logging
    log = logging.getLogger("audioEqualizer")


def _get_log_file_path() -> str:
    """Devuelve la ruta del archivo de auditoría audioEqualizer.log dentro de la carpeta de configuración activa de NVDA."""
    try:
        import globalVars
        cfg = getattr(getattr(globalVars, "appArgs", None), "configPath", None)
        if cfg:
            return os.path.join(cfg, "audioEqualizer.log")
    except Exception:
        pass
    try:
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(appdata, "nvda", "audioEqualizer.log")
    except Exception:
        return os.path.join(os.path.dirname(__file__), "audioEqualizer.log")


def get_log_file_path() -> str:
    """Resuelve dinámicamente la ruta del log en cada llamada (no cacheada en import)."""
    try:
        dynamic = _get_log_file_path()
    except Exception:
        dynamic = os.path.join(os.path.dirname(__file__), "audioEqualizer.log")
    try:
        cached = globals().get("LOG_FILE_PATH")
        orig = globals().get("_ORIG_LOG_FILE_PATH")
        if cached and cached != dynamic and cached != orig:
            return cached
        if cached != dynamic:
            try:
                globals()["LOG_FILE_PATH"] = dynamic
            except Exception:
                pass
    except Exception:
        pass
    return dynamic


LOG_FILE_PATH = _get_log_file_path()
_ORIG_LOG_FILE_PATH = LOG_FILE_PATH


def write_audit_log(
    enabled: bool = False,
    preamp: float = 0.0,
    auto_preamp: bool = False,
    mono: bool = False,
    swap_channels: bool = False,
    balance: int = 0,
    tone_bass: float = 0.0,
    tone_treble: float = 0.0,
    sub_bass: bool = False,
    clarity: bool = False,
    anti_sibilance: bool = False,
    anti_fatigue: bool = False,
    ground_hum: bool = False,
    loudness: bool = False,
    subsonic: bool = False,
    nvda_voice: bool = False,
    surround_3d: bool = False,
    radar_mode: bool = False,
    stereo_width: int = 100,
    channel_mode: str = "stereo",
    center_gain: float = 0.0,
    subwoofer_gain: float = 0.0,
    surround_gain: float = 0.0,
    gains: List[float] = None,
    lines_written: List[str] = None,
    apo_config_path: str = "",
    apo_include_ok: bool = True,
    **kwargs
) -> None:
    """Registra en audioEqualizer.log el volcado detallado de parámetros, ganancias y sintaxis generada para Equalizer APO."""
    if gains is None:
        gains = []
    if lines_written is None:
        lines_written = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sep = "=" * 70
    subsep = "-" * 70

    report_lines = [
        sep,
        f"FECHA Y HORA DE ACTUALIZACIÓN: {now_str}",
        subsep,
    ]

    if not enabled:
        report_lines.extend([
            "ESTADO DEL ECUALIZADOR: [DESACTIVADO]",
            "¡ALERTA DE EFECTO PLACEBO!:",
            "  La casilla principal 'Ecualizador activado' está desmarcada.",
            "  Cualquier casilla o control que tengas marcado NO está teniendo efecto sonoro.",
            "  Para que las mejoras afecten el audio real, debes marcar 'Ecualizador activado'.",
            subsep,
        ])
    else:
        report_lines.extend([
            "ESTADO DEL ECUALIZADOR: [ACTIVADO Y PROCESANDO AUDIO]",
            "Las opciones marcadas con [EFECTO REAL: APLICADO] sí están modificando el sonido:",
            subsep,
        ])

        def _check(name: str, active: bool, directive: str):
            """Formatea una línea de auditoría indicando si el filtro está aplicado o inactivo."""
            if active:
                return f"  * {name}: [EFECTO REAL: APLICADO] -> {directive}"
            return f"  * {name}: [INACTIVO: NO MARCADO]"

        report_lines.append("MEJORAS PARA AURICULARES:")
        report_lines.append(_check(
            "Filtro subsónico infrasónico",
            subsonic,
            "Filter: ON HP Fc 20 Hz Q 0.707 (Protege transductores y limpia sobre-excursión)"
        ))
        report_lines.append(_check(
            "Claridad para sintetizador de voz (NVDA)",
            nvda_voice,
            "Filtros: -3.5 dB en 850 Hz, +4.5 dB en 2.8 kHz, -3.0 dB en 6.2 kHz (Máxima inteligibilidad)"
        ))

        report_lines.append(_check(
            "Extensión de subgraves 50-53 mm",
            sub_bass,
            "Filter: ON LS Fc 70 Hz Gain 6.0 dB Q 0.8"
        ))
        report_lines.append(_check(
            "Realce de claridad 5.5 kHz",
            clarity,
            "Filter: ON PK Fc 5500 Hz Gain 5.5 dB Q 1.2"
        ))
        report_lines.append(_check(
            "Filtro anti-sibilancia 7.5 kHz",
            anti_sibilance,
            "Filter: ON PK Fc 7500 Hz Gain -5.0 dB Q 1.8"
        ))
        report_lines.append(_check(
            "Filtro anti-fatiga auditiva 14 kHz",
            anti_fatigue,
            "Filter: ON HS Fc 14000 Hz Gain -4.5 dB Q 0.7 (Sonido cálido, suaviza estridencias)"
        ))
        report_lines.append(_check(
            "Filtro anti-zumbido eléctrico 50/60 Hz",
            ground_hum,
            "Filter: ON NO Fc 50 Hz Q 6 + NO Fc 60 Hz Q 6 (Elimina ground loop)"
        ))


        report_lines.append("\nMEJORAS ESPACIALES Y DE CANAL:")
        try:
            from .apo_backend import DISABLE_COPY_COMMANDS as _no_copy
        except Exception:
            _no_copy = False
        if stereo_width != 100:
            if _no_copy:
                report_lines.append(f"  * Ancho estéreo Mid/Side: [DESACTIVADO EN MODO COMPATIBLE] -> {stereo_width}% (sin efecto en este equipo)")
            else:
                report_lines.append(f"  * Ancho estéreo Mid/Side: [EFECTO REAL: APLICADO] -> {stereo_width}% (Procesamiento matricial)")
        else:
            report_lines.append("  * Ancho estéreo Mid/Side: [100%: ESTÉREO ESTÁNDAR]")

        report_lines.append(_check(
            "Compensación Loudness (Fletcher-Munson)",
            loudness,
            "Filter: ON LS Fc 80 Hz Gain 4.5 dB + Filter: ON HS Fc 9000 Hz Gain 3.0 dB"
        ))
        if _no_copy and mono:
            report_lines.append("  * Forzado de audio mono: [DESACTIVADO EN MODO COMPATIBLE]")
        else:
            report_lines.append(_check(
                "Forzado de audio mono",
                mono,
                "Copy: L=0.5*L+0.5*R R=0.5*L+0.5*R"
            ))
        if _no_copy and swap_channels:
            report_lines.append("  * Invertir canales estéreo (L/R): [DESACTIVADO EN MODO COMPATIBLE]")
        else:
            report_lines.append(_check(
                "Invertir canales estéreo (L/R)",
                swap_channels,
                "Copy: L=R R=L"
            ))
        if _no_copy and surround_3d:
            report_lines.append("  * Efecto 3D Espacial (Haas): [DESACTIVADO EN MODO COMPATIBLE]")
        else:
            report_lines.append(_check(
                "Efecto 3D Espacial (Haas)",
                surround_3d,
                "Delay: 15 ms + Preamp: -6 dB + Filter: LP Fc 4000 Hz"
            ))
        if _no_copy and radar_mode:
            report_lines.append("  * Modo Radar Posicional (HRTF crossfeed): [DESACTIVADO EN MODO COMPATIBLE]")
        else:
            report_lines.append(_check(
                "Modo Radar Posicional (HRTF crossfeed)",
                radar_mode,
                "Delay: 0.35 ms + LP Fc 1500 Hz + EQ 4 kHz"
            ))
        try:
            from . import constants as _consts
            _es_estereo = (channel_mode == _consts.CHANNEL_MODE_STEREO)
        except Exception:
            _es_estereo = (channel_mode == "stereo")
        if _es_estereo:
            if abs(center_gain) > 0.05:
                report_lines.append(f"  * Voces (aprox. estéreo de central): [EFECTO REAL: APLICADO] -> Filter: ON PK Fc 2800 Hz Gain {center_gain:.1f} dB")
            if abs(subwoofer_gain) > 0.05:
                report_lines.append(f"  * Graves LFE (aprox. estéreo de subwoofer): [EFECTO REAL: APLICADO] -> Filter: ON LS Fc 70 Hz Gain {subwoofer_gain:.1f} dB")

        if balance != 0:
            canal = "derecho" if balance < 0 else "izquierdo"
            att = round((abs(balance) / 100.0) * 20.0, 1)
            report_lines.append(f"  * Balance estéreo: [EFECTO REAL: APLICADO] -> {balance}% (Atenuación de -{att} dB en canal {canal})")
        else:
            report_lines.append("  * Balance estéreo: [CENTRAD0: SIN ALTERACIÓN]")

        if abs(tone_bass) > 0.05:
            report_lines.append(f"  * Graves rápidos (100 Hz): [EFECTO REAL: APLICADO] -> {tone_bass:.1f} dB")
        else:
            report_lines.append("  * Graves rápidos: [0.0 dB: SIN CAMBIOS]")

        if abs(tone_treble) > 0.05:
            report_lines.append(f"  * Agudos rápidos (8 kHz): [EFECTO REAL: APLICADO] -> {tone_treble:.1f} dB")
        else:
            report_lines.append("  * Agudos rápidos: [0.0 dB: SIN CAMBIOS]")

        report_lines.append(f"  * Preamplificación segura: {preamp:.1f} dB (Preamp automático: {'Sí' if auto_preamp else 'No'})")
        
        non_zero_bands = sum(1 for g in gains if abs(g) > 0.05)
        report_lines.append(f"  * Bandas de ecualización activas: {non_zero_bands} de {len(gains)} bandas con ganancia distinta de 0 dB.")

    report_lines.append(subsep)
    report_lines.append("DIAGNÓSTICO DEL MOTOR (EQUALIZER APO):")
    report_lines.append(f"  * Archivo del complemento: {apo_config_path} (Actualizado con {len(lines_written)} directivas)")
    report_lines.append(f"  * Vinculación en config.txt: {'CORRECTA (Include activo)' if apo_include_ok else 'FALLO: No se encontró el include'}")
    report_lines.append(sep + "\n")

    _log_path = get_log_file_path()
    try:
        os.makedirs(os.path.dirname(_log_path) or ".", exist_ok=True)
        if os.path.exists(_log_path) and os.path.getsize(_log_path) > 1024 * 1024:
            try:
                old_log = _log_path + ".old"
                if os.path.exists(old_log):
                    os.remove(old_log)
                os.rename(_log_path, old_log)
            except Exception:
                pass
        with open(_log_path, "a", encoding="utf-8", errors="replace") as f:
            f.write("\n".join(report_lines) + "\n")
    except Exception:
        log.error("AudioEqualizer: Error al escribir en el registro de auditoría.", exc_info=True)


def log_error(
    error_msg: str,
    exc: Optional[Exception] = None,
    component: str = "AudioEqualizer",
    context: Optional[Dict[str, Any]] = None
) -> None:
    """Registra errores detallados tanto en el nvda.log oficial como en audioEqualizer.log."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tb_str = ""
    if exc is not None:
        tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    elif traceback.format_exc().strip() != "NoneType: None":
        tb_str = traceback.format_exc()

    context_lines = []
    if context:
        context_lines.append("CONTEXTO Y PARÁMETROS:")
        for k, v in context.items():
            context_lines.append(f"  * {k}: {v}")

    err_lines = [
        "=" * 70,
        f"FECHA Y HORA: {now_str} - ERROR EN {component.upper()}",
        "-" * 70,
        f"DESCRIPCIÓN: {error_msg}",
    ]
    if context_lines:
        err_lines.extend(context_lines)
    if tb_str:
        err_lines.append("-" * 70)
        err_lines.append("TRAZA DE ERROR (TRACEBACK):")
        err_lines.append(tb_str.strip())
    err_lines.append("=" * 70 + "\n")

    # Registrar en el log del núcleo de NVDA (visible en NVDA+F1)
    log.error(f"{component}: {error_msg} | Detalle: {exc}\n{tb_str if tb_str else ''}")

    # Registrar de forma persistente en audioEqualizer.log
    _log_path2 = get_log_file_path()
    try:
        os.makedirs(os.path.dirname(_log_path2) or ".", exist_ok=True)
        if os.path.exists(_log_path2) and os.path.getsize(_log_path2) > 1024 * 1024:
            try:
                old_log = _log_path2 + ".old"
                if os.path.exists(old_log):
                    os.remove(old_log)
                os.rename(_log_path2, old_log)
            except Exception:
                pass
        with open(_log_path2, "a", encoding="utf-8", errors="replace") as f:
            f.write("\n".join(err_lines) + "\n")
    except Exception as io_err:
        log.error(f"AudioEqualizer: No se pudo escribir error en {_log_path2}: {io_err}", exc_info=True)


def get_voice_summary(profile: Any, profile_name: str = "") -> str:
    """Devuelve un resumen hablado claro para el lector de pantalla NVDA."""
    if not getattr(profile, 'enabled', False):
        return "Atención: El ecualizador general está desactivado. Todas las opciones marcadas son efecto placebo y no están sonando."

    active = []
    if getattr(profile, 'subsonic', False):
        active.append("Filtro subsónico 20 Hz")
    if getattr(profile, 'nvda_voice', False):
        active.append("Claridad para voz NVDA")
    
    if getattr(profile, 'sub_bass', False):
        active.append("Subgraves 70 Hz (+6 dB)")
    if getattr(profile, 'clarity', False):
        active.append("Claridad (+5.5 dB)")
    if getattr(profile, 'anti_sibilance', False):
        active.append("Filtro anti-sibilancia (-5 dB)")
    if getattr(profile, 'anti_fatigue', False):
        active.append("Filtro anti-fatiga 14 kHz")
    if getattr(profile, 'ground_hum', False):
        active.append("Filtro anti-zumbido 50/60 Hz")
    if getattr(profile, 'loudness', False):
        active.append("Loudness isofónico")
    try:
        from .apo_backend import DISABLE_COPY_COMMANDS as _no_copy_voz
    except Exception:
        _no_copy_voz = False
    if not _no_copy_voz:
        if getattr(profile, 'mono', False):
            active.append("Modo Mono")
        elif getattr(profile, 'stereo_width', 100) != 100:
            active.append(f"Ancho estéreo {profile.stereo_width}%")
        if getattr(profile, 'swap_channels', False):
            active.append("Canales invertidos")
    if getattr(profile, 'balance', 0) != 0:
        active.append(f"Balance {profile.balance}%")
    if abs(getattr(profile, 'tone_bass', 0.0)) > 0.05:
        active.append(f"Graves {profile.tone_bass:.1f} dB")
    if abs(getattr(profile, 'tone_treble', 0.0)) > 0.05:
        active.append(f"Agudos {profile.tone_treble:.1f} dB")
    try:
        from . import constants as _c2
        _st2 = (getattr(profile, 'channel_mode', 'stereo') == _c2.CHANNEL_MODE_STEREO)
    except Exception:
        _st2 = True
    if _st2:
        try:
            if abs(float(getattr(profile, 'center_gain', 0.0))) > 0.05:
                active.append(f"Voces {float(getattr(profile, 'center_gain', 0.0)):+.1f} dB")
            if abs(float(getattr(profile, 'subwoofer_gain', 0.0))) > 0.05:
                active.append(f"Graves LFE {float(getattr(profile, 'subwoofer_gain', 0.0)):+.1f} dB")
        except Exception:
            pass
    chan_m = getattr(profile, 'channel_mode', 'stereo')
    if chan_m == '5.1':
        active.append("Modo 5.1 envolvente")
    elif chan_m == '7.1':
        active.append("Modo 7.1 envolvente")
    elif chan_m == 'quad':
        active.append("Modo Cuadrafónico")
    elif chan_m == 'downmix_5_1':
        active.append("Mezcla 5.1 a estéreo")
    elif chan_m == 'downmix_7_1':
        active.append("Mezcla 7.1 a estéreo")

    header_parts = ["Ecualizador activo"]
    if profile_name:
        header_parts.append(f"Perfil: {profile_name}")
    preamp_val = getattr(profile, 'preamp', 0.0)
    if abs(preamp_val) > 0.05:
        header_parts.append(f"Preamplificación: {preamp_val:.1f} dB")
        
    prefix = ". ".join(header_parts)
    if not active:
        return f"{prefix}. Solo bandas de frecuencia aplicadas."
        
    return f"{prefix}. Mejoras aplicadas: {', '.join(active)}."


def open_log_file() -> None:
    """Abre el archivo de registro en el Bloc de notas o editor predeterminado."""
    _p = get_log_file_path()
    try:
        os.makedirs(os.path.dirname(_p) or ".", exist_ok=True)
    except Exception:
        pass
    if not os.path.isfile(_p):
        try:
            with open(_p, "w", encoding="utf-8", errors="replace") as f:
                f.write("# Registro de filtros y auditoría acústica de Audio Equalizer\n\nNo se han registrado cambios aún.\n")
        except Exception as e:
            log.error(f"AudioEqualizer: No se pudo crear el archivo de log: {e}", exc_info=True)
            try:
                import ui
                ui.message("No se pudo crear el archivo de registro.")
            except Exception:
                pass
            return
    try:
        os.startfile(_p)
    except Exception as e:
        log.error(f"AudioEqualizer: No se pudo abrir el archivo de log: {e}", exc_info=True)
        try:
            import ui
            ui.message("No se pudo abrir el archivo de registro.")
        except Exception:
            pass
