# -*- coding: utf-8 -*-
"""
Perfiles profesionales de ecualización para auriculares (31 bandas ISO).
Cada perfil incluye su configuración acústica óptima completa:
- Bandas de ecualización (gains)
- Filtros para auriculares (sub_bass, anti_box, clarity, anti_sibilance, subsonic, nvda_voice)
- Procesamiento acústico y espacial (loudness, stereo_width)
- Controles de tono rápido (tone_bass, tone_treble)
"""

from . import constants

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
        "anti_box": False,
        "clarity": False,
        "anti_sibilance": False,
        "subsonic": False,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 100,
    },
    {
        "name": "Música (Curva dinámica V-Shape)",
        "gains": [
            7.0, 7.0, 7.0, 6.5, 6.0, 5.0, 3.5, 2.0, 1.0, 0.0,
            -0.5, -1.0, -1.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0,
            1.5, 2.5, 3.5, 4.5, 5.5, 6.0, 6.5, 6.0, 5.0, 4.0, 2.5
        ],
        "tone_bass": 0.0,
        "tone_treble": 0.0,
        "sub_bass": True,
        "anti_box": True,
        "clarity": True,
        "anti_sibilance": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 120,
    },
    {
        "name": "Estudio de grabación (Analítico)",
        "gains": [
            -3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0,
            4.0, 4.0, 4.0, 3.5, 3.0, 3.0, 3.5, 3.5, 3.0, 2.5, 2.0
        ],
        "tone_bass": 0.0,
        "tone_treble": 0.0,
        "sub_bass": False,
        "anti_box": True,
        "clarity": False,
        "anti_sibilance": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 100,
    },
    {
        "name": "Películas y series (Cine y diálogo)",
        "gains": [
            8.5, 8.5, 8.5, 8.0, 7.5, 6.0, 4.0, 2.0, 0.5, -1.0,
            -2.5, -3.5, -4.0, -3.5, -2.0, 0.0, 1.5, 3.5, 5.0, 6.0,
            6.0, 5.5, 4.5, 3.5, 2.0, 1.0, 0.0, -1.0, -2.0, -3.0, -4.0
        ],
        "tone_bass": 0.0,
        "tone_treble": 0.0,
        "sub_bass": True,
        "anti_box": True,
        "clarity": True,
        "anti_sibilance": True,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 140,
    },
    {
        "name": "Juegos (Pasos y detalles)",
        "gains": [
            -9.0, -9.0, -8.0, -7.0, -6.0, -4.0, -2.0, 0.0, 1.0, 1.5,
            2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 7.5, 8.0, 8.0,
            7.5, 7.0, 6.5, 6.0, 5.5, 5.0, 4.5, 4.0, 3.0, 1.5, 0.0
        ],
        "tone_bass": 0.0,
        "tone_treble": 0.0,
        "sub_bass": False,
        "anti_box": True,
        "clarity": True,
        "anti_sibilance": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 130,
    },
    {
        "name": "Voz y podcasts (Máxima claridad)",
        "gains": [
            -12.0, -12.0, -11.0, -10.0, -9.0, -7.0, -5.0, -3.0, -1.0, 0.0,
            1.0, 2.0, 3.0, 4.5, 6.0, 7.5, 8.0, 8.0, 7.5, 6.5,
            5.5, 4.0, 2.5, 1.0, -1.0, -3.0, -5.0, -7.0, -9.0, -10.0, -11.0
        ],
        "tone_bass": 0.0,
        "tone_treble": 0.0,
        "sub_bass": False,
        "anti_box": True,
        "clarity": True,
        "anti_sibilance": True,
        "subsonic": True,
        "nvda_voice": True,
        "loudness": False,
        "stereo_width": 100,
    },
    {
        "name": "Rock y metal (Pegada y guitarras)",
        "gains": [
            4.0, 5.0, 6.0, 7.0, 7.5, 6.5, 4.5, 2.5, 0.5, -1.0,
            -2.5, -3.5, -4.5, -4.0, -2.5, -1.0, 0.5, 2.0, 3.5, 5.0,
            6.5, 6.5, 6.0, 5.5, 5.0, 5.5, 6.0, 5.0, 4.0, 2.5, 1.0
        ],
        "tone_bass": 0.0,
        "tone_treble": 0.0,
        "sub_bass": True,
        "anti_box": True,
        "clarity": True,
        "anti_sibilance": True,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 125,
    },
    {
        "name": "Pop y acústico (Voz suave y brillo)",
        "gains": [
            3.5, 4.0, 4.5, 5.0, 5.5, 5.0, 4.0, 3.0, 2.0, 1.0,
            0.5, 0.0, 0.0, 0.5, 1.0, 1.5, 2.5, 3.5, 4.5, 5.5,
            5.5, 5.0, 4.5, 4.5, 5.0, 6.0, 6.5, 6.0, 5.5, 4.5, 3.5
        ],
        "tone_bass": 0.0,
        "tone_treble": 0.0,
        "sub_bass": False,
        "anti_box": True,
        "clarity": True,
        "anti_sibilance": True,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 115,
    },
    {
        "name": "Música electrónica (Sub-Bass potente)",
        "gains": [
            9.5, 9.5, 9.5, 9.0, 8.5, 7.0, 5.0, 3.0, 1.0, 0.0,
            -1.0, -2.0, -3.0, -3.5, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0,
            3.0, 4.0, 5.0, 6.0, 7.0, 7.5, 8.0, 8.0, 7.5, 6.5, 5.0
        ],
        "tone_bass": 0.0,
        "tone_treble": 0.0,
        "sub_bass": True,
        "anti_box": True,
        "clarity": True,
        "anti_sibilance": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 135,
    },
    {
        "name": "Música clásica (Acústica orquestal)",
        "gains": [
            0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
            0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0,
            5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.0, 7.5, 7.0, 6.0, 5.0
        ],
        "tone_bass": 0.0,
        "tone_treble": 0.0,
        "sub_bass": False,
        "anti_box": False,
        "clarity": True,
        "anti_sibilance": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 130,
    },
    {
        "name": "Jazz y blues (Calidez íntima)",
        "gains": [
            4.5, 5.0, 5.5, 6.0, 6.5, 6.5, 6.0, 5.5, 4.5, 3.5,
            2.5, 2.0, 1.5, 1.5, 2.0, 2.5, 3.5, 4.5, 5.0, 5.0,
            4.5, 3.5, 2.5, 1.5, 0.5, 0.0, -1.0, -2.0, -3.0, -4.0, -5.0
        ],
        "tone_bass": 0.0,
        "tone_treble": 0.0,
        "sub_bass": False,
        "anti_box": True,
        "clarity": False,
        "anti_sibilance": True,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 105,
    },
    {
        "name": "Más graves (Bass Boost)",
        "gains": [
            10.0, 10.0, 10.0, 9.5, 9.0, 8.5, 7.5, 6.5, 5.0, 3.5,
            2.0, 1.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ],
        "tone_bass": 2.0,
        "tone_treble": 0.0,
        "sub_bass": True,
        "anti_box": True,
        "clarity": False,
        "anti_sibilance": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 100,
    },
    {
        "name": "Más agudos (Treble Boost)",
        "gains": [
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.5, 1.0, 1.5, 2.5, 3.5, 4.5, 5.5,
            6.5, 7.5, 8.5, 9.0, 9.5, 10.0, 10.0, 9.5, 9.0, 8.5, 7.5
        ],
        "tone_bass": 0.0,
        "tone_treble": 2.0,
        "sub_bass": False,
        "anti_box": True,
        "clarity": True,
        "anti_sibilance": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 110,
    },
    {
        "name": "Modo nocturno (Suave y relajante)",
        "gains": [
            -7.0, -7.0, -6.5, -6.0, -5.0, -4.0, -3.0, -2.0, -1.0, 0.0,
            0.5, 1.0, 1.5, 1.5, 1.5, 1.5, 1.0, 0.5, 0.0, -0.5,
            -1.0, -1.5, -2.5, -3.5, -4.5, -5.5, -6.5, -7.5, -8.5, -9.5, -10.0
        ],
        "tone_bass": -1.0,
        "tone_treble": -2.0,
        "sub_bass": False,
        "anti_box": True,
        "clarity": False,
        "anti_sibilance": True,
        "anti_fatigue": True,
        "ground_hum": False,
        "subsonic": True,
        "nvda_voice": False,
        "loudness": False,
        "stereo_width": 100,
    },
]

# Lista ordenada de nombres legibles para la interfaz gráfica y los anuncios de voz de NVDA
PROFILE_NAMES = [p["name"] for p in PREDEFINED_PROFILES]

# Índice especial reservado para el perfil 'Personalizado' (inmediatamente después de los predefinidos)
CUSTOM_INDEX = len(PREDEFINED_PROFILES)

