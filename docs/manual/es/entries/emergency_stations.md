# Estaciones de policía y bomberos (línea recta)

[← Volver al contenido](../README.md)

Las estaciones se leen de la capa de equipamiento del IMIP, cada especificación con su propio archivo y filtro, recortadas a la región de estudio ampliada por su distancia máxima y fuera de la región de exclusión (California). La cobertura se mide en línea recta porque los servicios de emergencia no siguen las banquetas.

| Variable en puntos de muestra | Variable de área (valor medido) | Descripción | Región de estudio (Mexicali con Condesa) | Condesa |
|---|---|---|---|---|
| `sp_euclid_dist_imip_police_station` | `avg_euclid_dist_imip_police_station` | Distancia en línea recta a la estación de policía más cercana (m) | 1,406 m | 4,156 m |
| `sp_euclid_dist_imip_fire_station` | `avg_euclid_dist_imip_fire_station` | Distancia en línea recta a la estación de bomberos más cercana (m) | 2,297 m | 6,371 m |

- **`imip_police_station`** (Police stations (IMIP)): `MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "TIPO = 'INSTALACIONES POLICIALES'"`; distancias [15000], max_distance 45000. 27 police facilities in the IMIP equipamiento layer (administración pública). (IMIP / CFC; Provided by IMIP via CFC)
- **`imip_fire_station`** (Municipal fire stations (IMIP)): `MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "TIPO = 'ESTACION DE BOMBEROS MUNICIPAL'"`; distancias [75000]. 10 municipal fire stations in the IMIP equipamiento layer (administración pública). (IMIP / CFC; Provided by IMIP via CFC)

## Método: práctica

**Recetas:** [R5. Áreas de servicio en línea recta](../03_recipes.md#r5)

**Configuración** ([`MX_Mexicali_2025_ULI.yml:679`](../../data/MX_Mexicali_2025_ULI.yml#L679)):

```yaml
euclidean:
  destinations:
    - name: imip_police_station
      dest_name_full: Police stations (IMIP)
      data: MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "TIPO = 'INSTALACIONES POLICIALES'"
      distances: [15000]
      max_distance: 45000
      source: IMIP / CFC
      licence: Provided by IMIP via CFC
      notes: 27 police facilities in the IMIP equipamiento layer (administración pública).
    - name: imip_fire_station
      dest_name_full: Municipal fire stations (IMIP)
      data: MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "TIPO = 'ESTACION DE BOMBEROS MUNICIPAL'"
      distances: [75000]
      source: IMIP / CFC
      licence: Provided by IMIP via CFC
      notes: 10 municipal fire stations in the IMIP equipamiento layer (administración pública).
```

**Código (GHSCI):**

- [`process/subprocesses/_euclidean_accessibility.py:66`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_euclidean_accessibility.py#L66) `resolve_spec()`
- [`process/subprocesses/_euclidean_accessibility.py:177`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_euclidean_accessibility.py#L177) `import_destinations()`
- [`process/subprocesses/_euclidean_accessibility.py:247`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_euclidean_accessibility.py#L247) `nearest_distances()`

## Lo usan

[Estación de bomberos a menos de 3 km](fire_3km.md), [Estación de policía a menos de 2 km](police_2km.md)
