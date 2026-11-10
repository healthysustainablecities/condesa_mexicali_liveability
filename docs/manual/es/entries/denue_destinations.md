# Destinos del DENUE por código SCIAN

[← Volver al contenido](../README.md)

Las categorías funcionales de destinos se leen del Directorio Estadístico Nacional de Unidades Económicas (DENUE, INEGI, mayo de 2026) para Baja California, cada una con un filtro OGR por código de actividad SCIAN (`codigo_act`), y se recortan a la región de estudio con su zona de amortiguamiento. Los códigos se derivaron del propio conjunto de datos. Cada establecimiento conserva su código SCIAN como etiqueta, lo que permite subdividir una categoría para las medidas de diversidad. La tabla reproduce los filtros tal como están configurados.

| Destino | Nombre | Filtro SCIAN (OGR) | Lo usan |
|---|---|---|---|
| `denue_fresh_food` | Fresh food retail (DENUE) | `"codigo_act IN ('461121','461122','461123','461130','461140','461150','462111','462112')"` | [Alimentos frescos a menos de 300 m](fresh_food.md), [Diversidad de alimentos frescos a 500 m](div_fresh_food_500m.md) |
| `denue_food_retail` | Food retail, any (DENUE) | `"(codigo_act LIKE '4611%' AND codigo_act NOT IN ('461211','461212','461213','461220')) OR codigo_act LIKE '4621%'"` | [Tiendas de conveniencia a menos de 300 m](convenience.md) |
| `denue_bakery_tortilleria` | Bakeries and tortillerias (DENUE) | `"codigo_act IN ('311812','311813','311830')"` | [Diversidad de alimentos frescos a 500 m](div_fresh_food_500m.md) |
| `denue_household_goods` | Basic household goods (DENUE) | `"codigo_act IN ('465311','465914','466111','466112','466114','467111','467115')"` |  |
| `denue_pharmacy` | Pharmacies and medicine retail (DENUE) | `"codigo_act IN ('464111','464112','464113')"` | [Diversidad de servicios de salud a 500 m](div_health_500m.md) |
| `denue_finance_comms` | Financial and postal services (DENUE) | `"codigo_act IN ('522110','522210','522320','523122','491110')"` |  |
| `denue_preschool` | Preschools (DENUE) | `"codigo_act IN ('611111','611112','611171','611172')"` | [Diversidad educativa a 500 m](div_education_500m.md) |
| `denue_primary_school` | Primary schools (DENUE) | `"codigo_act IN ('611121','611122','611171','611172')"` | [Escuelas primarias a menos de 300 m](primary_school.md), [Diversidad educativa a 500 m](div_education_500m.md) |
| `denue_secondary_school` | Secondary and upper secondary schools (DENUE) | `"codigo_act IN ('611131','611132','611142','611151','611152','611161','611162','611171','611172')"` | [Diversidad educativa a 500 m](div_education_500m.md) |
| `denue_tertiary_education` | Tertiary and vocational education (DENUE) | `"codigo_act LIKE '6112%' OR codigo_act LIKE '6113%' OR codigo_act IN ('611411','611412','611511','611512')"` | [Diversidad educativa a 500 m](div_education_500m.md) |
| `denue_primary_healthcare` | Primary healthcare (DENUE) | `"codigo_act IN ('621111','621112','621115','621116')"` | [Atención primaria de salud a menos de 300 m](primary_healthcare.md), [Diversidad de servicios de salud a 500 m](div_health_500m.md) |
| `denue_medical_clinic` | Specialist and diagnostic clinics (DENUE) | `"codigo_act IN ('621113','621211','621212','621511')"` | [Diversidad de servicios de salud a 500 m](div_health_500m.md) |
| `denue_hospital` | Hospitals (DENUE) | `"codigo_act LIKE '622%'"` | [Diversidad de servicios de salud a 500 m](div_health_500m.md) |
| `denue_care_support` | Care and social support services (DENUE) | `"codigo_act LIKE '623%' OR codigo_act LIKE '624%'"` | [Diversidad de servicios de salud a 500 m](div_health_500m.md), [Servicios de cuidado a menos de 300 m](care_support.md), [Diversidad de servicios de cuidado a 500 m](div_care_500m.md) |
| `denue_childcare` | Childcare (DENUE) | `"codigo_act IN ('624411','624412')"` |  |
| `denue_community` | Community and social facilities (DENUE) | `"codigo_act IN ('813210','813230','931610')"` | [Comunidad, cultura y recreación a menos de 300 m](ccr_any.md), [Diversidad de comunidad, cultura y recreación a 500 m](div_ccr_500m.md) |
| `denue_culture` | Cultural facilities (DENUE) | `"codigo_act IN ('712111','712112','519211','519212','512130','711311','711312')"` | [Comunidad, cultura y recreación a menos de 300 m](ccr_any.md), [Diversidad de comunidad, cultura y recreación a 500 m](div_ccr_500m.md) |
| `denue_sport` | Sports and active recreation (DENUE) | `"codigo_act IN ('713941','713942','713943','713944','713910','713950','611621','611622')"` | [Comunidad, cultura y recreación a menos de 300 m](ccr_any.md), [Diversidad de comunidad, cultura y recreación a 500 m](div_ccr_500m.md) |
| `denue_recreation` | Public recreation venues (DENUE) | `"codigo_act IN ('713111','713112','713113','712131','712132')"` | [Comunidad, cultura y recreación a menos de 300 m](ccr_any.md), [Diversidad de comunidad, cultura y recreación a 500 m](div_ccr_500m.md) |
| `denue_employment_any` | Any economic establishment (DENUE) | `(todos)` |  |
| `denue_employer_medium` | Employers of 11 or more people (DENUE) | `"per_ocu NOT IN ('0 a 5 personas','6 a 10 personas')"` |  |
| `denue_manufacturing` | Manufacturing and industrial establishments (DENUE) | `"codigo_act LIKE '31%' OR codigo_act LIKE '32%' OR codigo_act LIKE '33%'"` | [Manufactura a menos de 1 km](manufacturing_1000m.md) |
| `denue_petrol_station` | Petrol stations (DENUE) | `"codigo_act IN ('468411','468413')"` | [A 250 m o más de gasolineras](petrol_250m.md) |

