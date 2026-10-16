# Audio Equalizer

* Autor: Daliana
* Versión: 1.6.4
* Compatibilidad con NVDA: 2023.1 en adelante
* Descarga de la versión estable: https://github.com/daliana907/audioEqualizer

Este complemento es un ecualizador paramétrico completo de 31 bandas y procesador de efectos acústicos, diseñado específicamente para ser manejado al 100% mediante lectores de pantalla, integrándose perfectamente en NVDA.

A diferencia de otros ecualizadores que dependen de interfaces gráficas inaccesibles o que obligan a usar el ratón para mover controles deslizantes, Audio Equalizer te permite ajustar cada frecuencia de forma milimétrica utilizando atajos de teclado y ventanas nativas.

Para funcionar, el complemento se enlaza al motor de procesamiento de audio de código abierto Equalizer APO. A través de este motor, Audio Equalizer es capaz de modificar el sonido de todo tu sistema en tiempo real.

Sus capacidades incluyen:

*   Ecualización de 31 bandas: Permite realzar o atenuar frecuencias específicas que van desde los bajos más profundos (20 Hz) hasta los agudos más cristalinos (20 kHz), pudiendo guardar tus ajustes como perfiles personalizados.
*   Control de ganancia y preamplificación: Regula el volumen maestro y previene la saturación o recorte del audio.
*   Gestión Estéreo y Paneo: Ajustes para centrar el sonido, ensanchar la imagen estéreo o cambiar el balance entre el auricular izquierdo y derecho, ideal para personas con asimetría auditiva.
*   Efecto 3D Espacial (Haas): Amplitud acústica envolvente e inmersiva que ensancha el campo de sonido recreando la reverberación y el retardo natural de una sala física.
*   Modo Radar Posicional (eSports): Filtro de precisión posicional 360 grados que combina un cruce de canales (crossfeed) con una ecualización extrema tipo lupa en los agudos (+6 dB en 4 kHz) para amplificar pasos y detalles del entorno en juegos competitivos.
*   Preamplificación Manual Extrema: Ahora puedes desactivar el preamplificador automático y empujar el volumen crudo de tu sistema hasta +20 dB para contenidos que se grabaron muy bajos.
*   Filtros de Accesibilidad y Fatiga: Funciones especiales como compresión de sonidos estridentes (Anti-Sibilancia), mitigación de ruidos eléctricos graves (Ground Hum) y reducción de frecuencias que causan cansancio tras muchas horas de escucha (Anti-Fatiga).
*   Voz de NVDA: Cuenta con un filtro exclusivo que aísla y potencia las frecuencias centrales donde habita la voz de NVDA, permitiendo que el lector resalte por encima de la música o de juegos muy ruidosos sin tener que bajar su volumen de forma general.

## Novedades en la versión 1.6.4

*   Canales y sonido envolvente: lista de configuración de canales con niveles de central, subwoofer y traseros.
*   Ancho estéreo con la sintaxis que entiende el motor de sonido.
*   Perfiles con ancho en valor normal y registro honesto del estado real.

## Novedades en la versión 1.6.3

*   **Prevención de saltos de foco y auto-apertura del menú**: mnemónico único 'Ecualizador de &Audio' (tecla A) en el menú Herramientas, eliminando la colisión con la letra E y el despliegue automático involuntario al navegar con el teclado.
*   **Corrección de lectura en nvda.ini**: resolución del fallo interno de desempaquetado de diccionario al leer AggregatedSection de NVDA en el arranque, garantizando la carga fidedigna del estado guardado.
*   **Limpieza preventiva de submenús** al recargar complementos sin reiniciar NVDA.

## Novedades en la versión 1.6.2

*   **Estabilidad de menús**: corrección y blindaje del ciclo de vida del submenú en el menú Herramientas de NVDA, garantizando la desvinculación limpia de eventos y eliminación segura al reiniciar o recargar complementos.
*   **Prevención de activaciones involuntarias**: texto de ayuda accesible y gestión precisa de identificadores para evitar saltos de foco o aperturas accidentales.

## Novedades en la versión 1.6.1

*   **Persistencia indestructible**: Corrección definitiva del problema donde el ecualizador amanecía apagado o se cambiaba a perfil "sin personalizar" al reiniciar NVDA o el equipo.
*   **Doble capa de guardado**: La configuración ahora se guarda forzando la escritura inmediata a disco (`config.conf.save()`) y manteniendo simultáneamente un archivo de respaldo atómico JSON tolerante a cierres forzados (`NVDA + Control + F3`).
*   **Lectura resiliente y a prueba de fallos**: Protección contra listas de ganancias serializadas como cadenas por ConfigObj y conversiones erróneas que forzaban la restauración de valores por defecto.
*   **Guardado en botón Aplicar**: Al presionar el botón "Aplicar" en la ventana de ajustes, los cambios se guardan permanentemente en disco además de aplicarse acústicamente en tiempo real.
*   **Restauración automática de sobreescrituras**: Los perfiles de fábrica modificados por el usuario se cargan automáticamente al iniciar NVDA.

