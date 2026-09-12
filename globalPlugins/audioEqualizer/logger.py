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

from . import constants

def _get_log_file_path() -> str:
    try:
        import globalVars
        return os.path.join(globalVars.appArgs.configPath, "audioEqualizer.log")
    except Exception:
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(appdata, "nvda", "audioEqualizer.log")

LOG_FILE_PATH = _get_log_file_path()


def write_audit_log(
    enabled: bool,
    preamp: float,
    auto_preamp: bool,
    mono: bool,
    swap_channels: bool,
    balance: int,
    tone_bass: float,
    tone_treble: float,
    sub_bass: bool,
    anti_box: bool,
    clarity: bool,
    anti_sibilance: bool = False,
    anti_fatigue: bool = False,
    ground_hum: bool = False,
    loudness: bool = False,
    subsonic: bool = False,
    nvda_voice: bool = False,
    stereo_width: int = 100,
    gains: List[float] = None,
    lines_written: List[str] = None,
    apo_config_path: str = "",
    apo_include_ok: bool = True
) -> None:
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
            "Filtro anti-encajonamiento 400 Hz",
            anti_box,
            "Filter: ON PK Fc 400 Hz Gain -4.5 dB Q 1.1"
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
        if stereo_width != 100:
            report_lines.append(f"  * Ancho estéreo Mid/Side: [EFECTO REAL: APLICADO] -> {stereo_width}% (Procesamiento matricial)")
        else:
            report_lines.append("  * Ancho estéreo Mid/Side: [100%: ESTÉREO ESTÁNDAR]")

        report_lines.append(_check(
            "Compensación Loudness (Fletcher-Munson)",
            loudness,
            "Filter: ON LS Fc 80 Hz Gain 4.5 dB + Filter: ON HS Fc 9000 Hz Gain 3.0 dB"
        ))
        report_lines.append(_check(
            "Forzado de audio mono",
            mono,
            "Copy: L=0.5*L+0.5*R R=0.5*L+0.5*R"
        ))
        report_lines.append(_check(
            "Invertir canales estéreo (L/R)",
            swap_channels,
            "Copy: L=R R=L"
        ))

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

    try:
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
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
    try:
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write("\n".join(err_lines) + "\n")
    except Exception as io_err:
        log.error(f"AudioEqualizer: No se pudo escribir error en {LOG_FILE_PATH}: {io_err}", exc_info=True)


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
    if getattr(profile, 'anti_box', False):
        active.append("Filtro anti-caja (-4.5 dB)")
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
    if not os.path.isfile(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("# Registro de filtros y auditoría acústica de Audio Equalizer\n\nNo se han registrado cambios aún.\n")
    try:
        os.startfile(LOG_FILE_PATH)
    except Exception:
        log.error("AudioEqualizer: No se pudo abrir el archivo de log.", exc_info=True)
