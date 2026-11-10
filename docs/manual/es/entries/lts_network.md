# Red ciclista por nivel de estrés del tráfico (LTS)

[← Volver al contenido](../README.md)

Cada tramo de la red de OpenStreetMap recibe un tipo de infraestructura ciclista (vía exclusiva, sendero compartido, carril separado, carril simple, calle compartida o ninguna), una velocidad (`maxspeed`, o una velocidad por defecto según la clase de vía) y un tránsito diario promedio supuesto (local 750, terciaria 3,000, secundaria 10,000). El LTS se asigna en cascada; gana la primera regla que se cumple:

| LTS | Reglas (resumen de `assign_lts`) |
|---|---|
| 1 | vía exclusiva o sendero compartido; vías fuera de calle; carril separado ≤ 50 km/h; carril simple en vía local/terciaria/secundaria con TDPA ≤ 10,000 y ≤ 30 km/h; vía local con TDPA ≤ 2,000 y ≤ 30 km/h |
| 2 | carril separado ≤ 60; carril simple ≤ 50 (TDPA ≤ 10,000); carril simple en vía primaria (o TDPA > 10,000) ≤ 40; vía local con TDPA ≤ 750 y ≤ 50 o TDPA ≤ 2,000 y ≤ 40; local/terciaria con TDPA ≤ 3,000 y ≤ 30 |
| 3 | carril simple ≤ 60; local con TDPA ≤ 750 y ≤ 60; local/terciaria con TDPA ≤ 3,000 y ≤ 50; secundaria/primaria (o TDPA > 3,000) ≤ 40 |
| 4 | cualquier otro caso |

La red de **bajo estrés** es la de los tramos con LTS ≤ 2 donde se permite circular en bicicleta o desmontar y empujarla; su costo es la longitud (triplicada en los tramos donde hay que desmontar).

| Variable en puntos de muestra | Variable de área (valor medido) | Descripción | Región de estudio (Mexicali con Condesa) | Condesa |
|---|---|---|---|---|
| `sp_cycle_safe_nearest_node_fresh_food_pooled` | `avg_cycle_dist_safe_fresh_food_pooled` | Distancia media por la red hasta lo más cercano: Alimentos frescos o tienda de conveniencia (OSM) — red: Ruta de bajo estrés (LTS 1–2) | 826 m | 1,025 m |

## Método: práctica

**Recetas:** [R6. Nivel de estrés del tráfico y red ciclista de bajo estrés](../03_recipes.md#r6)

**Configuración** ([`MX_Mexicali_2025_ULI.yml:698`](../../data/MX_Mexicali_2025_ULI.yml#L698)):

```yaml
cycling_indicators: true
```

**Código (GHSCI):**

- [`process/subprocesses/_cycling_lts_network.py:432`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_lts_network.py#L432) `classify_cycleway()`
- [`process/subprocesses/_cycling_lts_network.py:491`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_lts_network.py#L491) `assign_adt()`
- [`process/subprocesses/_cycling_lts_network.py:546`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_lts_network.py#L546) `assign_lts()`
- [`process/subprocesses/_cycling_lts_network.py:607`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_lts_network.py#L607) `add_impedance()`
- [`process/subprocesses/_cycling_accessibility.py:469`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_accessibility.py#L469) `cycling_poi_distance()`

## Lo usan

[Alimentos a menos de 1.5 km en bicicleta de bajo estrés](cycle_low_stress_food.md)
