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
import addonHandler
addonHandler.initTranslation()


import os
import platform
import threading
import urllib.request
import ssl

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
            """Imprime en consola el mensaje cuando se ejecuta fuera del entorno de NVDA."""
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

try:
    _
except NameError:
    try:
        import addonHandler
        addonHandler.initTranslation()
    except Exception:
        pass
    try:
        _
    except NameError:
        _ = lambda s: s



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
    esperado de bytes (bastante por debajo del tamaño real informado por SourceForge)
    para evitar que una descarga cortada a medias se confunda con un instalador válido.
    """
    arch = get_system_arch()
    if arch == "64":
        return {
            "arch": "64",
            "arch_label": "64 bits (x64)",
            "filename": "EqualizerAPO-x64-1.4.2.exe",
            "url": "https://downloads.sourceforge.net/project/equalizerapo/1.4.2/EqualizerAPO-x64-1.4.2.exe",
            "approx_size_mb": 12.0,
            "min_expected_bytes": 9000000,
        }
    else:
        return {
            "arch": "32",
            "arch_label": "32 bits (x86)",
            "filename": "EqualizerAPO-x86-1.4.2.exe",
            "url": "https://downloads.sourceforge.net/project/equalizerapo/1.4.2/EqualizerAPO-x86-1.4.2.exe",
            "approx_size_mb": 11.0,
            "min_expected_bytes": 8000000,
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
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8),
            ]

        _ole32 = ctypes.windll.ole32
        _shell32 = ctypes.windll.shell32
        try:
            _ole32.CLSIDFromString.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(GUID)]
            _ole32.CLSIDFromString.restype = ctypes.c_long
            _shell32.SHGetKnownFolderPath.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)]
            _shell32.SHGetKnownFolderPath.restype = ctypes.c_long
            _ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
            _ole32.CoTaskMemFree.restype = None
        except Exception:
            pass
        _guid = GUID()
        hr = _ole32.CLSIDFromString("{374DE290-123F-4565-9164-39C4925E467B}", ctypes.byref(_guid))
        if hr == 0:
            _buf = ctypes.c_wchar_p()
            hr2 = _shell32.SHGetKnownFolderPath(ctypes.byref(_guid), 0, None, ctypes.byref(_buf))
            try:
                if hr2 == 0 and _buf.value:
                    downloads_path = _buf.value
                    if os.path.isdir(downloads_path):
                        return downloads_path
            finally:
                try:
                    if _buf.value:
                        _ole32.CoTaskMemFree(ctypes.cast(_buf, ctypes.c_void_p))
                except Exception:
                    pass
    except Exception as e:
        log.debug(f"AudioEqualizer: Error obteniendo carpeta Descargas vía API: {e}")

    fallback = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.exists(fallback):
        try:
            os.makedirs(fallback, exist_ok=True)
        except Exception:
            pass
    return fallback


def _compute_sha256(path: str) -> str:
    """Calcula SHA-256 de un fichero por bloques para no cargar instaladores en RAM."""
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_installer(path: str, info: dict) -> tuple:
    """Verifica tamaño exacto/mínimo y opcionalmente SHA-256 antes de ejecutar.

    Devuelve (ok, motivo). Re-verificar justo antes de os.startfile es obligatorio
    porque el fichero pudo cambiar entre la descarga y la ejecución (TOCTOU).
    """
    try:
        if not path or not os.path.isfile(path):
            return False, "no existe el instalador"
        size = os.path.getsize(path)
        min_expected = int(info.get("min_expected_bytes", 5000000) or 5000000)
        if size < min_expected:
            return False, f"tamaño {size} < mínimo {min_expected}"
        exact = info.get("exact_size")
        if exact is not None:
            try:
                if size != int(exact):
                    return False, f"tamaño {size} != esperado {exact}"
            except (ValueError, TypeError):
                pass
        expected_sha = info.get("sha256")
        if expected_sha:
            actual = _compute_sha256(path)
            if actual.lower() != str(expected_sha).lower():
                return False, "SHA-256 no coincide"
        return True, ""
    except Exception as e:
        return False, str(e)


def _safe_launch_installer(path: str, info: dict, parent_win=None) -> bool:
    """Re-verifica el instalador justo antes de ejecutar y lo lanza."""
    ok, reason = verify_installer(path, info)
    if not ok:
        log.error(f"AudioEqualizer: Instalador no verificado ({reason}): {path}")
        try:
            if wx and parent_win is not None:
                wx.MessageBox(_("El instalador no pasó la verificación ({reason}). Descárguelo de nuevo.").format(reason=reason), _("Error"), wx.OK | wx.ICON_ERROR, parent=parent_win)
            else:
                ui.message(_("El instalador no pasó la verificación. Descárguelo de nuevo."))
        except Exception:
            pass
        return False
    try:
        os.startfile(path)
        ui.message(_("Abriendo instalador de Equalizer APO. Sigue las instrucciones del asistente en pantalla."))
        return True
    except Exception as e:
        if getattr(e, "winerror", None) == 1223:
            ui.message(_("Apertura del instalador cancelada."))
        else:
            try:
                if wx:
                    wx.MessageBox(_("No se pudo abrir el instalador: {e}").format(e=e), _("Error"), wx.OK | wx.ICON_ERROR, parent=parent_win)
            except Exception:
                pass
        return False


class DownloadProgressDialog(wx.Dialog if wx else object):
    """
    Ventana de espera accesible que muestra el progreso de la descarga
    e informa periódicamente por voz el avance.
    """
    def __init__(self, parent, info: dict, target_path: str, on_finished):
        """Construye la ventana de descarga, inicializa la barra de progreso y conecta los eventos de cancelación."""
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
        self._active_resp = None
        self._resp_lock = threading.Lock()

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
        """Inicia el subproceso de descarga en segundo plano y muestra la ventana modal con la barra de progreso."""
        self._download_thread = threading.Thread(target=self._download_worker, daemon=True)
        self._download_thread.start()
        self.ShowModal()

    def _on_cancel(self, evt):
        """Maneja el clic en el botón Cancelar delegando en _cancel."""
        self._cancel()

    def _on_close(self, evt):
        """Maneja el cierre de la ventana por el usuario delegando en _cancel."""
        self._cancel()

    def _cancel(self):
        """Marca la descarga como cancelada, cierra el socket, limpia el temporal y cierra la ventana."""
        if not self._is_cancelled:
            self._is_cancelled = True
            try:
                with getattr(self, "_resp_lock", threading.Lock()):
                    resp = getattr(self, "_active_resp", None)
                if resp is not None:
                    try:
                        resp.close()
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                if hasattr(self, "_lbl_status") and self._lbl_status:
                    self._lbl_status.SetLabel("Cancelando descarga...")
            except Exception:
                pass
            ui.message(_("Cancelando descarga de Equalizer APO..."))
            try:
                if os.path.exists(self._tmp_path):
                    os.remove(self._tmp_path)
            except Exception:
                pass
            try:
                wx.CallAfter(self._close_with_result, False, "Descarga cancelada por el usuario.")
            except Exception:
                pass

    def _update_progress(self, downloaded_bytes, total_bytes):
        """Actualiza la barra de progreso y anuncia por voz los hitos del 25%, 50%, 75% y 100%."""
        if self._is_cancelled:
            return
        try:
            if total_bytes > 0:
                percent = int((downloaded_bytes / total_bytes) * 100)
                percent = min(100, max(0, percent))
                mb_down = downloaded_bytes / (1024 * 1024)
                mb_tot = total_bytes / (1024 * 1024)
                status_str = f"Descargado: {mb_down:.1f} MB de {mb_tot:.1f} MB ({percent}%)"
                if hasattr(self, "_gauge") and self._gauge:
                    self._gauge.SetValue(percent)
                if hasattr(self, "_lbl_status") and self._lbl_status:
                    self._lbl_status.SetLabel(status_str)

                # Anunciar por voz los hitos de descarga
                if percent in (25, 50, 75, 100) and percent != self._last_spoken_percent:
                    self._last_spoken_percent = percent
                    ui.message(_("Descargando Equalizer APO: {percent}%").format(percent=percent))
            else:
                mb_down = downloaded_bytes / (1024 * 1024)
                if hasattr(self, "_gauge") and self._gauge:
                    self._gauge.Pulse()
                if hasattr(self, "_lbl_status") and self._lbl_status:
                    self._lbl_status.SetLabel(f"Descargado: {mb_down:.1f} MB...")
        except Exception as e:
            log.debug(f"AudioEqualizer: Error actualizando progreso de descarga: {e}")

    def _download_worker(self):
        """Descarga con 3 reintentos (backoff 2**attempt), timeout 15 y verificación de integridad."""
        import time
        url = self._info["url"]
        headers = {"User-Agent": "Wget/1.20.3 (mingw32)"}
        last_err = None
        for attempt in range(3):
            if self._is_cancelled:
                return
            req = urllib.request.Request(url, headers=headers)
            try:
                ctx = ssl.create_default_context()
                with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                    try:
                        with getattr(self, "_resp_lock", threading.Lock()):
                            self._active_resp = resp
                    except Exception:
                        pass
                    try:
                        total_bytes = int(resp.headers.get("Content-Length", 0) or 0)
                    except (ValueError, TypeError):
                        total_bytes = 0
                    downloaded_bytes = 0
                    chunk_size = 64 * 1024

                    os.makedirs(os.path.dirname(self._tmp_path), exist_ok=True)
                    with open(self._tmp_path, "wb") as f:
                        while True:
                            if self._is_cancelled:
                                try:
                                    resp.close()
                                except Exception:
                                    pass
                                return
                            chunk = resp.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded_bytes += len(chunk)
                            try:
                                wx.CallAfter(self._update_progress, downloaded_bytes, total_bytes)
                            except Exception:
                                pass

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

                    try:
                        wx.CallAfter(self._close_with_result, True, None)
                    except Exception:
                        pass
                    return
            except Exception as e:
                last_err = e
                log.warning(f"AudioEqualizer: Intento {attempt + 1}/3 fallido: {e}")
                if self._is_cancelled:
                    return
                if attempt < 2:
                    try:
                        time.sleep(2 ** attempt)
                    except Exception:
                        pass
                    continue
                log.error(f"AudioEqualizer: Error durante la descarga tras 3 intentos: {e}", exc_info=True)
                if not self._is_cancelled:
                    try:
                        wx.CallAfter(self._close_with_result, False, str(e))
                    except Exception:
                        pass
            finally:
                try:
                    with getattr(self, "_resp_lock", threading.Lock()):
                        self._active_resp = None
                except Exception:
                    pass
                if self._is_cancelled or not os.path.exists(self._target_path):
                    try:
                        if os.path.exists(self._tmp_path):
                            os.remove(self._tmp_path)
                    except Exception:
                        pass

    def _close_with_result(self, success: bool, error_msg: str):
        """Destruye la ventana modal y llama al callback on_finished con el resultado de la descarga."""
        try:
            if hasattr(self, "IsModal") and self.IsModal():
                self.EndModal(wx.ID_OK if success else wx.ID_CANCEL)
        except Exception:
            pass
        try:
            self.Destroy()
        except Exception:
            pass
        on_finished = getattr(self, "_on_finished", None)
        if on_finished:
            try:
                target_path = getattr(self, "_target_path", "")
                on_finished(success, error_msg, target_path)
            except Exception as e:
                log.error(f"AudioEqualizer: Error en callback _on_finished: {e}", exc_info=True)


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
    _ok_exist, _ = verify_installer(target_path, info)
    if _ok_exist:
        res = wx.MessageBox(
            _("El instalador oficial de Equalizer APO ({info_filename}) ya se encuentra en tu carpeta Descargas:\n\n{target_path}\n\n¿Deseas abrirlo ahora para realizar la instalación manual?").format(info_filename=info["filename"], target_path=target_path),
            "Instalador encontrado",
            wx.YES_NO | wx.ICON_QUESTION,
            parent=parent_win
        )
        if res == wx.YES:
            _safe_launch_installer(target_path, info, parent_win)
            return
        
        # Preguntar si prefiere volver a descargarlo
        res_re = wx.MessageBox(
            _("¿Deseas volver a descargar una copia nueva del instalador?"),
            _("Descargar de nuevo"),
            wx.YES_NO | wx.ICON_QUESTION,
            parent=parent_win
        )
        if res_re != wx.YES:
            ui.message(_("Operación cancelada. El instalador sigue disponible en tu carpeta Descargas."))
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
        _("Motor de audio requerido (Equalizer APO)"),
        wx.YES_NO | wx.ICON_QUESTION,
        parent=parent_win
    )
    
    if res != wx.YES:
        ui.message(_("Descarga pospuesta. Puedes iniciarla cuando desees desde el menú de NVDA > Herramientas > Ecualizador de Audio."))
        return

    # 3. Callback al terminar la descarga
    def on_download_finished(success: bool, error_msg: str, final_path: str):
        """Callback ejecutado al finalizar la descarga para informar el resultado o ejecutar el instalador."""
        if not success:
            if error_msg and "cancelada" not in error_msg.lower():
                wx.MessageBox(
                    _("Ocurrió un error al intentar descargar Equalizer APO:\n\n{error_msg}\n\nPor favor, verifica tu conexión a internet o descarga el instalador manualmente desde:\nhttps://sourceforge.net/projects/equalizerapo/").format(error_msg=error_msg),
                    _("Error de descarga"),
                    wx.OK | wx.ICON_ERROR,
                    parent=parent_win
                )
            return
        
        # 4. Preguntar si desea abrirlo cuando termine la descarga para instalarlo
        ok_verify, reason = verify_installer(final_path, info)
        if not ok_verify:
            wx.MessageBox(
                _("El instalador descargado no pasó la verificación ({reason}). Por favor, descárguelo de nuevo.").format(reason=reason),
                _("Error de verificación"),
                wx.OK | wx.ICON_ERROR,
                parent=parent_win
            )
            return
        open_res = wx.MessageBox(
            _("Equalizer APO se ha descargado correctamente en tu carpeta Descargas:\n\n{final_path}\n\n¿Deseas abrir el instalador ahora para realizar la instalación manual?").format(final_path=final_path),
            _("Descarga completada"),
            wx.YES_NO | wx.ICON_QUESTION,
            parent=parent_win
        )
        
        if open_res == wx.YES:
            _safe_launch_installer(final_path, info, parent_win)
        else:
            ui.message(_("El instalador de Equalizer APO está listo en tu carpeta Descargas para cuando desees instalarlo."))

    # 5. Abrir la ventana de espera modal
    dlg = DownloadProgressDialog(
        parent=parent_win,
        info=info,
        target_path=target_path,
        on_finished=on_download_finished
    )
    dlg.start()
