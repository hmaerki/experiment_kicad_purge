# kicad purge

## User Manual

Given: <folder>/<filename>.kicad_pro

-> .kicad_sch, .kicad_pcb

### Kicad project files

<folder>/fp-lib-table
  
  * `(lib (name "00_project_library")(type "KiCad")(uri "${KIPRJMOD}/00_project_library.pretty")`

<folder>/sym-lib-table

  * `(lib (name "00_project_library")(type "KiCad")(uri "${KIPRJMOD}/00_project_library.kicad_sym")`

<filename>.kicad_sch: Starting with kicad_sch find hierarchical .kicad_sch.

<folder>.glob("*.kidac_sym"): Symbol files

<folder>.glob("*.pretty"): Footprint files

### Models

* `(model "${KIPRJMOD}/00_project_parts/KF235-2P/KF235-2P.step"`

### Symbols

In all .kicad_sch find

  * `(symbol "00_project_library:TPS259474LRPWR"`
  * `(property "Footprint" "00_project_library:TPS259474LRPWR"`

In .kicad_pcb find

  * `(footprint "00_project_library:octohub4_mounting_hole"`

