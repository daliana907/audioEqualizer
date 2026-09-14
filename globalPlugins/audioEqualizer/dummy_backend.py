# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Backend simulado (Dummy) para pruebas y desarrollo.
Cumple con la interfaz AudioBackend pero no procesa audio real.
"""

from typing import List
from .backend import AudioBackend


class DummyBackend(AudioBackend):
    """Backend simulado en memoria para entornos de pruebas automatizadas o sin Equalizer APO instalado."""

    def __init__(self):
        """Inicializa el estado interno del backend simulado: ecualizador desactivado, 31 ganancias a cero y preamp a 0 dB."""
        self._enabled = False
        self._gains = [0.0] * 31
        self._preamp = 0.0

    def is_available(self) -> bool:
        """El backend simulado siempre se reporta como disponible."""
        return True

    def get_enabled(self) -> bool:
        """Devuelve el estado de activación en memoria."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Actualiza el estado de activación en memoria."""
        self._enabled = enabled

    def get_gains(self) -> List[float]:
        """Devuelve la lista actual de ganancias en memoria."""
        return self._gains

    def set_gains(self, gains: List[float], preamp: float) -> None:
        """Guarda las ganancias y el nivel de preamplificación en memoria."""
        self._gains = list(gains)
        self._preamp = preamp

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
        stereo_width: int = 100,
    ) -> None:
        """Almacena el estado completo de ecualización y procesamiento en memoria."""
        self._enabled = enabled
        self._gains = list(gains)
        self._preamp = preamp
        self.auto_preamp = auto_preamp
        self.loudness = loudness
        self.mono = mono
        self.swap_channels = swap_channels
        self.balance = balance
        self.tone_bass = tone_bass
        self.tone_treble = tone_treble
        self.sub_bass = sub_bass
        self.clarity = clarity
        self.anti_sibilance = anti_sibilance
        self.anti_fatigue = anti_fatigue
        self.ground_hum = ground_hum
        self.subsonic = subsonic
        self.nvda_voice = nvda_voice
        self.stereo_width = stereo_width

    def close(self) -> None:
        """No requiere liberación de recursos externos al ser una simulación en memoria."""
        pass
