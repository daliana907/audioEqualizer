# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Modelo de datos, validación y persistencia para Audio Equalizer.

Define la estructura de datos EqualizerProfile, que encapsula los parámetros de las 31 bandas ISO,
el anticlíping, el volumen seguro, los controles de tono y los filtros acústicos avanzados.
Gestiona tanto la persistencia centralizada en la configuración oficial de NVDA (nvda.ini a través de configspec)
como el almacenamiento de perfiles personalizados creados por el usuario en formato JSON.
"""

try:
    import config
except ImportError:
    config = None

import os
import json
from typing import List, Dict, Any
from . import constants

try:
    from logHandler import log
except ImportError:
    import logging
    log = logging.getLogger("audioEqualizer")

def _get_user_profiles_file() -> str:
    """Devuelve la ruta correcta para guardar los perfiles personalizados del usuario.

    Intenta guardarlo en la carpeta de configuración activa del perfil de NVDA
    (junto a nvda.ini) para que no se pierdan al actualizar el complemento.
    Si NVDA no está corriendo, recurre a la carpeta local del complemento.
    """
    try:
        import globalVars
        return os.path.join(globalVars.appArgs.configPath, "audioEqualizer_user_profiles.json")
    except Exception:
        return os.path.join(os.path.dirname(__file__), "user_profiles.json")

USER_PROFILES_FILE = _get_user_profiles_file()


class EqualizerProfile:
    """Representa el estado acústico completo de un ajuste de ecualización.

    Contiene las 31 bandas estándar ISO, preamplificación de ganancia, banderas de
    filtros de auriculares, controles rápidos de tono y opciones de escena estéreo.
    Asegura mediante propiedades que ningún valor salga de los rangos seguros en decibelios.
    """

    def __init__(
        self,
        enabled: bool = constants.DEFAULT_ENABLED,
        preamp: float = constants.DEFAULT_PREAMP,
        auto_preamp: bool = constants.DEFAULT_AUTO_PREAMP,
        loudness: bool = constants.DEFAULT_LOUDNESS,
        mono: bool = constants.DEFAULT_MONO,
        swap_channels: bool = constants.DEFAULT_SWAP,
        balance: int = constants.DEFAULT_BALANCE,
        tone_bass: float = constants.DEFAULT_TONE_BASS,
        tone_treble: float = constants.DEFAULT_TONE_TREBLE,
        sub_bass: bool = constants.DEFAULT_SUB_BASS,
        clarity: bool = constants.DEFAULT_CLARITY,
        anti_sibilance: bool = constants.DEFAULT_ANTI_SIBILANCE,
        anti_fatigue: bool = constants.DEFAULT_ANTI_FATIGUE,
        ground_hum: bool = constants.DEFAULT_GROUND_HUM,
        subsonic: bool = constants.DEFAULT_SUBSONIC,
        nvda_voice: bool = constants.DEFAULT_NVDA_VOICE,
        stereo_width: int = constants.DEFAULT_STEREO_WIDTH,
        gains: List[float] = None,
        profile_index: int = 0,
    ):
        self._enabled = bool(enabled)
        self._preamp = float(preamp)
        self.auto_preamp = bool(auto_preamp)
        self.loudness = bool(loudness)
        self.mono = bool(mono)
        self.swap_channels = bool(swap_channels)
        self.balance = int(balance)
        self.tone_bass = float(tone_bass)
        self.tone_treble = float(tone_treble)
        self.sub_bass = bool(sub_bass)
        self.clarity = bool(clarity)
        self.anti_sibilance = bool(anti_sibilance)
        self.anti_fatigue = bool(anti_fatigue)
        self.ground_hum = bool(ground_hum)
        self.subsonic = bool(subsonic)
        self.nvda_voice = bool(nvda_voice)
        self.stereo_width = int(stereo_width)
        self._profile_index = int(profile_index)
        self._gains = list(constants.DEFAULT_GAINS)
        
        if gains is not None:
            self.gains = gains

    @property
    def profile_index(self) -> int:
        """Índice numérico del perfil activo en la lista desplegable."""
        return self._profile_index
        
    @profile_index.setter
    def profile_index(self, value: int) -> None:
        try:
            self._profile_index = int(value)
        except (ValueError, TypeError):
            self._profile_index = 0

    @property
    def enabled(self) -> bool:
        """Indica si la ecualización está activada."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("Enabled debe ser booleano.")
        self._enabled = value

    @property
    def preamp(self) -> float:
        """Ganancia de preamplificación manual en decibelios (-20.0 dB a +20.0 dB)."""
        return self._preamp

    @preamp.setter
    def preamp(self, value: float) -> None:
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise TypeError("Preamp debe ser numérico.")
            
        if not (constants.MIN_PREAMP <= val <= constants.MAX_PREAMP):
            raise ValueError(f"Preamp fuera de rango: {val}.")
        self._preamp = val

    @property
    def gains(self) -> List[float]:
        """Copia de la lista de ganancias de las 31 bandas ISO."""
        return list(self._gains)

    @gains.setter
    def gains(self, values: List[float]) -> None:
        """Valida que haya exactamente 31 bandas y que cada una esté entre -24 dB y +24 dB."""
        if not isinstance(values, (list, tuple)):
            raise TypeError("Las ganancias deben ser una lista o tupla.")
            
        if len(values) != constants.NUM_BANDS:
            raise ValueError(f"Se esperaban {constants.NUM_BANDS} bandas, recibidas {len(values)}.")
            
        clean_gains = []
        for v in values:
            try:
                f_val = float(v)
            except (ValueError, TypeError):
                raise TypeError(f"Valor de ganancia '{v}' no numérico.")
                
            if not (constants.MIN_GAIN <= f_val <= constants.MAX_GAIN):
                raise ValueError(f"Ganancia {f_val} fuera de rango.")
            clean_gains.append(f_val)
            
        self._gains = clean_gains

    def clone(self) -> "EqualizerProfile":
        """Crea una copia profunda independiente del perfil para edición sin alterar el original."""
        return EqualizerProfile(
            enabled=self._enabled,
            preamp=self._preamp,
            auto_preamp=self.auto_preamp,
            loudness=self.loudness,
            mono=self.mono,
            swap_channels=self.swap_channels,
            balance=self.balance,
            tone_bass=self.tone_bass,
            tone_treble=self.tone_treble,
            sub_bass=self.sub_bass,
            clarity=self.clarity,
            anti_sibilance=self.anti_sibilance,
            anti_fatigue=self.anti_fatigue,
            ground_hum=self.ground_hum,
            subsonic=self.subsonic,
            nvda_voice=self.nvda_voice,
            stereo_width=self.stereo_width,
            gains=list(self._gains),
            profile_index=self._profile_index,
        )


