# Paradas de transporte público

[← Volver al contenido](../README.md)

Mexicali no tiene un GTFS, por lo que la capa de equipamiento del IMIP es la fuente local de paradas (categoría de transporte, excluida la terminal interior de carga). Con `replace` en su valor por defecto (falso), se combinan con las paradas identificadas en OpenStreetMap bajo el mismo nombre de destino, `pt_any`.

| Variable en puntos de muestra | Variable de área (valor medido) | Descripción | Región de estudio (Mexicali con Condesa) | Condesa |
|---|---|---|---|---|
| `sp_walk_nearest_node_pt_any` | `avg_walk_dist_pt_any` | Distancia media por la red hasta lo más cercano: Transporte público — red: Caminando | 882 m | 1,432 m |

## Método: práctica

**Recetas:** [R2. Distancia por la red al destino más cercano, censurada](../03_recipes.md#r2)

**Configuración** ([`MX_Mexicali_2025_ULI.yml:168`](../../data/MX_Mexicali_2025_ULI.yml#L168)):

```yaml
pt_any:
  data: MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "equipamiento_category='transp' AND TIPO != 'TERMINAL INTERIOR DE CARGA (CENTRAL DE SERVICIOS DE CARGA)'"
  source: IMIP / CFC
  publication_date: 2026-05-18
  url: ""
  licence: "Provided by IMIP via CFC"
  citation: As per advice from Juan Ernesto Díaz Noguez
```

## Lo usan

[Transporte público a menos de 300 m](public_transport.md)
