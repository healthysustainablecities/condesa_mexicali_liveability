# Anexo C. Metas y pesos

Metas y pesos efectivos de cada índice, tal como los escribió el análisis (`data/`). Las metas están en la escala que se puntúa: la puntuación de acceso suave (0 a 1) donde hay umbral, la escala escalonada donde la hay, y si no el valor medido. Ref. es el promedio de la región de estudio y puntúa 0.

## `uli`

Metas resueltas el 2026-09-26 a partir de 154,239 puntos de muestra; método `ampi`, centro 0.

| Indicador | Variable | Dominios (parte del peso) | Se puntúa como | Mín. · Ref. · Máx. | Peso efectivo |
|---|---|---|---|---|---|
| [Exposición al calor (GUHVI)](entries/heat_exposure.md) | `sp_urban_heat_exposure_index` | Entorno medioambiental | tal cual | 0 · 47 · 100 | 2.8% |
| [Sensibilidad al calor (GUHVI)](entries/heat_sensitivity.md) | `sp_urban_heat_sensitivity_index` | Entorno medioambiental | tal cual | 0 · 58 · 100 | 2.8% |
| [Capacidad de adaptación al calor (GUHVI)](entries/adaptive_capability.md) | `sp_urban_heat_adaptive_capability_index` | Entorno medioambiental | tal cual | 0 · 22 · 100 | 2.8% |
| [Espacios azules naturales cercanos](entries/blue_space.md) | `sp_walk_nearest_node_blue_space` | Entorno medioambiental | escala escalonada | 56.9 · 76.9 · 96.9 | 2.8% |
| [Cobertura vegetal (NDVI)](entries/vegetation.md) | `sp_ext_ndvi` | Entorno medioambiental (50%), Ambiente construido (50%) | tal cual | −0.251 · 0.082 · 0.415 | 4.0% |
| [Parques a menos de 300 m](entries/parks.md) | `sp_walk_nearest_node_public_open_space_any` | Entorno medioambiental (50%), Ambiente construido (50%) | acceso suave, umbral de 300 m | −0.197 · 0.299 · 0.796 | 4.0% |
| [Gran espacio verde público a menos de 500 m](entries/lpugs.md) | `sp_access_large_public_green_space_score` | Entorno medioambiental (50%), Ambiente construido (50%) | tal cual | −0.419 · 0.081 · 0.581 | 4.0% |
| [Proximidad a vialidades principales](entries/major_roads.md) | `sp_ext_major_road_length_300m` | Entorno medioambiental (50%), Seguridad y protección (50%) | tal cual | −2,429 · 1,756 · 5,940 | 5.9% |
| [Caminabilidad (300 m), atenuada por confort térmico](entries/walkability.md) | `sp_walk_idx_300_tm` | Ambiente construido (33%), Movilidad y transporte (33%), Infraestructura social (33%) | tal cual | −0.022 · 0.315 · 0.651 | 3.7% |
| [Tamaño de manzana (perímetro)](entries/block_size.md) | `sp_ext_block_perimeter_m` | Ambiente construido (33%), Movilidad y transporte (33%), Seguridad y protección (33%) | tal cual | −3,860 · 856 · 5,572 | 6.2% |
| [Estación de policía a menos de 2 km](entries/police_2km.md) | `sp_euclid_dist_imip_police_station` | Seguridad y protección (33%), Movilidad y transporte (33%), Ambiente construido (33%) | acceso suave, umbral de 2,000 m | 0.115 · 0.611 · 1.108 | 6.2% |
| [Estación de bomberos a menos de 3 km](entries/fire_3km.md) | `sp_euclid_dist_imip_fire_station` | Seguridad y protección (33%), Movilidad y transporte (33%), Ambiente construido (33%) | acceso suave, umbral de 3,000 m | 0.096 · 0.592 · 1.089 | 6.2% |
| [Alimentos a menos de 1.5 km en bicicleta de bajo estrés](entries/cycle_low_stress_food.md) | `sp_cycle_safe_nearest_node_fresh_food_pooled` | Seguridad y protección (33%), Movilidad y transporte (33%), Ambiente construido (33%) | acceso suave, umbral de 1,500 m | 0.059 · 0.555 · 1.052 | 6.2% |
| [Transporte público a menos de 300 m](entries/public_transport.md) | `sp_walk_nearest_node_pt_any` | Movilidad y transporte | acceso suave, umbral de 300 m | −0.433 · 0.064 · 0.561 | 4.2% |
| [Alimentos frescos a menos de 300 m](entries/fresh_food.md) | `sp_walk_nearest_node_denue_fresh_food` | Infraestructura social (33%), Movilidad y transporte (33%), Desarrollo económico (33%) | acceso suave, umbral de 300 m | −0.091 · 0.405 · 0.902 | 3.6% |
| [Diversidad de alimentos frescos a 500 m](entries/div_fresh_food_500m.md) | `sp_walk_diversity_fresh_food_500m` | Infraestructura social (33%), Movilidad y transporte (33%), Desarrollo económico (33%) | tal cual | −0.167 · 0.269 · 0.705 | 3.6% |
| [Tiendas de conveniencia a menos de 300 m](entries/convenience.md) | `sp_walk_nearest_node_denue_food_retail` | Infraestructura social (33%), Movilidad y transporte (33%), Desarrollo económico (33%) | acceso suave, umbral de 300 m | 0.179 · 0.675 · 1.172 | 3.6% |
| [A 250 m o más de gasolineras](entries/petrol_250m.md) | `sp_walk_beyond_denue_petrol_station_250m` | Infraestructura social (33%), Movilidad y transporte (33%), Desarrollo económico (33%) | tal cual | 0.421 · 0.921 · 1.421 | 3.6% |
| [Escuelas primarias a menos de 300 m](entries/primary_school.md) | `sp_walk_nearest_node_denue_primary_school` | Infraestructura social | acceso suave, umbral de 300 m | −0.330 · 0.166 · 0.663 | 1.7% |
| [Diversidad educativa a 500 m](entries/div_education_500m.md) | `sp_walk_diversity_education_500m` | Infraestructura social | tal cual | −0.232 · 0.268 · 0.768 | 1.7% |
| [Atención primaria de salud a menos de 300 m](entries/primary_healthcare.md) | `sp_walk_nearest_node_denue_primary_healthcare` | Infraestructura social | acceso suave, umbral de 300 m | −0.358 · 0.139 · 0.636 | 1.7% |
| [Diversidad de servicios de salud a 500 m](entries/div_health_500m.md) | `sp_walk_diversity_health_care_500m` | Infraestructura social | tal cual | −0.190 · 0.310 · 0.810 | 1.7% |
| [Servicios de cuidado a menos de 300 m](entries/care_support.md) | `sp_walk_nearest_node_denue_care_support` | Infraestructura social | acceso suave, umbral de 300 m | −0.336 · 0.161 · 0.657 | 1.7% |
| [Diversidad de servicios de cuidado a 500 m](entries/div_care_500m.md) | `sp_walk_diversity_care_500m` | Infraestructura social | tal cual | −0.440 · 0.060 · 0.560 | 1.7% |
| [Comunidad, cultura y recreación a menos de 300 m](entries/ccr_any.md) | `sp_walk_nearest_node_denue_ccr_any` | Infraestructura social | acceso suave, umbral de 300 m | −0.077 · 0.420 · 0.916 | 1.7% |
| [Diversidad de comunidad, cultura y recreación a 500 m](entries/div_ccr_500m.md) | `sp_walk_diversity_community_culture_recreation_500m` | Infraestructura social | tal cual | −0.331 · 0.163 · 0.656 | 1.7% |
| [Manufactura a menos de 1 km](entries/manufacturing_1000m.md) | `sp_walk_access_denue_manufacturing_1000m` | Desarrollo económico | tal cual | 0.435 · 0.935 · 1.435 | 5.0% |
| [Diversidad de empleos](entries/job_diversity.md) | `sp_ext_economic_sector_diversity` | Desarrollo económico | tal cual | −0.236 · 0.264 · 0.764 | 5.0% |

