# Appendix G. Excluded and pending indicators

The ULI includes every sub-variable of the project's variable sheet (`excel_work_sheet_key.xlsx`, revised 25 September 2026) whose data have been delivered and vary across the city. The configuration records why the others are not scored ({{cfg:## Deliberately not included}}):

| Sub-variable or core measure | Reason not scored |
|---|---|
| Flooding: population exposed; flooded area on main roads | Delivered values are missing for almost every area (none on the grid), pending the work package's reply on whether missing means no exposure. They are linked with missing taken as zero (`null_as`), for reference only. |
| Tree canopy cover | 210 manzanas only, no grid values: too sparse to vary. |
| Protected cycle lane coverage | Almost all zero. INVI 2020 does not distinguish protected lanes, and OpenStreetMap was not available to the work package (sheet note). |
| Heat exposure (core measure 3): land surface temperature, extreme heat frequency, night-time heat retention | Awaiting delivery. |
| Sidewalk coverage, street lighting, bicycle lane coverage, reachable jobs, access to basic services (Housing) | Awaiting delivery. |
| Crime exposure | One municipal rate for every location, so it cannot distinguish between them. |
| Large public open space *availability*: the share of an area's land that is large public green space | Access to large public green space is calculated by the core GHSCI workflow and **is scored** in the index ([Large public green space within 500 m](entries/lpugs.md)); walking and cycling access to large public open space (over 1.5 ha) at each distance band is also calculated and shown in the general dashboard. Availability is the sheet's separate sub-variable. It describes an area's land, not a sample point's surroundings, so the index, which scores sample points, does not include it as it stands. |
| Net residential density, commercial land use, land use mix | Components of the walkability core measure, which walkability itself represents: scoring them too would count density twice. They remain in the general dashboard. |
| Night-time thermal comfort | Varies too little within the city (30.3–30.6 °C). |
| Fire station coverage within 75 km | Universal coverage: recorded for completeness; the 3 km soft threshold is scored instead. |

Two domains, **Housing** and **Sociodemographic characteristics**, have no indicator yet. They are described but not scored, so the index is the composite of six domains.

## Open questions recorded with the analysis

- Whether a missing flood value means no exposure (work package 5).
- Heat exposure core measure 3 (work package 2).
- The level of traffic stress indicator's destination and threshold (a provisional single choice from a suite).
- The Spanish names of the core measures (`group`), and the `about` and `sources` text of each indicator, drafted on 25 September 2026, await review.
