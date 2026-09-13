# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Contrato de abstracción para el backend de audio.
"""

import abc
from typing import List


class AudioBackend(abc.ABC):
    @abc.abstractmethod
    def is_available(self) -> bool:
        pass

    @abc.abstractmethod
    def get_enabled(self) -> bool:
        pass

    @abc.abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        pass

    @abc.abstractmethod
    def get_gains(self) -> List[float]:
        pass

    @abc.abstractmethod
    def set_gains(self, gains: List[float], preamp: float) -> None:
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    def close(self) -> None:
        pass
