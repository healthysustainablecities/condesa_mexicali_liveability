# Conjuntos de diversidad y sus subtipos

[← Volver al contenido](../README.md)

Cada conjunto de diversidad declara sus subtipos como filtros SQL sobre la capa de destinos. El número de subtipos `k` es fijo, de modo que las puntuaciones son comparables entre áreas. La tabla reproduce la configuración.

| Conjunto | Subtipo | Filtro (SQL) |
|---|---|---|
| `fresh_food` (k = 7) | `meat` | `dest_name = 'denue_fresh_food' AND tags->>'codigo_act' IN ('461121','461122','461123')` |
| `fresh_food` (k = 7) | `produce` | `dest_name = 'denue_fresh_food' AND tags->>'codigo_act' = '461130'` |
| `fresh_food` (k = 7) | `grains_and_spices` | `dest_name = 'denue_fresh_food' AND tags->>'codigo_act' = '461140'` |
| `fresh_food` (k = 7) | `dairy` | `dest_name = 'denue_fresh_food' AND tags->>'codigo_act' = '461150'` |
| `fresh_food` (k = 7) | `supermarket` | `dest_name = 'denue_fresh_food' AND tags->>'codigo_act' = '462111'` |
| `fresh_food` (k = 7) | `minisuper` | `dest_name = 'denue_fresh_food' AND tags->>'codigo_act' = '462112'` |
| `fresh_food` (k = 7) | `bakery_tortilleria` | `dest_name = 'denue_bakery_tortilleria'` |
| `education` (k = 4) | `preschool` | `dest_name = 'denue_preschool'` |
| `education` (k = 4) | `primary` | `dest_name = 'denue_primary_school'` |
| `education` (k = 4) | `secondary` | `dest_name = 'denue_secondary_school'` |
| `education` (k = 4) | `tertiary` | `dest_name = 'denue_tertiary_education'` |
| `health_care` (k = 5) | `primary_healthcare` | `dest_name = 'denue_primary_healthcare'` |
| `health_care` (k = 5) | `specialist_clinic` | `dest_name = 'denue_medical_clinic'` |
| `health_care` (k = 5) | `hospital` | `dest_name = 'denue_hospital'` |
| `health_care` (k = 5) | `pharmacy` | `dest_name = 'denue_pharmacy'` |
| `health_care` (k = 5) | `care_support` | `dest_name = 'denue_care_support'` |
| `care` (k = 3) | `childcare` | `dest_name = 'denue_care_support' AND tags->>'codigo_act' IN ('624411','624412')` |
| `care` (k = 3) | `residential_care` | `dest_name = 'denue_care_support' AND tags->>'codigo_act' LIKE '623%'` |
| `care` (k = 3) | `social_assistance` | `dest_name = 'denue_care_support' AND tags->>'codigo_act' LIKE '624%' AND tags->>'codigo_act' NOT IN ('624411','624412')` |
| `community_culture_rec` (k = 4) | `community` | `dest_name = 'denue_community'` |
| `community_culture_rec` (k = 4) | `culture` | `dest_name = 'denue_culture'` |
| `community_culture_rec` (k = 4) | `sport` | `dest_name = 'denue_sport'` |
| `community_culture_rec` (k = 4) | `recreation` | `dest_name = 'denue_recreation'` |

## Método: práctica

**Recetas:** [R4. Diversidad de lo alcanzable](../03_recipes.md#r4)

**Configuración** ([`MX_Mexicali_2025_ULI.yml:595`](../../data/MX_Mexicali_2025_ULI.yml#L595)):

```yaml
diversity:
  ## Sub-types within one imported category, separated by activity code
  ## (hence keep_columns: codigo_act above), plus bakeries and tortillerias,
  ## which SCIAN classifies as manufacturing and which are therefore a
  ## separate category rather than a code subset.
  fresh_food:
    distances: [300, 500, 1000, 1500]
    groups:
      meat: "dest_name = 'denue_fresh_food' AND tags->>'codigo_act' IN ('461121','461122','461123')"
      produce: "dest_name = 'denue_fresh_food' AND tags->>'codigo_act' = '461130'"
      grains_and_spices: "dest_name = 'denue_fresh_food' AND tags->>'codigo_act' = '461140'"
      dairy: "dest_name = 'denue_fresh_food' AND tags->>'codigo_act' = '461150'"
      supermarket: "dest_name = 'denue_fresh_food' AND tags->>'codigo_act' = '462111'"
      minisuper: "dest_name = 'denue_fresh_food' AND tags->>'codigo_act' = '462112'"
      bakery_tortilleria: "dest_name = 'denue_bakery_tortilleria'"
  ## Sub-types that are already separate imported categories, so no code
  ## filtering is needed.  A school combining several levels (611171 /
  ## 611172) is imported under each level it serves and so counts towards
  ## each, which is the intended reading: a school serving that level is
  ## available.
  education:
    distances: [300, 500, 1000, 1500]
    groups:
      preschool: "dest_name = 'denue_preschool'"
      primary: "dest_name = 'denue_primary_school'"
      secondary: "dest_name = 'denue_secondary_school'"
      tertiary: "dest_name = 'denue_tertiary_education'"
  ## denue_childcare is a subset of denue_care_support, so only the broader
  ## category is used here; counting both would count a creche twice and
  ## overstate the evenness of what is available.
  health_care:
    distances: [300, 500, 1000, 1500]
    groups:
      primary_healthcare: "dest_name = 'denue_primary_healthcare'"
      specialist_clinic: "dest_name = 'denue_medical_clinic'"
      hospital: "dest_name = 'denue_hospital'"
      pharmacy: "dest_name = 'denue_pharmacy'"
      care_support: "dest_name = 'denue_care_support'"
  ## Diversity of care services (ULI sub-variable "Diversity of care
  ## services"): the SCIAN groups within care and social support.
  ## Childcare is taken from the care category by code, not from
  ## denue_childcare, so that no establishment is counted twice.
  care:
    distances: [300, 500, 1000, 1500]
    groups:
      childcare: "dest_name = 'denue_care_support' AND tags->>'codigo_act' IN ('624411','624412')"
      residential_care: "dest_name = 'denue_care_support' AND tags->>'codigo_act' LIKE '623%'"
      social_assistance: "dest_name = 'denue_care_support' AND tags->>'codigo_act' LIKE '624%' AND tags->>'codigo_act' NOT IN ('624411','624412')"
  community_culture_rec:
    distances: [300, 500, 1000, 1500]
    groups:
      community: "dest_name = 'denue_community'"
      culture: "dest_name = 'denue_culture'"
      sport: "dest_name = 'denue_sport'"
      recreation: "dest_name = 'denue_recreation'"
```

**Código (GHSCI):**

- [`process/subprocesses/_accessibility_spec.py:299`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_accessibility_spec.py#L299) `diversity_sets()`
- [`process/subprocesses/_accessibility_spec.py:466`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_accessibility_spec.py#L466) `normalised_entropy()`
- [`process/subprocesses/_accessibility_spec.py:493`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_accessibility_spec.py#L493) `richness()`

## Lo usan

[Diversidad de alimentos frescos a 500 m](div_fresh_food_500m.md), [Diversidad de comunidad, cultura y recreación a 500 m](div_ccr_500m.md), [Diversidad de servicios de cuidado a 500 m](div_care_500m.md), [Diversidad educativa a 500 m](div_education_500m.md), [Diversidad de servicios de salud a 500 m](div_health_500m.md)
