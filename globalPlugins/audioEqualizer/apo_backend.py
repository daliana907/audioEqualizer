# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Backend de audio nativo para Equalizer APO.

Traduce las preferencias de ecualización, balance y calibración acústica de NVDA
a las directivas de texto del motor de Equalizer APO. Genera un archivo dedicado
('nvda_equalizer.txt') dentro de la carpeta de configuración de APO y se asegura
de que el archivo principal 'config.txt' lo cargue mediante la directiva 'Include',
garantizando una convivencia limpia, no destructiva y en tiempo real.
"""

import os
import time
import math
from typing import List

try:
    from logHandler import log
except ImportError:
    import logging
    log = logging.getLogger("audioEqualizer")

from .backend import AudioBackend
from . import constants


# Compatibilidad: en algunos auriculares USB / controladores, cualquier directiva
# Copy: de Equalizer APO detiene todo el audio hasta el siguiente cambio de
# configuración. Si está en True no se emite ninguna directiva Copy:
# ni ancho estéreo, ni mono, ni inversión, ni enrutados 3D/radar. El resto del
# perfil (bandas, filtros, preamp, tonos) se aplica con normalidad.
# En False las órdenes se mandan como antes (puede silenciar esos equipos).
DISABLE_COPY_COMMANDS = False


def _clean_float(val, default: float = 0.0, min_v: float = -30.0, max_v: float = 30.0) -> float:
    """Valida, limpia y acota valores flotantes asegurando que no sean NaN ni Inf."""
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return max(min_v, min(max_v, f))
    except (TypeError, ValueError, OverflowError):
        return default


class ApoBackend(AudioBackend):
    """Implementación de backend que interactúa directamente con Equalizer APO.

    Escribe configuraciones en formato de texto estándar que el controlador de audio de
    Windows (audiodg.exe) procesa a nivel de kernel con latencia cero y máxima fidelidad.
    """

    def __init__(self):
        """Inicializa las rutas a los archivos de configuración de Equalizer APO en el sistema.

        Detecta automáticamente la carpeta 'Program Files' (incluso si NVDA corre bajo emulación
        de 32 bits en Windows de 64 bits mediante la variable ProgramW6432) y prepara las
        rutas a config.txt y al archivo privado del complemento nvda_equalizer.txt.
        """
        log.debug("AudioEqualizer: Instanciando APO backend nativo.")
        self._addon_file_name = "nvda_equalizer.txt"
        self._include_directive = f"Include: {self._addon_file_name}"
        self._detect_and_init_paths()
        
        self._enabled = False
        self._gains = list(constants.DEFAULT_GAINS)
        self._preamp = constants.DEFAULT_PREAMP
        self._auto_preamp = constants.DEFAULT_AUTO_PREAMP
        self._loudness = constants.DEFAULT_LOUDNESS
        self._mono = constants.DEFAULT_MONO
        self._swap_channels = constants.DEFAULT_SWAP
        self._balance = constants.DEFAULT_BALANCE
        self._tone_bass = constants.DEFAULT_TONE_BASS
        self._tone_treble = constants.DEFAULT_TONE_TREBLE
        self._sub_bass = constants.DEFAULT_SUB_BASS
        self._clarity = constants.DEFAULT_CLARITY
        self._anti_sibilance = constants.DEFAULT_ANTI_SIBILANCE
        self._anti_fatigue = constants.DEFAULT_ANTI_FATIGUE
        self._ground_hum = constants.DEFAULT_GROUND_HUM
        self._subsonic = constants.DEFAULT_SUBSONIC
        self._nvda_voice = constants.DEFAULT_NVDA_VOICE
        self._surround_3d = False
        self._radar_mode = False
        self._stereo_width = constants.DEFAULT_STEREO_WIDTH
        self._channel_mode = constants.DEFAULT_CHANNEL_MODE
        self._center_gain = constants.DEFAULT_CENTER_GAIN
        self._subwoofer_gain = constants.DEFAULT_SUBWOOFER_GAIN
        self._surround_gain = constants.DEFAULT_SURROUND_GAIN
        self._last_flushed_lines = None

    def _detect_and_init_paths(self) -> None:
        """Localiza de forma exhaustiva la carpeta de configuración de Equalizer APO."""
        candidates = []
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\EqualizerAPO") as key:
                val, _ = winreg.QueryValueEx(key, "InstallPath")
                if val:
                    candidates.append(val)
        except Exception:
            pass
        for env_var in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)"):
            val = os.environ.get(env_var)
            if val:
                candidates.append(os.path.join(val, "EqualizerAPO"))
        candidates.extend([
            r"C:\Program Files\EqualizerAPO",
            r"C:\Program Files (x86)\EqualizerAPO",
        ])
        
        chosen_apo = None
        for p in candidates:
            if os.path.isdir(os.path.join(p, "config")):
                chosen_apo = p
                break
                
        if not chosen_apo:
            pf = os.environ.get("ProgramW6432") or os.environ.get("ProgramFiles", r"C:\Program Files")
            chosen_apo = os.path.join(pf, "EqualizerAPO")

        self._apo_dir = chosen_apo
        self._config_dir = os.path.join(self._apo_dir, "config")
        self._main_config = os.path.join(self._config_dir, "config.txt")
        self._addon_config_path = os.path.join(self._config_dir, self._addon_file_name)

    def is_available(self) -> bool:
        """Comprueba si Equalizer APO está instalado en el equipo.

        Verifica si la carpeta de configuración en Program Files existe en el disco.
        """
        if os.path.isdir(self._config_dir):
            return True
        self._detect_and_init_paths()
        return os.path.isdir(self._config_dir)

    def get_enabled(self) -> bool:
        """Indica si la ecualización está activa en este momento."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Activa o desactiva la ecualización y actualiza el archivo en el disco."""
        if self._enabled == enabled:
            return
        old_val = self._enabled
        self._enabled = enabled
        log.debug(f"AudioEqualizer: APO backend estado cambiado a {enabled}.")
        try:
            self._flush_to_disk()
        except Exception:
            self._enabled = old_val
            raise

    def get_gains(self) -> List[float]:
        """Devuelve una copia de las ganancias actuales de las 31 bandas."""
        return list(self._gains)

    def set_gains(self, gains: List[float], preamp: float) -> None:
        """Establece las ganancias de las 31 bandas y el valor de preamplificación."""
        if len(gains) != constants.NUM_BANDS:
            raise ValueError(f"El backend esperaba {constants.NUM_BANDS} bandas, recibidas {len(gains)}.")
        old_gains = self._gains
        old_preamp = self._preamp
        self._gains = list(gains)
        self._preamp = preamp
        if self._enabled:
            try:
                log.debug("AudioEqualizer: Actualizando ganancias en el disco (APO).")
                self._flush_to_disk()
            except Exception:
                self._gains = old_gains
                self._preamp = old_preamp
                raise

    def update(
        self,
        enabled: bool,
        gains: List[float],
        preamp: float,
        auto_preamp: bool = False,
        loudness: bool = False,
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
        subsonic: bool = False,
        nvda_voice: bool = False,
        surround_3d: bool = False,
        radar_mode: bool = False,
        stereo_width: int = 100,
        channel_mode: str = "stereo",
        center_gain: float = 0.0,
        subwoofer_gain: float = 0.0,
        surround_gain: float = 0.0,
    ) -> None:
        """Actualiza en bloque todos los ajustes acústicos y los escribe de inmediato en disco."""
        if len(gains) != constants.NUM_BANDS:
            raise ValueError(f"El backend esperaba {constants.NUM_BANDS} bandas, recibidas {len(gains)}.")
        # Exclusión mutua radar/surround: no pueden sonar a la vez (doble crossfeed).
        if bool(surround_3d) and bool(radar_mode):
            radar_mode = False
            try:
                log.warning("AudioEqualizer: surround_3d y radar_mode mutuamente excluyentes; se desactiva radar_mode.")
            except Exception:
                pass
        self._enabled = enabled
        self._gains = list(gains)
        self._preamp = preamp
        self._auto_preamp = bool(auto_preamp)
        self._loudness = bool(loudness)
        self._mono = mono
        self._swap_channels = swap_channels
        self._balance = int(balance)
        self._tone_bass = float(tone_bass)
        self._tone_treble = float(tone_treble)
        self._sub_bass = bool(sub_bass)
        self._clarity = bool(clarity)
        self._anti_sibilance = bool(anti_sibilance)
        self._anti_fatigue = bool(anti_fatigue)
        self._ground_hum = bool(ground_hum)
        self._subsonic = bool(subsonic)
        self._nvda_voice = bool(nvda_voice)
        self._surround_3d = bool(surround_3d)
        self._radar_mode = bool(radar_mode)
        self._stereo_width = int(stereo_width)
        self._channel_mode = str(channel_mode) if str(channel_mode) in constants.CHANNEL_MODES else constants.DEFAULT_CHANNEL_MODE
        self._center_gain = float(center_gain)
        self._subwoofer_gain = float(subwoofer_gain)
        self._surround_gain = float(surround_gain)
        self._flush_to_disk()

    def close(self) -> None:
        """Cierra el backend sin alterar los archivos de configuración."""
        log.debug("AudioEqualizer: Backend cerrado.")

    _ADMIN_WARNED = False
    _ROUTING_WARNED = False

    def _ensure_include_directive(self) -> None:
        """Asegura que config.txt de Equalizer APO contenga la directiva 'Include: nvda_equalizer.txt'.

        Si el archivo no existe, lanza un error claro para orientar al usuario a instalar APO.
        Si la directiva ya está presente, no toca el archivo para evitar escrituras innecesarias.
        Si necesita escribirla, maneja posibles bloqueos de audiodg.exe reintentando hasta 10 veces
        con pequeñas pausas.
        """
        if not os.path.isfile(self._main_config):
            err_msg = f"No se encuentra el archivo principal de Equalizer APO en {self._main_config}"
            log.error(f"AudioEqualizer: {err_msg}")
            try:
                from . import logger
                logger.log_error(err_msg, component="ApoBackend", context={"main_config": self._main_config, "config_dir": self._config_dir})
            except Exception:
                pass
            raise RuntimeError(err_msg)

        try:
            try:
                if os.path.getsize(self._main_config) > 1024 * 1024:
                    raise RuntimeError(f"config.txt supera el límite de 1 MB ({self._main_config}); se aborta lectura por seguridad.")
            except OSError:
                pass
            try:
                with open(self._main_config, "r", encoding="utf-8-sig", errors="replace") as f:
                    content = f.read(1024 * 1024 + 1)
                    if len(content) > 1024 * 1024:
                        raise RuntimeError("config.txt supera el límite de 1 MB; se aborta lectura por seguridad.")
            except UnicodeDecodeError:
                with open(self._main_config, "r", encoding="mbcs", errors="replace") as f:
                    content = f.read(1024 * 1024 + 1)
                    if len(content) > 1024 * 1024:
                        raise RuntimeError("config.txt supera el límite de 1 MB; se aborta lectura por seguridad.")

            # Buscamos la directiva línea por línea (ignorando espacios de sobra), en vez de
            # exigir que todo el archivo sea idéntico a lo que este complemento esperaría escribir.
            existing_lines = [line.strip() for line in content.splitlines()]
            if self._include_directive.strip() in existing_lines:
                log.debug("AudioEqualizer: Directiva include ya presente en config.txt.")
                return

            log.info("AudioEqualizer: Agregando directiva include en config.txt sin tocar el resto del archivo.")
            separator = "" if (not content or content.endswith("\n")) else "\n"
            new_content = (
                content
                + separator
                + "# Directiva agregada por el complemento Audio Equalizer para NVDA\n"
                + f"{self._include_directive}\n"
            )
            temp_path = self._main_config + ".tmp"
            try:
                with open(temp_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(new_content)
                
                last_err = None
                admin_notified = False
                for attempt in range(10):
                    try:
                        os.replace(temp_path, self._main_config)
                        log.debug(f"AudioEqualizer: config.txt actualizado en intento {attempt + 1}.")
                        break
                    except (PermissionError, OSError) as pe:
                        last_err = pe
                        if isinstance(pe, PermissionError) and not ApoBackend._ADMIN_WARNED and not admin_notified:
                            admin_notified = True
                            ApoBackend._ADMIN_WARNED = True
                            try:
                                log.warning("AudioEqualizer: Sin permiso para escribir config.txt; ejecute NVDA como administrador una vez para autorizar.")
                                try:
                                    import ui
                                    import core
                                    core.callLater(0, ui.message, "Sin permiso para actualizar Equalizer APO. Ejecute NVDA como administrador una vez.")
                                except Exception:
                                    pass
                            except Exception:
                                pass
                        log.debug(f"AudioEqualizer: config.txt bloqueado en intento {attempt + 1}/10, reintentando...")
                        time.sleep(0.05)
                else:
                    raise IOError(f"Archivo config.txt bloqueado tras 10 intentos: {last_err}")
            finally:
                try:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception:
                    pass
                
        except Exception as e:
            log.error(f"AudioEqualizer: Fallo al asegurar config.txt en APO: {e}", exc_info=True)
            try:
                from . import logger
                logger.log_error(f"Fallo al asegurar include en config.txt: {e}", exc=e, component="ApoBackend", context={"main_config": self._main_config})
            except Exception:
                pass
            raise RuntimeError(f"Fallo de E/S al configurar Equalizer APO: {e}")

    def _build_config_lines(self) -> List[str]:
        """Genera la lista de líneas de directivas de Equalizer APO según el estado actual."""
        lines = [
            "# Archivo de configuracion del complemento Audio Equalizer para NVDA",
            "# Generado automaticamente con comandos nativos de Equalizer APO.",
            "# No modificar manualmente.",
            "",
            # Reinicia el alcance de canales a "todos" antes de cualquier otra instrucción.
            # Sin esto, si config.txt (que ya no se sobrescribe) dejara activo un alcance de
            # un solo canal justo antes de la línea Include que carga este archivo, todos los
            # filtros de abajo se aplicarían solo a ese canal en lugar de a los dos oídos.
            "Channel: all",
        ]

        if not self._enabled:
            lines.append("# Ecualizador desactivado")
        else:
            # 0. Configuración de canales multicanal y mezcla envolvente
            channel_mode = getattr(self, "_channel_mode", constants.DEFAULT_CHANNEL_MODE)
            if channel_mode not in constants.CHANNEL_MODES:
                channel_mode = constants.DEFAULT_CHANNEL_MODE

            center_gain = _clean_float(getattr(self, "_center_gain", 0.0), default=0.0, min_v=-20.0, max_v=20.0)
            sub_gain = _clean_float(getattr(self, "_subwoofer_gain", 0.0), default=0.0, min_v=-20.0, max_v=20.0)
            sur_gain = _clean_float(getattr(self, "_surround_gain", 0.0), default=0.0, min_v=-20.0, max_v=20.0)

            if not DISABLE_COPY_COMMANDS:
                if channel_mode == constants.CHANNEL_MODE_DOWNMIX_5_1:
                    lines.append("# Mezcla inteligente 5.1 a Estereo (Downmixing para auriculares)")
                    c_fac = round(0.707 * (10.0 ** (center_gain / 20.0)), 3)
                    sub_fac = round(0.500 * (10.0 ** (sub_gain / 20.0)), 3)
                    sur_fac = round(0.707 * (10.0 ** (sur_gain / 20.0)), 3)
                    lines.append(f"Copy: L=1.0*L+{c_fac}*C+{sur_fac}*RL+{sub_fac}*SUB R=1.0*R+{c_fac}*C+{sur_fac}*RR+{sub_fac}*SUB")
                    lines.append("Channel: L R")
                elif channel_mode == constants.CHANNEL_MODE_DOWNMIX_7_1:
                    lines.append("# Mezcla inteligente 7.1 a Estereo (Downmixing para auriculares)")
                    c_fac = round(0.707 * (10.0 ** (center_gain / 20.0)), 3)
                    sub_fac = round(0.500 * (10.0 ** (sub_gain / 20.0)), 3)
                    sur_fac = round(0.500 * (10.0 ** (sur_gain / 20.0)), 3)
                    lines.append(f"Copy: L=1.0*L+{c_fac}*C+{sur_fac}*RL+{sur_fac}*SL+{sub_fac}*SUB R=1.0*R+{c_fac}*C+{sur_fac}*RR+{sur_fac}*SR+{sub_fac}*SUB")
                    lines.append("Channel: L R")
                elif channel_mode == constants.CHANNEL_MODE_QUAD:
                    if abs(sur_gain) > 0.05:
                        lines.append(f"# Nivel de canales traseros cuadrafonicos: {sur_gain:.1f} dB")
                        lines.append("Channel: RL RR SL SR")
                        lines.append(f"Preamp: {sur_gain:.1f} dB")
                        lines.append("Channel: all")
                elif channel_mode in (constants.CHANNEL_MODE_5_1, constants.CHANNEL_MODE_7_1):
                    if abs(center_gain) > 0.05:
                        lines.append(f"# Nivel canal Central / Voces: {center_gain:.1f} dB")
                        lines.append("Channel: C")
                        lines.append(f"Preamp: {center_gain:.1f} dB")
                        lines.append("Channel: all")
                    if abs(sub_gain) > 0.05:
                        lines.append(f"# Nivel Subwoofer / Graves LFE: {sub_gain:.1f} dB")
                        lines.append("Channel: SUB LFE")
                        lines.append(f"Preamp: {sub_gain:.1f} dB")
                        lines.append("Channel: all")
                    if abs(sur_gain) > 0.05:
                        lines.append(f"# Nivel canales envolventes Surround: {sur_gain:.1f} dB")
                        lines.append("Channel: RL RR SL SR")
                        lines.append(f"Preamp: {sur_gain:.1f} dB")
                        lines.append("Channel: all")

            if channel_mode == constants.CHANNEL_MODE_STEREO:
                # En estéreo no hay central ni LFE discretos: aproximación honesta
                # con ecualización (sin Copy), válida también en modo compatible.
                if abs(center_gain) > 0.05:
                    lines.append("# Voces (aproximación estéreo del canal central)")
                    lines.append(f"Filter: ON PK Fc 2800 Hz Gain {center_gain:.1f} dB Q 1.4")
                if abs(sub_gain) > 0.05:
                    lines.append("# Graves LFE (aproximación estéreo del subwoofer)")
                    lines.append(f"Filter: ON LS Fc 70 Hz Gain {sub_gain:.1f} dB Q 0.8")

            # 1. Enrutamiento de canales (Invertir canales, Mono, Ancho estéreo Mid/Side)
            if self._swap_channels and not DISABLE_COPY_COMMANDS:
                lines.append("Copy: L=R R=L")

            stereo_width = _clean_float(self._stereo_width, default=100.0, min_v=0.0, max_v=300.0)
            if DISABLE_COPY_COMMANDS and (self._swap_channels or self._mono or stereo_width != 100.0 or getattr(self, "_radar_mode", False) or getattr(self, "_surround_3d", False)):
                if not ApoBackend._ROUTING_WARNED:
                    ApoBackend._ROUTING_WARNED = True
                    log.warning("AudioEqualizer: enrutado de canales omitido (modo compatible sin directivas Copy).")
            if not DISABLE_COPY_COMMANDS and (self._mono or stereo_width == 0.0):
                # Mezcla monoaural perfecta 50/50 en ambos auriculares
                lines.append("Copy: L=0.5*L+0.5*R R=0.5*L+0.5*R")
            elif not DISABLE_COPY_COMMANDS and stereo_width != 100.0:
                # Matriz Mid/Side acústica: w=1.0 es estéreo normal, w>1.0 ensancha el campo auditivo
                w = stereo_width / 100.0
                # Si ensancha mucho, compensamos subiendo levemente el canal central (mid_boost)
                mid_boost = 1.0 + max(0.0, (w - 1.0) * 0.3)
                cL = round(0.5 * (mid_boost + w), 3)
                cR = round(0.5 * (mid_boost - w), 3)
                lines.append(f"# Ancho estereo compensado ({round(stereo_width)}%, mid_boost={round(mid_boost,2)})")
                # En Equalizer APO, la sustracción en directivas Copy: no admite el operador '-' infijo.
                # Escribir L=cL*L-a*R hace que el analizador de APO lo interprete como valor escalar 1.0 (DC offset puro de 32767,
                # silenciando por completo el audio). Se debe usar siempre el operador de suma '+' con el factor negativo '+-'.
                if cR < 0:
                    _copy_line = f"Copy: L={cL}*L+{cR}*R R={cL}*R+{cR}*L"
                else:
                    _copy_line = f"Copy: L={cL}*L+{cR}*R R={cR}*L+{cL}*R"
                lines.append(_copy_line)

            # 1.4. Modo Radar (Precisión Posicional / HRTF simulado)
            if getattr(self, "_radar_mode", False) and not DISABLE_COPY_COMMANDS:
                lines.append("# Modo Radar Posicional (Crossfeed HRTF natural)")
                lines.append("Copy: 3=L 4=R")
                lines.append("Channel: 3 4")
                # Retraso natural de cabeza humana (~0.3 ms)
                lines.append("Delay: 0.35 ms")
                # Atenuar frecuencias altas cruzadas (la cabeza hace sombra acústica)
                lines.append("Filter: ON LP Fc 1500 Hz")
                lines.append("Preamp: -5 dB") # Margen extra para que el boost de +6dB no sature
                lines.append("Channel: L R")
                # Cruzar la señal con la principal
                lines.append("Copy: L=L+0.5*4 R=R+0.5*3")
                
                # Compresión/EQ ascendente de detalles (Realzar zona de ubicación 2-6 kHz, achicar barro)
                lines.append("Filter: ON PK Fc 250 Hz Gain -2.0 dB Q 1.0")
                lines.append("Filter: ON PK Fc 4000 Hz Gain 6.0 dB Q 1.0")
                lines.append("Filter: ON HS Fc 8000 Hz Gain 3.0 dB")

            # 1.5. Audio 3D Espacial Inmersivo (HRTF Binaural Profesional)
            if getattr(self, "_surround_3d", False) and not DISABLE_COPY_COMMANDS:
                lines.append("# Audio 3D Espacial Inmersivo (HRTF Binaural Profesional)")
                # 1. Extraer señal cruzada con retardo anatómico craneal (0.28 ms) y sombra acústica
                lines.append("Copy: SL=L SR=R")
                lines.append("Channel: SL SR")
                lines.append("Delay: 0.28 ms")
                lines.append("Filter: ON LP Fc 1400 Hz")
                lines.append("Filter: ON HS Fc 2400 Hz Gain -7.0 dB")
                lines.append("Preamp: -9.5 dB")
                # 2. Generar canales laterales de profundidad mediante filtros Paso Todo (All-Pass)
                lines.append("Copy: RL=0.5*L+-0.5*R RR=0.5*R+-0.5*L")
                lines.append("Channel: RL RR")
                lines.append("Filter: ON AP Fc 850 Hz Q 0.707")
                lines.append("Filter: ON AP Fc 2200 Hz Q 0.707")
                lines.append("Preamp: -6.0 dB")
                # 3. Recomponer campo estéreo tridimensional proyectado fuera de la cabeza
                lines.append("Channel: L R")
                lines.append("Copy: L=0.75*L+RL+0.35*SR R=0.75*R+RR+0.35*SL")
                # 4. Ecualización anatómica de concha y pabellón auditivo (externalización 3D)
                lines.append("Filter: ON PK Fc 3200 Hz Gain 2.0 dB Q 1.5")
                lines.append("Filter: ON PK Fc 7200 Hz Gain -2.5 dB Q 2.0")
                # 5. Descompresión de cámara acústica para controladores de 53 mm (Redragon H510)
                lines.append("Filter: ON PK Fc 320 Hz Gain -1.5 dB Q 1.2")

            # 2. Balance Estéreo (-100 a +100): exclusivamente por atenuación suave del canal opuesto
            balance = _clean_float(self._balance, default=0.0, min_v=-100.0, max_v=100.0)
            if balance < 0:
                # Inclinado hacia la izquierda: atenuamos el canal derecho
                att = round((balance / 100.0) * 20.0, 1)
                lines.append("Channel: R")
                lines.append(f"Preamp: {att:.1f} dB")
                lines.append("Channel: all")
            elif balance > 0:
                # Inclinado hacia la derecha: atenuamos el canal izquierdo
                att = round((-balance / 100.0) * 20.0, 1)
                lines.append("Channel: L")
                lines.append(f"Preamp: {att:.1f} dB")
                lines.append("Channel: all")

            # 3. Preamplificación segura para control de volumen y anticlíping
            preamp = _clean_float(self._preamp, default=0.0, min_v=-30.0, max_v=20.0)
            lines.append(f"Preamp: {preamp:.1f} dB")

            # 4. Controles rápidos de tono (filtros de estantería en 100 Hz y 8000 Hz)
            tone_bass = _clean_float(self._tone_bass, default=0.0, min_v=-20.0, max_v=20.0)
            tone_treble = _clean_float(self._tone_treble, default=0.0, min_v=-20.0, max_v=20.0)
            if abs(tone_bass) > 0.05:
                lines.append(f"Filter: ON LSC Fc 100 Hz Gain {tone_bass:.1f} dB")
            if abs(tone_treble) > 0.05:
                lines.append(f"Filter: ON HSC Fc 8000 Hz Gain {tone_treble:.1f} dB")

            # 5. Mejoras acústicas para auriculares profesionales (filtros biquad nativos)
            if self._subsonic:
                lines.append("# Filtro subsonico (Proteccion contra sobre-excursion < 20 Hz)")
                lines.append("Filter: ON HP Fc 20 Hz Q 0.707")
            if self._sub_bass:
                lines.append("Filter: ON LS Fc 70 Hz Gain 6.0 dB Q 0.8")
            if self._clarity:
                lines.append("Filter: ON PK Fc 5500 Hz Gain 5.5 dB Q 1.2")
            if self._anti_sibilance:
                lines.append("Filter: ON PK Fc 7500 Hz Gain -5.0 dB Q 1.8")
            if self._anti_fatigue:
                lines.append("# Filtro anti-fatiga auditiva (Sonido calido roll-off en 14 kHz)")
                lines.append("Filter: ON HS Fc 14000 Hz Gain -4.5 dB Q 0.7")
            if self._ground_hum:
                lines.append("# Filtro anti-zumbido electrico (Notch en 50/60 Hz y sus ecos en 100/120 Hz)")
                lines.append("Filter: ON NO Fc 50 Hz Q 6")
                lines.append("Filter: ON NO Fc 60 Hz Q 6")
                lines.append("Filter: ON NO Fc 100 Hz Q 8")
                lines.append("Filter: ON NO Fc 120 Hz Q 8")
            if self._loudness:
                lines.append("# Compensacion isofonica Loudness (Fletcher-Munson para bajo volumen)")
                lines.append("Filter: ON LS Fc 80 Hz Gain 4.5 dB Q 0.7")
                lines.append("Filter: ON HS Fc 9000 Hz Gain 3.0 dB Q 0.7")
            if self._nvda_voice:
                lines.append("# Claridad optimizada para sintetizadores de voz / NVDA")
                lines.append("Filter: ON PK Fc 850 Hz Gain -3.5 dB Q 2.0")
                lines.append("Filter: ON PK Fc 2800 Hz Gain 4.5 dB Q 1.4")
                lines.append("Filter: ON PK Fc 6200 Hz Gain -3.0 dB Q 2.5")

            # 6. Ecualizador gráfico de 31 bandas ISO estándar
            pairs = []
            for freq, gain in zip(constants.EQ_BANDS, self._gains):
                clean_g = _clean_float(gain, default=0.0, min_v=-24.0, max_v=24.0)
                pairs.append(f"{freq} {clean_g:.1f}")
            lines.append(f"GraphicEQ: {'; '.join(pairs)}")
        return lines

    def _flush_to_disk(self) -> None:
        """Escribe todos los comandos de procesamiento de audio en 'nvda_equalizer.txt'."""
        if not self.is_available():
            raise RuntimeError("Equalizer APO no está disponible en este sistema.")

        self._ensure_include_directive()
        lines = self._build_config_lines()
        tmp_path = self._addon_config_path + ".tmp"
        try:
            content = "\n".join(lines) + "\n"
            last_err = None
            for attempt in range(10):
                try:
                    with open(tmp_path, "w", encoding="utf-8", errors="replace") as f:
                        f.write(content)
                    os.replace(tmp_path, self._addon_config_path)
                    log.debug(f"AudioEqualizer: {self._addon_file_name} escrito exitosamente en intento {attempt + 1}.")
                    break
                except (PermissionError, IOError) as write_err:
                    last_err = write_err
                    try:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except Exception:
                        pass
                    log.debug(f"AudioEqualizer: {self._addon_file_name} bloqueado en intento {attempt + 1}/10 ({write_err}), reintentando...")
                    time.sleep(0.04)
            else:
                raise IOError(f"Archivo {self._addon_file_name} bloqueado por audiodg.exe u otro proceso tras 10 intentos: {last_err}")
            
            # Forzar recarga en Equalizer APO solo si hubo cambios estructurales.
            # Si solo cambió GraphicEQ, APO ya detecta el cambio del include sin tocar config.txt.
            try:
                _prev = getattr(self, "_last_flushed_lines", None)
                _only_gains = False
                if _prev is not None and isinstance(_prev, list):
                    if len(_prev) == len(lines):
                        _diffs = [i for i, (a, b) in enumerate(zip(_prev, lines)) if a != b]
                        if _diffs and all(l.startswith("GraphicEQ:") for l in (lines[i] for i in _diffs)):
                            _only_gains = True
                if not _only_gains:
                    os.utime(self._main_config, None)
                    log.debug("AudioEqualizer: Timestamp de config.txt actualizado para recarga en tiempo real.")
                else:
                    log.debug("AudioEqualizer: Solo cambiaron ganancias; se omite utime de config.txt.")
                try:
                    self._last_flushed_lines = list(lines)
                except Exception:
                    pass
            except Exception as utime_err:
                log.debug(f"AudioEqualizer: No se pudo actualizar timestamp de config.txt ({utime_err}).")

            # Registrar auditoría de filtros aplicados
            try:
                from . import logger
                logger.write_audit_log(
                    enabled=self._enabled,
                    preamp=self._preamp,
                    auto_preamp=self._auto_preamp,
                    loudness=self._loudness,
                    mono=self._mono,
                    swap_channels=self._swap_channels,
                    balance=self._balance,
                    tone_bass=self._tone_bass,
                    tone_treble=self._tone_treble,
                    sub_bass=self._sub_bass,
                    clarity=self._clarity,
                    anti_sibilance=self._anti_sibilance,
                    anti_fatigue=self._anti_fatigue,
                    ground_hum=self._ground_hum,
                    subsonic=self._subsonic,
                    nvda_voice=self._nvda_voice,
                    surround_3d=self._surround_3d,
                    radar_mode=self._radar_mode,
                    stereo_width=self._stereo_width,
                    channel_mode=self._channel_mode,
                    center_gain=self._center_gain,
                    subwoofer_gain=self._subwoofer_gain,
                    surround_gain=self._surround_gain,
                    gains=self._gains,
                    lines_written=lines,
                    apo_config_path=self._addon_config_path,
                    apo_include_ok=True
                )
            except Exception as audit_err:
                log.error(f"AudioEqualizer: Error llamando a logger.write_audit_log: {audit_err}", exc_info=True)
                
        except Exception as e:
            log.error(f"AudioEqualizer: Fallo al escribir {self._addon_file_name}: {e}", exc_info=True)
            try:
                from . import logger
                ctx = {
                    "addon_config_path": self._addon_config_path,
                    "main_config": self._main_config,
                    "enabled": self._enabled,
                    "preamp": self._preamp,
                    "num_lines": len(lines)
                }
                logger.log_error(f"Fallo crítico al aplicar filtros en APO ({self._addon_file_name}): {e}", exc=e, component="ApoBackend", context=ctx)
            except Exception:
                pass
            raise RuntimeError(f"Error de E/S guardando archivo para Equalizer APO: {e}")
        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
