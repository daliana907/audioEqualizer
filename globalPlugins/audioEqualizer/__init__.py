# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Punto de entrada del complemento para NVDA.
Registra el esquema de configuración, inicializa el controlador
y define únicamente los comandos necesarios, evitando lógica de negocio aquí.
"""

import globalPluginHandler
try:
    import globalVars
except ImportError:
    globalVars = None
from scriptHandler import script
import addonHandler
import wx
import gui
import os

from . import config
from .equalizer import EqualizerController
from .apo_backend import ApoBackend

addonHandler.initTranslation()
try:
    _
except NameError:
    _ = lambda s: s


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    """Punto de integración de Audio Equalizer con el lector de pantalla NVDA.

    Registra los atajos de teclado globales en el diálogo 'Gestos de entrada', monta
    las opciones en el menú Herramientas y coordina el ciclo de vida del complemento.
    """
    scriptCategory = _("Ecualizador de audio")

    def __init__(self):
        """Arranca el complemento cuando NVDA lo carga en memoria.

        Registra primero el esquema de configuración (configspec) para que NVDA valide
        correctamente los tipos de datos en nvda.ini, instancia el motor acústico de
        Equalizer APO y el controlador de audio, y añade el submenú 'Ecualizador de Audio'
        al menú Herramientas de la bandeja del sistema.
        """
        super().__init__()
        if globalVars and getattr(globalVars.appArgs, "secureMode", False):
            import logHandler
            logHandler.log.warning("Audio Equalizer: NVDA en modo seguro. Se cancela la carga del complemento por seguridad.")
            raise globalPluginHandler.ActionCancelled()
        
        # Registrar esquema en NVDA config antes de cargar o guardar parámetros
        config.init_config_spec()
        
        # Inyección de dependencias: conectamos el controlador con el backend real de APO
        backend = ApoBackend()
        self._controller = EqualizerController(backend)
        
        self._create_menu()

    def _create_menu(self):
        """Crea el submenú 'Ecualizador de Audio' dentro del menú Herramientas de NVDA.

        Agrupa de forma limpia y accesible el acceso a la ventana principal, la apertura
        del registro de auditoría, la comprobación de conflictos, la descarga de APO y la ayuda.
        """
        self._tools_menu = wx.Menu()
        
        # Translators: Elemento de menú para abrir la ventana de configuración del ecualizador.
        settings_item = self._tools_menu.Append(wx.ID_ANY, _("Configuración..."))
        gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self._on_settings_menu, settings_item)
        
        # Translators: Elemento de menú para ver el registro técnico y auditoría de filtros.
        log_item = self._tools_menu.Append(wx.ID_ANY, _("Ver registro de filtros (Log)..."))
        gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self._open_log, log_item)

        # Translators: Elemento de menú para comprobar posibles conflictos con otros complementos.
        conflict_item = self._tools_menu.Append(wx.ID_ANY, _("Comprobar conflictos con otros complementos..."))
        gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self._check_conflicts, conflict_item)

        # Translators: Elemento de menú para descargar e instalar Equalizer APO.
        install_item = self._tools_menu.Append(wx.ID_ANY, _("Descargar e instalar motor de audio (Equalizer APO)..."))
        gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self._install_apo, install_item)
        
        self._submenu_item = gui.mainFrame.sysTrayIcon.toolsMenu.AppendSubMenu(
            self._tools_menu, 
            # Translators: Nombre del submenú en el menú Herramientas de NVDA.
            _("Ecualizador de Audio")
        )

    def _on_settings_menu(self, evt):
        """Abre la ventana de configuración accesible al pulsar en el menú."""
        wx.CallAfter(self._controller.show_gui)

    def _open_log(self, evt):
        """Abre el archivo de registro y auditoría de filtros con el visor predeterminado."""
        from . import logger
        logger.open_log_file()

    def _check_conflicts(self, evt):
        """Inicia el análisis dinámico de conflictos de atajos de teclado con otros complementos."""
        from . import conflicts
        conflicts.show_conflict_dialog(self)

    def _install_apo(self, evt):
        """Abre el asistente de descarga e instalación de Equalizer APO."""
        from . import downloader
        downloader.start_apo_download_flow()


    def terminate(self):
        """Descarga el complemento de forma ordenada al cerrar o reiniciar NVDA.

        Cierra el backend de audio y elimina el submenú de Herramientas para que no
        queden elementos huérfanos en la interfaz gráfica.
        """
        if self._controller:
            self._controller.terminate()
            
        try:
            tools_menu = gui.mainFrame.sysTrayIcon.toolsMenu
            if hasattr(self, "_submenu_item") and self._submenu_item:
                tools_menu.DestroyItem(self._submenu_item)
        except Exception:
            pass
        super().terminate()

    # --- Comandos y Atajos de Teclado Reasignables en NVDA ---

    @script(
        # Translators: Descripción del script para abrir la ventana de configuración del ecualizador.
        description=_("Abre el diálogo de configuración del ecualizador de audio."),
        category=scriptCategory,
    )
    def script_openEqualizer(self, gesture):
        """Abre o enfoca la ventana accesible con los controles de las 31 bandas y filtros."""
        wx.CallAfter(self._controller.show_gui)

    @script(
        # Translators: Descripción del script para conmutar el ecualizador de audio.
        description=_("Activa o desactiva rápidamente el ecualizador de audio."),
        category=scriptCategory,
    )
    def script_toggleEqualizer(self, gesture):
        """Conmuta el encendido/apagado general del ecualizador y lo anuncia por voz."""
        self._controller.toggle_equalizer()

    @script(
        # Translators: Descripción del script para avanzar al siguiente perfil.
        description=_("Cambia al siguiente perfil de ecualización."),
        category=scriptCategory,
    )
    def script_nextProfile(self, gesture):
        """Avanza al siguiente perfil de ecualización en la lista circular."""
        self._controller.next_profile()

    @script(
        # Translators: Descripción del script para retroceder al perfil anterior.
        description=_("Cambia al perfil de ecualización anterior."),
        category=scriptCategory,
    )
    def script_prevProfile(self, gesture):
        """Retrocede al perfil anterior en la lista de perfiles disponibles."""
        self._controller.previous_profile()

    @script(
        # Translators: Descripción del script para anunciar el estado de filtros y perfil activo.
        description=_("Anuncia por voz el estado completo del ecualizador: perfil activo, preamplificación y mejoras aplicadas."),
        category=scriptCategory,
    )
    def script_speakFilterStatus(self, gesture):
        """Verbaliza un resumen detallado con el perfil activo, preamplificación y filtros."""
        self._controller.speak_filter_status()

    @script(
        description=_("Ejecuta la comprobación auditiva de canales de audio (izquierdo, derecho y centro)."),
        category=scriptCategory,
    )
    def script_testChannels(self, gesture):
        """Emite tonos espaciales para verificar que los auriculares estén bien colocados."""
        self._controller.test_channels()

    @script(
        description=_("Aumenta los graves rápidos en 1 dB."),
        category=scriptCategory,
    )
    def script_increaseBass(self, gesture):
        """Incrementa el control de graves en 1 dB."""
        self._controller.adjust_tone_bass(1.0)

    @script(
        description=_("Disminuye los graves rápidos en 1 dB."),
        category=scriptCategory,
    )
    def script_decreaseBass(self, gesture):
        """Reduce el control de graves en 1 dB."""
        self._controller.adjust_tone_bass(-1.0)

    @script(
        description=_("Aumenta los agudos rápidos en 1 dB."),
        category=scriptCategory,
    )
    def script_increaseTreble(self, gesture):
        """Incrementa el control de agudos en 1 dB."""
        self._controller.adjust_tone_treble(1.0)

    @script(
        description=_("Disminuye los agudos rápidos en 1 dB."),
        category=scriptCategory,
    )
    def script_decreaseTreble(self, gesture):
        """Reduce el control de agudos en 1 dB."""
        self._controller.adjust_tone_treble(-1.0)

    @script(
        description=_("Aumenta la preamplificación manual en 1 dB."),
        category=scriptCategory,
    )
    def script_increasePreamp(self, gesture):
        """Incrementa la preamplificación manual en 1 dB."""
        self._controller.adjust_preamp(1.0)

    @script(
        description=_("Disminuye la preamplificación manual en 1 dB."),
        category=scriptCategory,
    )
    def script_decreasePreamp(self, gesture):
        """Reduce la preamplificación manual en 1 dB."""
        self._controller.adjust_preamp(-1.0)

    @script(
        description=_("Activa o desactiva la preamplificación automática para evitar distorsión."),
        category=scriptCategory,
    )
    def script_toggleAutoPreamp(self, gesture):
        """Conmuta la protección automática contra distorsión y saturación digital."""
        self._controller.toggle_auto_preamp()

    @script(
        description=_("Aumenta el balance hacia el canal derecho."),
        category=scriptCategory,
    )
    def script_increaseBalance(self, gesture):
        """Mueve el balance de audio hacia la derecha en 5%."""
        self._controller.adjust_balance(5)

    @script(
        description=_("Mueve el balance hacia el canal izquierdo."),
        category=scriptCategory,
    )
    def script_decreaseBalance(self, gesture):
        """Mueve el balance de audio hacia la izquierda en 5%."""
        self._controller.adjust_balance(-5)

    @script(
        description=_("Centra el balance de audio estéreo."),
        category=scriptCategory,
    )
    def script_centerBalance(self, gesture):
        """Restablece el balance al centro exacto (0%)."""
        self._controller.center_balance()

    @script(
        description=_("Aumenta el ancho estéreo en 10 %."),
        category=scriptCategory,
    )
    def script_increaseStereoWidth(self, gesture):
        """Ensancha la separación espacial estéreo Mid/Side en 10%."""
        self._controller.adjust_stereo_width(10)

    @script(
        description=_("Disminuye el ancho estéreo en 10 %."),
        category=scriptCategory,
    )
    def script_decreaseStereoWidth(self, gesture):
        """Reduce la separación espacial estéreo Mid/Side en 10%."""
        self._controller.adjust_stereo_width(-10)

    @script(
        description=_("Activa o desactiva el modo de audio mono."),
        category=scriptCategory,
    )
    def script_toggleMono(self, gesture):
        """Conmuta entre reproducción estéreo y mezcla monoaural 50/50."""
        self._controller.toggle_mono()

    @script(
        description=_("Invierte o restaura los canales izquierdo y derecho (L/R)."),
        category=scriptCategory,
    )
    def script_toggleSwapChannels(self, gesture):
        """Intercambia los canales izquierdo y derecho."""
        self._controller.toggle_swap_channels()

    @script(
        description=_("Activa o desactiva la compensación de volumen (Loudness)."),
        category=scriptCategory,
    )
    def script_toggleLoudness(self, gesture):
        """Conmuta la compensación acústica para escucha a bajo volumen."""
        self._controller.toggle_loudness()

    @script(
        description=_("Activa o desactiva la optimización acústica para la voz de NVDA."),
        category=scriptCategory,
    )
    def script_toggleNvdaVoice(self, gesture):
        """Conmuta el perfil acústico de inteligibilidad vocal para sintetizadores de pantalla."""
        self._controller.toggle_nvda_voice()

    @script(
        description=_("Activa o desactiva el realce de claridad vocal y presencia."),
        category=scriptCategory,
    )
    def script_toggleClarity(self, gesture):
        """Conmuta el realce en 5.5 kHz para destacar detalles vocales."""
        self._controller.toggle_clarity()

    @script(
        description=_("Activa o desactiva el filtro anti-sibilancia para suavizar el seseo."),
        category=scriptCategory,
    )
    def script_toggleAntiSibilance(self, gesture):
        """Conmuta el filtro en 7.5 kHz para atenuar frecuencias estridentes."""
        self._controller.toggle_anti_sibilance()

    @script(
        description=_("Activa o desactiva el filtro contra la fatiga auditiva."),
        category=scriptCategory,
    )
    def script_toggleAntiFatigue(self, gesture):
        """Conmuta el corte suave en 14 kHz para un sonido cálido y descansado."""
        self._controller.toggle_anti_fatigue()

    @script(
        description=_("Activa o desactiva el filtro subsónico para frecuencias inaudibles."),
        category=scriptCategory,
    )
    def script_toggleSubsonic(self, gesture):
        """Conmuta el filtro paso alto en 20 Hz para eliminar vibraciones inaudibles."""
        self._controller.toggle_subsonic()

    @script(
        description=_("Activa o desactiva la extensión de subgraves profundos (70 Hz)."),
        category=scriptCategory,
    )
    def script_toggleSubBass(self, gesture):
        """Conmuta el realce en 70 Hz para mayor pegada en graves."""
        self._controller.toggle_sub_bass()

    @script(
        description=_("Activa o desactiva el filtro anti-encajonamiento (400 Hz)."),
        category=scriptCategory,
    )
    def script_toggleAntiBox(self, gesture):
        """Conmuta el filtro en 400 Hz para eliminar resonancias nasales o de caja."""
        self._controller.toggle_anti_box()

    @script(
        description=_("Activa o desactiva el filtro contra zumbidos eléctricos de red."),
        category=scriptCategory,
    )
    def script_toggleGroundHum(self, gesture):
        """Conmuta los filtros notch contra ruido de masa e interferencias eléctricas."""
        self._controller.toggle_ground_hum()

    @script(
        description=_("Restablece la ecualización a una respuesta plana (0 dB)."),
        category=scriptCategory,
    )
    def script_resetEqualizer(self, gesture):
        """Pone todas las bandas a 0 dB y desactiva filtros acústicos."""
        self._controller.reset_to_flat()

    @script(
        description=_("Comprueba si existen conflictos de atajos de teclado con otros complementos."),
        category=scriptCategory,
    )
    def script_checkConflicts(self, gesture):
        """Revisa si algún atajo configurado colisiona con otros complementos en tiempo real."""
        self._check_conflicts(None)