def get_default_profile() -> EqualizerProfile:
    """Devuelve un perfil con los valores acústicos de fábrica.

    Todas las bandas están en 0.0 dB (respuesta plana), el ecualizador comienza
    desactivado para no alterar el sonido sin intervención del usuario y los
    filtros avanzados permanecen apagados.
    """
    return EqualizerProfile(
        enabled=constants.DEFAULT_ENABLED,
        preamp=constants.DEFAULT_PREAMP,
        auto_preamp=constants.DEFAULT_AUTO_PREAMP,
        loudness=constants.DEFAULT_LOUDNESS,
        mono=constants.DEFAULT_MONO,
        swap_channels=constants.DEFAULT_SWAP,
        balance=constants.DEFAULT_BALANCE,
        tone_bass=constants.DEFAULT_TONE_BASS,
        tone_treble=constants.DEFAULT_TONE_TREBLE,
        sub_bass=constants.DEFAULT_SUB_BASS,
        clarity=constants.DEFAULT_CLARITY,
        anti_sibilance=constants.DEFAULT_ANTI_SIBILANCE,
        anti_fatigue=constants.DEFAULT_ANTI_FATIGUE,
        ground_hum=constants.DEFAULT_GROUND_HUM,
        subsonic=constants.DEFAULT_SUBSONIC,
        nvda_voice=constants.DEFAULT_NVDA_VOICE,
        stereo_width=constants.DEFAULT_STEREO_WIDTH,
        gains=list(constants.DEFAULT_GAINS),
        profile_index=0,
    )


