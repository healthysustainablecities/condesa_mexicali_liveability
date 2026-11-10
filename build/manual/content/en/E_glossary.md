# Appendix E. Glossary

| Term | Spanish | Definition |
|---|---|---|
| AGEB | AGEB (área geoestadística básica) | INEGI's basic census area; median 36 ha in Mexicali. |
| AMPI | AMPI (índice ajustado de Mazziotta–Pareto) | Composite index method re-scaling each indicator against goalposts and penalising imbalance between components (Mazziotta & Pareto 2018) ([R11](03_recipes.md#r11)). |
| Censoring | Censura | Distances are searched only to the largest band (1,500 m walking); a point with nothing within it has no distance and no access. |
| Core measure | Medida central | The variable sheet's grouping of sub-variables (`group`), for example "Daily essential-services access". |
| DENUE | DENUE | INEGI's National Statistical Directory of Economic Units: establishments with SCIAN activity codes. |
| Domain | Dominio | One of the eight domains of the Adapted Urban Liveability Framework; six are scored. |
| Effective weight | Peso efectivo | An indicator's share of the index's mean level, after domain shares and domain weights ([R12](03_recipes.md#r12)). |
| Fraccionamiento | Fraccionamiento | A subdivision, often gated; Condesa has 40. |
| Goalposts | Metas | Ref, Min and Max against which an indicator is re-scaled; frozen goalposts make scenarios comparable ([R14](03_recipes.md#r14)). |
| GUHVI | GUHVI | Global Urban Heat Vulnerability Index (Turner et al. 2025): exposure, sensitivity and adaptive capability. |
| CFC | CFC | Centro para el Futuro de las Ciudades (Tecnológico de Monterrey); source of the Condesa boundaries, lots and updated manzana geometries. |
| IMIP | IMIP | Mexicali's municipal planning institute; source of the facilities layer (public transport stops, police and fire stations), provided via CFC. |
| Lens | Enfoque | The framework's view of an indicator: quality, proximity, diversity, accessibility or presence. |
| LPUGS | LPUGS (gran espacio verde público urbano) | Large public urban green space: public open space ≥ 1 ha with NDVI ≥ 0.2. |
| LTS | LTS (nivel de estrés del tráfico) | Level of traffic stress for cycling, 1 (all ages) to 4 (most stressful) ([R6](03_recipes.md#r6)). |
| Manzana | Manzana | Census block; median 0.71 ha in Mexicali. |
| Penalty | Penalización | `S · cv`, subtracted from a composite's mean so that doing well on one component cannot wholly make up for doing badly on another. |
| Reference (Ref) | Referencia | The study region average of an indicator over all sample points; scores 0. |
| Sample point | Punto de muestra | A location every 30 m along the pedestrian network (and one per Condesa lot) at which indicators are computed ([R1](03_recipes.md#r1)). |
| SCIAN | SCIAN | Sistema de Clasificación Industrial de América del Norte, the North American Industry Classification System as used in Mexico. |
| Soft threshold | Umbral suave | Logistic transform of a distance, 0.5 at the threshold ([R10](03_recipes.md#r10)). |
| Study region | Región de estudio | The Mexicali urban area together with the Condesa development. |
| UTCI | UTCI | Universal Thermal Climate Index (°C): felt temperature from air temperature, radiant temperature, humidity and wind. |
