# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Generador y reproductor de comprobación de canales de audio (Test estéreo).

Crea de forma procedural un archivo WAV estéreo temporal de alta fidelidad con:
1. Canal Izquierdo: tono senoidal de 500 Hz emitido exclusivamente por el auricular izquierdo.
2. Silencio de separación de 150 milisegundos.
3. Canal Derecho: tono senoidal de 500 Hz emitido exclusivamente por el auricular derecho.
4. Silencio de separación de 150 milisegundos.
5. Centro Estéreo: acorde armónico consonante (Do5 523.25 Hz + Mi5 659.25 Hz) centrado al 50% en ambos lados.

Aplica una rampa de desvanecimiento suave (fade-in y fade-out) de 20 milisegundos para eliminar
cualquier chasquido (pop) por discontinuidad de fase al arrancar o cortar la onda sonora.
"""
import addonHandler
addonHandler.initTranslation()


import os
import math
import wave
import struct
import tempfile
import threading

try:
    import winsound
except ImportError:
    winsound = None

try:
    from logHandler import log
except ImportError:
    import logging
    log = logging.getLogger("audioEqualizer")

try:
    import ui
except ImportError:
    class _UIFallback:
        @staticmethod
        def message(msg):
            """Emite un mensaje informativo o actúa como no-op en entornos de prueba."""
            pass
    ui = _UIFallback()

_TEST_WAV_PATH = os.path.join(tempfile.gettempdir(), "audio_equalizer_channel_test.wav")


def generate_channel_test_wav(sample_rate: int = 44100) -> str:
    """Genera en el disco temporal el archivo WAV calibrado para la prueba de canales.

    Sintetiza matemáticamente las ondas sonoras en formato PCM estéreo de 16 bits a 44.1 kHz.
    Devuelve la ruta absoluta al archivo generado.
    """
    tone_dur = 0.35      # 350 milisegundos para cada canal individual
    silence_dur = 0.15   # 150 milisegundos de silencio entre tonos
    center_dur = 0.55    # 550 milisegundos para el acorde armónico centrado
    fade_dur = 0.02      # 20 milisegundos de rampa suave anti-chasquidos
    fade_samples = int(sample_rate * fade_dur)

    def _generate_segment(freqs, duration: float, pan_l: float = 1.0, pan_r: float = 1.0):
        """Genera muestras PCM normalizadas para una o más frecuencias con panoramización."""
        num_samples = int(sample_rate * duration)
        amp = 0.7 / len(freqs)  # Normalizamos la amplitud para no sobrepasar el techo digital
        samples = []
        for i in range(num_samples):
            # Envolvente lineal para suavizar entrada y salida
            if i < fade_samples:
                env = i / fade_samples
            elif i > num_samples - fade_samples:
                env = (num_samples - i) / fade_samples
            else:
                env = 1.0

            t = float(i) / sample_rate
            val = sum(math.sin(2.0 * math.pi * f * t) * amp for f in freqs) * env
            samples.append((int(val * pan_l * 32767.0), int(val * pan_r * 32767.0)))
        return samples

    silence = [(0, 0)] * int(sample_rate * silence_dur)
    all_samples = (
        _generate_segment([500.0], tone_dur, pan_l=1.0, pan_r=0.0)
        + silence
        + _generate_segment([500.0], tone_dur, pan_l=0.0, pan_r=1.0)
        + silence
        + _generate_segment([523.25, 659.25], center_dur, pan_l=1.0, pan_r=1.0)
    )

    tmp_path = _TEST_WAV_PATH + ".tmp"
    try:
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            packed_frames = bytearray()
            for sl, sr in all_samples:
                packed_frames.extend(struct.pack("<hh", sl, sr))
            wf.writeframes(packed_frames)
        os.replace(tmp_path, _TEST_WAV_PATH)
    except Exception as e:
        log.error(f"AudioEqualizer: Error al generar WAV de prueba en {_TEST_WAV_PATH}: {e}", exc_info=True)
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        try:
            from . import logger
            logger.log_error(f"Error generando archivo WAV temporal: {e}", exc=e, component="ChannelTester", context={"path": _TEST_WAV_PATH})
        except Exception:
            pass
        raise

    return _TEST_WAV_PATH


_test_in_progress = threading.Lock()


def play_channel_test() -> None:
    """Reproduce la prueba de canales de forma asíncrona en un hilo en segundo plano.

    Garantiza que el hilo principal de NVDA permanezca receptivo y el sintetizador de voz
    pueda seguir hablando sin bloqueos ni tartamudeos mientras se reproduce el sonido.
    """
    if not winsound:
        log.warning("AudioEqualizer: Módulo winsound no disponible; omitiendo prueba de canales.")
        ui.message(_("No se puede reproducir audio: winsound no está disponible."))
        return

    if not _test_in_progress.acquire(blocking=False):
        # Ya hay una prueba de canales en curso: si generáramos otra a la vez, ambas
        # escribirían sobre el mismo archivo temporal al mismo tiempo y podrían dañarlo.
        ui.message(_("Ya se está reproduciendo la comprobación de canales."))
        return

    def _worker():
        """Genera el WAV si no existe y lo reproduce en segundo plano con winsound."""
        try:
            if not os.path.exists(_TEST_WAV_PATH) or os.path.getsize(_TEST_WAV_PATH) == 0:
                generate_channel_test_wav()
            winsound.PlaySound(_TEST_WAV_PATH, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
        except Exception as e:
            log.error(f"AudioEqualizer: Error reproduciendo comprobación de canales: {e}", exc_info=True)
            try:
                if os.path.exists(_TEST_WAV_PATH):
                    os.remove(_TEST_WAV_PATH)
            except Exception:
                pass
            try:
                from . import logger
                logger.log_error(f"Error en reproducción de canales: {e}", exc=e, component="ChannelTester")
            except Exception:
                pass
            try:
                import core
                core.callLater(0, ui.message, _("Error al reproducir comprobación de canales: {e}").format(e=e))
            except Exception:
                ui.message(_("Error al reproducir comprobación de canales: {e}").format(e=e))
        finally:
            _test_in_progress.release()

    threading.Thread(target=_worker, daemon=True).start()