def init_config_spec():
    """Registra las especificaciones de configuración en el motor de NVDA.

    Define los tipos de datos exactos (booleanos, enteros con límites mínimo y máximo,
    números flotantes y listas) para la sección [audioEqualizer] en el archivo nvda.ini.
    Esto garantiza que NVDA pueda validar y reparar automáticamente valores corruptos
    sin cerrarse inesperadamente.
    """
    gains_default_str = ", ".join(["0.0"] * constants.NUM_BANDS)
    config.conf.spec["audioEqualizer"] = {
        "enabled": "boolean(default=False)",
        "preamp": "float(default=0.0)",
        "auto_preamp": "boolean(default=False)",
        "loudness": "boolean(default=False)",
        "mono": "boolean(default=False)",
        "swap_channels": "boolean(default=False)",
        "balance": f"integer(default={constants.DEFAULT_BALANCE}, min={constants.MIN_BALANCE}, max={constants.MAX_BALANCE})",
        "tone_bass": f"float(default={constants.DEFAULT_TONE_BASS})",
        "tone_treble": f"float(default={constants.DEFAULT_TONE_TREBLE})",
        "sub_bass": "boolean(default=False)",
        "clarity": "boolean(default=False)",
        "anti_sibilance": "boolean(default=False)",
        "anti_fatigue": "boolean(default=False)",
        "ground_hum": "boolean(default=False)",
        "subsonic": "boolean(default=False)",
        "nvda_voice": "boolean(default=False)",
        "stereo_width": f"integer(default={constants.DEFAULT_STEREO_WIDTH}, min={constants.MIN_STEREO_WIDTH}, max={constants.MAX_STEREO_WIDTH})",
        "profile_index": "integer(default=0)",
        "gains": f"list(default=list({gains_default_str}))",
    }


def load_profile() -> EqualizerProfile:
    """Carga los parámetros del ecualizador desde el archivo nvda.ini de NVDA.

    Si los datos de las ganancias no coinciden exactamente con las 31 bandas ISO,
    o si ocurre un fallo al leer la configuración, recurre al perfil plano por defecto
    y deja constancia en el registro de errores para que el complemento nunca bloquee el arranque.
    """
    try:
        c = config.conf["audioEqualizer"]
        raw_gains = c.get("gains", [])
        parsed_gains = [float(x) for x in raw_gains]
        if len(parsed_gains) != constants.NUM_BANDS:
            parsed_gains = list(constants.DEFAULT_GAINS)
            
        return EqualizerProfile(
            enabled=c.get("enabled", False),
            preamp=float(c.get("preamp", 0.0)),
            auto_preamp=c.get("auto_preamp", False),
            loudness=c.get("loudness", False),
            mono=c.get("mono", False),
            swap_channels=c.get("swap_channels", False),
            balance=int(c.get("balance", constants.DEFAULT_BALANCE)),
            tone_bass=float(c.get("tone_bass", constants.DEFAULT_TONE_BASS)),
            tone_treble=float(c.get("tone_treble", constants.DEFAULT_TONE_TREBLE)),
            sub_bass=c.get("sub_bass", False),
            clarity=c.get("clarity", False),
            anti_sibilance=c.get("anti_sibilance", False),
            anti_fatigue=c.get("anti_fatigue", False),
            ground_hum=c.get("ground_hum", False),
            subsonic=c.get("subsonic", False),
            nvda_voice=c.get("nvda_voice", False),
            stereo_width=int(c.get("stereo_width", constants.DEFAULT_STEREO_WIDTH)),
            profile_index=int(c.get("profile_index", 0)),
            gains=parsed_gains,
        )
    except Exception as e:
        log.error(f"AudioEqualizer: Error cargando configuración: {e}", exc_info=True)
        try:
            from . import logger
            logger.log_error(f"Error cargando configuración nativa: {e}", exc=e, component="Config")
        except Exception:
            pass
        return get_default_profile()


def save_profile(profile: EqualizerProfile) -> None:
    """Guarda los parámetros de un perfil en el archivo de configuración de NVDA.

    Actualiza los valores en config.conf['audioEqualizer'] para que persistan
    entre reinicios del lector de pantalla.
    """
    try:
        c = config.conf["audioEqualizer"]
        c["enabled"] = profile.enabled
        c["preamp"] = profile.preamp
        c["auto_preamp"] = profile.auto_preamp
        c["loudness"] = profile.loudness
        c["mono"] = profile.mono
        c["swap_channels"] = profile.swap_channels
        c["balance"] = profile.balance
        c["tone_bass"] = profile.tone_bass
        c["tone_treble"] = profile.tone_treble
        c["sub_bass"] = profile.sub_bass
        c["clarity"] = profile.clarity
        c["anti_sibilance"] = profile.anti_sibilance
        c["anti_fatigue"] = profile.anti_fatigue
        c["ground_hum"] = profile.ground_hum
        c["subsonic"] = profile.subsonic
        c["nvda_voice"] = profile.nvda_voice
        c["stereo_width"] = profile.stereo_width
        c["profile_index"] = profile.profile_index
        c["gains"] = profile.gains
    except Exception as e:
        log.error(f"AudioEqualizer: Error guardando configuración nativa: {e}", exc_info=True)
        try:
            from . import logger
            logger.log_error(f"Error guardando configuración en config.conf: {e}", exc=e, component="Config")
        except Exception:
            pass


