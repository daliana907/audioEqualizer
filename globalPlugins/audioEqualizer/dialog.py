# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Interfaz gráfica de usuario completamente accesible para NVDA.

Construye una ventana con desplazamiento vertical con soporte para lectores de pantalla.
Cada deslizador actualiza dinámicamente su nombre accesible con el valor exacto en decibelios
y porcentajes para que el sintetizador de voz lo verbalice de inmediato al interactuar con el teclado.
Permite gestionar perfiles (guardar, eliminar y cargar), activar filtros acústicos biquad,
controlar el balance suave y el ancho estéreo Mid/Side, y escuchar los cambios en tiempo real.
"""
import addonHandler
addonHandler.initTranslation()
try:
    _
except NameError:
    def _(s): return s


import wx
_raw_dead = getattr(wx, "PyDeadObjectError", RuntimeError)
DeadObjectError = (RuntimeError, _raw_dead) if isinstance(_raw_dead, type) and issubclass(_raw_dead, BaseException) else RuntimeError
import math
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
        self._cleaned_up = False
        self._apply_timer = None
        
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
        self._profile_choice.Bind(wx.EVT_KEY_UP, self._on_profile_choice_keyup)
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

        self._test_audio_btn = wx.Button(scroll_panel, label="Comprobar canales de a&udio")
        self._test_audio_btn.Bind(wx.EVT_BUTTON, self._on_test_audio)
        btn_row.Add(self._test_audio_btn, 0)
        profile_box_sizer.Add(btn_row, 0, wx.ALL, 4)

        main_sizer.Add(profile_box_sizer, 0, wx.EXPAND | wx.ALL, 8)

        # 2. Casilla Activar ecualizador
        self._enabled_cb = wx.CheckBox(scroll_panel, label="&Ecualizador activado")
        self._enabled_cb.SetValue(self._profile.enabled)
        self._enabled_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        main_sizer.Add(self._enabled_cb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # 3. Configuración de canales y sonido envolvente
        chan_box = wx.StaticBox(scroll_panel, label="Canales y sonido envolvente")
        chan_sizer = wx.StaticBoxSizer(chan_box, wx.VERTICAL)

        mode_row = wx.BoxSizer(wx.HORIZONTAL)
        mode_lbl = wx.StaticText(scroll_panel, label="Configuración de canales:")
        self._channel_mode_keys = [
            constants.CHANNEL_MODE_STEREO,
            constants.CHANNEL_MODE_5_1,
            constants.CHANNEL_MODE_7_1,
            constants.CHANNEL_MODE_QUAD,
            constants.CHANNEL_MODE_DOWNMIX_5_1,
            constants.CHANNEL_MODE_DOWNMIX_7_1,
        ]
        self._channel_mode_choice = wx.Choice(
            scroll_panel,
            name=_("Configuración de canales"),
            choices=[
                _("Estéreo estándar (2.0)"),
                _("Envolvente 5.1 (Frontal, Central, Subwoofer, Traseros)"),
                _("Envolvente 7.1 (Frontal, Central, Subwoofer, Traseros, Laterales)"),
                _("Cuadrafónico (4.0 - 4 altavoces)"),
                _("Mezcla inteligente 5.1 a Estéreo (Películas/juegos a auriculares)"),
                _("Mezcla inteligente 7.1 a Estéreo (Películas/juegos a auriculares)"),
            ]
        )
        cur_mode = getattr(self._profile, "channel_mode", constants.DEFAULT_CHANNEL_MODE)
        if cur_mode in self._channel_mode_keys:
            self._channel_mode_choice.SetSelection(self._channel_mode_keys.index(cur_mode))
        else:
            self._channel_mode_choice.SetSelection(0)
        self._channel_mode_choice.SetName(_("Configuración de canales"))
        self._channel_mode_choice.Bind(wx.EVT_CHOICE, self._on_channel_mode_choice)
        mode_row.Add(mode_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        mode_row.Add(self._channel_mode_choice, 1, wx.EXPAND)
        chan_sizer.Add(mode_row, 0, wx.EXPAND | wx.ALL, 4)

        c_row = wx.BoxSizer(wx.HORIZONTAL)
        c_lbl = wx.StaticText(scroll_panel, label="Canal Central (voces):", size=(175, -1))
        self._center_slider = wx.Slider(
            scroll_panel,
            value=int(round(getattr(self._profile, "center_gain", constants.DEFAULT_CENTER_GAIN))),
            minValue=int(constants.MIN_CHANNEL_GAIN),
            maxValue=int(constants.MAX_CHANNEL_GAIN),
            style=wx.SL_HORIZONTAL,
            name="Canal Central (voces)"
        )
        self._center_slider.Bind(wx.EVT_SLIDER, self._on_center_scroll)
        c_row.Add(c_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        c_row.Add(self._center_slider, 1, wx.EXPAND)
        chan_sizer.Add(c_row, 0, wx.EXPAND | wx.ALL, 4)

        sub_row = wx.BoxSizer(wx.HORIZONTAL)
        sub_lbl = wx.StaticText(scroll_panel, label="Subwoofer (graves LFE):", size=(175, -1))
        self._subwoofer_slider = wx.Slider(
            scroll_panel,
            value=int(round(getattr(self._profile, "subwoofer_gain", constants.DEFAULT_SUBWOOFER_GAIN))),
            minValue=int(constants.MIN_CHANNEL_GAIN),
            maxValue=int(constants.MAX_CHANNEL_GAIN),
            style=wx.SL_HORIZONTAL,
            name="Subwoofer (graves LFE)"
        )
        self._subwoofer_slider.Bind(wx.EVT_SLIDER, self._on_subwoofer_scroll)
        sub_row.Add(sub_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        sub_row.Add(self._subwoofer_slider, 1, wx.EXPAND)
        chan_sizer.Add(sub_row, 0, wx.EXPAND | wx.ALL, 4)

        sur_row = wx.BoxSizer(wx.HORIZONTAL)
        sur_lbl = wx.StaticText(scroll_panel, label="Canales traseros / Surround:", size=(175, -1))
        self._surround_slider = wx.Slider(
            scroll_panel,
            value=int(round(getattr(self._profile, "surround_gain", constants.DEFAULT_SURROUND_GAIN))),
            minValue=int(constants.MIN_CHANNEL_GAIN),
            maxValue=int(constants.MAX_CHANNEL_GAIN),
            style=wx.SL_HORIZONTAL,
            name="Canales traseros / Surround"
        )
        self._surround_slider.Bind(wx.EVT_SLIDER, self._on_surround_scroll)
        sur_row.Add(sur_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        sur_row.Add(self._surround_slider, 1, wx.EXPAND)
        chan_sizer.Add(sur_row, 0, wx.EXPAND | wx.ALL, 4)

        self._update_channel_controls_state()
        self._update_channel_names()

        main_sizer.Add(chan_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # 4. Preamplificación
        preamp_box = wx.StaticBox(scroll_panel, label="Preamplificación y control de ganancia")
        preamp_sizer = wx.StaticBoxSizer(preamp_box, wx.VERTICAL)
        
        preamp_row = wx.BoxSizer(wx.HORIZONTAL)
        preamp_lbl = wx.StaticText(scroll_panel, label="Preamplificación:", size=(120, -1))
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

        self._auto_preamp_cb = wx.CheckBox(scroll_panel, label="Preamp au&tomático (evita saturación y distorsión)")
        self._auto_preamp_cb.SetValue(self._profile.auto_preamp)
        self._auto_preamp_cb.Bind(wx.EVT_CHECKBOX, self._on_auto_preamp_check)
        self._preamp_slider.Enable(not self._profile.auto_preamp)
        preamp_sizer.Add(self._auto_preamp_cb, 0, wx.ALL, 4)
        
        main_sizer.Add(preamp_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # 4. Mejoras acústicas y espaciales seguras
        opt_box = wx.StaticBox(scroll_panel, label="Mejoras acústicas y espaciales")
        opt_sizer = wx.StaticBoxSizer(opt_box, wx.VERTICAL)

        self._loudness_cb = wx.CheckBox(scroll_panel, label="Loudness isofónico (Compensación para bajo volumen Fletcher-Munson)")
        self._loudness_cb.SetValue(self._profile.loudness)
        self._loudness_cb.Bind(wx.EVT_CHECKBOX, self._on_enhancement_check)
        opt_sizer.Add(self._loudness_cb, 0, wx.ALL, 4)

        self._ground_hum_cb = wx.CheckBox(scroll_panel, label="Filtro anti-&zumbido eléctrico (Notch 50 y 60 Hz, elimina ruidos de masa)")
        self._ground_hum_cb.SetValue(self._profile.ground_hum)
        self._ground_hum_cb.Bind(wx.EVT_CHECKBOX, self._on_enhancement_check)
        opt_sizer.Add(self._ground_hum_cb, 0, wx.ALL, 4)


        self._mono_cb = wx.CheckBox(scroll_panel, label="Forzar audio &mono")
        self._mono_cb.SetValue(self._profile.mono)
        self._mono_cb.Bind(wx.EVT_CHECKBOX, self._on_apply)
        opt_sizer.Add(self._mono_cb, 0, wx.ALL, 4)

        

        self._surround_3d_cb = wx.CheckBox(scroll_panel, label="Audio &3D Inmersivo (Binaural HRTF profesional)")
        self._surround_3d_cb.SetValue(getattr(self._profile, "surround_3d", False))
        self._surround_3d_cb.Bind(wx.EVT_CHECKBOX, self._on_enhancement_check)
        opt_sizer.Add(self._surround_3d_cb, 0, wx.ALL, 4)

        self._radar_mode_cb = wx.CheckBox(scroll_panel, label="Mo&do Radar (Precisión posicional 360 para detalles)")
        self._radar_mode_cb.SetValue(getattr(self._profile, "radar_mode", False))
        self._radar_mode_cb.Bind(wx.EVT_CHECKBOX, self._on_enhancement_check)
        opt_sizer.Add(self._radar_mode_cb, 0, wx.ALL, 4)

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
        self._width_slider.SetLineSize(5)
        self._width_slider.SetPageSize(10)
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
        treble_lbl = wx.StaticText(scroll_panel, label="Agudos rápidos (8 &kHz):", size=(150, -1))
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

        # 6. Mejoras acústicas para auriculares profesionales
        hp_box = wx.StaticBox(scroll_panel, label="Mejoras para auriculares profesionales")
        hp_sizer = wx.StaticBoxSizer(hp_box, wx.VERTICAL)

        self._subsonic_cb = wx.CheckBox(scroll_panel, label="Filtro subsó&nico infrasónico (Corta < 20 Hz, libera potencia en graves)")
        self._subsonic_cb.SetValue(self._profile.subsonic)
        self._subsonic_cb.Bind(wx.EVT_CHECKBOX, self._on_enhancement_check)
        hp_sizer.Add(self._subsonic_cb, 0, wx.ALL, 4)

        self._nvda_voice_cb = wx.CheckBox(scroll_panel, label="Claridad para sintetizador de &voz (Optimiza NVDA, menos fatiga)")
        self._nvda_voice_cb.SetValue(self._profile.nvda_voice)
        self._nvda_voice_cb.Bind(wx.EVT_CHECKBOX, self._on_enhancement_check)
        hp_sizer.Add(self._nvda_voice_cb, 0, wx.ALL, 4)

        self._sub_bass_cb = wx.CheckBox(scroll_panel, label="E&xtensión de subgraves profundos (+6 dB en 70 Hz para drivers 50-53 mm)")
        self._sub_bass_cb.SetValue(self._profile.sub_bass)
        self._sub_bass_cb.Bind(wx.EVT_CHECKBOX, self._on_enhancement_check)
        hp_sizer.Add(self._sub_bass_cb, 0, wx.ALL, 4)

        self._clarity_cb = wx.CheckBox(scroll_panel, label="Realce de claridad &y presencia (+5.5 dB en 5.5 kHz, voz y brillo nítidos)")
        self._clarity_cb.SetValue(self._profile.clarity)
        self._clarity_cb.Bind(wx.EVT_CHECKBOX, self._on_enhancement_check)
        hp_sizer.Add(self._clarity_cb, 0, wx.ALL, 4)

        self._anti_sibilance_cb = wx.CheckBox(scroll_panel, label="Filtro anti-&sibilancia (recorte fijo y constante de -5 dB en 7.5 kHz, suaviza seseo y estridencias)")
        self._anti_sibilance_cb.SetValue(self._profile.anti_sibilance)
        self._anti_sibilance_cb.Bind(wx.EVT_CHECKBOX, self._on_enhancement_check)
        hp_sizer.Add(self._anti_sibilance_cb, 0, wx.ALL, 4)

        self._anti_fatigue_cb = wx.CheckBox(scroll_panel, label="Filtro anti-&fatiga auditiva (recorte fijo y constante de -4.5 dB en 14 kHz, sonido cálido relajante)")
        self._anti_fatigue_cb.SetValue(self._profile.anti_fatigue)
        self._anti_fatigue_cb.Bind(wx.EVT_CHECKBOX, self._on_enhancement_check)
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
        
        apply_btn = wx.Button(btn_panel, label="Aplicar")
        apply_btn.Bind(wx.EVT_BUTTON, self._on_apply_button)
        btn_sizer.Add(apply_btn, 0, wx.RIGHT, 5)

        reset_btn = wx.Button(btn_panel, label="&Restablecer")
        reset_btn.Bind(wx.EVT_BUTTON, self._on_reset)
        btn_sizer.Add(reset_btn, 0, wx.RIGHT, 5)

        log_btn = wx.Button(btn_panel, label="Ver registr&o (Log)")
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
        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_window_destroy)
        # Foco inicial en el selector de perfil (tab order = orden de creación).
        try:
            self._profile_choice.SetFocus()
        except Exception:
            pass

    def _update_balance_name(self):
        """Actualiza el nombre accesible del slider de balance según si está centrado, a la izquierda o a la derecha."""
        val = self._balance_slider.GetValue()
        if val == 0:
            txt = "centrado"
        elif val < 0:
            txt = f"{abs(val)} por ciento a la izquierda"
        else:
            txt = f"{val} por ciento a la derecha"
        self._balance_slider.SetName(f"Balance estéreo, {txt}")

    def _on_balance_scroll(self, event):
        """Maneja el desplazamiento del slider de balance: actualiza el nombre accesible y aplica el cambio."""
        self._update_balance_name()
        self._on_apply(event)
        event.Skip()

    def _update_width_name(self):
        """Actualiza el nombre accesible del slider de ancho estéreo con la descripción del modo actual."""
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

    def _mark_custom_profile(self):
        """Conmuta la selección a 'Personalizado' si se estaba en un perfil predefinido."""
        if hasattr(self, "_profile_choice") and self._profile_choice:
            cur = self._profile_choice.GetSelection()
            if cur != profiles.CUSTOM_INDEX:
                self._profile_choice.SetSelection(profiles.CUSTOM_INDEX)
                if hasattr(self, "_update_profile_buttons_state"):
                    self._update_profile_buttons_state()

    def _on_enhancement_check(self, event):
        """Maneja la conmutación de cualquier mejora acústica con exclusión radar/surround."""
        try:
            # Exclusión mutua: radar y surround no pueden estar activos a la vez.
            ctrl = getattr(event, "GetEventObject", lambda: None)() if event else None
            is_surround_evt = ctrl is getattr(self, "_surround_3d_cb", None)
            is_radar_evt = ctrl is getattr(self, "_radar_mode_cb", None)
            if is_surround_evt and self._surround_3d_cb.GetValue() and self._radar_mode_cb.GetValue():
                self._radar_mode_cb.SetValue(False)
                ui.message(_("Audio 3D activado; modo radar desactivado por exclusión mutua."))
            elif is_radar_evt and self._radar_mode_cb.GetValue() and self._surround_3d_cb.GetValue():
                self._surround_3d_cb.SetValue(False)
                ui.message(_("Modo radar activado; audio 3D desactivado por exclusión mutua."))
        except DeadObjectError:
            return
        except Exception:
            pass
        self._mark_custom_profile()
        self._on_apply(event)
        if event and hasattr(event, "Skip"):
            event.Skip()

    def _on_width_scroll(self, event):
        """Maneja el desplazamiento del slider de ancho estéreo: anuncia el valor por voz y aplica el cambio."""
        self._update_width_name()
        self._mark_custom_profile()
        val = self._width_slider.GetValue()
        ui.message(_("Ancho estéreo: {val}%").format(val=val))
        self._on_apply(event)
        event.Skip()

    def _update_tone_names(self):
        """Actualiza los nombres accesibles de los sliders de graves y agudos con sus valores en dB."""
        b_val = self._tone_bass_slider.GetValue()
        self._tone_bass_slider.SetName(f"Graves rápidos, {b_val} decibelios")
        t_val = self._tone_treble_slider.GetValue()
        self._tone_treble_slider.SetName(f"Agudos rápidos, {t_val} decibelios")

    def _on_tone_scroll(self, event):
        """Maneja el desplazamiento de los sliders de tono rápido: actualiza nombres accesibles y aplica el cambio."""
        self._update_tone_names()
        self._mark_custom_profile()
        self._on_apply(event)
        event.Skip()

    def _update_channel_controls_state(self):
        """Mantiene los controles de canales siempre activos y accesibles por teclado para el usuario."""
        if hasattr(self, "_center_slider"):
            self._center_slider.Enable(True)
        if hasattr(self, "_subwoofer_slider"):
            self._subwoofer_slider.Enable(True)
        if hasattr(self, "_surround_slider"):
            self._surround_slider.Enable(True)

    def _update_channel_names(self):
        """Actualiza los nombres accesibles de la configuración de canales para NVDA."""
        if hasattr(self, "_channel_mode_choice") and self._channel_mode_choice:
            self._channel_mode_choice.SetName(_("Configuración de canales"))
        if hasattr(self, "_center_slider") and self._center_slider:
            c_val = self._center_slider.GetValue()
            self._center_slider.SetName(f"Canal Central (voces), {c_val} decibelios")
        if hasattr(self, "_subwoofer_slider") and self._subwoofer_slider:
            sub_val = self._subwoofer_slider.GetValue()
            self._subwoofer_slider.SetName(f"Subwoofer (graves LFE), {sub_val} decibelios")
        if hasattr(self, "_surround_slider") and self._surround_slider:
            sur_val = self._surround_slider.GetValue()
            self._surround_slider.SetName(f"Canales traseros y envolventes, {sur_val} decibelios")

    def _on_channel_mode_choice(self, event=None):
        """Maneja la selección de configuración de canales: verbaliza la elección, actualiza nombres y aplica."""
        self._update_channel_controls_state()
        self._update_channel_names()
        sel = self._channel_mode_choice.GetSelection()
        all_strs = self._channel_mode_choice.GetStrings()
        if 0 <= sel < len(all_strs):
            try:
                ui.message(_("Configuración de canales: {mode}").format(mode=all_strs[sel]))
            except Exception:
                pass
        self._mark_custom_profile()
        self._on_apply(event)
        if event and hasattr(event, "Skip"):
            event.Skip()

    def _on_center_scroll(self, event):
        """Maneja el desplazamiento del deslizador del canal Central."""
        self._update_channel_names()
        self._mark_custom_profile()
        self._on_apply(event)
        event.Skip()

    def _on_subwoofer_scroll(self, event):
        """Maneja el desplazamiento del deslizador del Subwoofer."""
        self._update_channel_names()
        self._mark_custom_profile()
        self._on_apply(event)
        event.Skip()

    def _on_surround_scroll(self, event):
        """Maneja el desplazamiento del deslizador de canales traseros / surround."""
        self._update_channel_names()
        self._mark_custom_profile()
        self._on_apply(event)
        event.Skip()

    def _refresh_profiles_list(self):
        """Recarga la lista desplegable de perfiles desde el disco, preservando la selección actual cuando es posible."""
        user_profs = config.load_user_profiles()
        choice_items = list(profiles.PROFILE_NAMES) + ["Personalizado"]
        for up in user_profs:
            p_name = up.get("name") if isinstance(up, dict) else ""
            if p_name:
                choice_items.append(f"Usuario: {p_name}")

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
        """Habilita o deshabilita el botón de borrado de perfil según si la selección actual es un perfil de usuario."""
        if not hasattr(self, "_delete_profile_btn") or not self._delete_profile_btn:
            return
        sel = self._profile_choice.GetSelection()
        is_user_profile = sel > profiles.CUSTOM_INDEX
        self._delete_profile_btn.Enable(is_user_profile)

    def _on_save_profile_as(self, event):
        """Solicita un nombre al usuario y guarda el perfil actual como perfil personalizado en disco."""
        try:
            dlg = wx.TextEntryDialog(
                self,
                "Introduce un nombre para el nuevo perfil personalizado:",
                "Guardar perfil personalizado",
                ""
            )
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    name = dlg.GetValue().strip()
                    valid, err_msg = config.validate_profile_name(name)
                    if not valid:
                        ui.message(err_msg)
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
                        ui.message(_("Perfil '{name}' guardado correctamente.").format(name=name))
                    else:
                        ui.message(_("Error al guardar el perfil personalizado."))
            finally:
                dlg.Destroy()
        except Exception as e:
            log.error(f"AudioEqualizer: Error al guardar perfil personalizado: {e}", exc_info=True)
            logger.log_error(f"Error al guardar perfil personalizado: {e}", exc=e, component="EqualizerDialog")
            ui.message(_("Error al guardar perfil: {e}").format(e=e))

    def _on_delete_profile(self, event):
        """Solicita confirmación y elimina el perfil de usuario seleccionado de la lista y del disco."""
        try:
            sel = self._profile_choice.GetSelection()
            if sel <= profiles.CUSTOM_INDEX:
                return
            user_profs = config.load_user_profiles()
            user_idx = sel - profiles.CUSTOM_INDEX - 1
            if 0 <= user_idx < len(user_profs):
                prof_entry = user_profs[user_idx]
                prof_name = prof_entry.get("name") if isinstance(prof_entry, dict) else ""
                if not prof_name:
                    return
                dlg = wx.MessageDialog(
                    self,
                    f"¿Estás seguro de que deseas eliminar el perfil '{prof_name}'?",
                    "Confirmar eliminación",
                    wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
                )
                try:
                    if dlg.ShowModal() == wx.ID_YES:
                        config.delete_user_profile(prof_name)
                        self._refresh_profiles_list()
                        self._profile_choice.SetSelection(0)
                        self._apply_profile_to_ui(0)
                        self._sync_profile_from_ui()
                        self._controller.apply_profile(self._profile, save=True)
                        ui.message(_("Perfil '{prof_name}' eliminado.").format(prof_name=prof_name))
                finally:
                    dlg.Destroy()
        except Exception as e:
            log.error(f"AudioEqualizer: Error al eliminar perfil personalizado: {e}", exc_info=True)
            logger.log_error(f"Error al eliminar perfil personalizado: {e}", exc=e, component="EqualizerDialog")
            ui.message(_("Error al eliminar perfil: {e}").format(e=e))

    def _on_test_audio(self, event):
        """Lanza la prueba de canales de audio izquierdo, derecho y centro estéreo."""
        from . import channel_tester
        ui.message(_("Iniciando prueba: Canal izquierdo... Canal derecho... Centro estéreo."))
        channel_tester.play_channel_test()

    def _apply_profile_to_ui(self, prof_index):
        """Carga los valores de un perfil predefinido o de usuario en todos los controles del diálogo."""
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

        gains = config._parse_gains(prof.get("gains", []))
        for i, slider in enumerate(self._band_sliders):
            if i < len(gains):
                val_gain = max(constants.MIN_GAIN, min(constants.MAX_GAIN, gains[i]))
                slider.SetValue(int(round(val_gain)))
                freq = constants.EQ_BANDS[i]
                f_str = f"{freq} Hz" if freq < 1000 else f"{freq/1000:g} kHz"
                slider.SetName(f"{f_str}, ganancia, {int(round(val_gain))} decibelios")

        if "preamp" in prof:
            try:
                val_preamp = float(prof["preamp"])
                if math.isnan(val_preamp) or math.isinf(val_preamp):
                    val_preamp = 0.0
                else:
                    val_preamp = max(constants.MIN_PREAMP, min(constants.MAX_PREAMP, val_preamp))
            except (ValueError, TypeError, OverflowError):
                val_preamp = 0.0
            self._preamp_slider.SetValue(int(round(val_preamp)))
            self._preamp_slider.SetName(f"Preamplificación, {int(round(val_preamp))} decibelios")
            self._auto_preamp_cb.SetValue(bool(prof.get("auto_preamp", False)))
        else:
            self._auto_preamp_cb.SetValue(True)
        self._preamp_slider.Enable(not self._auto_preamp_cb.GetValue())

        # Controles de tono rápido del perfil
        try:
            val_tb = float(prof.get("tone_bass", 0.0))
            if math.isnan(val_tb) or math.isinf(val_tb):
                val_tb = 0.0
            else:
                val_tb = max(constants.MIN_TONE, min(constants.MAX_TONE, val_tb))
        except (ValueError, TypeError, OverflowError):
            val_tb = 0.0
        self._tone_bass_slider.SetValue(int(round(val_tb)))

        try:
            val_tt = float(prof.get("tone_treble", 0.0))
            if math.isnan(val_tt) or math.isinf(val_tt):
                val_tt = 0.0
            else:
                val_tt = max(constants.MIN_TONE, min(constants.MAX_TONE, val_tt))
        except (ValueError, TypeError, OverflowError):
            val_tt = 0.0
        self._tone_treble_slider.SetValue(int(round(val_tt)))
        self._update_tone_names()

        # Ancho estéreo óptimo del perfil
        try:
            val_sw = int(round(float(prof.get("stereo_width", 100))))
            val_sw = max(constants.MIN_STEREO_WIDTH, min(constants.MAX_STEREO_WIDTH, val_sw))
        except (ValueError, TypeError, OverflowError):
            val_sw = 100
        self._width_slider.SetValue(val_sw)
        self._update_width_name()

        # Mejoras para auriculares profesionales
        if hasattr(self, "_sub_bass_cb") and self._sub_bass_cb:
            self._sub_bass_cb.SetValue(bool(prof.get("sub_bass", False)))
        if hasattr(self, "_clarity_cb") and self._clarity_cb:
            self._clarity_cb.SetValue(bool(prof.get("clarity", False)))
        if hasattr(self, "_anti_sibilance_cb") and self._anti_sibilance_cb:
            self._anti_sibilance_cb.SetValue(bool(prof.get("anti_sibilance", False)))
        if hasattr(self, "_anti_fatigue_cb") and self._anti_fatigue_cb:
            self._anti_fatigue_cb.SetValue(bool(prof.get("anti_fatigue", False)))
        if hasattr(self, "_subsonic_cb") and self._subsonic_cb:
            self._subsonic_cb.SetValue(bool(prof.get("subsonic", False)))
        if hasattr(self, "_nvda_voice_cb") and self._nvda_voice_cb:
            self._nvda_voice_cb.SetValue(bool(prof.get("nvda_voice", False)))

        # Procesamiento espacial y acústico
        if hasattr(self, "_loudness_cb") and self._loudness_cb:
            self._loudness_cb.SetValue(bool(prof.get("loudness", False)))
        if hasattr(self, "_ground_hum_cb") and self._ground_hum_cb:
            self._ground_hum_cb.SetValue(bool(prof.get("ground_hum", False)))
        if hasattr(self, "_mono_cb") and self._mono_cb:
            self._mono_cb.SetValue(bool(prof.get("mono", False)))
        if hasattr(self, "_swap_cb") and self._swap_cb:
            self._swap_cb.SetValue(bool(prof.get("swap_channels", False)))
        if hasattr(self, "_surround_3d_cb") and self._surround_3d_cb:
            self._surround_3d_cb.SetValue(bool(prof.get("surround_3d", False)))
        if hasattr(self, "_radar_mode_cb") and self._radar_mode_cb:
            self._radar_mode_cb.SetValue(bool(prof.get("radar_mode", False)))

        # Configuración de canales multicanal
        mode_val = prof.get("channel_mode", constants.DEFAULT_CHANNEL_MODE)
        if hasattr(self, "_channel_mode_choice") and self._channel_mode_choice:
            if mode_val in self._channel_mode_keys:
                self._channel_mode_choice.SetSelection(self._channel_mode_keys.index(mode_val))
            else:
                self._channel_mode_choice.SetSelection(0)
        if hasattr(self, "_center_slider") and self._center_slider:
            self._center_slider.SetValue(int(round(float(prof.get("center_gain", constants.DEFAULT_CENTER_GAIN)))))
        if hasattr(self, "_subwoofer_slider") and self._subwoofer_slider:
            self._subwoofer_slider.SetValue(int(round(float(prof.get("subwoofer_gain", constants.DEFAULT_SUBWOOFER_GAIN)))))
        if hasattr(self, "_surround_slider") and self._surround_slider:
            self._surround_slider.SetValue(int(round(float(prof.get("surround_gain", constants.DEFAULT_SURROUND_GAIN)))))
        self._update_channel_controls_state()
        self._update_channel_names()

        self._update_profile_buttons_state()

    
    def _activarPerfilSeleccionado(self, idx, event=None):
        """Aplica el perfil en la interfaz, guarda los cambios, actualiza botones y lo verbaliza."""
        self._last_profile_idx = idx
        self._apply_profile_to_ui(idx)
        self._on_apply(event)
        self._update_profile_buttons_state()
        all_choices = self._profile_choice.GetStrings()
        if 0 <= idx < len(all_choices):
            try:
                ui.message(_("Perfil: {choice}").format(choice=all_choices[idx]))
            except Exception:
                pass

    def _on_profile_choice_keyup(self, event):
        idx = self._profile_choice.GetSelection()
        if hasattr(self, "_last_profile_idx") and self._last_profile_idx != idx:
            self._activarPerfilSeleccionado(idx, event=None)
        event.Skip()

    def _on_profile_choice(self, event):
        """Aplica el perfil elegido en la lista desplegable, anuncia el nombre del perfil y actualiza los botones."""
        idx = self._profile_choice.GetSelection()
        self._activarPerfilSeleccionado(idx, event=event)
        event.Skip()

    def _on_band_slider_scroll(self, event, slider, f_txt):
        """Maneja el desplazamiento de un slider de banda EQ: actualiza su nombre accesible y aplica el cambio."""
        val = slider.GetValue()
        slider.SetName(f"{f_txt}, ganancia, {val} decibelios")
        self._mark_custom_profile()
        self._on_apply(event)
        event.Skip()

    def _on_preamp_scroll(self, event):
        """Maneja el desplazamiento del slider de preamplificación: actualiza el nombre accesible y aplica el cambio."""
        val = self._preamp_slider.GetValue()
        self._preamp_slider.SetName(f"Preamplificación, {val} decibelios")
        self._on_apply(event)
        event.Skip()

    def _on_auto_preamp_check(self, event):
        """Habilita o deshabilita el slider de preamplificación según si el automático está marcado."""
        is_auto = self._auto_preamp_cb.GetValue()
        self._preamp_slider.Enable(not is_auto)
        self._on_apply(event)
        event.Skip()

    def _sync_profile_from_ui(self):
        """Lee el estado de todos los controles y actualiza el perfil sin mutación parcial.

        Valida todos los GetValue primero; si algún control está muerto
        (DeadObject) aborta sin modificar _profile. Preserva float en tonos/gains.
        """
        try:
            v_enabled = self._enabled_cb.GetValue()
            v_preamp = self._preamp_slider.GetValue()
            v_auto = self._auto_preamp_cb.GetValue()
            v_loud = self._loudness_cb.GetValue()
            v_hum = self._ground_hum_cb.GetValue()
            v_mono = self._mono_cb.GetValue()
            v_sur = self._surround_3d_cb.GetValue() if hasattr(self, "_surround_3d_cb") and self._surround_3d_cb else False
            v_radar = self._radar_mode_cb.GetValue() if hasattr(self, "_radar_mode_cb") and self._radar_mode_cb else False
            v_swap = self._swap_cb.GetValue()
            v_bal = self._balance_slider.GetValue()
            v_bass = self._tone_bass_slider.GetValue()
            v_treble = self._tone_treble_slider.GetValue()
            v_subbass = self._sub_bass_cb.GetValue()
            v_clarity = self._clarity_cb.GetValue()
            v_sib = self._anti_sibilance_cb.GetValue()
            v_fat = self._anti_fatigue_cb.GetValue()
            v_subsonic = self._subsonic_cb.GetValue()
            v_voice = self._nvda_voice_cb.GetValue()
            v_width = self._width_slider.GetValue()
            v_chan_idx = self._channel_mode_choice.GetSelection() if hasattr(self, "_channel_mode_choice") else 0
            v_center = self._center_slider.GetValue() if hasattr(self, "_center_slider") else 0
            v_sub = self._subwoofer_slider.GetValue() if hasattr(self, "_subwoofer_slider") else 0
            v_surround = self._surround_slider.GetValue() if hasattr(self, "_surround_slider") else 0
            v_idx = self._profile_choice.GetSelection()
            v_gains = [float(s.GetValue()) for s in self._band_sliders]
        except DeadObjectError:
            log.debug("AudioEqualizer: _sync_profile_from_ui abortado por DeadObject; sin mutación parcial.")
            raise
        except RuntimeError as e:
            if "deleted" in str(e).lower() or "dead" in str(e).lower():
                log.debug(f"AudioEqualizer: _sync abortado por objeto destruido: {e}")
                raise
            raise
        # Exclusión mutua también al sincronizar desde UI.
        if bool(v_sur) and bool(v_radar):
            v_radar = False
            try:
                if hasattr(self, "_radar_mode_cb") and self._radar_mode_cb:
                    self._radar_mode_cb.SetValue(False)
                ui.message(_("Audio 3D y radar son excluyentes; se desactivó radar."))
            except Exception:
                pass
        # Solo tras validar todo, asignar al perfil (preservando float).
        self._profile.enabled = bool(v_enabled)
        self._profile.preamp = float(v_preamp)
        self._profile.auto_preamp = bool(v_auto)
        self._profile.loudness = bool(v_loud)
        self._profile.ground_hum = bool(v_hum)
        self._profile.mono = bool(v_mono)
        self._profile.surround_3d = bool(v_sur)
        self._profile.radar_mode = bool(v_radar)
        self._profile.swap_channels = bool(v_swap)
        self._profile.balance = int(v_bal)
        self._profile.tone_bass = float(v_bass)
        self._profile.tone_treble = float(v_treble)
        self._profile.sub_bass = bool(v_subbass)
        self._profile.clarity = bool(v_clarity)
        self._profile.anti_sibilance = bool(v_sib)
        self._profile.anti_fatigue = bool(v_fat)
        self._profile.subsonic = bool(v_subsonic)
        self._profile.nvda_voice = bool(v_voice)
        self._profile.stereo_width = int(v_width)
        if 0 <= v_chan_idx < len(self._channel_mode_keys):
            self._profile.channel_mode = self._channel_mode_keys[v_chan_idx]
        else:
            self._profile.channel_mode = constants.DEFAULT_CHANNEL_MODE
        self._profile.center_gain = float(v_center)
        self._profile.subwoofer_gain = float(v_sub)
        self._profile.surround_gain = float(v_surround)
        
        prof_idx = int(v_idx)
        self._profile.profile_index = prof_idx
        # LECTURA DIRECTA DE LA INTERFAZ SIEMPRE (para guardar modificaciones en perfiles de fábrica)
        self._profile.gains = [float(g) for g in v_gains]
        
        # SI ESTAMOS EN UN PERFIL DE FÁBRICA, GUARDAR EL OVERRIDE EN DISCO Y MEMORIA
        if prof_idx < profiles.CUSTOM_INDEX:
            config.save_factory_override(prof_idx, self._profile)

    def _on_apply(self, event=None):
        """Aplica los cambios en tiempo real con debounce coalescente de 350 ms.

        Permite escuchar inmediatamente el resultado acústico mientras se ajustan los deslizadores.
        Coalesca movimientos rápidos: cancela el timer previo y programa uno nuevo.
        """
        if event and hasattr(event, "Skip"):
            try:
                event.Skip()
            except Exception:
                pass
        if getattr(self, "_cleaned_up", False):
            return
        try:
            _t = getattr(self, "_apply_timer", None)
            if _t is not None:
                try:
                    _t.Stop()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self._apply_timer = wx.CallLater(350, self._do_apply_now)
        except Exception:
            # Si CallLater no disponible (tests), aplicar directo.
            try:
                self._do_apply_now()
            except Exception:
                pass

    def _do_apply_now(self):
        """Aplica de verdad, en disco, el último estado de los controles tras la breve espera de _on_apply."""
        if getattr(self, "_cleaned_up", False):
            return
        try:
            self._sync_profile_from_ui()
            self._controller.apply_profile(self._profile, save=False)
        except Exception as e:
            log.error(f"AudioEqualizer: Error aplicando cambios desde la interfaz: {e}", exc_info=True)
            logger.log_error(f"Error aplicando cambios en GUI: {e}", exc=e, component="EqualizerDialog")
            ui.message(_("Error al aplicar cambios: {e}").format(e=e))

    def _on_apply_button(self, event=None):
        """Maneja el clic explícito en el botón 'Aplicar', guardando inmediatamente en disco."""
        if getattr(self, "_cleaned_up", False):
            return
        if getattr(self, "_apply_timer", None) is not None:
            try:
                self._apply_timer.Stop()
            except Exception:
                pass
        try:
            self._sync_profile_from_ui()
            self._controller.apply_profile(self._profile, save=True)
            ui.message(_("Configuración aplicada y guardada."))
        except Exception as e:
            log.error(f"AudioEqualizer: Error en botón Aplicar: {e}", exc_info=True)
            logger.log_error(f"Error en botón Aplicar: {e}", exc=e, component="EqualizerDialog")
            ui.message(_("Error al aplicar cambios: {e}").format(e=e))

    def _on_ok(self, event=None):
        """Guarda permanentemente la configuración en NVDA y cierra la ventana."""
        if getattr(self, "_apply_timer", None) is not None:
            try:
                self._apply_timer.Stop()
            except Exception:
                pass
        try:
            self._sync_profile_from_ui()
            self._controller.apply_profile(self._profile, save=True)
            self._cleanup(wx.ID_OK)
        except Exception as e:
            log.error(f"AudioEqualizer: Error al guardar cambios y cerrar: {e}", exc_info=True)
            try:
                logger.log_error(f"Error al guardar cambios en GUI (Aceptar): {e}", exc=e, component="EqualizerDialog")
            except Exception:
                pass
            ui.message(_("Error al guardar cambios: {e}").format(e=e))

    def _on_cancel(self, event=None):
        """Descarta las modificaciones temporales, restaura el estado previo y cierra la ventana."""
        try:
            self._controller.restore_persisted_state()
        except Exception as e:
            log.error(f"AudioEqualizer: Error al restaurar estado en Cancelar: {e}", exc_info=True)
            try:
                logger.log_error(f"Error en Cancelar de GUI: {e}", exc=e, component="EqualizerDialog")
            except Exception:
                pass
        self._cleanup(wx.ID_CANCEL)

    def _on_reset(self, event):
        """Restablece los controles a sus valores iniciales.

        Si se trata de un perfil predefinido de fábrica, vuelve a los valores de diseño del perfil.
        Si se trata del perfil personalizado, pone todas las 31 bandas en 0.0 dB (plano).
        """
        try:
            prof_idx = self._profile_choice.GetSelection()
            if hasattr(self, "_loudness_cb") and self._loudness_cb:
                self._loudness_cb.SetValue(False)
            if hasattr(self, "_mono_cb") and self._mono_cb:
                self._mono_cb.SetValue(False)
            if hasattr(self, "_radar_mode_cb") and self._radar_mode_cb:
                self._radar_mode_cb.SetValue(False)
            if hasattr(self, "_swap_cb") and self._swap_cb:
                self._swap_cb.SetValue(False)
            if hasattr(self, "_balance_slider") and self._balance_slider:
                self._balance_slider.SetValue(0)
                if hasattr(self, "_update_balance_name"):
                    self._update_balance_name()
            if hasattr(self, "_width_slider") and self._width_slider:
                self._width_slider.SetValue(100)
                if hasattr(self, "_update_width_name"):
                    self._update_width_name()
            if hasattr(self, "_tone_bass_slider") and self._tone_bass_slider:
                self._tone_bass_slider.SetValue(0)
            if hasattr(self, "_tone_treble_slider") and self._tone_treble_slider:
                self._tone_treble_slider.SetValue(0)
            if hasattr(self, "_update_tone_names"):
                self._update_tone_names()
            if hasattr(self, "_sub_bass_cb") and self._sub_bass_cb:
                self._sub_bass_cb.SetValue(False)
            if hasattr(self, "_clarity_cb") and self._clarity_cb:
                self._clarity_cb.SetValue(False)
            if hasattr(self, "_anti_sibilance_cb") and self._anti_sibilance_cb:
                self._anti_sibilance_cb.SetValue(False)
            if hasattr(self, "_anti_fatigue_cb") and self._anti_fatigue_cb:
                self._anti_fatigue_cb.SetValue(False)
            if hasattr(self, "_ground_hum_cb") and self._ground_hum_cb:
                self._ground_hum_cb.SetValue(False)
            if hasattr(self, "_subsonic_cb") and self._subsonic_cb:
                self._subsonic_cb.SetValue(False)
            if hasattr(self, "_nvda_voice_cb") and self._nvda_voice_cb:
                self._nvda_voice_cb.SetValue(False)
            if hasattr(self, "_surround_3d_cb") and self._surround_3d_cb:
                self._surround_3d_cb.SetValue(False)

            if prof_idx < profiles.CUSTOM_INDEX:
                from . import config
                config.remove_factory_override(prof_idx)
                prof = profiles.PREDEFINED_PROFILES[prof_idx]
                self._apply_profile_to_ui(prof_idx)
                self._on_apply(event)
                ui.message(_("Perfil '{prof_name}' restablecido a sus valores originales").format(prof_name=prof['name']))
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
                ui.message(_("Perfil personalizado restablecido a 0 dB"))
        except Exception as e:
            log.error(f"AudioEqualizer: Error al restablecer perfil en GUI: {e}", exc_info=True)
            logger.log_error(f"Error al restablecer valores en GUI: {e}", exc=e, component="EqualizerDialog")
            ui.message(_("Error al restablecer valores: {e}").format(e=e))

    def _on_view_log(self, event):
        """Abre el archivo de auditoría audioEqualizer.log con el programa predeterminado del sistema."""
        try:
            logger.open_log_file()
        except Exception as e:
            log.error(f"AudioEqualizer: Error al abrir log: {e}", exc_info=True)
            ui.message(_("No se pudo abrir el archivo de log: {e}").format(e=e))
        if event and hasattr(event, "Skip"):
            event.Skip()

    def _on_window_destroy(self, event=None):
        """Notificación del sistema wx cuando la ventana es destruida."""
        self._cleanup_controller_ref()
        if event and hasattr(event, "Skip"):
            event.Skip()

    def _cleanup_controller_ref(self):
        """Libera la referencia en el controlador y notifica a NVDA mainFrame."""
        if getattr(self, "_cleaned_up", False):
            return
        self._cleaned_up = True
        if getattr(self, "_apply_timer", None) is not None:
            try:
                self._apply_timer.Stop()
            except Exception:
                pass
        try:
            if self._controller and getattr(self._controller, "_dialog_instance", None) is self:
                self._controller._dialog_instance = None
        except Exception:
            pass
        try:
            from gui import mainFrame
            mainFrame.postPopup()
        except Exception:
            pass

    def _cleanup(self, code=None):
        """Cierra y destruye la ventana asegurando la liberación de recursos."""
        self._cleanup_controller_ref()
        if code is None:
            code = getattr(wx, "ID_OK", 5100)
        if hasattr(self, "IsModal") and self.IsModal():
            self.EndModal(code)
        try:
            self.Destroy()
        except DeadObjectError:
            pass
