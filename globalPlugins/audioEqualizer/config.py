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
        surround_3d: bool = constants.DEFAULT_SURROUND_3D,
        radar_mode: bool = constants.DEFAULT_RADAR_MODE,
        stereo_width: int = constants.DEFAULT_STEREO_WIDTH,
        gains: List[float] = None,
        profile_index: int = 0,
    ):
        """Inicializa el perfil con todos los parámetros acústicos, usando los valores por defecto de constants cuando no se especifican."""
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
        self.surround_3d = bool(surround_3d)
        self.radar_mode = bool(radar_mode)
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
        """Asigna el índice del perfil activo garantizando valor entero no negativo."""
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
        """Modifica el estado de activación booleano."""
        if not isinstance(value, bool):
            raise TypeError("Enabled debe ser booleano.")
        self._enabled = value

    @property
    def preamp(self) -> float:
        """Ganancia de preamplificación manual en decibelios (-20.0 dB a +20.0 dB)."""
        return self._preamp

    @preamp.setter
    def preamp(self, value: float) -> None:
        """Ajusta el nivel de preamplificación validando los límites acústicos permitidos."""
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
            surround_3d=self.surround_3d,
            radar_mode=self.radar_mode,
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
        surround_3d=constants.DEFAULT_SURROUND_3D,
        radar_mode=constants.DEFAULT_RADAR_MODE,
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
        "surround_3d": "boolean(default=False)",
        "radar_mode": "boolean(default=False)",
        "stereo_width": f"integer(default={constants.DEFAULT_STEREO_WIDTH}, min={constants.MIN_STEREO_WIDTH}, max={constants.MAX_STEREO_WIDTH})",
        "profile_index": "integer(default=0)",
        "gains": f"list(default=list({gains_default_str}))",
    }


def _parse_bool(val, default: bool = False) -> bool:
    """Parsea de forma segura cualquier representación de booleano (bool, int, str) sin fallar."""
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        v = val.strip().lower()
        if v in ("true", "1", "yes", "on", "t", "si", "s"):
            return True
        if v in ("false", "0", "no", "off", "f"):
            return False
    return default


