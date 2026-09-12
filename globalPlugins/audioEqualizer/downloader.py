# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)
"""
Módulo de descarga e instalación asistida de Equalizer APO para Audio Equalizer.

Detecta la arquitectura del sistema operativo (32 o 64 bits) contemplando la emulación WOW64,
gestiona la descarga oficial con ventana de espera y progreso accesible en la carpeta de Descargas
del usuario (comprobando integridad mínima en bytes), y guía paso a paso al usuario con mensajes de voz.
"""

import os
import sys
import platform
import threading
import urllib.request
import time

try:
    import wx
except ImportError:
    wx = None

try:
    import ui
except ImportError:
    class _FallbackUI:
        @staticmethod
        def message(msg):
            print(f"[UI MESSAGE]: {msg}")
    ui = _FallbackUI()

try:
    import gui as nvda_gui
except ImportError:
    nvda_gui = None

try:
    from logHandler import log
except ImportError:
    import logging
    log = logging.getLogger("audioEqualizer.downloader")


def get_system_arch() -> str:
    """Detecta si el sistema operativo Windows es de 64 bits o 32 bits.

    Examina tanto si NVDA corre bajo emulación Wow64 (Python de 32 bits en Windows de 64 bits,
    a través de la variable de entorno PROCESSOR_ARCHITEW6432) como si corre de forma nativa
    en 64 bits. Esto es fundamental porque instalar Equalizer APO de 32 bits en un Windows de
    64 bits provocaría que el filtro APO no se enganche en el controlador del sistema.
    """
    arch = os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE", "")
    if "64" in arch or platform.machine().endswith("64"):
        return "64"
    return "32"


def get_apo_download_info() -> dict:
    """Devuelve los metadatos y URL oficial de descarga de Equalizer APO según la arquitectura.

    Incluye el nombre de archivo, la URL directa en SourceForge y el umbral mínimo
    esperado de bytes (alrededor de 7-8 MB) para evitar que una descarga cortada a medias
    se confunda con un instalador válido.
    """
    arch = get_system_arch()
    if arch == "64":
        return {
            "arch": "64",
            "arch_label": "64 bits (x64)",
            "filename": "EqualizerAPO64-1.3.exe",
            "url": "https://downloads.sourceforge.net/project/equalizerapo/1.3/EqualizerAPO64-1.3.exe",
            "approx_size_mb": 8.7,
            "min_expected_bytes": 7000000,
        }
    else:
        return {
            "arch": "32",
            "arch_label": "32 bits (x86)",
            "filename": "EqualizerAPO32-1.3.exe",
            "url": "https://downloads.sourceforge.net/project/equalizerapo/1.3/EqualizerAPO32-1.3.exe",
            "approx_size_mb": 7.6,
            "min_expected_bytes": 6000000,
        }


def get_downloads_dir() -> str:
    """Obtiene la ruta a la carpeta 'Descargas' estándar del usuario en Windows.

    Utiliza la API oficial de Windows SHGetKnownFolderPath con el identificador
    FOLDERID_Downloads ({374DE290-123F-4565-9164-39C4925E467B}) para respetar
    si el usuario movió su carpeta de descargas a otro disco o partición.
    Si la llamada falla, recurre a la carpeta predeterminada Downloads en su perfil.
    """
    try:
        import ctypes
        import uuid
        FOLDERID_Downloads = uuid.UUID('{374DE290-123F-4565-9164-39C4925E467B}')
        buf = ctypes.c_wchar_p()
        res = ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(ctypes.c_buffer(FOLDERID_Downloads.bytes_le)),
            0,
            None,
            ctypes.byref(buf)
        )
        if res == 0 and buf.value and os.path.isdir(buf.value):
            return buf.value
    except Exception as e:
        log.debug(f"AudioEqualizer: Error obteniendo carpeta Descargas vía API: {e}")

    fallback = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.exists(fallback):
        try:
            os.makedirs(fallback, exist_ok=True)
        except Exception:
            pass
    return fallback