## Método: práctica

**Recetas:** [R2. Distancia por la red al destino más cercano, censurada](../03_recipes.md#r2)

**Configuración** ([`MX_Mexicali_2025_ULI.yml:192`](../../data/MX_Mexicali_2025_ULI.yml#L192)):

```yaml
denue_fresh_food: &denue
  data: MX/INEGI/DENUE_2026/denue_inegi_02_.shp -where "codigo_act IN ('461121','461122','461123','461130','461140','461150','462111','462112')"
  dest_name_full: Fresh food retail (DENUE)
  domain: Daily essential services
  ## Retain each establishment's SCIAN activity code as a destination tag, so
  ## that a category imported once can be subdivided into its sub-types for
  ## the diversity measures below without declaring a separate entry for each.
  ## Shared by every DENUE category through this anchor.
  keep_columns: codigo_act
  source: INEGI, Directorio Estadistico Nacional de Unidades Economicas (DENUE)
  publication_date: 2026-05
  url: https://www.inegi.org.mx/app/mapa/denue/
  licence: Terminos de Libre Uso de la Informacion del INEGI
  citation: "INEGI (2026). Directorio Estadistico Nacional de Unidades Economicas (DENUE), mayo 2026. Instituto Nacional de Estadistica y Geografia, Mexico."
```

**Código (GHSCI):**

- [`process/subprocesses/_05_compile_destinations.py:201`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_05_compile_destinations.py#L201) `compile_poi_destinations()`

## Lo usan

[A 250 m o más de gasolineras](petrol_250m.md), [Tiendas de conveniencia a menos de 300 m](convenience.md), [Diversidad de alimentos frescos a 500 m](div_fresh_food_500m.md), [Alimentos frescos a menos de 300 m](fresh_food.md), [Manufactura a menos de 1 km](manufacturing_1000m.md), [Diversidad de comunidad, cultura y recreación a 500 m](div_ccr_500m.md), [Comunidad, cultura y recreación a menos de 300 m](ccr_any.md), [Diversidad de servicios de cuidado a 500 m](div_care_500m.md), [Servicios de cuidado a menos de 300 m](care_support.md), [Diversidad educativa a 500 m](div_education_500m.md), [Diversidad de servicios de salud a 500 m](div_health_500m.md), [Atención primaria de salud a menos de 300 m](primary_healthcare.md), [Escuelas primarias a menos de 300 m](primary_school.md)
