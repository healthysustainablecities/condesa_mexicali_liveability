# Espacios azules naturales

[← Volver al contenido](../README.md)

El espacio azul se deriva de forma independiente del espacio público abierto, con etiquetas de agua de OpenStreetMap en **polígonos y líneas**: los canales y drenes de Mexicali están mapeados mayormente como líneas y nunca entrarían en un proceso basado en polígonos. Se excluyen albercas, parques acuáticos y elementos de acceso privado. Los polígonos se muestrean en su anillo exterior y las líneas a lo largo; se generan puntos cada 20 m y se retienen los que tienen una calle a menos de 30 m (`blue_space_nodes_30m_line`), hasta los que se mide la distancia a pie.

| Variable en puntos de muestra | Variable de área (valor medido) | Descripción | Región de estudio (Mexicali con Condesa) | Condesa |
|---|---|---|---|---|
| `sp_walk_nearest_node_blue_space` | `avg_walk_dist_blue_space` | Distancia media por la red hasta lo más cercano: Espacio azul natural — red: Caminando | 797 m | 590 m |

## Método: práctica

**Recetas:** [R2. Distancia por la red al destino más cercano, censurada](../03_recipes.md#r2)

**Configuración** ([`MX_Mexicali_2025_ULI.yml:489`](../../data/MX_Mexicali_2025_ULI.yml#L489)):

```yaml
- {name: blue_space, category: blue_space, variant: any, layer: blue_space_nodes_30m_line}
```

**Código (GHSCI):**

- [`process/subprocesses/_06_open_space_areas_setup.py:365`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_06_open_space_areas_setup.py#L365) `blue_space_criteria()`
- [`process/subprocesses/_06_open_space_areas_setup.py:381`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_06_open_space_areas_setup.py#L381) `blue_space_setup()`
- [`process/subprocesses/_06_open_space_areas_setup.py:485`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_06_open_space_areas_setup.py#L485) `blue_space_nodes_setup_query()`

## Lo usan

[Espacios azules naturales cercanos](blue_space.md)
