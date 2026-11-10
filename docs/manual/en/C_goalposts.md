# Appendix C. Goalposts and weights

Goalposts and effective weights of each index, as the analysis wrote them (`data/`). Goalposts are on the scale scored: the soft access score (0 to 1) where there is a threshold, the ladder where there is one, otherwise the value as measured. Ref is the study region average, and scores 0.

## `uli`

Goalposts resolved on 2026-09-26 from 154,239 sample points; method `ampi`, centre 0.

| Indicator | Variable | Domains (share of weight) | Scored as | Min · Ref · Max | Effective weight |
|---|---|---|---|---|---|
| [Heat exposure (GUHVI)](entries/heat_exposure.md) | `sp_urban_heat_exposure_index` | Ambient environment | as measured | 0 · 47 · 100 | 2.8% |
| [Heat sensitivity (GUHVI)](entries/heat_sensitivity.md) | `sp_urban_heat_sensitivity_index` | Ambient environment | as measured | 0 · 58 · 100 | 2.8% |
| [Heat adaptive capability (GUHVI)](entries/adaptive_capability.md) | `sp_urban_heat_adaptive_capability_index` | Ambient environment | as measured | 0 · 22 · 100 | 2.8% |
| [Natural blue space nearby](entries/blue_space.md) | `sp_walk_nearest_node_blue_space` | Ambient environment | stepped ladder | 56.9 · 76.9 · 96.9 | 2.8% |
| [Vegetation cover (NDVI)](entries/vegetation.md) | `sp_ext_ndvi` | Ambient environment (50%), Built environment (50%) | as measured | −0.251 · 0.082 · 0.415 | 4.0% |
| [Parks within 300 m](entries/parks.md) | `sp_walk_nearest_node_public_open_space_any` | Ambient environment (50%), Built environment (50%) | soft access, 300 m threshold | −0.197 · 0.299 · 0.796 | 4.0% |
| [Large public green space within 500 m](entries/lpugs.md) | `sp_access_large_public_green_space_score` | Ambient environment (50%), Built environment (50%) | as measured | −0.419 · 0.081 · 0.581 | 4.0% |
| [Proximity to major roads](entries/major_roads.md) | `sp_ext_major_road_length_300m` | Ambient environment (50%), Safety and protection (50%) | as measured | −2,429 · 1,756 · 5,940 | 5.9% |
| [Walkability (300 m), attenuated by thermal comfort](entries/walkability.md) | `sp_walk_idx_300_tm` | Built environment (33%), Mobility and transport (33%), Social infrastructure (33%) | as measured | −0.022 · 0.315 · 0.651 | 3.7% |
| [Block size (perimeter)](entries/block_size.md) | `sp_ext_block_perimeter_m` | Built environment (33%), Mobility and transport (33%), Safety and protection (33%) | as measured | −3,860 · 856 · 5,572 | 6.2% |
| [Police station within 2 km](entries/police_2km.md) | `sp_euclid_dist_imip_police_station` | Safety and protection (33%), Mobility and transport (33%), Built environment (33%) | soft access, 2,000 m threshold | 0.115 · 0.611 · 1.108 | 6.2% |
| [Fire station within 3 km](entries/fire_3km.md) | `sp_euclid_dist_imip_fire_station` | Safety and protection (33%), Mobility and transport (33%), Built environment (33%) | soft access, 3,000 m threshold | 0.096 · 0.592 · 1.089 | 6.2% |
| [Food within 1.5 km by low-stress cycling](entries/cycle_low_stress_food.md) | `sp_cycle_safe_nearest_node_fresh_food_pooled` | Safety and protection (33%), Mobility and transport (33%), Built environment (33%) | soft access, 1,500 m threshold | 0.059 · 0.555 · 1.052 | 6.2% |
| [Public transport within 300 m](entries/public_transport.md) | `sp_walk_nearest_node_pt_any` | Mobility and transport | soft access, 300 m threshold | −0.433 · 0.064 · 0.561 | 4.2% |
| [Fresh food within 300 m](entries/fresh_food.md) | `sp_walk_nearest_node_denue_fresh_food` | Social infrastructure (33%), Mobility and transport (33%), Economic development (33%) | soft access, 300 m threshold | −0.091 · 0.405 · 0.902 | 3.6% |
| [Fresh food diversity within 500 m](entries/div_fresh_food_500m.md) | `sp_walk_diversity_fresh_food_500m` | Social infrastructure (33%), Mobility and transport (33%), Economic development (33%) | as measured | −0.167 · 0.269 · 0.705 | 3.6% |
| [Convenience stores within 300 m](entries/convenience.md) | `sp_walk_nearest_node_denue_food_retail` | Social infrastructure (33%), Mobility and transport (33%), Economic development (33%) | soft access, 300 m threshold | 0.179 · 0.675 · 1.172 | 3.6% |
| [250 m or more from petrol stations](entries/petrol_250m.md) | `sp_walk_beyond_denue_petrol_station_250m` | Social infrastructure (33%), Mobility and transport (33%), Economic development (33%) | as measured | 0.421 · 0.921 · 1.421 | 3.6% |
| [Primary schools within 300 m](entries/primary_school.md) | `sp_walk_nearest_node_denue_primary_school` | Social infrastructure | soft access, 300 m threshold | −0.330 · 0.166 · 0.663 | 1.7% |
| [Education diversity within 500 m](entries/div_education_500m.md) | `sp_walk_diversity_education_500m` | Social infrastructure | as measured | −0.232 · 0.268 · 0.768 | 1.7% |
| [Primary healthcare within 300 m](entries/primary_healthcare.md) | `sp_walk_nearest_node_denue_primary_healthcare` | Social infrastructure | soft access, 300 m threshold | −0.358 · 0.139 · 0.636 | 1.7% |
| [Health service diversity within 500 m](entries/div_health_500m.md) | `sp_walk_diversity_health_care_500m` | Social infrastructure | as measured | −0.190 · 0.310 · 0.810 | 1.7% |
| [Care services within 300 m](entries/care_support.md) | `sp_walk_nearest_node_denue_care_support` | Social infrastructure | soft access, 300 m threshold | −0.336 · 0.161 · 0.657 | 1.7% |
| [Care service diversity within 500 m](entries/div_care_500m.md) | `sp_walk_diversity_care_500m` | Social infrastructure | as measured | −0.440 · 0.060 · 0.560 | 1.7% |
| [Community, culture and recreation within 300 m](entries/ccr_any.md) | `sp_walk_nearest_node_denue_ccr_any` | Social infrastructure | soft access, 300 m threshold | −0.077 · 0.420 · 0.916 | 1.7% |
| [Community, culture and recreation diversity within 500 m](entries/div_ccr_500m.md) | `sp_walk_diversity_community_culture_recreation_500m` | Social infrastructure | as measured | −0.331 · 0.163 · 0.656 | 1.7% |
| [Manufacturing within 1 km](entries/manufacturing_1000m.md) | `sp_walk_access_denue_manufacturing_1000m` | Economic development | as measured | 0.435 · 0.935 · 1.435 | 5.0% |
| [Job diversity](entries/job_diversity.md) | `sp_ext_economic_sector_diversity` | Economic development | as measured | −0.236 · 0.264 · 0.764 | 5.0% |

