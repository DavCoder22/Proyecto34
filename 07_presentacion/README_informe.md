# Informe práctico del Examen Complexivo

Este directorio contiene el informe escrito solicitado en la sección 9 de la guía metodológica del Examen Complexivo, con el formato de los lineamientos APA 7 de la Universidad Central del Ecuador.

## Archivos

- `Informe_Practico_APA.docx`: documento editable.
- `Informe_Practico_APA.pdf`: versión final para entrega.
- `datos_portada.json`: datos de portada y firmas. Reemplazar los placeholders antes de la entrega.
- `assets/`: figuras y sello institucional de referencia.
- `../evidencias/`: capturas de pantalla utilizadas en el Anexo E (Jupyter, staging, Neon, calidad y dashboard).
- `build_informe.py`: script que recalcula cifras, genera figuras, arma el DOCX y actualiza el índice y las listas.

## Regeneración

Desde la raíz del repositorio:

```bash
.venv/bin/python 07_presentacion/build_informe.py
```

El script consulta `03_dw/dw.db` y `06_calidad/`, genera las figuras y escribe el DOCX. La conversión a PDF se realiza con LibreOffice. Si el equipo no tiene instaladas las fuentes de Microsoft, LibreOffice sustituye Times New Roman y Arial por Liberation Serif y Liberation Sans, que son métricamente compatibles. El DOCX conserva la especificación de Times New Roman y Arial para abrirlo en Word.

Si LibreOffice presenta un error de `libboost_locale`, el script crea un enlace temporal en `/tmp/lo_libs` para resolver la dependencia sin modificar el sistema.

## Antes de entregar

1. Verificar `datos_portada.json` con los nombres, la cédula, el correo, los datos del tutor, la fecha de aprobación y los datos del componente.
2. Regenerar el documento para que el índice y las listas reflejen la paginación final.
3. Revisar las páginas de Derechos de autor y Aprobación del tutor.
4. Revisar la firma de la página de Derechos de autor (`evidencias/firma.png`) y el sello de la portada (`assets/sello_uce.png`).
5. Firmar electrónicamente la página de Aprobación del tutor.
6. Adjuntar la certificación de traducción del abstract si la carrera la exige.

## Estructura del informe

- Preliminares: portada, datos del componente, derechos de autor, aprobación del tutor, tabla de contenidos, listas de tablas, figuras y anexos, resumen y abstract.
- Cuerpo: introducción, teoría, metodología experimental, análisis y resultados, discusión, conclusiones, recomendaciones y referencias.
- Complementarios: anexos A-E. El Anexo E reúne las capturas de evidencias del proceso ETL, la carga en Neon y el dashboard en Apache Superset.

No se incluyeron dedicatoria ni agradecimiento, conforme a la indicación de dejar solo las páginas obligatorias.

## Dependencias usadas

- Python 3.10 o superior.
- `pandas`, `openpyxl`, `python-docx`, `matplotlib`, `pillow`.
- LibreOffice y `poppler-utils` para la conversión y verificación del PDF.

## Presentaciones

- `Presentacion_Defensa_Complexivo_UCE.pptx`: versión ejecutiva para la defensa (23 diapositivas).
- `Presentacion_Estudio_Complexivo_UCE.pptx`: versión completa de estudio (57 diapositivas, incluye marco teórico, glosario y simulación de jurado).
- `PlantillaoficialUCE.pptx`: plantilla institucional usada como base (fondos, tema y estilos).
- `build_presentaciones.py`: reconstruye ambas presentaciones.
- `pres_common.py`, `build_defensa.py`, `build_estudio.py`: utilidades, contenido y estructura de cada versión.

Para regenerarlas desde la raíz del repositorio:

```bash
.venv/bin/python 07_presentacion/build_presentaciones.py
```
