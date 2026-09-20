# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Perfiles profesionales de ecualización para auriculares (31 bandas ISO).
Cada perfil incluye su configuración acústica óptima completa:
- Bandas de ecualización (gains)
- Procesamiento acústico y espacial (loudness, stereo_width)
- Controles de tono rápido (tone_bass, tone_treble)
- Filtros especializados (sub_bass, clarity, anti_sibilance, anti_fatigue, ground_hum, subsonic, nvda_voice)
"""

PREDEFINED_PROFILES = [
    {
        "name": "Plano (Sin ecualizar)",
        "gains": [
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ],
        "tone_bass": 0.0,
        "tone_treble": 0.0,
        "sub_bass": False,
        "clarity": False,
        "anti_sibilance": False,
        "anti_fatigue": False,
        "ground_hum": False,
        "subsonic": False,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 100,
    },
    {
        "name": "Música (Curva Harman)",
        "gains": [
            5.5, 5.5, 5.0, 4.5, 4.0, 3.0, 2.0, 1.0, 0.5, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.8,
            2.5, 3.0, 3.5, 2.5, 1.5, 1.0, 0.5, 0.0, 0.0, -0.5, -1.0
        ],
        "tone_bass": 1.0,
        "tone_treble": 0.0,
        "sub_bass": False,
        "clarity": False,
        "anti_sibilance": True,
        "anti_fatigue": False,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 105,
    },
    {
        "name": "Estudio de grabación (Analítico)",
        "gains": [
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.5,
            2.0, 2.0, 2.0, 1.5, 1.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0
        ],
        "tone_bass": 0.0,
        "tone_treble": 0.0,
        "sub_bass": False,
        "clarity": False,
        "anti_sibilance": False,
        "anti_fatigue": False,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 100,
    },
    {
        "name": "Películas y series (Cine y diálogo)",
        "gains": [
            4.0, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 1.0, 1.5, 2.2,
            2.8, 3.2, 3.0, 2.2, 1.2, 0.5, 0.0, -0.5, -1.0, -1.5, -2.0
        ],
        "tone_bass": 2.0,
        "tone_treble": 0.0,
        "sub_bass": True,
        "clarity": True,
        "anti_sibilance": True,
        "anti_fatigue": False,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 110,
    },
    {
        "name": "Juegos (Pasos y detalles)",
        "gains": [
            -3.0, -3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.5, 2.0, 2.8,
            3.5, 4.0, 4.5, 4.0, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5, 0.0
        ],
        "tone_bass": -2.0,
        "tone_treble": 2.0,
        "sub_bass": False,
        "clarity": True,
        "anti_sibilance": False,
        "anti_fatigue": False,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 115,
    },
    {
        "name": "Voz y podcasts (Máxima claridad)",
        "gains": [
            -6.0, -5.5, -5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 0.0, 0.0,
            0.5, 0.5, 0.5, 0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.8,
            3.5, 3.5, 3.0, 2.0, 1.0, 0.0, -1.0, -2.0, -3.0, -4.0, -5.0
        ],
        "tone_bass": -2.0,
        "tone_treble": 1.0,
        "sub_bass": False,
        "clarity": True,
        "anti_sibilance": True,
        "anti_fatigue": False,
        "ground_hum": True,
        "subsonic": True,
        "nvda_voice": True,
        "loudness": False,
        "stereo_width": 100,
    },
    {
        "name": "Rock y metal (Pegada y guitarras)",
        "gains": [
            3.5, 4.0, 4.5, 5.0, 5.0, 4.5, 3.5, 2.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 1.0, 1.5, 2.0, 2.5,
            3.0, 3.5, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5, 0.0, 0.0
        ],
        "tone_bass": 2.0,
        "tone_treble": 1.0,
        "sub_bass": False,
        "clarity": True,
        "anti_sibilance": True,
        "anti_fatigue": False,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 105,
    },
    {
        "name": "Pop y acústico (Voz suave y brillo)",
        "gains": [
            4.0, 4.0, 4.0, 3.5, 3.0, 2.5, 2.0, 1.2, 0.5, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.5, 2.0,
            2.5, 3.0, 3.2, 2.8, 2.2, 1.8, 1.5, 1.5, 1.2, 0.8, 0.5
        ],
        "tone_bass": 1.0,
        "tone_treble": 1.0,
        "sub_bass": False,
        "clarity": True,
        "anti_sibilance": True,
        "anti_fatigue": False,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 105,
    },
    {
        "name": "Música electrónica (Sub-Bass potente)",
        "gains": [
            6.5, 6.5, 6.0, 5.5, 4.5, 3.5, 2.5, 1.5, 0.8, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.5, 2.0,
            2.5, 3.0, 3.5, 3.0, 2.5, 2.5, 2.0, 1.5, 1.0, 0.5, 0.0
        ],
        "tone_bass": 3.0,
        "tone_treble": 1.0,
        "sub_bass": True,
        "clarity": True,
        "anti_sibilance": False,
        "anti_fatigue": False,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 110,
    },
    {
        "name": "Música clásica (Acústica orquestal)",
        "gains": [
            2.0, 2.0, 2.0, 1.5, 1.0, 0.5, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.5,
            2.0, 2.5, 2.5, 2.0, 1.8, 1.5, 1.5, 1.2, 1.0, 0.5, 0.0
        ],
        "tone_bass": 1.0,
        "tone_treble": 1.0,
        "sub_bass": False,
        "clarity": True,
        "anti_sibilance": False,
        "anti_fatigue": False,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": True,
        "stereo_width": 115,
    },
    {
        "name": "Jazz y blues (Calidez íntima)",
        "gains": [
            2.0, 2.5, 3.0, 3.5, 3.5, 3.0, 2.5, 1.8, 1.0, 0.5,
            0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.8, 1.0, 1.2, 1.5,
            1.8, 2.0, 2.0, 1.5, 1.0, 0.5, 0.0, -0.5, -1.0, -1.5, -2.0
        ],
        "tone_bass": 1.0,
        "tone_treble": -1.0,
        "sub_bass": False,
        "clarity": False,
        "anti_sibilance": True,
        "anti_fatigue": True,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 100,
    },
    {
        "name": "Más graves (Bass Boost)",
        "gains": [
            6.5, 6.5, 6.0, 5.5, 4.5, 3.5, 2.5, 1.5, 0.8, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ],
        "tone_bass": 4.0,
        "tone_treble": 0.0,
        "sub_bass": True,
        "clarity": False,
        "anti_sibilance": False,
        "anti_fatigue": False,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 100,
    },
    {
        "name": "Más agudos (Treble Boost)",
        "gains": [
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.5, 1.0, 1.8, 2.5, 3.2, 3.8, 4.0, 4.0, 3.5, 3.0, 2.0
        ],
        "tone_bass": 0.0,
        "tone_treble": 4.0,
        "sub_bass": False,
        "clarity": True,
        "anti_sibilance": False,
        "anti_fatigue": False,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 100,
    },
    {
        "name": "Modo nocturno (Suave y relajante)",
        "gains": [
            1.5, 2.0, 2.0, 2.0, 1.8, 1.5, 1.0, 0.5, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5,
            0.5, 0.5, 0.0, -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, -4.0, -5.0
        ],
        "tone_bass": 0.0,
        "tone_treble": -2.0,
        "sub_bass": False,
        "clarity": False,
        "anti_sibilance": True,
        "anti_fatigue": True,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": True,
        "stereo_width": 100,
    },
]

# Lista ordenada de nombres legibles para la interfaz gráfica y los anuncios de voz de NVDA
PROFILE_NAMES = [p["name"] for p in PREDEFINED_PROFILES]

# Índice especial reservado para el perfil 'Personalizado' (inmediatamente después de los predefinidos)
CUSTOM_INDEX = len(PREDEFINED_PROFILES)
