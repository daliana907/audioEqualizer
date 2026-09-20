# Audio Equalizer

* Autor: Daliana
* Compatibilidad con NVDA: 2023.1 en adelante
* Descarga de la versión estable: https://github.com/daliana907/audioEqualizer

Este complemento es un ecualizador paramétrico completo de 31 bandas y procesador de efectos acústicos, diseñado específicamente para ser manejado al 100% mediante lectores de pantalla, integrándose perfectamente en NVDA.

A diferencia de otros ecualizadores que dependen de interfaces gráficas inaccesibles o que obligan a usar el ratón para mover controles deslizantes, Audio Equalizer te permite ajustar cada frecuencia de forma milimétrica utilizando atajos de teclado y ventanas nativas.

Para funcionar, el complemento se enlaza al motor de procesamiento de audio de código abierto Equalizer APO. A través de este motor, Audio Equalizer es capaz de modificar el sonido de todo tu sistema en tiempo real.

Sus capacidades incluyen:

*   Ecualización de 31 bandas: Permite realzar o atenuar frecuencias específicas que van desde los bajos más profundos (20 Hz) hasta los agudos más cristalinos (20 kHz), pudiendo guardar tus ajustes como perfiles personalizados.
*   Control de ganancia y preamplificación: Regula el volumen maestro y previene la saturación o recorte del audio.
*   Gestión Estéreo y Paneo: Ajustes para centrar el sonido, ensanchar la imagen estéreo o cambiar el balance entre el auricular izquierdo y derecho, ideal para personas con asimetría auditiva.
*   Filtros de Accesibilidad y Fatiga: Funciones especiales como compresión de sonidos estridentes (Anti-Sibilancia), mitigación de ruidos eléctricos graves (Ground Hum) y reducción de frecuencias que causan cansancio tras muchas horas de escucha (Anti-Fatiga).
*   Voz de NVDA: Cuenta con un filtro exclusivo que aísla y potencia las frecuencias centrales donde habita la voz de NVDA, permitiendo que el lector resalte por encima de la música o de juegos muy ruidosos sin tener que bajar su volumen de forma general.

## Cómo usarlo

El panel de control principal se abre mediante atajos de teclado o desde el menú de herramientas de NVDA. Dentro de este panel, podrás saltar entre pestañas para ajustar las bandas de frecuencia, activar los efectos especiales o probar el sonido de cada auricular por separado.

Además, cuenta con una lista de perfiles acústicos de fábrica y te permite guardar, nombrar y borrar los tuyos propios de forma ilimitada.

## Requisito Obligatorio

Para que el complemento surta efecto, es indispensable tener instalado en tu computadora el programa gratuito Equalizer APO. Una vez instalado, debes abrir su herramienta "Configurator" y marcar allí la tarjeta de sonido, los altavoces o auriculares que quieras ecualizar. Luego, reinicias tu equipo y el complemento se encargará de darle las instrucciones de sonido a ese programa por detrás.

## Créditos

Desarrollado y mantenido por Daliana, operando sobre la tecnología de procesamiento acústico de código abierto Equalizer APO (https://sourceforge.net/projects/equalizerapo).

## Licencia y derechos de autor

Este complemento está protegido por derechos de autor y se distribuye bajo los términos de la Licencia Pública General de GNU (GPL), versión 2 o posterior. Eres libre de usar, modificar y distribuir este software bajo dichas condiciones. Puedes consultar el texto completo de la licencia en: https://www.gnu.org/licenses/gpl-2.0.html

Aclaración sobre el uso de Inteligencia Artificial: Para programar partes de la lógica interna de este complemento y para redactar estos manuales me apoyé en herramientas de Inteligencia Artificial, tal como sugieren declarar las reglas de publicación de NVDA. De todos modos, cada línea de código y cada función fueron dirigidas, revisadas y probadas a fondo por mí.
