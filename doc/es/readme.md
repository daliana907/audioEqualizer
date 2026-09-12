# Audio Equalizer para NVDA

Autora: Daliana
Versión: 1.2.0
Compatibilidad: NVDA 2024.1 o posterior
Licencia: GNU GPL v2

Este complemento añade un ecualizador de 31 bandas para calibrar el sonido de Windows con NVDA de forma completamente accesible. Puedes ajustar graves y agudos al instante, elegir o crear perfiles de sonido, corregir el balance de auriculares y aplicar filtros para mejorar la claridad de la voz del lector de pantalla o descansar el oído en sesiones largas.

## Requisitos y funcionamiento

El ecualizador aplica los ajustes directamente a través de Equalizer APO, un motor de sonido para Windows que procesa el audio en tiempo real sin retrasos ni distorsión.

- Para que funcione, necesitas tener instalado Equalizer APO en el equipo.
- Si todavía no lo tienes instalado, el complemento lo detecta solo al abrirlo y te ofrece descargarlo en tu carpeta de descargas según tu versión de Windows (de 32 o 64 bits). Al terminar la descarga, podrás abrir el instalador y seguir los pasos normales.
- También puedes descargarlo cuando quieras desde el menú de NVDA > Herramientas > Ecualizador de Audio > Descargar e instalar motor de audio (Equalizer APO)... o desde su página web oficial: https://sourceforge.net/projects/equalizerapo/

## Atajos de teclado y personalización

Para no interferir con las órdenes nativas de NVDA ni con otros complementos (como Monitor del Sistema), este complemento no asigna atajos de teclado por defecto.

Puedes abrir todas sus funciones directamente desde el menú de NVDA > Herramientas > Ecualizador de Audio, o bien asignar tus combinaciones preferidas en el menú de NVDA > Preferencias > Gestos de entrada, dentro de la categoría "Ecualizador de audio".

Entre las acciones que puedes asignar se encuentran:
- Subir y bajar graves rápidos (pasos de 1 dB).
- Subir y bajar agudos rápidos (pasos de 1 dB).
- Subir y bajar la preamplificación (pasos de 1 dB).
- Activar o desactivar la preamplificación automática para evitar distorsión.
- Mover el balance a la izquierda o a la derecha, y centrarlo.
- Aumentar o reducir el ancho estéreo.
- Activar o desactivar el modo mono y la inversión de canales izquierdo y derecho.
- Activar o desactivar la compensación de volumen (Loudness).
- Activar o desactivar la claridad de la voz de NVDA o el realce de presencia vocal.
- Activar o desactivar los filtros para auriculares: anti-fatiga, anti-sibilancia, anti-encajonamiento, subgraves, subsónico y anti-zumbido eléctrico.
- Comprobar la orientación de los auriculares con tonos de prueba en canal izquierdo, derecho y centro.
- Restablecer el ecualizador a una curva plana (0 dB).
- Comprobar si hay conflictos de teclas con otros complementos.

## Opciones disponibles en la ventana

Al abrir la configuración desde el menú NVDA > Herramientas > Ecualizador de Audio (o con el atajo personalizado que decidas asignarle en Gestos de entrada), se abre una ventana accesible organizada con los siguientes apartados:

### Perfiles de sonido
Puedes elegir entre varios perfiles ya preparados (Plano, Música, Estudio, Películas, Juegos, Voz y Podcasts, Rock, Pop, Electrónica, Clásica, Jazz, Refuerzo de graves, Refuerzo de agudos y Modo nocturno). Además, puedes guardar tus propios ajustes con el nombre que quieras o borrar los que ya no uses. Incluye un botón para probar los canales y verificar que tienes los auriculares bien colocados.

### Preamplificación y control de ganancia
Un deslizador para ajustar el volumen general de entrada y una casilla de preamplificación automática que baja la ganancia si subes mucho alguna frecuencia para evitar saturación digital.

### Balance y ajustes estéreo
Controles para forzar sonido en mono, invertir canales izquierdo y derecho, ajustar el balance hacia un lado u otro y regular la amplitud estéreo desde un sonido cerrado hasta una imagen más amplia.

### Filtros para auriculares y claridad
Casillas opcionales pensadas para el uso con auriculares o sintetizadores de voz:
- Modo Loudness para compensar la pérdida de graves y agudos cuando escuchas a poco volumen.
- Claridad para la voz de NVDA y realce de presencia vocal para que el lector de pantalla y las conversaciones se entiendan con nitidez.
- Filtro anti-sibilancia para suavizar las eses molestas y filtro anti-fatiga auditiva para reducir el cansancio en los oídos.
- Filtro contra sonido hueco o encajonado y filtro contra zumbidos eléctricos de red (50 y 60 Hz).
- Refuerzo de subgraves profundos y corte subsónico para limpiar frecuencias inaudibles.

### Ecualizador de 31 bandas
Treinta y un deslizadores accesibles desde 20 Hz hasta 20 kHz para ajustar cada rango de frecuencia de forma independiente entre -12 dB y +12 dB.

### Herramientas y diagnóstico
- Botón Ver registro: muestra los cambios técnicos aplicados en Equalizer APO para comprobar que el motor está respondiendo.
- Detección de conflictos: disponible en el menú de Herramientas de NVDA para avisarte si algún atajo configurado coincide con otro complemento.