## Novedades en la versión 1.6.0

*   Corrección integral de compatibilidad en Windows 10 y Windows 11: resolución de fallos y excepciones internas (`TypeError` / `AttributeError`) con los nuevos atributos espaciales.
*   Registro y auditoría (`write_audit_log`) completamente protegido contra argumentos imprevistos y enriquecido con el estado en vivo de las mejoras 3D y Radar.
*   Casilla interactiva para activar/desactivar el Efecto 3D Espacial en la ventana de ajustes y nuevos scripts configurables en Gestos de entrada de NVDA.
*   Descargador de Equalizer APO seguro: conexión mediante contexto SSL verificado para evitar problemas de certificación en Windows 11 y Python 3.12+.
*   Corrección en las sobreescrituras de fábrica (`factory_overrides`) y desinstalación limpia que elimina todos los archivos residuales.
*   Paso automático a perfil "Personalizado" al tocar cualquier control acústico o espacial.

## Cómo usarlo

El panel de control principal se abre mediante atajos de teclado o desde el menú de herramientas de NVDA. Dentro de este panel, podrás saltar entre secciones para ajustar las bandas de frecuencia, activar los efectos especiales o probar el sonido de cada auricular por separado.

El complemento no asigna gestos por defecto para evitar conflictos; puedes asignar tus propios atajos en el menú NVDA > Preferencias > Gestos de entrada, categoría "Audio Equalizer".

Además, cuenta con una lista de perfiles acústicos de fábrica y te permite guardar, nombrar y borrar los tuyos propios de forma ilimitada.

## Canales y sonido envolvente

La ventana incluye una lista de configuración de canales (estéreo, 5.1, 7.1, cuadrafónico y mezclas inteligentes a estéreo) con niveles de canal central, subwoofer y traseros. En equipos estéreo, los niveles de central y subwoofer actúan como realce de voces y de graves; el nivel de traseros necesita contenido multicanal. Las mezclas inteligentes actúan con películas o juegos con sonido multicanal.

## Requisito Obligatorio

Para que el complemento surta efecto, es indispensable tener instalado en tu computadora el programa gratuito Equalizer APO. Una vez instalado, debes abrir su herramienta "Configurator" y marcar allí la tarjeta de sonido, los altavoces o auriculares que quieras ecualizar. Luego, reinicias tu equipo y el complemento se encargará de darle las instrucciones de sonido a ese programa por detrás.

## Seguridad y recuperación

*   Tus perfiles y el estado activo se validan antes de cargarse. Si un archivo de ajustes se daña, el complemento recupera valores seguros en lugar de impedir que NVDA arranque.
*   Al modificar perfiles de fábrica, el complemento conserva una copia fechada de las modificaciones antes de sustituirlas.
*   Órdenes de canales: el ancho estéreo, mono, inversión, 3D y radar se mandan al motor de sonido. En algunos auriculares USB pueden cortar el audio; si pasa, deja el ancho en 100.
*   La descarga de Equalizer APO usa conexión segura, tiempo de espera, reintentos y comprobación del archivo descargado. Puedes cancelarla desde su ventana.
*   Las opciones Radar y sonido 3D no se activan juntas, porque son efectos alternativos.
*   Si Equalizer APO requiere permisos para actualizar su configuración, NVDA lo anuncia en vez de repetir el error en silencio.

## Créditos de terceros

*   Equalizer APO (https://sourceforge.net/projects/equalizerapo) por jthedering y colaboradores, bajo GNU GPLv2.

## Créditos

Desarrollado y mantenido por Daliana, operando sobre la tecnología de procesamiento acústico de código abierto Equalizer APO (https://sourceforge.net/projects/equalizerapo).

## Licencia y derechos de autor

Este complemento está protegido por derechos de autor y se distribuye bajo los términos de la Licencia Pública General de GNU (GPL), versión 2 o posterior. Eres libre de usar, modificar y distribuir este software bajo dichas condiciones. Puedes consultar el texto completo de la licencia en: https://www.gnu.org/licenses/gpl-2.0.html

Aclaración sobre el uso de Inteligencia Artificial: Para programar partes de la lógica interna de este complemento y para redactar estos manuales me apoyé en herramientas de Inteligencia Artificial, tal como sugieren declarar las reglas de publicación de NVDA. De todos modos, cada línea de código y cada función fueron dirigidas, revisadas y probadas a fondo por mí.
