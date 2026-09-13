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
from typing import List

try:
    from logHandler import log
except ImportError:
    import logging
    log = logging.getLogger("audioEqualizer")

from .backend import AudioBackend
from . import constants


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
        self._anti_box = constants.DEFAULT_ANTI_BOX
        self._clarity = constants.DEFAULT_CLARITY
        self._anti_sibilance = constants.DEFAULT_ANTI_SIBILANCE
        self._anti_fatigue = constants.DEFAULT_ANTI_FATIGUE
        self._ground_hum = constants.DEFAULT_GROUND_HUM
        self._subsonic = constants.DEFAULT_SUBSONIC
        self._nvda_voice = constants.DEFAULT_NVDA_VOICE
        self._stereo_width = constants.DEFAULT_STEREO_WIDTH

    def _detect_and_init_paths(self) -> None:
        """Localiza de forma exhaustiva la carpeta de configuración de Equalizer APO."""
        candidates = []
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
        self._enabled = enabled
        log.debug(f"AudioEqualizer: APO backend estado cambiado a {enabled}.")
        self._flush_to_disk()

    def get_gains(self) -> List[float]:
        """Devuelve una copia de las ganancias actuales de las 31 bandas."""
        return list(self._gains)

    def set_gains(self, gains: List[float], preamp: float) -> None:
        """Establece las ganancias de las 31 bandas y el valor de preamplificación."""
        if len(gains) != constants.NUM_BANDS:
            raise ValueError(f"El backend esperaba {constants.NUM_BANDS} bandas, recibidas {len(gains)}.")
        self._gains = list(gains)
        self._preamp = preamp
        if self._enabled:
            log.debug("AudioEqualizer: Actualizando ganancias en el disco (APO).")
            self._flush_to_disk()

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
        anti_box: bool = False,
        clarity: bool = False,
        anti_sibilance: bool = False,
        anti_fatigue: bool = False,
        ground_hum: bool = False,
        subsonic: bool = False,
        nvda_voice: bool = False,
        stereo_width: int = 100,
    ) -> None:
        """Actualiza en bloque todos los ajustes acústicos y los escribe de inmediato en disco."""
        if len(gains) != constants.NUM_BANDS:
            raise ValueError(f"El backend esperaba {constants.NUM_BANDS} bandas, recibidas {len(gains)}.")
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
        self._anti_box = bool(anti_box)
        self._clarity = bool(clarity)
        self._anti_sibilance = bool(anti_sibilance)
        self._anti_fatigue = bool(anti_fatigue)
        self._ground_hum = bool(ground_hum)
        self._subsonic = bool(subsonic)
        self._nvda_voice = bool(nvda_voice)
        self._stereo_width = int(stereo_width)
        self._flush_to_disk()

    def close(self) -> None:
        """Cierra el backend sin alterar los archivos de configuración."""
        log.debug("AudioEqualizer: Backend cerrado.")

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

        desired_content = (
            "# Archivo principal de configuracion de Equalizer APO\n"
            f"{self._include_directive}\n"
        )
        try:
            with open(self._main_config, "r", encoding="utf-8-sig") as f:
                content = f.read()

            if content.strip() == desired_content.strip():
                log.debug("AudioEqualizer: Directiva include ya presente y correcta en config.txt.")
                return

            log.info("AudioEqualizer: Insertando directiva include en config.txt.")
            temp_path = self._main_config + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(desired_content)
                
            last_err = None
            for attempt in range(10):
                try:
                    os.replace(temp_path, self._main_config)
                    log.debug(f"AudioEqualizer: config.txt actualizado en intento {attempt + 1}.")
                    break
                except PermissionError as pe:
                    last_err = pe
                    log.debug(f"AudioEqualizer: config.txt bloqueado en intento {attempt + 1}/10, reintentando...")
                    time.sleep(0.05)
            else:
                raise IOError(f"Archivo config.txt bloqueado tras 10 intentos: {last_err}")
                
        except Exception as e:
            log.error(f"AudioEqualizer: Fallo al asegurar config.txt en APO: {e}", exc_info=True)
            try:
                from . import logger
                logger.log_error(f"Fallo al asegurar include en config.txt: {e}", exc=e, component="ApoBackend", context={"main_config": self._main_config})
            except Exception:
                pass
            raise RuntimeError(f"Fallo de E/S al configurar Equalizer APO: {e}")

    def _flush_to_disk(self) -> None:
        """Escribe todos los comandos de procesamiento de audio en 'nvda_equalizer.txt'.

        Construye el archivo línea por línea usando exclusivamente comandos nativos
        de Equalizer APO en el orden acústico óptimo:
        1. Enrutamiento de canales: inversión L/R, mezcla mono (L=0.5*L+0.5*R), o
           ensanchamiento estéreo mediante matriz Mid/Side (L=cL*L+cR*R) que amplía la escena
           sonora sin introducir desfases ni colorear el timbre.
        2. Balance estéreo (-100 a +100): atenúa suavemente el canal opuesto hasta un máximo
           de -20 dB. Atenuar en lugar de amplificar evita la saturación digital en el DAC.
        3. Preamplificación segura: ajusta el nivel global en decibelios para evitar clíping.
        4. Controles rápidos de tono: filtros de estantería suave para graves (100 Hz) y agudos (8000 Hz).
        5. Filtros acústicos especializados para auriculares:
           - Subsónico: filtro paso-alto en 20 Hz (Butterworth Q=0.707) para eliminar oscilaciones inaudibles.
           - Subgraves: realce de pegada en 70 Hz (+6 dB) para compensar la falta de cuerpo en auriculares abiertos.
           - Anti-caja: corte en 400 Hz (-4.5 dB) para eliminar el sonido hueco y nasal.
           - Claridad vocal: realce en 5500 Hz (+5.5 dB) que resalta detalles y presencia en la voz humana.
           - Anti-sibilancia: filtro paramétrico en 7500 Hz (-5.0 dB) que suaviza los molestos sonidos de 's' y 'ch'.
           - Anti-fatiga auditiva: corte suave en agudos extremos en 14000 Hz (-4.5 dB) para sesiones prolongadas.
           - Anti-zumbido eléctrico: dos filtros notch muy estrechos en 50 Hz y 60 Hz para ruidos de masa.
           - Compensación isofónica (Loudness): curvas de Fletcher-Munson (+4.5 dB en 80 Hz y +3 dB en 9 kHz)
             para escuchar música o voz a bajo volumen sin perder graves ni brillo.
           - Voz de NVDA: ecualización de tres bandas diseñada específicamente para sintetizadores
             de voz (-3.5 dB en 850 Hz para quitar resonancia plástica, +4.5 dB en 2800 Hz para inteligibilidad
             y -3.0 dB en 6200 Hz para suavizar fricativas digitales).
        6. Ecualizador gráfico de 31 bandas ISO estándar mediante la directiva 'GraphicEQ'.

        El archivo se escribe de forma atómica y gestiona hasta 10 reintentos si el proceso de
        audio de Windows (audiodg.exe) lo mantiene temporalmente bloqueado mientras reproduce sonido.
        """
        if not self.is_available():
            raise RuntimeError("Equalizer APO no está disponible en este sistema.")

        self._ensure_include_directive()

        lines = [
            "# Archivo de configuracion del complemento Audio Equalizer para NVDA",
            "# Generado automaticamente con comandos nativos de Equalizer APO.",
            "# No modificar manualmente.",
            ""
        ]

        if not self._enabled:
            lines.append("# Ecualizador desactivado")
        else:
            # 1. Enrutamiento de canales (Invertir canales, Mono, Ancho estéreo Mid/Side)
            if self._swap_channels:
                lines.append("Copy: L=R R=L")

            if self._mono or self._stereo_width == 0:
                # Mezcla monoaural perfecta 50/50 en ambos auriculares
                lines.append("Copy: L=0.5*L+0.5*R R=0.5*L+0.5*R")
            elif self._stereo_width != 100:
                # Matriz Mid/Side acústica: w=1.0 es estéreo normal, w>1.0 ensancha el campo auditivo
                w = self._stereo_width / 100.0
                cL = round(0.5 * (1.0 + w), 3)
                cR = round(0.5 * (1.0 - w), 3)
                lines.append(f"# Ancho estereo Mid/Side ({self._stereo_width}%)")
                lines.append(f"Copy: L={cL}*L+{cR}*R R={cR}*L+{cL}*R")

            # 2. Balance Estéreo (-100 a +100): exclusivamente por atenuación suave del canal opuesto
            if self._balance < 0:
                # Inclinado hacia la izquierda: atenuamos el canal derecho
                att = round((self._balance / 100.0) * 20.0, 1)
                lines.append("Channel: R")
                lines.append(f"Preamp: {att:.1f} dB")
                lines.append("Channel: all")
            elif self._balance > 0:
                # Inclinado hacia la derecha: atenuamos el canal izquierdo
                att = round((-self._balance / 100.0) * 20.0, 1)
                lines.append("Channel: L")
                lines.append(f"Preamp: {att:.1f} dB")
                lines.append("Channel: all")

            # 3. Preamplificación segura para control de volumen y anticlíping
            lines.append(f"Preamp: {self._preamp:.1f} dB")

            # 4. Controles rápidos de tono (filtros de estantería en 100 Hz y 8000 Hz)
            if abs(self._tone_bass) > 0.05:
                lines.append(f"Filter: ON LSC Fc 100 Hz Gain {self._tone_bass:.1f} dB")
            if abs(self._tone_treble) > 0.05:
                lines.append(f"Filter: ON HSC Fc 8000 Hz Gain {self._tone_treble:.1f} dB")

            # 5. Mejoras acústicas para auriculares profesionales (filtros biquad nativos)
            if self._subsonic:
                lines.append("# Filtro subsonico (Proteccion contra sobre-excursion < 20 Hz)")
                lines.append("Filter: ON HP Fc 20 Hz Q 0.707")
            if self._sub_bass:
                lines.append("Filter: ON LS Fc 70 Hz Gain 6.0 dB Q 0.8")
            if self._anti_box:
                lines.append("Filter: ON PK Fc 400 Hz Gain -4.5 dB Q 1.1")
            if self._clarity:
                lines.append("Filter: ON PK Fc 5500 Hz Gain 5.5 dB Q 1.2")
            if self._anti_sibilance:
                lines.append("Filter: ON PK Fc 7500 Hz Gain -5.0 dB Q 1.8")
            if self._anti_fatigue:
                lines.append("# Filtro anti-fatiga auditiva (Sonido calido roll-off en 14 kHz)")
                lines.append("Filter: ON HS Fc 14000 Hz Gain -4.5 dB Q 0.7")
            if self._ground_hum:
                lines.append("# Filtro anti-zumbido electrico (Notch 50 y 60 Hz)")
                lines.append("Filter: ON NO Fc 50 Hz Q 6")
                lines.append("Filter: ON NO Fc 60 Hz Q 6")
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
                pairs.append(f"{freq} {gain:.1f}")
            lines.append(f"GraphicEQ: {'; '.join(pairs)}")

        try:
            content = "\n".join(lines) + "\n"
            last_err = None
            for attempt in range(10):
                try:
                    with open(self._addon_config_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    log.debug(f"AudioEqualizer: {self._addon_file_name} escrito exitosamente en intento {attempt + 1}.")
                    break
                except (PermissionError, IOError) as write_err:
                    last_err = write_err
                    log.debug(f"AudioEqualizer: {self._addon_file_name} bloqueado en intento {attempt + 1}/10 ({write_err}), reintentando...")
                    time.sleep(0.04)
            else:
                raise IOError(f"Archivo {self._addon_file_name} bloqueado por audiodg.exe u otro proceso tras 10 intentos: {last_err}")
            
            # Forzar recarga en Equalizer APO
            try:
                os.utime(self._main_config, None)
                log.debug("AudioEqualizer: Timestamp de config.txt actualizado para recarga en tiempo real.")
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
                    anti_box=self._anti_box,
                    clarity=self._clarity,
                    anti_sibilance=self._anti_sibilance,
                    anti_fatigue=self._anti_fatigue,
                    ground_hum=self._ground_hum,
                    subsonic=self._subsonic,
                    nvda_voice=self._nvda_voice,
                    stereo_width=self._stereo_width,
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