## `uli_plain`

Metas resueltas el 2026-09-26 a partir de 154,239 puntos de muestra; método `ampi`, centro 0.

| Indicador | Variable | Dominios (parte del peso) | Se puntúa como | Mín. · Ref. · Máx. | Peso efectivo |
|---|---|---|---|---|---|
| [Exposición al calor (GUHVI)](entries/heat_exposure.md) | `sp_urban_heat_exposure_index` | Entorno medioambiental | tal cual | 0 · 47 · 100 | 2.4% |
| [Sensibilidad al calor (GUHVI)](entries/heat_sensitivity.md) | `sp_urban_heat_sensitivity_index` | Entorno medioambiental | tal cual | 0 · 58 · 100 | 2.4% |
| [Capacidad de adaptación al calor (GUHVI)](entries/adaptive_capability.md) | `sp_urban_heat_adaptive_capability_index` | Entorno medioambiental | tal cual | 0 · 22 · 100 | 2.4% |
| [Confort térmico diurno](entries/thermal_comfort.md) | `sp_utci_day_mean` | Entorno medioambiental | tal cual | 41.938 · 44.949 · 47.960 | 2.4% |
| [Espacios azules naturales cercanos](entries/blue_space.md) | `sp_walk_nearest_node_blue_space` | Entorno medioambiental | escala escalonada | 56.9 · 76.9 · 96.9 | 2.4% |
| [Cobertura vegetal (NDVI)](entries/vegetation.md) | `sp_ext_ndvi` | Entorno medioambiental (50%), Ambiente construido (50%) | tal cual | −0.251 · 0.082 · 0.415 | 3.8% |
| [Parques a menos de 300 m](entries/parks.md) | `sp_walk_nearest_node_public_open_space_any` | Entorno medioambiental (50%), Ambiente construido (50%) | acceso suave, umbral de 300 m | −0.197 · 0.299 · 0.796 | 3.8% |
| [Gran espacio verde público a menos de 500 m](entries/lpugs.md) | `sp_access_large_public_green_space_score` | Entorno medioambiental (50%), Ambiente construido (50%) | tal cual | −0.419 · 0.081 · 0.581 | 3.8% |
| [Proximidad a vialidades principales](entries/major_roads.md) | `sp_ext_major_road_length_300m` | Entorno medioambiental (50%), Seguridad y protección (50%) | tal cual | −2,429 · 1,756 · 5,940 | 5.7% |
| [Caminabilidad (300 m), atenuada por confort térmico](entries/walkability.md) | `sp_walk_idx_300` | Ambiente construido (33%), Movilidad y transporte (33%), Infraestructura social (33%) | tal cual | −10.0 · 0.0 · 10.0 | 3.7% |
| [Tamaño de manzana (perímetro)](entries/block_size.md) | `sp_ext_block_perimeter_m` | Ambiente construido (33%), Movilidad y transporte (33%), Seguridad y protección (33%) | tal cual | −3,860 · 856 · 5,572 | 6.2% |
| [Estación de policía a menos de 2 km](entries/police_2km.md) | `sp_euclid_dist_imip_police_station` | Seguridad y protección (33%), Movilidad y transporte (33%), Ambiente construido (33%) | acceso suave, umbral de 2,000 m | 0.115 · 0.611 · 1.108 | 6.2% |
| [Estación de bomberos a menos de 3 km](entries/fire_3km.md) | `sp_euclid_dist_imip_fire_station` | Seguridad y protección (33%), Movilidad y transporte (33%), Ambiente construido (33%) | acceso suave, umbral de 3,000 m | 0.096 · 0.592 · 1.089 | 6.2% |
| [Alimentos a menos de 1.5 km en bicicleta de bajo estrés](entries/cycle_low_stress_food.md) | `sp_cycle_safe_nearest_node_fresh_food_pooled` | Seguridad y protección (33%), Movilidad y transporte (33%), Ambiente construido (33%) | acceso suave, umbral de 1,500 m | 0.059 · 0.555 · 1.052 | 6.2% |
| [Transporte público a menos de 300 m](entries/public_transport.md) | `sp_walk_nearest_node_pt_any` | Movilidad y transporte | acceso suave, umbral de 300 m | −0.433 · 0.064 · 0.561 | 4.2% |
| [Alimentos frescos a menos de 300 m](entries/fresh_food.md) | `sp_walk_nearest_node_denue_fresh_food` | Infraestructura social (33%), Movilidad y transporte (33%), Desarrollo económico (33%) | acceso suave, umbral de 300 m | −0.091 · 0.405 · 0.902 | 3.6% |
| [Diversidad de alimentos frescos a 500 m](entries/div_fresh_food_500m.md) | `sp_walk_diversity_fresh_food_500m` | Infraestructura social (33%), Movilidad y transporte (33%), Desarrollo económico (33%) | tal cual | −0.167 · 0.269 · 0.705 | 3.6% |
| [Tiendas de conveniencia a menos de 300 m](entries/convenience.md) | `sp_walk_nearest_node_denue_food_retail` | Infraestructura social (33%), Movilidad y transporte (33%), Desarrollo económico (33%) | acceso suave, umbral de 300 m | 0.179 · 0.675 · 1.172 | 3.6% |
| [A 250 m o más de gasolineras](entries/petrol_250m.md) | `sp_walk_beyond_denue_petrol_station_250m` | Infraestructura social (33%), Movilidad y transporte (33%), Desarrollo económico (33%) | tal cual | 0.421 · 0.921 · 1.421 | 3.6% |
| [Escuelas primarias a menos de 300 m](entries/primary_school.md) | `sp_walk_nearest_node_denue_primary_school` | Infraestructura social | acceso suave, umbral de 300 m | −0.330 · 0.166 · 0.663 | 1.7% |
| [Diversidad educativa a 500 m](entries/div_education_500m.md) | `sp_walk_diversity_education_500m` | Infraestructura social | tal cual | −0.232 · 0.268 · 0.768 | 1.7% |
| [Atención primaria de salud a menos de 300 m](entries/primary_healthcare.md) | `sp_walk_nearest_node_denue_primary_healthcare` | Infraestructura social | acceso suave, umbral de 300 m | −0.358 · 0.139 · 0.636 | 1.7% |
| [Diversidad de servicios de salud a 500 m](entries/div_health_500m.md) | `sp_walk_diversity_health_care_500m` | Infraestructura social | tal cual | −0.190 · 0.310 · 0.810 | 1.7% |
| [Servicios de cuidado a menos de 300 m](entries/care_support.md) | `sp_walk_nearest_node_denue_care_support` | Infraestructura social | acceso suave, umbral de 300 m | −0.336 · 0.161 · 0.657 | 1.7% |
| [Diversidad de servicios de cuidado a 500 m](entries/div_care_500m.md) | `sp_walk_diversity_care_500m` | Infraestructura social | tal cual | −0.440 · 0.060 · 0.560 | 1.7% |
| [Comunidad, cultura y recreación a menos de 300 m](entries/ccr_any.md) | `sp_walk_nearest_node_denue_ccr_any` | Infraestructura social | acceso suave, umbral de 300 m | −0.077 · 0.420 · 0.916 | 1.7% |
| [Diversidad de comunidad, cultura y recreación a 500 m](entries/div_ccr_500m.md) | `sp_walk_diversity_community_culture_recreation_500m` | Infraestructura social | tal cual | −0.331 · 0.163 · 0.656 | 1.7% |
| [Manufactura a menos de 1 km](entries/manufacturing_1000m.md) | `sp_walk_access_denue_manufacturing_1000m` | Desarrollo económico | tal cual | 0.435 · 0.935 · 1.435 | 5.0% |
| [Diversidad de empleos](entries/job_diversity.md) | `sp_ext_economic_sector_diversity` | Desarrollo económico | tal cual | −0.236 · 0.264 · 0.764 | 5.0% |
