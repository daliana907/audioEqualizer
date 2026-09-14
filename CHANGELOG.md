# Registro de cambios / Changelog

## 1.3.0 — 2026-09-13

### Español
- Corrección en el ensanchamiento estéreo: al superar el 100 %, la directiva Copy de Equalizer APO ahora incluye explícitamente el operador de adición (+) antes de los coeficientes negativos de la matriz Mid/Side. Esto soluciona el fallo que provocaba que el canal izquierdo se enmudeciera o saturara con corriente continua y que el sonido saliera únicamente por el auricular derecho.
- Cálculo acumulado de preamplificación automática (auto preamp): el algoritmo de protección contra saturación digital ahora calcula la suma de todos los filtros activos de forma simultánea (refuerzo de subgraves a 40 Hz, compensación fisiológica Loudness en graves y agudos, realce de presencia vocal y expansión estéreo), previniendo saturaciones digitales y chasquidos sin requerir ajuste manual de ganancia.
- Retención del perfil seleccionado: al retocar cualquier banda de ecualización sobre un perfil personalizado propio, la ventana mantiene activo tu perfil en lugar de cambiar automáticamente a Personalizado, permitiendo guardar o ajustar con mayor comodidad.
- Escritura atómica de configuraciones y perfiles: el guardado de perfiles (profiles.json) y el archivo de directivas de Equalizer APO (nvda_equalizer.txt) se efectúa ahora mediante archivos temporales con sustitución atómica (os.replace), protegiendo los datos contra corrupciones en caso de reinicios forzados o cortes de energía.
- Validación estructural de perfiles de usuario: se introdujo una comprobación estricta de estructura para perfiles importados o editados, verificando la presencia de las 31 ganancias numéricas y previniendo errores de carga ante datos truncados.
- Rotación automática del archivo de registro: el fichero audioEqualizer.log ahora se rota de forma automática cuando supera 1 MB de tamaño, evitando un crecimiento descontrolado del registro en el disco.
- Descargador de Equalizer APO más robusto: soporte para respuestas HTTP chunked o sin cabecera fija Content-Length, liberación garantizada de memoria COM al localizar la carpeta Descargas de Windows y soporte completo de traducción Gettext en los cuadros de diálogo del asistente.
- Prueba de orientación de auriculares calibrada: síntesis matemática en memoria de tonos estéreo a 44.1 kHz con rampa de desvanecimiento suave (fade) de 20 ms para evitar chasquidos acústicos, reproducción asíncrona con el indicador SND_NODEFAULT para impedir sonidos predeterminados erróneos de Windows y limpieza de archivos temporales al finalizar.
- Mayor estabilidad en la interfaz gráfica: prevención de excepciones PyDeadObjectError en wxPython durante la destrucción o cierre de la ventana de ajustes y control ordenado del foco del teclado.
- Limpieza integral en la desinstalación: el script installTasks.py ahora elimina de forma garantizada los registros persistentes y los archivos de prueba generados en el directorio temporal al desinstalar el complemento.

### English
- Fixed stereo width expansion above 100%: the Equalizer APO Copy directive now explicitly inserts the addition operator (+) before negative coefficients in the Mid/Side matrix. This eliminates the parsing issue that caused Equalizer APO to abort channel parsing, muting or saturating the left earphone and outputting sound only on the right side.
- Cumulative automatic preamp calculation (auto preamp): the anti-clipping protection now computes the combined gain of all concurrently active filters (sub-bass boost at 40 Hz, Loudness physiological compensation in lows and highs, vocal presence boosts, and stereo expansion), preventing digital clipping and distortion without requiring manual gain attenuation.
- Custom profile retention: adjusting any frequency slider on a saved custom profile now retains the active profile selection instead of jumping to Custom, streamlining incremental adjustments.
- Atomic profile and directive file writes: user profiles (profiles.json) and Equalizer APO commands (nvda_equalizer.txt) are now written using temporary files followed by atomic replacement (os.replace), safeguarding configuration files against corruption from unexpected system shutdowns.
- Structural profile validation: added strict type and length verification when loading profiles, ensuring all 31 band gains are numeric and within valid bounds.
- Automatic log rotation: the diagnostic log audioEqualizer.log is now automatically rotated when reaching 1 MB to prevent unbounded disk usage.
- Resilient Equalizer APO downloader: full support for chunked HTTP transfer encoding without a predefined Content-Length header, guaranteed COM memory release when resolving the Windows Downloads folder, and full localization support for installer prompts.
- Calibrated headphone orientation test: mathematical synthesis of 44.1 kHz PCM stereo tones with 20 ms anti-pop fade envelopes, asynchronous playback using SND_NODEFAULT to avoid fallback system chime overlap, and automated cleanup.
- wxPython GUI lifecycle hardening: prevented PyDeadObjectError exceptions during window destruction and ensured reliable keyboard focus management upon dialog closure.
- Clean uninstallation: installTasks.py now thoroughly removes persistent audit logs and temporary test audio files upon add-on removal.

---

## 1.3.1 — 2026-09-13

### Español

Mantenimiento y limpieza interna del código. Sin cambios en el comportamiento del complemento.

Se eliminaron importaciones de módulos sin uso en varios archivos del complemento (`sys` y `time` en `downloader.py`, `os` en `equalizer.py` y `__init__.py`, `constants` en `logger.py` y `profiles.py`). Se completó la documentación técnica interna de todos los métodos que carecían de descripción en `config.py`, `dialog.py`, `downloader.py`, `dummy_backend.py`, `equalizer.py`, `logger.py` y `channel_tester.py`.

### English

Internal code cleanup and documentation. No behavioral changes.

Removed unused module imports across several files (`sys` and `time` in `downloader.py`, `os` in `equalizer.py` and `__init__.py`, `constants` in `logger.py` and `profiles.py`). Completed internal docstring coverage for all previously undocumented methods across `config.py`, `dialog.py`, `downloader.py`, `dummy_backend.py`, `equalizer.py`, `logger.py`, and `channel_tester.py`.

---

## 1.1.0 — 2026-09-12

### Novedades
- Añadidos comandos y scripts configurables para todas las funciones del ecualizador, permitiendo reasignar cualquier tecla desde Gestos de entrada de NVDA bajo la categoría "Ecualizador de audio".
- Añadidos atajos para control de balance estéreo (mover a la izquierda, a la derecha y centrar al 0%).
- Añadida comprobación de conflictos de atajos con otros complementos en el menú Herramientas.
- Redacción natural y accesible en toda la documentación del complemento.

---

## 1.0.0 — 2026-09-11

### Novedades
- Primera versión del ecualizador de 31 bandas ISO con motor Equalizer APO.
- 13 perfiles predefinidos de fábrica y gestión de perfiles de usuario.
- Filtros acústicos para auriculares, claridad de voz y prueba sonora de canales.