## `uli_plain`

Goalposts resolved on 2026-09-26 from 154,239 sample points; method `ampi`, centre 0.

| Indicator | Variable | Domains (share of weight) | Scored as | Min · Ref · Max | Effective weight |
|---|---|---|---|---|---|
| [Heat exposure (GUHVI)](entries/heat_exposure.md) | `sp_urban_heat_exposure_index` | Ambient environment | as measured | 0 · 47 · 100 | 2.4% |
| [Heat sensitivity (GUHVI)](entries/heat_sensitivity.md) | `sp_urban_heat_sensitivity_index` | Ambient environment | as measured | 0 · 58 · 100 | 2.4% |
| [Heat adaptive capability (GUHVI)](entries/adaptive_capability.md) | `sp_urban_heat_adaptive_capability_index` | Ambient environment | as measured | 0 · 22 · 100 | 2.4% |
| [Daytime thermal comfort](entries/thermal_comfort.md) | `sp_utci_day_mean` | Ambient environment | as measured | 41.938 · 44.949 · 47.960 | 2.4% |
| [Natural blue space nearby](entries/blue_space.md) | `sp_walk_nearest_node_blue_space` | Ambient environment | stepped ladder | 56.9 · 76.9 · 96.9 | 2.4% |
| [Vegetation cover (NDVI)](entries/vegetation.md) | `sp_ext_ndvi` | Ambient environment (50%), Built environment (50%) | as measured | −0.251 · 0.082 · 0.415 | 3.8% |
| [Parks within 300 m](entries/parks.md) | `sp_walk_nearest_node_public_open_space_any` | Ambient environment (50%), Built environment (50%) | soft access, 300 m threshold | −0.197 · 0.299 · 0.796 | 3.8% |
| [Large public green space within 500 m](entries/lpugs.md) | `sp_access_large_public_green_space_score` | Ambient environment (50%), Built environment (50%) | as measured | −0.419 · 0.081 · 0.581 | 3.8% |
| [Proximity to major roads](entries/major_roads.md) | `sp_ext_major_road_length_300m` | Ambient environment (50%), Safety and protection (50%) | as measured | −2,429 · 1,756 · 5,940 | 5.7% |
| [Walkability (300 m), attenuated by thermal comfort](entries/walkability.md) | `sp_walk_idx_300` | Built environment (33%), Mobility and transport (33%), Social infrastructure (33%) | as measured | −10.0 · 0.0 · 10.0 | 3.7% |
| [Block size (perimeter)](entries/block_size.md) | `sp_ext_block_perimeter_m` | Built environment (33%), Mobility and transport (33%), Safety and protection (33%) | as measured | −3,860 · 856 · 5,572 | 6.2% |
| [Police station within 2 km](entries/police_2km.md) | `sp_euclid_dist_imip_police_station` | Safety and protection (33%), Mobility and transport (33%), Built environment (33%) | soft access, 2,000 m threshold | 0.115 · 0.611 · 1.108 | 6.2% |
| [Fire station within 3 km](entries/fire_3km.md) | `sp_euclid_dist_imip_fire_station` | Safety and protection (33%), Mobility and transport (33%), Built environment (33%) | soft access, 3,000 m threshold | 0.096 · 0.592 · 1.089 | 6.2% |
| [Food within 1.5 km by low-stress cycling](entries/cycle_low_stress_food.md) | `sp_cycle_safe_nearest_node_fresh_food_pooled` | Safety and protection (33%), Mobility and transport (33%), Built environment (33%) | soft access, 1,500 m threshold | 0.059 · 0.555 · 1.052 | 6.2% |
| [Public transport within 300 m](entries/public_transport.md) | `sp_walk_nearest_node_pt_any` | Mobility and transport | soft access, 300 m threshold | −0.433 · 0.064 · 0.561 | 4.2% |
| [Fresh food within 300 m](entries/fresh_food.md) | `sp_walk_nearest_node_denue_fresh_food` | Social infrastructure (33%), Mobility and transport (33%), Economic development (33%) | soft access, 300 m threshold | −0.091 · 0.405 · 0.902 | 3.6% |
| [Fresh food diversity within 500 m](entries/div_fresh_food_500m.md) | `sp_walk_diversity_fresh_food_500m` | Social infrastructure (33%), Mobility and transport (33%), Economic development (33%) | as measured | −0.167 · 0.269 · 0.705 | 3.6% |
| [Convenience stores within 300 m](entries/convenience.md) | `sp_walk_nearest_node_denue_food_retail` | Social infrastructure (33%), Mobility and transport (33%), Economic development (33%) | soft access, 300 m threshold | 0.179 · 0.675 · 1.172 | 3.6% |
| [250 m or more from petrol stations](entries/petrol_250m.md) | `sp_walk_beyond_denue_petrol_station_250m` | Social infrastructure (33%), Mobility and transport (33%), Economic development (33%) | as measured | 0.421 · 0.921 · 1.421 | 3.6% |
| [Primary schools within 300 m](entries/primary_school.md) | `sp_walk_nearest_node_denue_primary_school` | Social infrastructure | soft access, 300 m threshold | −0.330 · 0.166 · 0.663 | 1.7% |
| [Education diversity within 500 m](entries/div_education_500m.md) | `sp_walk_diversity_education_500m` | Social infrastructure | as measured | −0.232 · 0.268 · 0.768 | 1.7% |
| [Primary healthcare within 300 m](entries/primary_healthcare.md) | `sp_walk_nearest_node_denue_primary_healthcare` | Social infrastructure | soft access, 300 m threshold | −0.358 · 0.139 · 0.636 | 1.7% |
| [Health service diversity within 500 m](entries/div_health_500m.md) | `sp_walk_diversity_health_care_500m` | Social infrastructure | as measured | −0.190 · 0.310 · 0.810 | 1.7% |
| [Care services within 300 m](entries/care_support.md) | `sp_walk_nearest_node_denue_care_support` | Social infrastructure | soft access, 300 m threshold | −0.336 · 0.161 · 0.657 | 1.7% |
| [Care service diversity within 500 m](entries/div_care_500m.md) | `sp_walk_diversity_care_500m` | Social infrastructure | as measured | −0.440 · 0.060 · 0.560 | 1.7% |
| [Community, culture and recreation within 300 m](entries/ccr_any.md) | `sp_walk_nearest_node_denue_ccr_any` | Social infrastructure | soft access, 300 m threshold | −0.077 · 0.420 · 0.916 | 1.7% |
| [Community, culture and recreation diversity within 500 m](entries/div_ccr_500m.md) | `sp_walk_diversity_community_culture_recreation_500m` | Social infrastructure | as measured | −0.331 · 0.163 · 0.656 | 1.7% |
| [Manufacturing within 1 km](entries/manufacturing_1000m.md) | `sp_walk_access_denue_manufacturing_1000m` | Economic development | as measured | 0.435 · 0.935 · 1.435 | 5.0% |
| [Job diversity](entries/job_diversity.md) | `sp_ext_economic_sector_diversity` | Economic development | as measured | −0.236 · 0.264 · 0.764 | 5.0% |
