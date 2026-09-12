# -*- coding: utf-8 -*-
"""
Interfaz gráfica de usuario completamente accesible para NVDA.

Construye una ventana con desplazamiento vertical con soporte para lectores de pantalla.
Cada deslizador actualiza dinámicamente su nombre accesible con el valor exacto en decibelios
y porcentajes para que el sintetizador de voz lo verbalice de inmediato al interactuar con el teclado.
Permite gestionar perfiles (guardar, eliminar y cargar), activar filtros acústicos biquad,
controlar el balance suave y el ancho estéreo Mid/Side, y escuchar los cambios en tiempo real.
"""

import wx
import ui
try:
    from logHandler import log
except ImportError:
    import logging
    log = logging.getLogger("audioEqualizer")

from . import constants
from . import config
from . import profiles
from . import logger


class EqualizerDialog(wx.Dialog):
    """Diálogo de configuración interactivo del ecualizador.

    Presenta en una estructura lógica y jerárquica todos los parámetros acústicos:
    desde la selección de perfiles y anticlíping hasta las 31 bandas ISO estándar.
    """

    def __init__(self, parent, controller, profile: config.EqualizerProfile):
        """Inicializa y monta la ventana accesible del ecualizador.

        Copia el perfil actual en memoria para permitir previsualizaciones y restaurar
        los valores previos si el usuario pulsa 'Cancelar'.
        """
        super().__init__(
            parent,
            title="Ecualizador de Audio (31 Bandas ISO)",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=(620, 800)
        )
        
        self._controller = controller
        self._profile = profile
        self._band_sliders = []
        
        self._build_ui()
        self.CenterOnScreen()

    def _build_ui(self):
        """Construye todos los grupos de controles de la ventana accesible de arriba hacia abajo.

        1. Selector y gestión de perfiles (guardar y borrar).
        2. Interruptor general de activación.
        3. Preamplificación manual y casilla de anticlíping automático.
        4. Opciones acústicas y espaciales (Loudness, notch anti-zumbido, mono, swap, balance y ancho).
        5. Mejoras acústicas especializadas para auriculares (claridad vocal, voz de NVDA, etc.).
        6. Deslizadores de las 31 bandas ISO estándar con nombres enriquecidos.
        7. Botones inferiores: Aplicar, Restablecer, Ver registro, Aceptar y Cancelar.
        """
        scroll_panel = wx.ScrolledWindow(self, style=wx.VSCROLL)
        scroll_panel.SetScrollRate(0, 20)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 1. Selector de Perfil
        profile_box = wx.StaticBox(scroll_panel, label="Perfil de ecualización")
        profile_box_sizer = wx.StaticBoxSizer(profile_box, wx.VERTICAL)

        p_row = wx.BoxSizer(wx.HORIZONTAL)
        profile_label = wx.StaticText(scroll_panel, label="Perfi&l:")
        self._profile_choice = wx.Choice(scroll_panel, choices=[])
        self._refresh_profiles_list()
        self._profile_choice.SetSelection(self._profile.profile_index)
        self._profile_choice.Bind(wx.EVT_CHOICE, self._on_profile_choice)
        p_row.Add(profile_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        p_row.Add(self._profile_choice, 1, wx.EXPAND)
        profile_box_sizer.Add(p_row, 0, wx.EXPAND | wx.ALL, 4)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self._save_profile_btn = wx.Button(scroll_panel, label="Guardar &perfil como...")
        self._save_profile_btn.Bind(wx.EVT_BUTTON, self._on_save_profile_as)
        btn_row.Add(self._save_profile_btn, 0, wx.RIGHT, 6)

        self._delete_profile_btn = wx.Button(scroll_panel, label="&Quitar perfil seleccionado")
        self._delete_profile_btn.Bind(wx.EVT_BUTTON, self._on_delete_profile)
        btn_row.Add(self._delete_profile_btn, 0, wx.RIGHT, 6)

        self._test_audio_btn = wx.Button(scroll_panel, label="Comprobar canales de audi&o")
        self._test_audio_btn.Bind(wx.EVT_BUTTON, self._on_test_audio)
        btn_row.Add(self._test_audio_btn, 0)
        profile_box_sizer.Add(btn_row, 0, wx.ALL, 4)

        main_sizer.Add(profile_box_sizer, 0, wx.EXPAND | wx.ALL, 8)

        # 2. Casilla Activar ecualizador
        self._enabled_cb = wx.CheckBox(scroll_panel, label="&Ecualizador activado")
        self._enabled_cb.SetValue(self._profile.enabled)
        self._enabled_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        main_sizer.Add(self._enabled_cb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # 3. Preamplificación
        preamp_box = wx.StaticBox(scroll_panel, label="Preamplificación y control de ganancia")
        preamp_sizer = wx.StaticBoxSizer(preamp_box, wx.VERTICAL)
        
        preamp_row = wx.BoxSizer(wx.HORIZONTAL)
        preamp_lbl = wx.StaticText(scroll_panel, label="&Preamplificación:", size=(120, -1))
        self._preamp_slider = wx.Slider(
            scroll_panel,
            value=int(self._profile.preamp),
            minValue=int(constants.MIN_PREAMP),
            maxValue=int(constants.MAX_PREAMP),
            style=wx.SL_HORIZONTAL
        )
        self._preamp_slider.SetName(f"Preamplificación, {int(self._profile.preamp)} decibelios")
        self._preamp_slider.Bind(wx.EVT_SLIDER, self._on_preamp_scroll)
        preamp_row.Add(preamp_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        preamp_row.Add(self._preamp_slider, 1, wx.EXPAND)
        preamp_sizer.Add(preamp_row, 0, wx.EXPAND | wx.ALL, 4)

        self._auto_preamp_cb = wx.CheckBox(scroll_panel, label="Preamp &automático (evita saturación y distorsión)")
        self._auto_preamp_cb.SetValue(self._profile.auto_preamp)
        self._auto_preamp_cb.Bind(wx.EVT_CHECKBOX, self._on_auto_preamp_check)
        self._preamp_slider.Enable(not self._profile.auto_preamp)
        preamp_sizer.Add(self._auto_preamp_cb, 0, wx.ALL, 4)
        
        main_sizer.Add(preamp_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # 4. Mejoras acústicas y espaciales seguras
        opt_box = wx.StaticBox(scroll_panel, label="Mejoras acústicas y espaciales")
        opt_sizer = wx.StaticBoxSizer(opt_box, wx.VERTICAL)

        self._loudness_cb = wx.CheckBox(scroll_panel, label="&Loudness isofónico (Compensación para bajo volumen Fletcher-Munson)")
        self._loudness_cb.SetValue(self._profile.loudness)
        self._loudness_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        opt_sizer.Add(self._loudness_cb, 0, wx.ALL, 4)

        self._ground_hum_cb = wx.CheckBox(scroll_panel, label="Filtro anti-&zumbido eléctrico (Notch 50 y 60 Hz, elimina ruidos de masa)")
        self._ground_hum_cb.SetValue(self._profile.ground_hum)
        self._ground_hum_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        opt_sizer.Add(self._ground_hum_cb, 0, wx.ALL, 4)


        self._mono_cb = wx.CheckBox(scroll_panel, label="Forzar audio &mono")
        self._mono_cb.SetValue(self._profile.mono)
        self._mono_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        opt_sizer.Add(self._mono_cb, 0, wx.ALL, 4)

        self._swap_cb = wx.CheckBox(scroll_panel, label="&Invertir canales estéreo (L/R)")
        self._swap_cb.SetValue(self._profile.swap_channels)
        self._swap_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        opt_sizer.Add(self._swap_cb, 0, wx.ALL, 4)

        # Deslizador de Balance Estéreo (-100 a +100)
        bal_row = wx.BoxSizer(wx.HORIZONTAL)
        bal_lbl = wx.StaticText(scroll_panel, label="&Balance estéreo (L/R):", size=(140, -1))
        self._balance_slider = wx.Slider(
            scroll_panel,
            value=self._profile.balance,
            minValue=constants.MIN_BALANCE,
            maxValue=constants.MAX_BALANCE,
            style=wx.SL_HORIZONTAL
        )
        self._update_balance_name()
        self._balance_slider.Bind(wx.EVT_SLIDER, self._on_balance_scroll)
        bal_row.Add(bal_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        bal_row.Add(self._balance_slider, 1, wx.EXPAND)
        opt_sizer.Add(bal_row, 0, wx.EXPAND | wx.ALL, 4)

        # Deslizador de Ancho Estéreo (0% a 200%)
        width_row = wx.BoxSizer(wx.HORIZONTAL)
        width_lbl = wx.StaticText(scroll_panel, label="Anc&ho estéreo (0%-200%):", size=(160, -1))
        self._width_slider = wx.Slider(
            scroll_panel,
            value=self._profile.stereo_width,
            minValue=constants.MIN_STEREO_WIDTH,
            maxValue=constants.MAX_STEREO_WIDTH,
            style=wx.SL_HORIZONTAL
        )
        self._update_width_name()
        self._width_slider.Bind(wx.EVT_SLIDER, self._on_width_scroll)
        width_row.Add(width_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        width_row.Add(self._width_slider, 1, wx.EXPAND)
        opt_sizer.Add(width_row, 0, wx.EXPAND | wx.ALL, 4)

        # Controles rápidos de tono (Graves y Agudos)
        tone_box = wx.StaticBox(scroll_panel, label="Controles rápidos de tono general")
        tone_sizer = wx.StaticBoxSizer(tone_box, wx.VERTICAL)

        bass_row = wx.BoxSizer(wx.HORIZONTAL)
        bass_lbl = wx.StaticText(scroll_panel, label="&Graves rápidos (100 Hz):", size=(150, -1))
        self._tone_bass_slider = wx.Slider(
            scroll_panel,
            value=int(round(self._profile.tone_bass)),
            minValue=int(constants.MIN_TONE),
            maxValue=int(constants.MAX_TONE),
            style=wx.SL_HORIZONTAL
        )
        bass_row.Add(bass_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        bass_row.Add(self._tone_bass_slider, 1, wx.EXPAND)
        tone_sizer.Add(bass_row, 0, wx.EXPAND | wx.ALL, 4)

        treble_row = wx.BoxSizer(wx.HORIZONTAL)
        treble_lbl = wx.StaticText(scroll_panel, label="A&gudos rápidos (8 kHz):", size=(150, -1))
        self._tone_treble_slider = wx.Slider(
            scroll_panel,
            value=int(round(self._profile.tone_treble)),
            minValue=int(constants.MIN_TONE),
            maxValue=int(constants.MAX_TONE),
            style=wx.SL_HORIZONTAL
        )
        treble_row.Add(treble_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        treble_row.Add(self._tone_treble_slider, 1, wx.EXPAND)
        tone_sizer.Add(treble_row, 0, wx.EXPAND | wx.ALL, 4)

        self._update_tone_names()
        self._tone_bass_slider.Bind(wx.EVT_SLIDER, self._on_tone_scroll)
        self._tone_treble_slider.Bind(wx.EVT_SLIDER, self._on_tone_scroll)

        opt_sizer.Add(tone_sizer, 0, wx.EXPAND | wx.ALL, 4)
        main_sizer.Add(opt_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # 5. Mejoras acústicas para auriculares profesionales
        hp_box = wx.StaticBox(scroll_panel, label="Mejoras para auriculares profesionales")
        hp_sizer = wx.StaticBoxSizer(hp_box, wx.VERTICAL)

        self._subsonic_cb = wx.CheckBox(scroll_panel, label="Filtro subsó&nico infrasónico (Corta < 20 Hz, libera potencia en graves)")
        self._subsonic_cb.SetValue(self._profile.subsonic)
        self._subsonic_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        hp_sizer.Add(self._subsonic_cb, 0, wx.ALL, 4)

        self._nvda_voice_cb = wx.CheckBox(scroll_panel, label="Claridad para sintetizador de &voz (Optimiza NVDA, menos fatiga)")
        self._nvda_voice_cb.SetValue(self._profile.nvda_voice)
        self._nvda_voice_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        hp_sizer.Add(self._nvda_voice_cb, 0, wx.ALL, 4)

        self._sub_bass_cb = wx.CheckBox(scroll_panel, label="E&xtensión de subgraves profundos (+6 dB en 70 Hz para drivers 50-53 mm)")
        self._sub_bass_cb.SetValue(self._profile.sub_bass)
        self._sub_bass_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        hp_sizer.Add(self._sub_bass_cb, 0, wx.ALL, 4)

        self._anti_box_cb = wx.CheckBox(scroll_panel, label="Filtro anti-encajonamien&to (-4.5 dB en 400 Hz, elimina sonido hueco/caja)")
        self._anti_box_cb.SetValue(self._profile.anti_box)
        self._anti_box_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        hp_sizer.Add(self._anti_box_cb, 0, wx.ALL, 4)

        self._clarity_cb = wx.CheckBox(scroll_panel, label="Realce de clari&dad y presencia (+5.5 dB en 5.5 kHz, voz y brillo nítidos)")
        self._clarity_cb.SetValue(self._profile.clarity)
        self._clarity_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        hp_sizer.Add(self._clarity_cb, 0, wx.ALL, 4)

        self._anti_sibilance_cb = wx.CheckBox(scroll_panel, label="Filtro anti-&sibilancia (-5 dB en 7.5 kHz, suaviza seseo y estridencias)")
        self._anti_sibilance_cb.SetValue(self._profile.anti_sibilance)
        self._anti_sibilance_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        hp_sizer.Add(self._anti_sibilance_cb, 0, wx.ALL, 4)

        self._anti_fatigue_cb = wx.CheckBox(scroll_panel, label="Filtro anti-&fatiga auditiva (-4.5 dB en 14 kHz, sonido cálido relajante)")
        self._anti_fatigue_cb.SetValue(self._profile.anti_fatigue)
        self._anti_fatigue_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        hp_sizer.Add(self._anti_fatigue_cb, 0, wx.ALL, 4)


        main_sizer.Add(hp_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # 6. Bandas de Frecuencia (31 bandas ISO)
        bands_box = wx.StaticBox(scroll_panel, label="Bandas de frecuencia (31 bandas ISO)")
        bands_sizer = wx.StaticBoxSizer(bands_box, wx.VERTICAL)

        for i, freq in enumerate(constants.EQ_BANDS):
            row_sizer = wx.BoxSizer(wx.HORIZONTAL)
            gain = self._profile.gains[i] if i < len(self._profile.gains) else 0.0
            
            freq_str = f"{freq} Hz" if freq < 1000 else f"{freq/1000:g} kHz"
            label = wx.StaticText(scroll_panel, label=f"{freq_str}:", size=(75, -1))
            row_sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
            
            slider = wx.Slider(
                scroll_panel,
                value=int(round(gain)),
                minValue=int(constants.MIN_GAIN),
                maxValue=int(constants.MAX_GAIN),
                style=wx.SL_HORIZONTAL
            )
            slider.SetName(f"{freq_str}, ganancia, {int(round(gain))} decibelios")
            slider.Bind(wx.EVT_SLIDER, lambda evt, s=slider, f_txt=freq_str: self._on_band_slider_scroll(evt, s, f_txt))
            
            row_sizer.Add(slider, 1, wx.EXPAND | wx.RIGHT, 8)
            bands_sizer.Add(row_sizer, 0, wx.EXPAND | wx.ALL, 2)
            self._band_sliders.append(slider)

        main_sizer.Add(bands_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        scroll_panel.SetSizer(main_sizer)

        dlg_sizer = wx.BoxSizer(wx.VERTICAL)
        dlg_sizer.Add(scroll_panel, 1, wx.EXPAND)

        # 6. Botones de acción inferiores
        btn_panel = wx.Panel(self)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        apply_btn = wx.Button(btn_panel, label="A&plicar")
        apply_btn.Bind(wx.EVT_BUTTON, self._on_apply)
        btn_sizer.Add(apply_btn, 0, wx.RIGHT, 5)

        reset_btn = wx.Button(btn_panel, label="&Restablecer")
        reset_btn.Bind(wx.EVT_BUTTON, self._on_reset)
        btn_sizer.Add(reset_btn, 0, wx.RIGHT, 5)

        log_btn = wx.Button(btn_panel, label="Ver &registro (Log)")
        log_btn.Bind(wx.EVT_BUTTON, self._on_view_log)
        btn_sizer.Add(log_btn, 0, wx.RIGHT, 5)

        ok_btn = wx.Button(btn_panel, id=wx.ID_OK, label="&Aceptar")
        ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)
        btn_sizer.Add(ok_btn, 0, wx.RIGHT, 5)

        cancel_btn = wx.Button(btn_panel, id=wx.ID_CANCEL, label="&Cancelar")
        cancel_btn.Bind(wx.EVT_BUTTON, self._on_cancel)
        btn_sizer.Add(cancel_btn, 0)

        btn_panel.SetSizer(btn_sizer)
        dlg_sizer.Add(btn_panel, 0, wx.ALIGN_RIGHT | wx.ALL, 8)

        self.SetSizer(dlg_sizer)
        self.SetAffirmativeId(wx.ID_OK)
        self.SetEscapeId(wx.ID_CANCEL)
        self.Bind(wx.EVT_CLOSE, self._on_cancel)

    def _update_balance_name(self):
        val = self._balance_slider.GetValue()
        if val == 0:
            txt = "centrado"
        elif val < 0:
            txt = f"{abs(val)} por ciento a la izquierda"
        else:
            txt = f"{val} por ciento a la derecha"
        self._balance_slider.SetName(f"Balance estéreo, {txt}")

    def _on_balance_scroll(self, event):
        self._update_balance_name()
        self._on_apply(event)
        event.Skip()

    def _update_width_name(self):
        val = self._width_slider.GetValue()
        if val == 0:
            txt = "0 por ciento, modo mono"
        elif val == 100:
            txt = "100 por ciento, estéreo estándar"
        elif val > 100:
            txt = f"{val} por ciento, expansión de estudio"
        else:
            txt = f"{val} por ciento, estéreo estrecho"
        self._width_slider.SetName(f"Ancho estéreo, {txt}")

    def _on_width_scroll(self, event):
        self._update_width_name()
        self._on_apply(event)
        event.Skip()

    def _update_tone_names(self):
        b_val = self._tone_bass_slider.GetValue()
        self._tone_bass_slider.SetName(f"Graves rápidos, {b_val} decibelios")
        t_val = self._tone_treble_slider.GetValue()
        self._tone_treble_slider.SetName(f"Agudos rápidos, {t_val} decibelios")

    def _on_tone_scroll(self, event):
        self._update_tone_names()
        self._on_apply(event)
        event.Skip()

    def _refresh_profiles_list(self):
        user_profs = config.load_user_profiles()
        choice_items = list(profiles.PROFILE_NAMES) + ["Personalizado"]
        for up in user_profs:
            choice_items.append(f"Usuario: {up['name']}")
        
        current_sel = self._profile_choice.GetSelection() if hasattr(self, "_profile_choice") and self._profile_choice else 0
        self._profile_choice.Clear()
        for item in choice_items:
            self._profile_choice.Append(item)
        if 0 <= current_sel < len(choice_items):
            self._profile_choice.SetSelection(current_sel)
        else:
            self._profile_choice.SetSelection(0)
        self._update_profile_buttons_state()

    def _update_profile_buttons_state(self):
        if not hasattr(self, "_delete_profile_btn") or not self._delete_profile_btn:
            return
        sel = self._profile_choice.GetSelection()
        is_user_profile = sel > profiles.CUSTOM_INDEX
        self._delete_profile_btn.Enable(is_user_profile)

    def _on_save_profile_as(self, event):
        try:
            dlg = wx.TextEntryDialog(
                self,
                "Introduce un nombre para el nuevo perfil personalizado:",
                "Guardar perfil personalizado",
                ""
            )
            if dlg.ShowModal() == wx.ID_OK:
                name = dlg.GetValue().strip()
                if not name:
                    ui.message("El nombre del perfil no puede estar vacío.")
                    dlg.Destroy()
                    return
                self._sync_profile_from_ui()
                success = config.save_user_profile(name, self._profile)
                if success:
                    self._refresh_profiles_list()
                    user_profs = config.load_user_profiles()
                    new_idx = profiles.CUSTOM_INDEX + len(user_profs)
                    self._profile_choice.SetSelection(new_idx)
                    self._profile.profile_index = new_idx
                    self._update_profile_buttons_state()
                    ui.message(f"Perfil '{name}' guardado correctamente.")
                else:
                    ui.message("Error al guardar el perfil personalizado.")
            dlg.Destroy()
        except Exception as e:
            log.error(f"AudioEqualizer: Error al guardar perfil personalizado: {e}", exc_info=True)
            logger.log_error(f"Error al guardar perfil personalizado: {e}", exc=e, component="EqualizerDialog")
            ui.message(f"Error al guardar perfil: {e}")

    def _on_delete_profile(self, event):
        try:
            sel = self._profile_choice.GetSelection()
            if sel <= profiles.CUSTOM_INDEX:
                return
            user_profs = config.load_user_profiles()
            user_idx = sel - profiles.CUSTOM_INDEX - 1
            if 0 <= user_idx < len(user_profs):
                prof_name = user_profs[user_idx]["name"]
                dlg = wx.MessageDialog(
                    self,
                    f"¿Estás seguro de que deseas eliminar el perfil '{prof_name}'?",
                    "Confirmar eliminación",
                    wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
                )
                if dlg.ShowModal() == wx.ID_YES:
                    config.delete_user_profile(prof_name)
                    self._refresh_profiles_list()
                    self._profile_choice.SetSelection(0)
                    self._apply_profile_to_ui(0)
                    self._on_apply(None)
                    ui.message(f"Perfil '{prof_name}' eliminado.")
                dlg.Destroy()
        except Exception as e:
            log.error(f"AudioEqualizer: Error al eliminar perfil personalizado: {e}", exc_info=True)
            logger.log_error(f"Error al eliminar perfil personalizado: {e}", exc=e, component="EqualizerDialog")
            ui.message(f"Error al eliminar perfil: {e}")

    def _on_test_audio(self, event):
        from . import channel_tester
        ui.message("Iniciando prueba: Canal izquierdo... Canal derecho... Centro estéreo.")
        channel_tester.play_channel_test()

    def _apply_profile_to_ui(self, prof_index):
        if prof_index < profiles.CUSTOM_INDEX:
            prof = profiles.PREDEFINED_PROFILES[prof_index]
        elif prof_index > profiles.CUSTOM_INDEX:
            user_profs = config.load_user_profiles()
            user_idx = prof_index - profiles.CUSTOM_INDEX - 1
            if 0 <= user_idx < len(user_profs):
                prof = user_profs[user_idx]
            else:
                self._update_profile_buttons_state()
                return
        else:
            self._update_profile_buttons_state()
            return

        gains = prof.get("gains", [])
        for i, slider in enumerate(self._band_sliders):
            if i < len(gains):
                slider.SetValue(int(round(gains[i])))
                freq = constants.EQ_BANDS[i]
                f_str = f"{freq} Hz" if freq < 1000 else f"{freq/1000:g} kHz"
                slider.SetName(f"{f_str}, ganancia, {int(round(gains[i]))} decibelios")

        if "preamp" in prof:
            self._preamp_slider.SetValue(int(round(prof["preamp"])))
            self._preamp_slider.SetName(f"Preamplificación, {int(round(prof['preamp']))} decibelios")

        # Controles de tono rápido del perfil
        self._tone_bass_slider.SetValue(int(round(prof.get("tone_bass", 0.0))))
        self._tone_treble_slider.SetValue(int(round(prof.get("tone_treble", 0.0))))
        self._update_tone_names()

        # Ancho estéreo óptimo del perfil
        self._width_slider.SetValue(int(prof.get("stereo_width", 100)))
        self._update_width_name()

        # Mejoras para auriculares profesionales
        self._sub_bass_cb.SetValue(bool(prof.get("sub_bass", False)))
        self._anti_box_cb.SetValue(bool(prof.get("anti_box", False)))
        self._clarity_cb.SetValue(bool(prof.get("clarity", False)))
        self._anti_sibilance_cb.SetValue(bool(prof.get("anti_sibilance", False)))
        self._anti_fatigue_cb.SetValue(bool(prof.get("anti_fatigue", False)))
        self._subsonic_cb.SetValue(bool(prof.get("subsonic", False)))
        self._nvda_voice_cb.SetValue(bool(prof.get("nvda_voice", False)))

        # Procesamiento espacial y acústico
        self._loudness_cb.SetValue(bool(prof.get("loudness", False)))
        self._ground_hum_cb.SetValue(bool(prof.get("ground_hum", False)))
        self._update_profile_buttons_state()

    def _on_profile_choice(self, event):
        idx = self._profile_choice.GetSelection()
        self._apply_profile_to_ui(idx)
        self._on_apply(event)
        self._update_profile_buttons_state()
        all_choices = self._profile_choice.GetStrings()
        if 0 <= idx < len(all_choices):
            ui.message(f"Perfil: {all_choices[idx]}")
        event.Skip()

    def _on_band_slider_scroll(self, event, slider, f_txt):
        val = slider.GetValue()
        slider.SetName(f"{f_txt}, ganancia, {val} decibelios")
        self._profile_choice.SetSelection(profiles.CUSTOM_INDEX)
        self._update_profile_buttons_state()
        self._on_apply(event)
        event.Skip()

    def _on_preamp_scroll(self, event):
        val = self._preamp_slider.GetValue()
        self._preamp_slider.SetName(f"Preamplificación, {val} decibelios")
        self._on_apply(event)
        event.Skip()

    def _on_auto_preamp_check(self, event):
        is_auto = self._auto_preamp_cb.GetValue()
        self._preamp_slider.Enable(not is_auto)
        self._on_apply(event)
        event.Skip()

    def _sync_profile_from_ui(self):
        self._profile.enabled = self._enabled_cb.GetValue()
        self._profile.preamp = float(self._preamp_slider.GetValue())
        self._profile.auto_preamp = self._auto_preamp_cb.GetValue()
        self._profile.loudness = self._loudness_cb.GetValue()
        self._profile.ground_hum = self._ground_hum_cb.GetValue()
        self._profile.mono = self._mono_cb.GetValue()
        self._profile.swap_channels = self._swap_cb.GetValue()
        self._profile.balance = self._balance_slider.GetValue()
        self._profile.tone_bass = float(self._tone_bass_slider.GetValue())
        self._profile.tone_treble = float(self._tone_treble_slider.GetValue())
        self._profile.sub_bass = self._sub_bass_cb.GetValue()
        self._profile.anti_box = self._anti_box_cb.GetValue()
        self._profile.clarity = self._clarity_cb.GetValue()
        self._profile.anti_sibilance = self._anti_sibilance_cb.GetValue()
        self._profile.anti_fatigue = self._anti_fatigue_cb.GetValue()
        self._profile.subsonic = self._subsonic_cb.GetValue()
        self._profile.nvda_voice = self._nvda_voice_cb.GetValue()
        self._profile.stereo_width = self._width_slider.GetValue()
        
        prof_idx = self._profile_choice.GetSelection()
        self._profile.profile_index = prof_idx
        if prof_idx < profiles.CUSTOM_INDEX:
            prof = profiles.PREDEFINED_PROFILES[prof_idx]
            self._profile.gains = list(prof["gains"])
        elif prof_idx > profiles.CUSTOM_INDEX:
            user_profs = config.load_user_profiles()
            user_idx = prof_idx - profiles.CUSTOM_INDEX - 1
            if 0 <= user_idx < len(user_profs):
                self._profile.gains = list(user_profs[user_idx]["gains"])
            else:
                self._profile.gains = [float(s.GetValue()) for s in self._band_sliders]
        else:
            gains = [float(s.GetValue()) for s in self._band_sliders]
            self._profile.gains = gains

    def _sync_profile_from_ui(self):
        """Lee el estado de todos los controles visuales y actualiza el objeto perfil en memoria.

        Recopila el estado de las casillas de verificación, los deslizadores de balance y
        ancho estéreo, los controles rápidos de graves/agudos y los deslizadores de las 31 bandas.
        """
        self._profile.enabled = self._enabled_cb.GetValue()
        self._profile.preamp = float(self._preamp_slider.GetValue())
        self._profile.auto_preamp = self._auto_preamp_cb.GetValue()
        self._profile.loudness = self._loudness_cb.GetValue()
        self._profile.ground_hum = self._ground_hum_cb.GetValue()
        self._profile.mono = self._mono_cb.GetValue()
        self._profile.swap_channels = self._swap_cb.GetValue()
        self._profile.balance = self._balance_slider.GetValue()
        self._profile.tone_bass = float(self._tone_bass_slider.GetValue())
        self._profile.tone_treble = float(self._tone_treble_slider.GetValue())
        self._profile.sub_bass = self._sub_bass_cb.GetValue()
        self._profile.anti_box = self._anti_box_cb.GetValue()
        self._profile.clarity = self._clarity_cb.GetValue()
        self._profile.anti_sibilance = self._anti_sibilance_cb.GetValue()
        self._profile.anti_fatigue = self._anti_fatigue_cb.GetValue()
        self._profile.subsonic = self._subsonic_cb.GetValue()
        self._profile.nvda_voice = self._nvda_voice_cb.GetValue()
        self._profile.stereo_width = self._width_slider.GetValue()
        
        prof_idx = self._profile_choice.GetSelection()
        self._profile.profile_index = prof_idx
        if prof_idx < profiles.CUSTOM_INDEX:
            prof = profiles.PREDEFINED_PROFILES[prof_idx]
            self._profile.gains = list(prof["gains"])
        elif prof_idx > profiles.CUSTOM_INDEX:
            user_profs = config.load_user_profiles()
            user_idx = prof_idx - profiles.CUSTOM_INDEX - 1
            if 0 <= user_idx < len(user_profs):
                self._profile.gains = list(user_profs[user_idx]["gains"])
            else:
                self._profile.gains = [float(s.GetValue()) for s in self._band_sliders]
        else:
            gains = [float(s.GetValue()) for s in self._band_sliders]
            self._profile.gains = gains

    def _on_apply(self, event=None):
        """Aplica los cambios en tiempo real en Equalizer APO sin cerrar la ventana.

        Permite escuchar inmediatamente el resultado acústico mientras se ajustan los deslizadores.
        """
        try:
            self._sync_profile_from_ui()
            self._controller.apply_profile(self._profile, save=False)
        except Exception as e:
            log.error(f"AudioEqualizer: Error aplicando cambios desde la interfaz: {e}", exc_info=True)
            logger.log_error(f"Error aplicando cambios en GUI: {e}", exc=e, component="EqualizerDialog")
            ui.message(f"Error al aplicar cambios: {e}")
        if event and hasattr(event, "Skip"):
            event.Skip()

    def _on_ok(self, event):
        """Guarda permanentemente la configuración en NVDA y cierra la ventana."""
        try:
            self._sync_profile_from_ui()
            self._controller.apply_profile(self._profile, save=True)
            self._cleanup()
        except Exception as e:
            log.error(f"AudioEqualizer: Error al guardar cambios y cerrar: {e}", exc_info=True)
            logger.log_error(f"Error al guardar cambios en GUI (Aceptar): {e}", exc=e, component="EqualizerDialog")
            ui.message(f"Error al guardar cambios: {e}")

    def _on_cancel(self, event):
        """Descarta las modificaciones temporales, restaura el estado previo y cierra la ventana."""
        try:
            self._controller.restore_persisted_state()
            self._cleanup()
        except Exception as e:
            log.error(f"AudioEqualizer: Error al restaurar estado en Cancelar: {e}", exc_info=True)
            logger.log_error(f"Error en Cancelar de GUI: {e}", exc=e, component="EqualizerDialog")
            self._cleanup()

    def _on_reset(self, event):
        """Restablece los controles a sus valores iniciales.

        Si se trata de un perfil predefinido de fábrica, vuelve a los valores de diseño del perfil.
        Si se trata del perfil personalizado, pone todas las 31 bandas en 0.0 dB (plano).
        """
        try:
            prof_idx = self._profile_choice.GetSelection()
            self._loudness_cb.SetValue(False)
            self._mono_cb.SetValue(False)
            self._swap_cb.SetValue(False)
            self._balance_slider.SetValue(0)
            self._update_balance_name()
            self._width_slider.SetValue(100)
            self._update_width_name()
            self._tone_bass_slider.SetValue(0)
            self._tone_treble_slider.SetValue(0)
            self._update_tone_names()
            self._sub_bass_cb.SetValue(False)
            self._anti_box_cb.SetValue(False)
            self._clarity_cb.SetValue(False)
            self._anti_sibilance_cb.SetValue(False)
            self._anti_fatigue_cb.SetValue(False)
            self._ground_hum_cb.SetValue(False)
            self._subsonic_cb.SetValue(False)
            self._nvda_voice_cb.SetValue(False)

            if prof_idx < profiles.CUSTOM_INDEX:
                prof = profiles.PREDEFINED_PROFILES[prof_idx]
                self._apply_profile_to_ui(prof_idx)
                self._preamp_slider.SetValue(0)
                self._preamp_slider.SetName("Preamplificación, 0 decibelios")
                self._auto_preamp_cb.SetValue(False)
                self._preamp_slider.Enable(True)
                self._on_apply(event)
                ui.message(f"Perfil '{prof['name']}' restablecido a sus valores originales")
            else:
                for i, s in enumerate(self._band_sliders):
                    s.SetValue(0)
                    freq = constants.EQ_BANDS[i]
                    f_str = f"{freq} Hz" if freq < 1000 else f"{freq/1000:g} kHz"
                    s.SetName(f"{f_str}, ganancia, 0 decibelios")
                self._preamp_slider.SetValue(0)
                self._preamp_slider.SetName("Preamplificación, 0 decibelios")
                self._auto_preamp_cb.SetValue(False)
                self._preamp_slider.Enable(True)
                self._on_apply(event)
                ui.message("Perfil personalizado restablecido a 0 dB")
        except Exception as e:
            log.error(f"AudioEqualizer: Error al restablecer perfil en GUI: {e}", exc_info=True)
            logger.log_error(f"Error al restablecer valores en GUI: {e}", exc=e, component="EqualizerDialog")
            ui.message(f"Error al restablecer valores: {e}")

    def _on_view_log(self, event):
        try:
            logger.open_log_file()
        except Exception as e:
            log.error(f"AudioEqualizer: Error al abrir log: {e}", exc_info=True)
            ui.message(f"No se pudo abrir el archivo de log: {e}")
        if event and hasattr(event, "Skip"):
            event.Skip()

    def _cleanup(self):
        if self._controller:
            self._controller._dialog_instance = None
        self.Destroy()