def _parse_float(val, default: float = 0.0) -> float:
    """Convierte de forma segura a float; si está corrupto o vacío, devuelve el valor por defecto."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _parse_int(val, default: int = 0) -> int:
    """Convierte a entero tolerando enteros, cadenas y números con decimales como '100.0'."""
    try:
        return int(round(float(val)))
    except (ValueError, TypeError):
        return default


def _parse_gains(val) -> List[float]:
    """Valida y limpia la lista de ganancias de las 31 bandas ISO, acotando a límites permitidos."""
    if val is None:
        return list(constants.DEFAULT_GAINS)
    if isinstance(val, str):
        val = [x.strip() for x in val.split(",") if x.strip()]
    if not isinstance(val, (list, tuple)):
        return list(constants.DEFAULT_GAINS)
    
    clean = []
    for item in val:
        try:
            f = float(item)
            clean.append(max(constants.MIN_GAIN, min(constants.MAX_GAIN, f)))
        except (ValueError, TypeError):
            clean.append(0.0)
            
    if len(clean) != constants.NUM_BANDS:
        if len(clean) < constants.NUM_BANDS:
            clean.extend([0.0] * (constants.NUM_BANDS - len(clean)))
        else:
            clean = clean[:constants.NUM_BANDS]
    return clean


def _get_state_file() -> str:
    """Ruta al archivo de estado persistente e indestructible de Audio Equalizer."""
    try:
        import globalVars
        if globalVars.appArgs and getattr(globalVars.appArgs, "configPath", None):
            return os.path.join(globalVars.appArgs.configPath, "audioEqualizer_state.json")
    except Exception:
        pass
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return os.path.join(appdata, "nvda", "audioEqualizer_state.json")
    return os.path.join(os.path.dirname(__file__), "audioEqualizer_state.json")


def _save_state_file(profile: EqualizerProfile) -> None:
    """Guarda una copia atómica e independiente del estado activo en JSON para evitar pérdidas en reinicios."""
    path = _get_state_file()
    tmp_path = path + ".tmp"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "enabled": bool(profile.enabled),
            "preamp": float(profile.preamp),
            "auto_preamp": bool(profile.auto_preamp),
            "loudness": bool(profile.loudness),
            "mono": bool(profile.mono),
            "swap_channels": bool(profile.swap_channels),
            "balance": int(profile.balance),
            "tone_bass": float(profile.tone_bass),
            "tone_treble": float(profile.tone_treble),
            "sub_bass": bool(profile.sub_bass),
            "clarity": bool(profile.clarity),
            "anti_sibilance": bool(profile.anti_sibilance),
            "anti_fatigue": bool(profile.anti_fatigue),
            "ground_hum": bool(profile.ground_hum),
            "subsonic": bool(profile.subsonic),
            "nvda_voice": bool(profile.nvda_voice),
            "surround_3d": bool(profile.surround_3d),
            "radar_mode": bool(profile.radar_mode),
            "stereo_width": int(profile.stereo_width),
            "profile_index": int(profile.profile_index),
            "gains": [float(g) for g in profile.gains],
        }
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp_path, path)
    except Exception as e:
        log.warning(f"AudioEqualizer: Error guardando estado de respaldo JSON: {e}")


def load_profile() -> EqualizerProfile:
    """Carga los parámetros del ecualizador desde nvda.ini o desde el archivo de respaldo seguro.

    Si nvda.ini está vacío, no se ha guardado aún, o cambia de perfil de NVDA, recurre
    al archivo de respaldo JSON para que el usuario nunca pierda sus ajustes ni amanezca apagado.
    """
    data = {}
    from_nvda_conf = False
    if config and hasattr(config, "conf"):
        try:
            if "audioEqualizer" in config.conf:
                sec = config.conf["audioEqualizer"]
                data = {str(k): sec[k] for k in sec}
                from_nvda_conf = True
        except Exception as e:
            log.warning(f"AudioEqualizer: No se pudo leer config.conf['audioEqualizer']: {e}")

    # Si nvda.ini no tiene audioEqualizer o le faltan claves críticas, leer de backup JSON
    state_file = _get_state_file()
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            if not from_nvda_conf or "enabled" not in data or "gains" not in data:
                data = json_data
            else:
                for k, v in json_data.items():
                    if k not in data or data[k] is None:
                        data[k] = v
        except Exception as e:
            log.warning(f"AudioEqualizer: Error leyendo estado de respaldo JSON: {e}")

    if not data:
        return get_default_profile()

    try:
        return EqualizerProfile(
            enabled=_parse_bool(data.get("enabled"), constants.DEFAULT_ENABLED),
            preamp=_parse_float(data.get("preamp"), constants.DEFAULT_PREAMP),
            auto_preamp=_parse_bool(data.get("auto_preamp"), constants.DEFAULT_AUTO_PREAMP),
            loudness=_parse_bool(data.get("loudness"), constants.DEFAULT_LOUDNESS),
            mono=_parse_bool(data.get("mono"), constants.DEFAULT_MONO),
            swap_channels=_parse_bool(data.get("swap_channels"), constants.DEFAULT_SWAP),
            balance=_parse_int(data.get("balance"), constants.DEFAULT_BALANCE),
            tone_bass=_parse_float(data.get("tone_bass"), constants.DEFAULT_TONE_BASS),
            tone_treble=_parse_float(data.get("tone_treble"), constants.DEFAULT_TONE_TREBLE),
            sub_bass=_parse_bool(data.get("sub_bass"), constants.DEFAULT_SUB_BASS),
            clarity=_parse_bool(data.get("clarity"), constants.DEFAULT_CLARITY),
            anti_sibilance=_parse_bool(data.get("anti_sibilance"), constants.DEFAULT_ANTI_SIBILANCE),
            anti_fatigue=_parse_bool(data.get("anti_fatigue"), constants.DEFAULT_ANTI_FATIGUE),
            ground_hum=_parse_bool(data.get("ground_hum"), constants.DEFAULT_GROUND_HUM),
            subsonic=_parse_bool(data.get("subsonic"), constants.DEFAULT_SUBSONIC),
            nvda_voice=_parse_bool(data.get("nvda_voice"), constants.DEFAULT_NVDA_VOICE),
            surround_3d=_parse_bool(data.get("surround_3d"), constants.DEFAULT_SURROUND_3D),
            radar_mode=_parse_bool(data.get("radar_mode"), constants.DEFAULT_RADAR_MODE),
            stereo_width=_parse_int(data.get("stereo_width"), constants.DEFAULT_STEREO_WIDTH),
            profile_index=_parse_int(data.get("profile_index"), 0),
            gains=_parse_gains(data.get("gains")),
        )
    except Exception as e:
        log.error(f"AudioEqualizer: Fallo inesperado al instanciar perfil: {e}", exc_info=True)
        return get_default_profile()


def save_profile(profile: EqualizerProfile) -> None:
    """Guarda permanentemente los parámetros de un perfil en nvda.ini y en el estado atómico de respaldo.

    Garantiza que la configuración sobreviva a reinicios de NVDA, reinicios de equipo y cambios de perfil.
    """
    # 1. Guardar en config.conf de NVDA y forzar escritura a nvda.ini
    try:
        if config and hasattr(config, "conf"):
            if "audioEqualizer" not in config.conf:
                config.conf["audioEqualizer"] = {}
            c = config.conf["audioEqualizer"]
            c["enabled"] = bool(profile.enabled)
            c["preamp"] = float(profile.preamp)
            c["auto_preamp"] = bool(profile.auto_preamp)
            c["loudness"] = bool(profile.loudness)
            c["mono"] = bool(profile.mono)
            c["swap_channels"] = bool(profile.swap_channels)
            c["balance"] = int(profile.balance)
            c["tone_bass"] = float(profile.tone_bass)
            c["tone_treble"] = float(profile.tone_treble)
            c["sub_bass"] = bool(profile.sub_bass)
            c["clarity"] = bool(profile.clarity)
            c["anti_sibilance"] = bool(profile.anti_sibilance)
            c["anti_fatigue"] = bool(profile.anti_fatigue)
            c["ground_hum"] = bool(profile.ground_hum)
            c["subsonic"] = bool(profile.subsonic)
            c["nvda_voice"] = bool(profile.nvda_voice)
            c["surround_3d"] = bool(profile.surround_3d)
            c["radar_mode"] = bool(profile.radar_mode)
            c["stereo_width"] = int(profile.stereo_width)
            c["profile_index"] = int(profile.profile_index)
            c["gains"] = [float(g) for g in profile.gains]
            
            if hasattr(config.conf, "save"):
                try:
                    config.conf.save()
                except Exception as e_save:
                    log.warning(f"AudioEqualizer: No se pudo guardar config.conf inmediatamente: {e_save}")
    except Exception as e:
        log.error(f"AudioEqualizer: Error guardando configuración nativa: {e}", exc_info=True)
        try:
            from . import logger
            logger.log_error(f"Error guardando configuración en config.conf: {e}", exc=e, component="Config")
        except Exception:
            pass

    # 2. Guardar en archivo de respaldo atómico JSON
    _save_state_file(profile)


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
                valid_profiles = []
                for p in data:
                    if isinstance(p, dict) and isinstance(p.get("name"), str) and p.get("name").strip():
                        valid_profiles.append(p)
                return valid_profiles
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
        "surround_3d": getattr(profile, "surround_3d", False),
        "radar_mode": getattr(profile, "radar_mode", False),
        "stereo_width": profile.stereo_width,
    }
    
    for i, p in enumerate(profiles_list):
        if isinstance(p, dict) and p.get("name") == name:
            profiles_list[i] = prof_dict
            break
    else:
        profiles_list.append(prof_dict)
        
    tmp_file = USER_PROFILES_FILE + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(profiles_list, f, indent=2, ensure_ascii=False)
        os.replace(tmp_file, USER_PROFILES_FILE)
        return True
    except Exception as e:
        log.error(f"AudioEqualizer: Error guardando perfil de usuario '{name}': {e}", exc_info=True)
        try:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
        except OSError:
            pass
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
    new_list = [p for p in profiles_list if isinstance(p, dict) and p.get("name") != name]
    if len(new_list) == len(profiles_list):
        return False
    tmp_file = USER_PROFILES_FILE + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(new_list, f, indent=2, ensure_ascii=False)
        os.replace(tmp_file, USER_PROFILES_FILE)
        return True
    except Exception as e:
        log.error(f"AudioEqualizer: Error eliminando perfil de usuario '{name}': {e}", exc_info=True)
        try:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
        except OSError:
            pass
        try:
            from . import logger
            ctx = {"profile_name": name, "file_path": USER_PROFILES_FILE}
            logger.log_error(f"Error eliminando perfil de usuario '{name}': {e}", exc=e, component="Config", context=ctx)
        except Exception:
            pass
        return False



def get_factory_override_file() -> str:
    try:
        import globalVars
        if getattr(globalVars, "appArgs", None) and getattr(globalVars.appArgs, "configPath", None):
            return os.path.join(globalVars.appArgs.configPath, "audioEqualizer_factory_overrides.json")
    except Exception:
        pass
    return os.path.join(os.path.dirname(__file__), "audioEqualizer_factory_overrides.json")

def save_factory_override(index: int, profile_obj) -> None:
    path = get_factory_override_file()
    try:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        else:
            data = {}
        
        data[str(index)] = {
            "gains": list(profile_obj.gains),
            "tone_bass": float(profile_obj.tone_bass),
            "tone_treble": float(profile_obj.tone_treble),
            "sub_bass": bool(profile_obj.sub_bass),
            "clarity": bool(profile_obj.clarity),
            "anti_sibilance": bool(profile_obj.anti_sibilance),
            "anti_fatigue": bool(profile_obj.anti_fatigue),
            "ground_hum": bool(profile_obj.ground_hum),
            "subsonic": bool(profile_obj.subsonic),
            "nvda_voice": bool(profile_obj.nvda_voice),
            "surround_3d": bool(getattr(profile_obj, "surround_3d", False)),
            "radar_mode": bool(getattr(profile_obj, "radar_mode", False)),
            "loudness": bool(profile_obj.loudness),
            "stereo_width": int(profile_obj.stereo_width),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        # Update in memory immediately
        from . import profiles
        if 0 <= index < len(profiles.PREDEFINED_PROFILES):
            for k, v in data[str(index)].items():
                profiles.PREDEFINED_PROFILES[index][k] = v
    except Exception as e:
        from . import logger
        logger.log_error(f"Error saving factory override: {e}", exc=e)

def remove_factory_override(index: int) -> None:
    path = get_factory_override_file()
    try:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
            if str(index) in data:
                del data[str(index)]
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
        
        # Restore in memory
        from . import profiles
        import copy
        if hasattr(profiles, "ORIGINAL_PREDEFINED_PROFILES") and 0 <= index < len(profiles.ORIGINAL_PREDEFINED_PROFILES):
            profiles.PREDEFINED_PROFILES[index] = copy.deepcopy(profiles.ORIGINAL_PREDEFINED_PROFILES[index])
    except Exception as e:
        from . import logger
        logger.log_error(f"Error removing factory override: {e}", exc=e)

def apply_factory_overrides_to_profiles():
    path = get_factory_override_file()
    try:
        from . import profiles
        import copy
        if not hasattr(profiles, "ORIGINAL_PREDEFINED_PROFILES"):
            profiles.ORIGINAL_PREDEFINED_PROFILES = copy.deepcopy(profiles.PREDEFINED_PROFILES)
            
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
            for k, v in data.items():
                idx = int(k)
                if 0 <= idx < len(profiles.PREDEFINED_PROFILES):
                    for key, val in v.items():
                        profiles.PREDEFINED_PROFILES[idx][key] = val
    except Exception as e:
        from . import logger
        logger.log_error(f"Error applying factory overrides: {e}", exc=e)
