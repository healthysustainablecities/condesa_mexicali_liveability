# 2. Reproducir el análisis

Esta sección es la guía de ejecución usada para Mexicali y Condesa, desde los insumos preparados hasta el tablero publicado y este manual. Los comandos se ejecutan en el contenedor de GHSCI con Earth Engine (`ghsci-ee`, imagen `globalhealthyliveablecities/global-indicators:v{{fact:software_environment}}.ee`, directorio de trabajo `/home/ghsci/process`) o en el equipo anfitrión, según se indica.

## Panorama

```text
insumos (INEGI, DENUE, IMIP, OSM, GHS-POP, CFC, paquetes de trabajo)
  │  scripts de preparación (CFC, áreas de referencia)
  ▼
configuración de la región  MX_Mexicali_2025_ULI.yml
  │  análisis (_00 … _12)  ─────────────►  base de datos PostGIS mx_mexicali_2025_uli
  │     _07 puntos de muestra, _11 acceso a pie, áreas en línea recta,
  │     LTS ciclista, Earth Engine (GUHVI, LPUGS), _12 agregación →
  │     indicadores vinculados → variantes de caminabilidad → índices compuestos
  ▼
generate  ─────►  GeoPackage, CSV, diccionario de datos, metadatos, reportes
export_dashboard ─►  manifest / indicators / stats / distributions + capas
  │  build_tiles.sh (tippecanoe) → deploy.sh
  ▼
tablero (sitio estático)    build_results_geopackage.py → GeoPackage de resultados
technical_report.py → PDF    build/manual/manual.py → este manual
```

## 1. Preparar los insumos (anfitrión o contenedor)

| Paso | Script | Produce |
|---|---|---|
| Región de estudio y capas de región | `process/data/MX/CFC/build_uli_boundaries.py` | la región de estudio disuelta (`INEGI-02l-NOMGEO-Mexicali-Condesa-Fraccionamientos.geojson`) y `mexicali_uli_boundaries.gpkg` (`region_mexicali`, `region_condesa`) |
| Manzanas | `process/data/MX/CFC/build_manzanas.py` | `mexicali_manzanas.gpkg`: manzanas del INEGI 2020 con geometrías del CFC y claves sintéticas `S` para 16 manzanas de Condesa sin clave |
| Puntos de muestra de los lotes de Condesa | `process/data/MX/CFC/build_condesa_sample_points.py` | `condesa_lot_sample_points.gpkg`: un punto por lote, para ajustarlo a la red |
| Áreas de referencia | `Mexicali Liveability/build/build_reference_areas.py` | `geography/mexicali_reference_areas.gpkg`: las seis capas de referencia que usan los paquetes de trabajo y la vinculación |

El DENUE (mayo de 2026), la capa de equipamiento del IMIP, el mosaico GHS-POP 2025, el extracto de Geofabrik, el GeoPackage de UTCI (paquete de trabajo 2) y `final_indicators.gpkg` (paquetes de trabajo) se usan tal como se entregaron; sus rutas están en la configuración ([Anexo D](D_datasets.md)).

## 2. Ejecutar el análisis (contenedor)

La configuración de la región está junto a sus datos, en `process/data/MX/MX_Mexicali_2025_ULI.yml`. En el contenedor, pase su ruta y no el nombre clave, pues un archivo de configuración suelto en `data/MX` no se encuentra por su nombre clave:

```bash
python analysis.py data/MX/MX_Mexicali_2025_ULI.yml
```

o, en Python:

```python
import ghsci
r = ghsci.Region('data/MX/MX_Mexicali_2025_ULI.yml')
r.analysis()
```

El proceso ejecuta `_00` a `_12` en secuencia ({{code:analysis.py:analysis}}). Para esta región agrega:

