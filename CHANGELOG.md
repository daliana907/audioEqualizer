# Registro de cambios / Changelog

## Versión 1.3.0 (13 de septiembre de 2026)

### Español
- Se corrigió la orden que ensancha el sonido estéreo para que el motor de audio siempre acepte los valores superiores al 100 % sin fallar.
- La protección automática contra distorsión (preamp) ahora calcula la suma de refuerzos graves y agudos combinados para evitar saturaciones y chasquidos en la tarjeta de sonido.
- Al retocar una frecuencia en un perfil guardado propio, el selector mantiene tu perfil seleccionado en vez de saltar al perfil genérico.

### English
- Fixed the stereo width expansion directive so the audio engine always accepts values above 100% without syntax errors.
- Improved automatic anti-clipping protection (auto preamp) to account for overlapping bass/treble boosts and stereo expansion, preventing digital distortion.
- Tweaking a frequency band on a saved custom profile now keeps that profile selected instead of jumping to Custom.

---

## Versión 1.1.0 (12 de septiembre de 2026)

### Novedades
- Añadidos comandos y scripts configurables para todas las funciones del ecualizador, permitiendo reasignar cualquier tecla desde Gestos de entrada de NVDA bajo la categoría "Ecualizador de audio".
- Añadidos atajos para control de balance estéreo (mover a la izquierda, a la derecha y centrar al 0%).
- Añadida comprobación de conflictos de atajos con otros complementos en el menú Herramientas.
- Redacción natural y accesible en toda la documentación del complemento.

---

## Versión 1.0.0 (11 de septiembre de 2026)

### Novedades
- Primera versión del ecualizador de 31 bandas ISO con motor Equalizer APO.
- 13 perfiles predefinidos de fábrica y gestión de perfiles de usuario.
- Filtros acústicos para auriculares, claridad de voz y prueba sonora de canales.
