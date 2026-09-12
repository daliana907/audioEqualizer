# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Controlador principal del ecualizador de audio para NVDA.

Actúa como el cerebro coordinador entre la interfaz gráfica accesible (wxPython), los atajos
de teclado de NVDA y el motor acústico de audio en segundo plano (Equalizer APO). Se encarga
de la sincronización en tiempo real, el cálculo matemático del anticlíping automático,
el cambio ordenado de perfiles, los controles de tono y la persistencia de ajustes.
"""

import os
try:
    from logHandler import log
except ImportError:
    import logging
    log = logging.getLogger("audioEqualizer")

import ui
import wx
import gui as nvda_gui

from . import config
from . import constants
from .backend import AudioBackend
from .dialog import EqualizerDialog


class EqualizerController:
    """Gestiona el estado y la lógica de negocio del ecualizador.

    Mantiene en memoria el perfil actualmente activo, coordina las llamadas al backend
    de audio para escribir en los archivos de Equalizer APO y notifica a NVDA y al usuario
    de cualquier cambio de estado.
    """

    def __init__(self, backend: AudioBackend):
        """Inicializa el controlador principal del ecualizador.

        Carga el último perfil guardado por el usuario en la configuración de NVDA
        y sincroniza de inmediato los filtros con el motor de audio del sistema
        para que entren en vigor desde el arranque sin necesidad de abrir la ventana.
        """
        log.debug("AudioEqualizer: Inicializando controlador principal.")
        self._backend = backend
        self._current_profile = config.load_profile()
        self._dialog_instance = None
        # Sincronizamos en silencio al arrancar para no saturar con mensajes de voz
        self._sync_backend(self._current_profile, notify_user=False)

    def _sync_backend(self, profile: config.EqualizerProfile, notify_user: bool = True) -> bool:
        """Envía los parámetros acústicos al motor de audio (Equalizer APO).

        Calcula la ganancia segura contra saturación digital (anticlíping).
        Si la opción de preamplificación automática (auto_preamp) está activada,
        busca el realce más alto de todo el procesamiento: compara las 31 bandas ISO,
        los controles rápidos de graves y agudos, y los filtros acústicos activos
        (subgraves con +6.0 dB, claridad con +5.5 dB, voz de NVDA con +4.5 dB o
        compensación isofónica con +4.5 dB). Al tomar ese pico máximo y aplicar exactamente
        ese valor en negativo (-peak_gain), garantiza que la señal final nunca supere 0 dBFS,
        eliminando la distorsión armónica digital y protegiendo los auriculares y oídos.

        profile: Perfil con todas las ganancias, tonos y opciones acústicas.
        notify_user: Si es True, anuncia errores mediante la voz de NVDA.
        Devuelve True si la sincronización fue exitosa, False en caso contrario.
        """
        if not self._backend.is_available():
            log.warning("AudioEqualizer: Motor de audio no disponible.")
            if notify_user:
                def _prompt_install():
                    from . import downloader
                    downloader.start_apo_download_flow()
                wx.CallAfter(_prompt_install)
            return False

        try:
            log.debug(f"AudioEqualizer: Sincronizando backend (enabled={profile.enabled}).")
            effective_preamp = profile.preamp
            if profile.auto_preamp:
                # Recolectamos todas las ganancias positivas para prevenir distorsión digital
                boosts = [0.0] + profile.gains + [max(0.0, profile.tone_bass), max(0.0, profile.tone_treble)]
                if profile.sub_bass:
                    boosts.append(6.0)
                if profile.clarity:
                    boosts.append(5.5)
                if profile.nvda_voice:
                    boosts.append(4.5)
                if profile.loudness:
                    boosts.append(4.5)
                peak_gain = max(boosts)
                # La preamplificación se establece en el negativo del pico más alto
                effective_preamp = -peak_gain
                
            self._backend.update(
                enabled=profile.enabled,
                gains=profile.gains,
                preamp=effective_preamp,
                auto_preamp=profile.auto_preamp,
                loudness=profile.loudness,
                mono=profile.mono,
                swap_channels=profile.swap_channels,
                balance=profile.balance,
                tone_bass=profile.tone_bass,
                tone_treble=profile.tone_treble,
                sub_bass=profile.sub_bass,
                anti_box=profile.anti_box,
                clarity=profile.clarity,
                anti_sibilance=profile.anti_sibilance,
                anti_fatigue=profile.anti_fatigue,
                ground_hum=profile.ground_hum,
                subsonic=profile.subsonic,
                nvda_voice=profile.nvda_voice,
                stereo_width=profile.stereo_width,
            )
            return True
        except ValueError as ve:
            log.error(f"AudioEqualizer: Error de validación: {ve}", exc_info=True)
            try:
                from . import logger
                ctx = {"profile_index": profile.profile_index, "preamp": profile.preamp, "bands": len(profile.gains)}
                logger.log_error(f"Error de validación de parámetros: {ve}", exc=ve, component="EqualizerController", context=ctx)
            except Exception:
                pass
            if notify_user:
                ui.message(f"Error en parámetros del ecualizador: {ve}")
            return False
        except RuntimeError as re:
            log.error(f"AudioEqualizer: Fallo en el motor: {re}", exc_info=True)
            try:
                from . import logger
                ctx = {"profile_index": profile.profile_index, "enabled": profile.enabled}
                logger.log_error(f"Fallo en el motor de audio Equalizer APO: {re}", exc=re, component="EqualizerController", context=ctx)
            except Exception:
                pass
            if notify_user:
                ui.message(f"Fallo al aplicar ecualización en el sistema: {re}")
            return False
        except Exception as e:
            log.error(f"AudioEqualizer: Error inesperado en el backend: {e}", exc_info=True)
            try:
                from . import logger
                ctx = {"profile_index": profile.profile_index, "error_type": type(e).__name__}
                logger.log_error(f"Error inesperado en el backend de ecualización: {e}", exc=e, component="EqualizerController", context=ctx)
            except Exception:
                pass
            if notify_user:
                ui.message(f"Error inesperado en el ecualizador: {e}")
            return False

    def toggle_equalizer(self) -> None:
        """Activa o desactiva la ecualización global en el sistema mediante atajo o comando.

        Si el cambio tiene éxito en el archivo de Equalizer APO, guarda el nuevo estado
        en la configuración persistente de NVDA y lo anuncia por voz ('activado' o 'desactivado').
        Si ocurre algún problema al comunicarse con el motor, revierte el estado para no inducir a error.
        """
        new_state = not self._current_profile.enabled
        log.info(f"AudioEqualizer: Conmutando estado a {new_state}.")
        self._current_profile.enabled = new_state
        
        success = self._sync_backend(self._current_profile, notify_user=True)
        if success:
            config.save_profile(self._current_profile)
            estado = "activado" if new_state else "desactivado"
            ui.message(f"Ecualizador {estado}")
        else:
            self._current_profile.enabled = not new_state

    def _apply_preset_to_profile(self, target_profile, preset_data):
        """Copia todos los valores acústicos de una plantilla de preajuste sobre un perfil destino.

        Actualiza las 31 ganancias ISO, los controles rápidos de graves y agudos, y cada
        uno de los conmutadores de filtros especializados (subgraves, claridad vocal,
        anti-sibilancia, ancho estéreo, etc.).
        """
        target_profile.gains = list(preset_data["gains"])
        if "preamp" in preset_data:
            target_profile.preamp = float(preset_data["preamp"])
        target_profile.tone_bass = float(preset_data.get("tone_bass", 0.0))
        target_profile.tone_treble = float(preset_data.get("tone_treble", 0.0))
        target_profile.sub_bass = bool(preset_data.get("sub_bass", False))
        target_profile.anti_box = bool(preset_data.get("anti_box", False))
        target_profile.clarity = bool(preset_data.get("clarity", False))
        target_profile.anti_sibilance = bool(preset_data.get("anti_sibilance", False))
        target_profile.anti_fatigue = bool(preset_data.get("anti_fatigue", False))
        target_profile.ground_hum = bool(preset_data.get("ground_hum", False))
        target_profile.subsonic = bool(preset_data.get("subsonic", False))
        target_profile.nvda_voice = bool(preset_data.get("nvda_voice", False))
        target_profile.loudness = bool(preset_data.get("loudness", False))
        target_profile.stereo_width = int(preset_data.get("stereo_width", 100))

    def _get_all_available_profiles(self):
        """Combina la lista de perfiles predefinidos de fábrica con los perfiles creados por el usuario.

        Lee el archivo JSON de perfiles personalizados del usuario en la carpeta de NVDA
        y los concatena al final de la lista de fábrica para que puedan recorrerse cíclicamente.
        """
        from . import profiles
        all_profs = list(profiles.PREDEFINED_PROFILES)
        user_profs = config.load_user_profiles()
        all_profs.extend(user_profs)
        return all_profs

    def _cycle_profile(self, delta: int) -> None:
        """Cambia al perfil de ecualización siguiente (+1) o anterior (-1) de forma circular.

        Aplica inmediatamente los filtros en Equalizer APO, guarda el perfil en la
        configuración de NVDA para la próxima sesión y anuncia el nombre del nuevo
        perfil mediante el sintetizador de voz. Si la ventana de configuración está
        abierta, refresca sus controles para reflejar el cambio.
        """
        all_profs = self._get_all_available_profiles()
        num_profiles = len(all_profs)
        if num_profiles == 0:
            return
        new_idx = (self._current_profile.profile_index + delta) % num_profiles
        self._current_profile.profile_index = new_idx
        prof = all_profs[new_idx]
        self._apply_preset_to_profile(self._current_profile, prof)
        success = self._sync_backend(self._current_profile, notify_user=False)
        if success:
            config.save_profile(self._current_profile)
            if self._dialog_instance:
                try:
                    self._dialog_instance._refresh_profiles_list()
                    self._dialog_instance._profile_choice.SetSelection(new_idx)
                    self._dialog_instance._apply_profile_to_ui(new_idx)
                except Exception as ex:
                    log.error(f"AudioEqualizer: Error actualizando UI tras cambiar de perfil: {ex}", exc_info=True)
            ui.message(f"Perfil: {prof['name']}")

    def next_profile(self) -> None:
        """Avanza al siguiente perfil de ecualización disponible."""
        self._cycle_profile(1)

    def previous_profile(self) -> None:
        """Retrocede al perfil de ecualización anterior en la lista."""
        self._cycle_profile(-1)

    def show_gui(self) -> None:
        """Abre la ventana accesible de configuración del ecualizador.

        Si la ventana ya se encontraba abierta en segundo plano, la trae al frente
        y le devuelve el foco para evitar abrir duplicados innecesarios.
        Si Equalizer APO no está instalado en el sistema, inicia el diálogo guiado
        de descarga para que el usuario pueda instalarlo fácilmente.
        """
        if not self._backend.is_available():
            self._sync_backend(self._current_profile, notify_user=True)
            return
            
        if self._dialog_instance:
            self._dialog_instance.Raise()
            self._dialog_instance.SetFocus()
            return

        def _run_gui():
            try:
                log.debug("AudioEqualizer: Mostrando interfaz gráfica.")
                self._dialog_instance = EqualizerDialog(
                    nvda_gui.mainFrame, 
                    self, 
                    self._current_profile.clone()
                )
                self._dialog_instance.Show()
            except Exception as e:
                log.error(f"AudioEqualizer: Error al abrir GUI: {e}", exc_info=True)
                try:
                    from . import logger
                    logger.log_error(f"Error al abrir interfaz gráfica: {e}", exc=e, component="EqualizerGUI")
                except Exception:
                    pass
                ui.message(f"Error al abrir la configuración del ecualizador: {e}")

        wx.CallAfter(_run_gui)

    def apply_profile(self, profile: config.EqualizerProfile, save: bool = False) -> bool:
        """Aplica un perfil completo proveniente del diálogo o de una carga externa.

        Si save es True, los valores se guardan en el archivo de configuración de NVDA.
        """
        success = self._sync_backend(profile, notify_user=True)
        if success:
            self._current_profile = profile.clone()
            if save:
                config.save_profile(self._current_profile)
        return success

    def restore_persisted_state(self) -> None:
        """Restaura los valores acústicos guardados en el disco cuando se cancela el diálogo."""
        persisted = config.load_profile()
        self._sync_backend(persisted, notify_user=False)
        self._current_profile = persisted

    def speak_filter_status(self) -> None:
        """Anuncia por voz un resumen completo del estado acústico actual.

        Indica si está activado o desactivado, el nombre del perfil, el valor de preamplificación
        efectivo y la lista exacta de filtros activos (por ejemplo: graves, claridad vocal,
        ancho estéreo al 120%), evitando dudas sobre qué está procesando el sonido.
        """
        from . import logger, profiles
        all_profs = self._get_all_available_profiles()
        idx = self._current_profile.profile_index
        prof_name = ""
        if 0 <= idx < len(all_profs):
            prof_name = all_profs[idx].get("name", "")
        elif idx == len(profiles.PREDEFINED_PROFILES):
            prof_name = "Personalizado"
        msg = logger.get_voice_summary(self._current_profile, prof_name)
        ui.message(msg)

    def _adjust_tone(self, is_bass: bool, delta: float) -> None:
        """Ajusta de forma rápida los graves o los agudos en pasos de 1 dB.

        Modifica el filtro de estantería (low-shelf a 100 Hz o high-shelf a 8000 Hz)
        respetando los límites de seguridad (-12 dB a +12 dB) y actualiza de inmediato
        la ventana gráfica si está en pantalla.
        """
        attr = "tone_bass" if is_bass else "tone_treble"
        label = "Graves" if is_bass else "Agudos"
        curr_val = getattr(self._current_profile, attr)
        new_val = max(constants.MIN_TONE, min(constants.MAX_TONE, round(curr_val + delta, 1)))
        setattr(self._current_profile, attr, new_val)
        self._sync_backend(self._current_profile, notify_user=False)
        config.save_profile(self._current_profile)
        if self._dialog_instance:
            try:
                slider = self._dialog_instance._tone_bass_slider if is_bass else self._dialog_instance._tone_treble_slider
                slider.SetValue(int(round(new_val)))
                self._dialog_instance._update_tone_names()
            except Exception as ex:
                log.error(f"AudioEqualizer: Error actualizando control de tono en GUI: {ex}", exc_info=True)
        ui.message(f"{label}: {new_val:+.1f} dB")

    def adjust_tone_bass(self, delta: float) -> None:
        """Aumenta o disminuye los graves rápidos en pasos de 1 dB."""
        self._adjust_tone(True, delta)

    def adjust_tone_treble(self, delta: float) -> None:
        """Aumenta o disminuye los agudos rápidos en pasos de 1 dB."""
        self._adjust_tone(False, delta)

    def test_channels(self) -> None:
        """Ejecuta una prueba auditiva estéreo para verificar la orientación de los auriculares.

        Reproduce una señal acústica en el canal izquierdo, luego en el canal derecho
        y finalmente en el centro estéreo, avisando previamente al usuario por síntesis de voz.
        """
        from . import channel_tester
        ui.message("Iniciando prueba: Canal izquierdo... Canal derecho... Centro estéreo.")
        channel_tester.play_channel_test()

    def adjust_preamp(self, delta: float) -> None:
        """Ajusta la preamplificación manual en pasos de 1 dB."""
        if self._current_profile.auto_preamp:
            ui.message("El preamplificador automático está activado. Desactívalo para ajustar manualmente.")
            return
        curr_val = self._current_profile.preamp
        new_val = max(constants.MIN_PREAMP, min(constants.MAX_PREAMP, round(curr_val + delta, 1)))
        self._current_profile.preamp = new_val
        self._sync_backend(self._current_profile, notify_user=False)
        config.save_profile(self._current_profile)
        if self._dialog_instance:
            try:
                self._dialog_instance._preamp_slider.SetValue(int(round(new_val)))
                self._dialog_instance._preamp_slider.SetName(f"Preamplificación, {int(round(new_val))} decibelios")
            except Exception as ex:
                log.error(f"AudioEqualizer: Error actualizando preamp en GUI: {ex}", exc_info=True)
        ui.message(f"Preamplificación: {new_val:+.1f} dB")

    def toggle_auto_preamp(self) -> None:
        """Activa o desactiva la preamplificación automática anticlíping."""
        new_state = not self._current_profile.auto_preamp
        self._current_profile.auto_preamp = new_state
        self._sync_backend(self._current_profile, notify_user=False)
        config.save_profile(self._current_profile)
        if self._dialog_instance:
            try:
                self._dialog_instance._auto_preamp_cb.SetValue(new_state)
                self._dialog_instance._preamp_slider.Enable(not new_state)
            except Exception as ex:
                log.error(f"AudioEqualizer: Error actualizando auto_preamp en GUI: {ex}", exc_info=True)
        estado = "activado" if new_state else "desactivado"
        ui.message(f"Preamplificador automático anticlíping {estado}")

    def adjust_stereo_width(self, delta: int) -> None:
        """Ajusta el ancho estéreo en pasos porcentuales."""
        curr_val = self._current_profile.stereo_width
        new_val = max(constants.MIN_STEREO_WIDTH, min(constants.MAX_STEREO_WIDTH, curr_val + delta))
        self._current_profile.stereo_width = new_val
        self._sync_backend(self._current_profile, notify_user=False)
        config.save_profile(self._current_profile)
        if self._dialog_instance:
            try:
                self._dialog_instance._width_slider.SetValue(new_val)
                self._dialog_instance._update_width_name()
            except Exception as ex:
                log.error(f"AudioEqualizer: Error actualizando ancho estéreo en GUI: {ex}", exc_info=True)
        ui.message(f"Ancho estéreo: {new_val} %")

    def adjust_balance(self, delta: int) -> None:
        """Ajusta el balance estéreo (L/R) en pasos porcentuales."""
        curr_val = self._current_profile.balance
        new_val = max(constants.MIN_BALANCE, min(constants.MAX_BALANCE, curr_val + delta))
        self._current_profile.balance = new_val
        self._sync_backend(self._current_profile, notify_user=False)
        config.save_profile(self._current_profile)
        if self._dialog_instance:
            try:
                self._dialog_instance._balance_slider.SetValue(new_val)
                self._dialog_instance._update_balance_name()
            except Exception as ex:
                log.error(f"AudioEqualizer: Error actualizando balance en GUI: {ex}", exc_info=True)
        if new_val == 0:
            ui.message("Balance estéreo: centrado")
        elif new_val < 0:
            ui.message(f"Balance estéreo: {abs(new_val)} % a la izquierda")
        else:
            ui.message(f"Balance estéreo: {new_val} % a la derecha")

    def center_balance(self) -> None:
        """Centra el balance estéreo."""
        self._current_profile.balance = 0
        self._sync_backend(self._current_profile, notify_user=False)
        config.save_profile(self._current_profile)
        if self._dialog_instance:
            try:
                self._dialog_instance._balance_slider.SetValue(0)
                self._dialog_instance._update_balance_name()
            except Exception as ex:
                log.error(f"AudioEqualizer: Error actualizando balance en GUI: {ex}", exc_info=True)
        ui.message("Balance estéreo: centrado")

    def _toggle_feature(self, attr_name: str, label_name: str) -> None:
        """Conmuta una opción booleana acústica, la guarda y la anuncia por voz."""
        curr = getattr(self._current_profile, attr_name, False)
        new_state = not curr
        setattr(self._current_profile, attr_name, new_state)
        self._sync_backend(self._current_profile, notify_user=False)
        config.save_profile(self._current_profile)
        if self._dialog_instance:
            try:
                cb_attr = f"_{attr_name}_cb"
                if hasattr(self._dialog_instance, cb_attr):
                    getattr(self._dialog_instance, cb_attr).SetValue(new_state)
            except Exception as ex:
                log.error(f"AudioEqualizer: Error actualizando {attr_name} en GUI: {ex}", exc_info=True)
        estado = "activado" if new_state else "desactivado"
        ui.message(f"{label_name} {estado}")

    def toggle_mono(self) -> None:
        self._toggle_feature("mono", "Modo mono")

    def toggle_swap_channels(self) -> None:
        self._toggle_feature("swap_channels", "Inversión de canales")

    def toggle_loudness(self) -> None:
        self._toggle_feature("loudness", "Loudness isofónico")

    def toggle_nvda_voice(self) -> None:
        self._toggle_feature("nvda_voice", "Claridad para voz de NVDA")

    def toggle_clarity(self) -> None:
        self._toggle_feature("clarity", "Realce de claridad vocal")

    def toggle_anti_sibilance(self) -> None:
        self._toggle_feature("anti_sibilance", "Filtro anti-sibilancia")

    def toggle_anti_fatigue(self) -> None:
        self._toggle_feature("anti_fatigue", "Filtro anti-fatiga auditiva")

    def toggle_subsonic(self) -> None:
        self._toggle_feature("subsonic", "Filtro subsónico")

    def toggle_sub_bass(self) -> None:
        self._toggle_feature("sub_bass", "Extensión de subgraves")

    def toggle_anti_box(self) -> None:
        self._toggle_feature("anti_box", "Filtro anti-caja")

    def toggle_ground_hum(self) -> None:
        self._toggle_feature("ground_hum", "Filtro anti-zumbido eléctrico")

    def reset_to_flat(self) -> None:
        """Restablece la ecualización a una respuesta plana (0 dB)."""
        self._current_profile = config.get_default_profile()
        self._current_profile.enabled = True
        self._sync_backend(self._current_profile, notify_user=False)
        config.save_profile(self._current_profile)
        if self._dialog_instance:
            try:
                self._dialog_instance._profile_choice.SetSelection(profiles.CUSTOM_INDEX)
                self._dialog_instance._apply_profile_to_ui(profiles.CUSTOM_INDEX)
            except Exception as ex:
                log.error(f"AudioEqualizer: Error actualizando reset en GUI: {ex}", exc_info=True)
        ui.message("Ecualizador restablecido a respuesta plana (0 dB)")

    def terminate(self) -> None:
        """Libera los recursos del backend de audio al cerrar o reiniciar NVDA."""
        try:
            self._backend.close()
        except Exception as e:
            log.error(f"AudioEqualizer: Error cerrando backend: {e}", exc_info=True)
