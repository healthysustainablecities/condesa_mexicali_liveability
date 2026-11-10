# About this manual

**{{title}}** — {{subtitle}}

| | |
|---|---|
| Project | Mexicali Urban Liveability Index (*Índice de entornos vivibles para Mexicali*), Mexicali and the Condesa district, Baja California, Mexico |
| Project team | Carl Higgs (RMIT University), Eugen Resendiz, Juan Ernesto Díaz Noguez and the team from Tecnológico de Monterrey |
| Funding | Tecnológico de Monterrey, 2026 |
| Software | Global Healthy and Sustainable City Indicators (GHSCI) {{fact:software_version}} (environment {{fact:software_environment}}), `mexicali` branch ([`{{fact:commit_short}}`]({{fact:commit_url}})) |
| Analysis run | {{fact:run_date}}; composite goalposts resolved {{fact:goalposts_created}} from {{fact:sample_points}} sample points |
| Manual built | {{fact:built}} from the ULI repository at `{{fact:site_commit}}` |
| Status | Draft for review by the project team. Spanish text drafted for review by Eugen Resendiz and Juan Ernesto Díaz Noguez; where the indicator register gives a rationale only in English, the Spanish edition marks its translation as preliminary. |
| Licence | This manual (text, maps and tables): [CC BY 4.0](../LICENSE.md). The code that builds it, and the rest of the repository: MIT. Input datasets keep their own licences ([Appendix D](D_datasets.md)), and maps and values derived from them remain subject to those terms where they impose conditions (for example, UTCI was modelled with FABDEM terrain, CC BY-NC-SA 4.0). |

**Suggested citation.** Higgs, C., Resendiz, E., Díaz Noguez, J. E. and the Tecnológico de Monterrey team (2026). *Mexicali Urban Liveability Index: technical manual.* Tecnológico de Monterrey and RMIT University. https://github.com/healthysustainablecities/condesa_mexicali_liveability

## What this manual is for

The Mexicali Urban Liveability Index (ULI) summarises how well the everyday environment of each location in Mexicali and the Condesa district supports a healthy, liveable life. It combines 28 indicators across six domains of the Adapted Urban Liveability Framework into one composite measure, for sample points along the pedestrian network, and summarises them for the 100 m grid, census areas (AGEB), blocks (manzanas), and Condesa's lots and subdivisions.

This manual is the **cookbook** for that work. It is written for a team re-implementing the methods, in particular in Reimagina Urbano, where indicators would be recalculated on the fly as environmental conditions change. It also serves as the project's technical record. For each indicator, sub-indicator, domain score and the index itself it gives:

- **identity:** names, variables at each scale, domains and weights;
- **rationale and interpretation:** why it matters, according to the project register, and how to read it;
- **data sources:** the configured records of every dataset it reads, with cross-references to upstream entries;
- **method:** the theory (formulae) and the practice (configuration, GHSCI functions, recalculation);
- **results:** a concise summary of the distribution for the study region (Mexicali, Condesa included) and for Condesa;
- **map:** manzanas across the study region, with Condesa's lots, a legend, scale bar and north arrow.

## How to read an entry

Recipes (R1–R14, [section 3](03_recipes.md)) describe each shared method once; entries cite them. Code references link to the exact line on GitHub at the commit given above. Configuration references point to the copy of the region configuration published with this manual ([`data/{{fact:config_name}}`](../data/{{fact:config_name}})), whose comments record why each choice was made.

Scores are points above or below the study region average (0): each indicator is re-scaled so that the study region's mean, over all sample points, scores 0, and 30 points span its observed range on either side ([R11](03_recipes.md#r11)). Domain and index scores combine those scores, less a penalty for imbalance ([R12](03_recipes.md#r12)).

Nothing in this manual is estimated by hand. Labels, descriptions and readings come from the region configuration. Goalposts and weights come from the parameters the analysis wrote. Classes and units come from the dashboard export, values from the full-precision results GeoPackage, and rationale from the project's indicator register. Where none of these records something, the manual says *Pending*.
