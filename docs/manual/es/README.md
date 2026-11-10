# Índice de entornos vivibles para Mexicali

**Manual técnico: recetario de indicadores, dominios e índice**

[English version](../en/README.md)

PDF: [`mexicali_uli_manual_es.pdf`](../pdf/mexicali_uli_manual_es.pdf)

## Contenido

- [Presentación](00_front.md)
- [1. Diseño del estudio](01_design.md)
- [2. Reproducir el análisis](02_reproduce.md)
- [3. Recetas de método](03_recipes.md)
  - [R1. Puntos de muestra y red peatonal](03_recipes.md#r1)
  - [R2. Distancia por la red al destino más cercano, censurada](03_recipes.md#r2)
  - [R3. Acceso por bandas y lejanía de una desamenidad](03_recipes.md#r3)
  - [R4. Diversidad de lo alcanzable](03_recipes.md#r4)
  - [R5. Áreas de servicio en línea recta](03_recipes.md#r5)
  - [R6. Nivel de estrés del tráfico y red ciclista de bajo estrés](03_recipes.md#r6)
  - [R7. Vinculación de indicadores preparados externamente](03_recipes.md#r7)
  - [R8. Earth Engine: vulnerabilidad al calor y grandes espacios verdes](03_recipes.md#r8)
  - [R9. Caminabilidad y su atenuación por confort térmico](03_recipes.md#r9)
  - [R10. Transformaciones: umbrales suaves y escalas escalonadas](03_recipes.md#r10)
  - [R11. Normalización: el Índice Ajustado de Mazziotta–Pareto (AMPI)](03_recipes.md#r11)
  - [R12. Agregación: dominios, indicadores compartidos e índice](03_recipes.md#r12)
  - [R13. De los puntos de muestra a las áreas](03_recipes.md#r13)
  - [R14. Metas congeladas y recálculo de un escenario](03_recipes.md#r14)
- **4. Índice**
  - [Índice de entornos vivibles para Mexicali](entries/uli.md)
  - [Índice de entornos vivibles para Mexicali: Caminabilidad (300 m), sin atenuación por confort térmico](entries/uli_plain.md)
- **5. Dominios**
  - [Entorno medioambiental](entries/domain_ambient_environment.md)
  - [Ambiente construido](entries/domain_built_environment.md)
  - [Desarrollo económico](entries/domain_economic_development.md)
  - [Vivienda](entries/domain_housing.md)
  - [Movilidad y transporte](entries/domain_mobility_transport.md)
  - [Seguridad y protección](entries/domain_safety.md)
  - [Infraestructura social](entries/domain_social_infrastructure.md)
  - [Características sociodemográficas](entries/domain_sociodemographics.md)
- **6. Indicadores**
  - [Espacios azules naturales cercanos](entries/blue_space.md) — *Entorno medioambiental*
  - [Capacidad de adaptación al calor (GUHVI)](entries/adaptive_capability.md) — *Entorno medioambiental*
  - [Exposición al calor (GUHVI)](entries/heat_exposure.md) — *Entorno medioambiental*
  - [Sensibilidad al calor (GUHVI)](entries/heat_sensitivity.md) — *Entorno medioambiental*
  - [Confort térmico diurno](entries/thermal_comfort.md) — *Entorno medioambiental*
  - [Parques a menos de 300 m](entries/parks.md) — *Entorno medioambiental, Ambiente construido*
  - [Gran espacio verde público a menos de 500 m](entries/lpugs.md) — *Entorno medioambiental, Ambiente construido*
  - [Cobertura vegetal (NDVI)](entries/vegetation.md) — *Entorno medioambiental, Ambiente construido*
  - [Proximidad a vialidades principales](entries/major_roads.md) — *Entorno medioambiental, Seguridad y protección*
  - [Alimentos a menos de 1.5 km en bicicleta de bajo estrés](entries/cycle_low_stress_food.md) — *Seguridad y protección, Movilidad y transporte, Ambiente construido*
  - [Tamaño de manzana (perímetro)](entries/block_size.md) — *Ambiente construido, Movilidad y transporte, Seguridad y protección*
  - [Estación de bomberos a menos de 3 km](entries/fire_3km.md) — *Seguridad y protección, Movilidad y transporte, Ambiente construido*
  - [Estación de policía a menos de 2 km](entries/police_2km.md) — *Seguridad y protección, Movilidad y transporte, Ambiente construido*
  - [Caminabilidad (300 m), atenuada por confort térmico](entries/walkability.md) — *Ambiente construido, Movilidad y transporte, Infraestructura social*
  - [A 250 m o más de gasolineras](entries/petrol_250m.md) — *Infraestructura social, Movilidad y transporte, Desarrollo económico*
  - [Tiendas de conveniencia a menos de 300 m](entries/convenience.md) — *Infraestructura social, Movilidad y transporte, Desarrollo económico*
  - [Diversidad de alimentos frescos a 500 m](entries/div_fresh_food_500m.md) — *Infraestructura social, Movilidad y transporte, Desarrollo económico*
  - [Alimentos frescos a menos de 300 m](entries/fresh_food.md) — *Infraestructura social, Movilidad y transporte, Desarrollo económico*
  - [Diversidad de empleos](entries/job_diversity.md) — *Desarrollo económico*
  - [Manufactura a menos de 1 km](entries/manufacturing_1000m.md) — *Desarrollo económico*
  - [Transporte público a menos de 300 m](entries/public_transport.md) — *Movilidad y transporte*
  - [Diversidad de comunidad, cultura y recreación a 500 m](entries/div_ccr_500m.md) — *Infraestructura social*
  - [Comunidad, cultura y recreación a menos de 300 m](entries/ccr_any.md) — *Infraestructura social*
  - [Diversidad de servicios de cuidado a 500 m](entries/div_care_500m.md) — *Infraestructura social*
  - [Servicios de cuidado a menos de 300 m](entries/care_support.md) — *Infraestructura social*
  - [Diversidad educativa a 500 m](entries/div_education_500m.md) — *Infraestructura social*
  - [Diversidad de servicios de salud a 500 m](entries/div_health_500m.md) — *Infraestructura social*
  - [Atención primaria de salud a menos de 300 m](entries/primary_healthcare.md) — *Infraestructura social*
  - [Escuelas primarias a menos de 300 m](entries/primary_school.md) — *Infraestructura social*
- **7. Insumos y subindicadores**
  - [Caminabilidad a 300 m y sus componentes](entries/walkability_components.md)
  - [Confort térmico exterior (UTCI)](entries/utci.md)
  - [Índice Global de Vulnerabilidad Urbana al Calor (GUHVI) y sus insumos](entries/guhvi.md)
  - [Espacio público abierto y grandes espacios verdes públicos](entries/public_open_space.md)
  - [Espacios azules naturales](entries/blue_space_layer.md)
  - [Destinos del DENUE por código SCIAN](entries/denue_destinations.md)
  - [Conjuntos de diversidad y sus subtipos](entries/diversity_sets.md)
  - [Red ciclista por nivel de estrés del tráfico (LTS)](entries/lts_network.md)
  - [Paradas de transporte público](entries/pt_stops.md)
  - [Estaciones de policía y bomberos (línea recta)](entries/emergency_stations.md)
  - [Indicadores de los paquetes de trabajo (vinculados)](entries/work_package_layers.md)
- **Anexos**
  - [Anexo A. Índice de variables](A_variables.md)
  - [Anexo B. Indicadores del tablero general](B_general.md)
  - [Anexo C. Metas y pesos](C_goalposts.md)
  - [Anexo D. Registro de fuentes de datos](D_datasets.md)
  - [Anexo E. Glosario](E_glossary.md)
  - [Anexo F. Referencias](F_references.md)
  - [Anexo G. Indicadores excluidos y pendientes](G_pending.md)
