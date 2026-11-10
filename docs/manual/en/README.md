# Mexicali Urban Liveability Index

**Technical manual: a cookbook of indicators, domains and index**

[Versión en español](../es/README.md)

PDF: [`mexicali_uli_manual_en.pdf`](../pdf/mexicali_uli_manual_en.pdf)

## Contents

- [About this manual](00_front.md)
- [1. Study design](01_design.md)
- [2. Reproducing the analysis](02_reproduce.md)
- [3. Method recipes](03_recipes.md)
  - [R1. Sample points and the pedestrian network](03_recipes.md#r1)
  - [R2. Network distance to the nearest destination, censored](03_recipes.md#r2)
  - [R3. Banded access, and distance from a disamenity](03_recipes.md#r3)
  - [R4. Diversity of what is reachable](03_recipes.md#r4)
  - [R5. Straight-line catchments](03_recipes.md#r5)
  - [R6. Level of traffic stress and the low-stress cycling network](03_recipes.md#r6)
  - [R7. Linking externally prepared indicators](03_recipes.md#r7)
  - [R8. Earth Engine: heat vulnerability and large green space](03_recipes.md#r8)
  - [R9. Walkability, and its attenuation by thermal comfort](03_recipes.md#r9)
  - [R10. Transforms: soft thresholds and stepped ladders](03_recipes.md#r10)
  - [R11. Normalisation: the Adjusted Mazziotta–Pareto Index (AMPI)](03_recipes.md#r11)
  - [R12. Aggregation: domains, shared indicators and the index](03_recipes.md#r12)
  - [R13. From sample points to areas](03_recipes.md#r13)
  - [R14. Frozen goalposts and recalculating a scenario](03_recipes.md#r14)
- **4. Index**
  - [Mexicali Urban Liveability Index](entries/uli.md)
  - [Mexicali Urban Liveability Index: Walkability (300 m), without thermal comfort attenuation](entries/uli_plain.md)
- **5. Domains**
  - [Ambient environment](entries/domain_ambient_environment.md)
  - [Built environment](entries/domain_built_environment.md)
  - [Economic development](entries/domain_economic_development.md)
  - [Housing](entries/domain_housing.md)
  - [Mobility and transport](entries/domain_mobility_transport.md)
  - [Safety and protection](entries/domain_safety.md)
  - [Social infrastructure](entries/domain_social_infrastructure.md)
  - [Sociodemographic characteristics](entries/domain_sociodemographics.md)
- **6. Indicators**
  - [Natural blue space nearby](entries/blue_space.md) — *Ambient environment*
  - [Heat adaptive capability (GUHVI)](entries/adaptive_capability.md) — *Ambient environment*
  - [Heat exposure (GUHVI)](entries/heat_exposure.md) — *Ambient environment*
  - [Heat sensitivity (GUHVI)](entries/heat_sensitivity.md) — *Ambient environment*
  - [Daytime thermal comfort](entries/thermal_comfort.md) — *Ambient environment*
  - [Parks within 300 m](entries/parks.md) — *Ambient environment, Built environment*
  - [Large public green space within 500 m](entries/lpugs.md) — *Ambient environment, Built environment*
  - [Vegetation cover (NDVI)](entries/vegetation.md) — *Ambient environment, Built environment*
  - [Proximity to major roads](entries/major_roads.md) — *Ambient environment, Safety and protection*
  - [Food within 1.5 km by low-stress cycling](entries/cycle_low_stress_food.md) — *Safety and protection, Mobility and transport, Built environment*
  - [Block size (perimeter)](entries/block_size.md) — *Built environment, Mobility and transport, Safety and protection*
  - [Fire station within 3 km](entries/fire_3km.md) — *Safety and protection, Mobility and transport, Built environment*
  - [Police station within 2 km](entries/police_2km.md) — *Safety and protection, Mobility and transport, Built environment*
  - [Walkability (300 m), attenuated by thermal comfort](entries/walkability.md) — *Built environment, Mobility and transport, Social infrastructure*
  - [250 m or more from petrol stations](entries/petrol_250m.md) — *Social infrastructure, Mobility and transport, Economic development*
  - [Convenience stores within 300 m](entries/convenience.md) — *Social infrastructure, Mobility and transport, Economic development*
  - [Fresh food diversity within 500 m](entries/div_fresh_food_500m.md) — *Social infrastructure, Mobility and transport, Economic development*
  - [Fresh food within 300 m](entries/fresh_food.md) — *Social infrastructure, Mobility and transport, Economic development*
  - [Job diversity](entries/job_diversity.md) — *Economic development*
  - [Manufacturing within 1 km](entries/manufacturing_1000m.md) — *Economic development*
  - [Public transport within 300 m](entries/public_transport.md) — *Mobility and transport*
  - [Community, culture and recreation diversity within 500 m](entries/div_ccr_500m.md) — *Social infrastructure*
  - [Community, culture and recreation within 300 m](entries/ccr_any.md) — *Social infrastructure*
  - [Care service diversity within 500 m](entries/div_care_500m.md) — *Social infrastructure*
  - [Care services within 300 m](entries/care_support.md) — *Social infrastructure*
  - [Education diversity within 500 m](entries/div_education_500m.md) — *Social infrastructure*
  - [Health service diversity within 500 m](entries/div_health_500m.md) — *Social infrastructure*
  - [Primary healthcare within 300 m](entries/primary_healthcare.md) — *Social infrastructure*
  - [Primary schools within 300 m](entries/primary_school.md) — *Social infrastructure*
- **7. Inputs and sub-indicators**
  - [Walkability within 300 m and its components](entries/walkability_components.md)
  - [Outdoor thermal comfort (UTCI)](entries/utci.md)
  - [Global Urban Heat Vulnerability Index (GUHVI) and its inputs](entries/guhvi.md)
  - [Public open space and large public green space](entries/public_open_space.md)
  - [Natural blue space](entries/blue_space_layer.md)
  - [DENUE destinations by SCIAN code](entries/denue_destinations.md)
  - [Diversity sets and their sub-types](entries/diversity_sets.md)
  - [Cycling network by level of traffic stress (LTS)](entries/lts_network.md)
  - [Public transport stops](entries/pt_stops.md)
  - [Police and fire stations (straight line)](entries/emergency_stations.md)
  - [Work package indicators (linked)](entries/work_package_layers.md)
- **Appendices**
  - [Appendix A. Variable index](A_variables.md)
  - [Appendix B. General dashboard indicators](B_general.md)
  - [Appendix C. Goalposts and weights](C_goalposts.md)
  - [Appendix D. Data source register](D_datasets.md)
  - [Appendix E. Glossary](E_glossary.md)
  - [Appendix F. References](F_references.md)
  - [Appendix G. Excluded and pending indicators](G_pending.md)
