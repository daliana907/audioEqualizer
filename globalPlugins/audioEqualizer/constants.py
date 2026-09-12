# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Constantes globales para el ecualizador de audio.
Define las 31 frecuencias de las bandas ISO, límites de ganancia, balance y valores por defecto.
"""

# Frecuencias estándar ISO de 31 bandas (1/3 de octava, en Hz)
EQ_BANDS = (
    20, 25, 31, 40, 50, 63, 80, 100, 125, 160,
    200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600,
    2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000
)
NUM_BANDS = len(EQ_BANDS)

# Límites de ganancia para las 31 bandas (en decibelios)
MIN_GAIN = -12.0
MAX_GAIN = 12.0

# Límites para preamplificación (en decibelios)
MIN_PREAMP = -20.0
MAX_PREAMP = 0.0

# Límites de balance estéreo (-100 a +100)
MIN_BALANCE = -100
MAX_BALANCE = 100
DEFAULT_BALANCE = 0

# Límites para controles de tono (en decibelios)
MIN_TONE = -6.0
MAX_TONE = 6.0
DEFAULT_TONE_BASS = 0.0
DEFAULT_TONE_TREBLE = 0.0

# Configuración por defecto
DEFAULT_ENABLED = False
DEFAULT_PREAMP = 0.0
DEFAULT_AUTO_PREAMP = False
DEFAULT_LOUDNESS = False
DEFAULT_MONO = False
DEFAULT_SWAP = False
DEFAULT_SUB_BASS = False
DEFAULT_ANTI_BOX = False
DEFAULT_CLARITY = False
DEFAULT_ANTI_SIBILANCE = False
DEFAULT_ANTI_FATIGUE = False
DEFAULT_GROUND_HUM = False
DEFAULT_SUBSONIC = False
DEFAULT_NVDA_VOICE = False

# Ancho estéreo (0% = mono, 100% = estéreo normal, 200% = máxima expansión)
MIN_STEREO_WIDTH = 0
MAX_STEREO_WIDTH = 200
DEFAULT_STEREO_WIDTH = 100

DEFAULT_GAINS = (0.0,) * NUM_BANDS