def load_user_profiles() -> List[Dict[str, Any]]:
    """Carga los perfiles acústicos creados por el usuario desde user_profiles.json.

    Si el archivo no existe aún (por ejemplo en una instalación nueva), devuelve una
    lista vacía sin generar errores. Si el archivo está dañado, captura el fallo y devuelve
    la lista vacía para permitir que NVDA continúe funcionando sin interrupciones.
    """
    if not os.path.exists(USER_PROFILES_FILE):
        return []
    try:
        with open(USER_PROFILES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception as e:
        log.error(f"AudioEqualizer: Error al cargar perfiles de usuario: {e}", exc_info=True)
        try:
            from . import logger
            logger.log_error(f"Error al cargar perfiles de usuario desde {USER_PROFILES_FILE}: {e}", exc=e, component="Config")
        except Exception:
            pass
    return []


def save_user_profile(name: str, profile: EqualizerProfile) -> bool:
    """Guarda un nuevo perfil personalizado o actualiza uno existente por su nombre.

    Escribe la curva de 31 bandas y todas las opciones acústicas asociadas en el archivo
    JSON del usuario con formato legible (indentado). Devuelve True si se guardó con éxito.
    """
    if not name or not name.strip():
        return False
    name = name.strip()
    profiles_list = load_user_profiles()
    
    prof_dict = {
        "name": name,
        "gains": list(profile.gains),
        "preamp": profile.preamp,
        "tone_bass": profile.tone_bass,
        "tone_treble": profile.tone_treble,
        "sub_bass": profile.sub_bass,
        "clarity": profile.clarity,
        "anti_sibilance": profile.anti_sibilance,
        "anti_fatigue": profile.anti_fatigue,
        "ground_hum": profile.ground_hum,
        "subsonic": profile.subsonic,
        "nvda_voice": profile.nvda_voice,
        "loudness": profile.loudness,
        "stereo_width": profile.stereo_width,
    }
    
    for i, p in enumerate(profiles_list):
        if p.get("name") == name:
            profiles_list[i] = prof_dict
            break
    else:
        profiles_list.append(prof_dict)
        
    try:
        tmp_file = USER_PROFILES_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(profiles_list, f, indent=2, ensure_ascii=False)
        os.replace(tmp_file, USER_PROFILES_FILE)
        return True
    except Exception as e:
        log.error(f"AudioEqualizer: Error guardando perfil de usuario '{name}': {e}", exc_info=True)
        try:
            from . import logger
            ctx = {"profile_name": name, "file_path": USER_PROFILES_FILE}
            logger.log_error(f"Error guardando perfil de usuario '{name}': {e}", exc=e, component="Config", context=ctx)
        except Exception:
            pass
        return False


def delete_user_profile(name: str) -> bool:
    """Elimina un perfil personalizado creado por el usuario en user_profiles.json.

    Busca el perfil por su nombre, lo remueve de la lista y actualiza el archivo en el disco.
    Devuelve True si el perfil fue encontrado y eliminado, o False si no existía.
    """
    profiles_list = load_user_profiles()
    new_list = [p for p in profiles_list if p.get("name") != name]
    if len(new_list) == len(profiles_list):
        return False
    try:
        tmp_file = USER_PROFILES_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(new_list, f, indent=2, ensure_ascii=False)
        os.replace(tmp_file, USER_PROFILES_FILE)
        return True
    except Exception as e:
        log.error(f"AudioEqualizer: Error eliminando perfil de usuario '{name}': {e}", exc_info=True)
        try:
            from . import logger
            ctx = {"profile_name": name, "file_path": USER_PROFILES_FILE}
            logger.log_error(f"Error eliminando perfil de usuario '{name}': {e}", exc=e, component="Config", context=ctx)
        except Exception:
            pass
        return False