- **Puntos de muestra** en áreas sin población y uno por lote de Condesa ([R1](03_recipes.md#r1)).
- **Acceso a pie** a cada destino configurado a 300, 500, 1,000 y 1,500 m, los conjuntos de diversidad y los centros de actividad ([R2](03_recipes.md#r2)–[R4](03_recipes.md#r4)).
- **Áreas de servicio en línea recta** a estaciones de policía y bomberos ([R5](03_recipes.md#r5)).
- **Nivel de estrés del tráfico ciclista** ([R6](03_recipes.md#r6)).
- **Earth Engine:** GUHVI y grandes espacios verdes públicos ([R8](03_recipes.md#r8)), que requieren el contenedor `.ee` y una cuenta de Earth Engine autenticada.
- **En `_12`, después de la agregación:**
  - indicadores vinculados: UTCI y los indicadores de los paquetes de trabajo ([R7](03_recipes.md#r7));
  - variantes de caminabilidad ([R9](03_recipes.md#r9));
  - los índices compuestos `uli` y `uli_plain` ([R10](03_recipes.md#r10)–[R13](03_recipes.md#r13)).

Una ejecución completa toma varias horas. El avance se registra en `process/data/_study_region_outputs/MX_Mexicali_2025_ULI/__Mexicali__MX_Mexicali_2025_ULI_processing_log.txt`.

El índice compuesto puede volver a puntuarse sin repetir todo el proceso, por ejemplo contra metas congeladas ([R14](03_recipes.md#r14)):

```python
r.composite_index(goalposts='…/MX_Mexicali_2025_ULI_composite_uli_parameters.yml')
```

## 3. Generar resultados (contenedor)

```python
r.generate()
```

escribe el GeoPackage, los CSV por escala, el diccionario de datos, los metadatos ISO 19115, los mapas y los reportes estándar de GHSCI en la carpeta de resultados de la región.

## 4. Exportar el tablero (contenedor y luego anfitrión)

```bash
# contenedor: capas, manifiesto, estadísticas, vocabulario (tableros combinado y general)
/env/bin/python subprocesses/_export_dashboard.py "data/MX/MX_Mexicali_2025_ULI.yml"
/env/bin/python subprocesses/_export_dashboard.py "data/MX/MX_Mexicali_2025_ULI.yml" --type=general
# anfitrión, en Mexicali Liveability/dashboard: archivos PMTiles y despliegue
docker build -t tippecanoe:local build/
bash build/build_tiles.sh mexicali mexicali_general
bash build/deploy.sh mexicali mexicali_general
```

Los intermedios grandes se guardan fuera de OneDrive (`/tmp/ghsci-dashboard`). Los cambios de nombres, temas, clases o textos solo requieren `--no-layers`. Todo el texto en pantalla se edita en `dashboard/data/mexicali/text.json`.

## 5. GeoPackage de resultados y reportes

```bash
# contenedor: valores a precisión completa por escala de referencia, con diccionario bilingüe
python "data/MX/Mexicali Liveability/build/build_results_geopackage.py" /export/mexicali
# anfitrión: el documento técnico del tablero (Edge sin interfaz)
python dashboard/build/technical_report.py
# anfitrión: este manual
python build/manual/manual.py
```

## 6. Respaldar y restaurar la base de datos

```python
r.dump(path='E:/backups')                # respaldo en formato personalizado con un archivo .dump.yml
ghsci.restore('…/mx_mexicali_2025_uli_AAAAMMDD.dump')
```

La base de datos del análisis del 26 de septiembre de 2026 está respaldada como `mx_mexicali_2025_uli_20260926.dump` (231 MB; los pasos de restauración están en el `.dump.txt` junto a ella).

## Dificultades encontradas en este proyecto

- **Fecha de la red.** Hasta el 26 de septiembre de 2026, la consulta a Overpass se fijaba al inicio de la fecha de publicación del extracto, lo que omitía calles de Condesa mapeadas esa mañana (26 calles; unos 1,200 lotes sin estimaciones). `_03` usa ahora la marca de tiempo de replicación del extracto.
- **Ruta de la región.** En el contenedor, `ghsci.Region('MX_Mexicali_2025_ULI')` no encuentra el archivo suelto de `data/MX`; pase su ruta.
- **Archivo de parámetros.** Si el usuario del contenedor no puede escribir en la carpeta de resultados, los parámetros del índice quedan registrados igualmente como comentario de la tabla `sample_points_composite`.
- **OneDrive.** Mantenga los mosaicos temporales y los respaldos de la base de datos fuera de la carpeta sincronizada.
- **Longitud de los identificadores.** PostgreSQL trunca los identificadores de más de 63 caracteres, por lo que los nombres derivados (por ejemplo, de los conjuntos de diversidad) se mantienen cortos: `community_culture_rec`.