class DownloadProgressDialog(wx.Dialog if wx else object):
    """
    Ventana de espera accesible que muestra el progreso de la descarga
    e informa periódicamente por voz el avance.
    """
    def __init__(self, parent, info: dict, target_path: str, on_finished):
        if not wx:
            return
        super().__init__(
            parent,
            title="Descargando Equalizer APO",
            style=wx.DEFAULT_DIALOG_STYLE & ~wx.CLOSE_BOX,
            size=(500, 240)
        )
        self.SetAffirmativeId(wx.ID_NONE)
        self.SetEscapeId(wx.ID_CANCEL)
        
        self._info = info
        self._target_path = target_path
        self._tmp_path = target_path + ".tmp"
        self._on_finished = on_finished
        self._is_cancelled = False
        self._download_thread = None
        self._last_spoken_percent = -1
        
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Etiqueta explicativa
        self._lbl_desc = wx.StaticText(
            panel,
            label=f"Descargando {info['filename']} para Windows de {info['arch_label']}...\nPor favor, espera unos momentos."
        )
        sizer.Add(self._lbl_desc, 0, wx.ALL | wx.EXPAND, 15)
        
        # Barra de progreso
        self._gauge = wx.Gauge(panel, range=100, style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)
        sizer.Add(self._gauge, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 15)
        
        # Texto de estado
        self._lbl_status = wx.StaticText(
            panel,
            label="Iniciando conexión con el servidor..."
        )
        sizer.Add(self._lbl_status, 0, wx.ALL | wx.EXPAND, 15)
        
        # Botón Cancelar
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._btn_cancel = wx.Button(panel, id=wx.ID_CANCEL, label="&Cancelar")
        btn_sizer.Add(self._btn_cancel, 0, wx.ALIGN_CENTER)
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 15)
        
        panel.SetSizer(sizer)
        self.Bind(wx.EVT_BUTTON, self._on_cancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        
        self.CenterOnScreen()

    def start(self):
        self._download_thread = threading.Thread(target=self._download_worker, daemon=True)
        self._download_thread.start()
        self.ShowModal()

    def _on_cancel(self, evt):
        self._cancel()

    def _on_close(self, evt):
        self._cancel()

    def _cancel(self):
        if not self._is_cancelled:
            self._is_cancelled = True
            self._lbl_status.SetLabel("Cancelando descarga...")
            ui.message("Cancelando descarga de Equalizer APO...")
            try:
                if os.path.exists(self._tmp_path):
                    os.remove(self._tmp_path)
            except Exception:
                pass
            wx.CallAfter(self._close_with_result, False, "Descarga cancelada por el usuario.")

    def _update_progress(self, downloaded_bytes, total_bytes):
        if self._is_cancelled:
            return
        if total_bytes > 0:
            percent = int((downloaded_bytes / total_bytes) * 100)
            percent = min(100, max(0, percent))
            mb_down = downloaded_bytes / (1024 * 1024)
            mb_tot = total_bytes / (1024 * 1024)
            status_str = f"Descargado: {mb_down:.1f} MB de {mb_tot:.1f} MB ({percent}%)"
            self._gauge.SetValue(percent)
            self._lbl_status.SetLabel(status_str)
            
            # Anunciar por voz los hitos de descarga
            if percent in (25, 50, 75, 100) and percent != self._last_spoken_percent:
                self._last_spoken_percent = percent
                ui.message(f"Descargando Equalizer APO: {percent}%")
        else:
            mb_down = downloaded_bytes / (1024 * 1024)
            self._gauge.Pulse()
            self._lbl_status.SetLabel(f"Descargado: {mb_down:.1f} MB...")

    def _download_worker(self):
        url = self._info["url"]
        headers = {"User-Agent": "Wget/1.20.3 (mingw32)"}
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                total_bytes = int(resp.headers.get("Content-Length", 0))
                downloaded_bytes = 0
                chunk_size = 64 * 1024
                
                os.makedirs(os.path.dirname(self._tmp_path), exist_ok=True)
                with open(self._tmp_path, "wb") as f:
                    while True:
                        if self._is_cancelled:
                            return
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded_bytes += len(chunk)
                        wx.CallAfter(self._update_progress, downloaded_bytes, total_bytes)
                
                if self._is_cancelled:
                    return
                
                if downloaded_bytes < self._info.get("min_expected_bytes", 5000000):
                    raise IOError(f"El archivo descargado está incompleto ({downloaded_bytes} bytes recibidos).")
                
                if os.path.exists(self._target_path):
                    try:
                        os.remove(self._target_path)
                    except Exception:
                        pass
                os.replace(self._tmp_path, self._target_path)
                
                wx.CallAfter(self._close_with_result, True, None)
                
        except Exception as e:
            log.error(f"AudioEqualizer: Error durante la descarga: {e}", exc_info=True)
            try:
                if os.path.exists(self._tmp_path):
                    os.remove(self._tmp_path)
            except Exception:
                pass
            if not self._is_cancelled:
                wx.CallAfter(self._close_with_result, False, str(e))

    def _close_with_result(self, success: bool, error_msg: str):
        try:
            self.Destroy()
        except Exception:
            pass
        if self._on_finished:
            self._on_finished(success, error_msg, self._target_path)


def start_apo_download_flow(parent=None):
    """
    Inicia el flujo interactivo guiado para descargar e instalar Equalizer APO:
    1. Pregunta si desea descargarlo ahora o más tarde informando la arquitectura detectada.
    2. Si confirma, abre una ventana de espera accesible y descarga en Descargas.
    3. Al finalizar, pregunta si desea abrir el instalador para instalarlo manualmente.
    """
    if not wx:
        return
    
    info = get_apo_download_info()
    downloads_dir = get_downloads_dir()
    target_path = os.path.join(downloads_dir, info["filename"])
    parent_win = parent or (nvda_gui.mainFrame if nvda_gui else None)
    
    # 1. Comprobar si ya existe en Descargas con tamaño válido
    if os.path.exists(target_path) and os.path.getsize(target_path) >= info["min_expected_bytes"]:
        res = wx.MessageBox(
            f"El instalador oficial de Equalizer APO ({info['filename']}) ya se encuentra en tu carpeta Descargas:\n\n"
            f"{target_path}\n\n"
            "¿Deseas abrirlo ahora para realizar la instalación manual?",
            "Instalador encontrado",
            wx.YES_NO | wx.ICON_QUESTION,
            parent=parent_win
        )
        if res == wx.YES:
            try:
                os.startfile(target_path)
                ui.message("Abriendo instalador de Equalizer APO. Sigue las instrucciones del asistente en pantalla.")
            except Exception as e:
                wx.MessageBox(f"No se pudo abrir el instalador: {e}", "Error", wx.OK | wx.ICON_ERROR, parent=parent_win)
            return
        
        # Preguntar si prefiere volver a descargarlo
        res_re = wx.MessageBox(
            "¿Deseas volver a descargar una copia nueva del instalador?",
            "Descargar de nuevo",
            wx.YES_NO | wx.ICON_QUESTION,
            parent=parent_win
        )
        if res_re != wx.YES:
            ui.message("Operación cancelada. El instalador sigue disponible en tu carpeta Descargas.")
            return

    # 2. Preguntar antes si desea descargarlo o más tarde
    prompt_msg = (
        "El ecualizador necesita el motor de audio Equalizer APO para funcionar.\n\n"
        f"• Sistema detectado: Windows de {info['arch_label']}\n"
        f"• Archivo a descargar: {info['filename']} (~{info['approx_size_mb']} MB)\n"
        f"• Destino: Carpeta Descargas ({downloads_dir})\n\n"
        "¿Deseas descargarlo ahora o prefieres hacerlo más tarde?"
    )
    res = wx.MessageBox(
        prompt_msg,
        "Motor de audio requerido (Equalizer APO)",
        wx.YES_NO | wx.ICON_QUESTION,
        parent=parent_win
    )
    
    if res != wx.YES:
        ui.message("Descarga pospuesta. Puedes iniciarla cuando desees desde el menú de NVDA > Herramientas > Ecualizador de Audio.")
        return

    # 3. Callback al terminar la descarga
    def on_download_finished(success: bool, error_msg: str, final_path: str):
        if not success:
            if error_msg and "cancelada" not in error_msg.lower():
                wx.MessageBox(
                    f"Ocurrió un error al intentar descargar Equalizer APO:\n\n{error_msg}\n\n"
                    "Por favor, verifica tu conexión a internet o descarga el instalador manualmente desde:\n"
                    "https://sourceforge.net/projects/equalizerapo/",
                    "Error de descarga",
                    wx.OK | wx.ICON_ERROR,
                    parent=parent_win
                )
            return
        
        # 4. Preguntar si desea abrirlo cuando termine la descarga para instalarlo
        open_res = wx.MessageBox(
            f"Equalizer APO se ha descargado correctamente en tu carpeta Descargas:\n\n"
            f"{final_path}\n\n"
            "¿Deseas abrir el instalador ahora para realizar la instalación manual?",
            "Descarga completada",
            wx.YES_NO | wx.ICON_QUESTION,
            parent=parent_win
        )
        
        if open_res == wx.YES:
            try:
                os.startfile(final_path)
                ui.message("Abriendo el instalador de Equalizer APO. Sigue las instrucciones del asistente en pantalla.")
            except Exception as e:
                wx.MessageBox(
                    f"No se pudo iniciar automáticamente el instalador:\n{e}\n\n"
                    f"Puedes abrirlo manualmente desde:\n{final_path}",
                    "Aviso",
                    wx.OK | wx.ICON_WARNING,
                    parent=parent_win
                )
        else:
            ui.message("El instalador de Equalizer APO está listo en tu carpeta Descargas para cuando desees instalarlo.")

    # 5. Abrir la ventana de espera modal
    dlg = DownloadProgressDialog(
        parent=parent_win,
        info=info,
        target_path=target_path,
        on_finished=on_download_finished
    )
    dlg.start()
