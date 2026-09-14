# Ecualizador de Audio para NVDA (Audio Equalizer)

- Autora: Daliana
- Versión: 1.3.0
- Compatibilidad: NVDA 2023.1 en adelante
- Licencia: GNU GPL v2

[Read in English](../en/readme.md)

---

## Versión en Español

El Ecualizador de Audio te permite mejorar y calibrar la calidad del sonido en Windows directamente desde NVDA. Puedes ajustar graves, medios y agudos, elegir perfiles listos para música, películas o juegos, regular el volumen de entrada, mejorar la claridad de la voz de NVDA y aplicar filtros diseñados especialmente para escuchar con auriculares cómodamente y sin fatiga.

### Motor de audio necesario (Equalizer APO)
Para aplicar los efectos en el sistema, este complemento utiliza **Equalizer APO**, un motor de procesamiento de audio libre y gratuito para Windows:
- Si no lo tienes instalado, la primera vez que abras el complemento te ofrecerá descargarlo e instalarlo de forma automática y guiada.
- También puedes descargarlo cuando quieras desde el menú de NVDA > Herramientas > Ecualizador de Audio > Descargar e instalar motor de audio (Equalizer APO)... o desde su página web oficial: https://sourceforge.net/projects/equalizerapo/

## Atajos de teclado y personalización

Para no interferir con las órdenes nativas de NVDA ni con otros complementos (como Monitoreo del Sistema), este complemento no asigna atajos de teclado por defecto.

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
- Activar o desactivar los filtros para auriculares: anti-fatiga, anti-sibilancia, subgraves, subsónico y anti-zumbido eléctrico.
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

### Filtros especiales para auriculares
Casillas opcionales pensadas para el uso con auriculares o salas silenciosas:

- Modo Loudness para compensar la pérdida de graves y agudos al escuchar a volumen bajo.
- Claridad de la voz de NVDA para hacer al lector más nítido sobre música de fondo.
- Presencia vocal para resaltar voces en llamadas, audiolibros o podcasts.
- Filtro anti-fatiga para sesiones largas de escucha.
- Filtro anti-sibilancia para suavizar las eses molestas.
- Refuerzo de subgraves para auriculares con pocos bajos.
- Filtro subsónico para eliminar ruidos de fondo inaudibles que saturan los altavoces.
- Filtro anti-zumbido eléctrico para limpiar interferencias de corriente de 50 o 60 Hz.

### Herramientas y diagnóstico

- Botón Ver registro: muestra los cambios aplicados en el archivo de configuración de Equalizer APO para comprobar su funcionamiento.
- Detección de conflictos: disponible en el menú de Herramientas de NVDA para avisarte si algún atajo configurado coincide con otro complemento.

---

## Novedades de la versión 1.3.1 (13 de septiembre de 2026)

- Mayor ligereza del complemento: se eliminaron dependencias internas que ya no se utilizaban en 5 módulos, reduciendo el código cargado por NVDA al arrancar.
- Documentación técnica interna completa de todos los controles de la ventana de ajustes, el diálogo de descarga, los perfiles de sonido y el generador de tonos de prueba.

## Novedades de la versión 1.3.0 (13 de septiembre de 2026)

- Corrección en la ampliación del sonido estéreo: si subías el ancho estéreo por encima del 100%, el sonido se cancelaba por un error de cálculo y solo se escuchaba por el auricular derecho. Ahora el efecto estéreo se amplía de manera limpia y equilibrada por ambos auriculares sin perder volumen ni calidad.
- Control de volumen automático más inteligente: al combinar varios ajustes y frecuencias a la vez, el complemento calcula con exactitud la ganancia total para que el sonido nunca sature ni distorsione, protegiendo tus oídos y tus auriculares.
- Conservación de tus ajustes al cambiar frecuencias: al subir o bajar los graves o agudos con las teclas rápidas, no se borran los demás valores que tenías configurados en tu ecualizador.
- Guardado seguro de perfiles: tus configuraciones se guardan de forma instantánea y protegida para evitar que se pierdan o dañen si el ordenador se apaga inesperadamente.
- Verificación automática de perfiles guardados: si un perfil guardado estuviera incompleto o dañado, el complemento lo detecta y restaura los valores seguros para que nunca te quedes sin sonido.
- Descarga guiada de Equalizer APO más fiable: la descarga del instalador desde el menú ahora se realiza en bloques continuos, informando del progreso y recuperándose de cortes temporales en la conexión de internet.
- Prueba de orientación de auriculares mejorada: los tonos de comprobación para canal izquierdo, derecho y centro ahora suenan de forma suave, sin chasquidos molestos y sin reproducir el sonido predeterminado de Windows si los auriculares están ocupados.
- Mayor estabilidad en la ventana de ajustes: se corrigieron errores que podían ocurrir al cerrar rápidamente la ventana mientras se aplicaban cambios de sonido.
- Desinstalación limpia: al desinstalar o actualizar el complemento, el sistema elimina automáticamente todos los archivos temporales sin dejar residuos en el equipo.

### Créditos y Agradecimientos
- Motor de procesamiento de audio: Basado en Equalizer APO, creado por jthedering y colaboradores bajo licencia GNU GPL.
- Complemento para NVDA: Desarrollado por Daliana.
