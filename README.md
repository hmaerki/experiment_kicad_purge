# Kicad purge

## Use case: Name, data&time

For every revision, some files have to be updated (v2.3.4, 2025-05-12).

The required locations are found automatically and updated.

## Use case: New project rename

A new project is started by 'git cloing' and old one and not 'new project rename':

* Find files with the old name: 'old_name.kicad_pro'
* Create git commands: 'git mv old_name.kicad_pro new_name.kicad_pro'
* Find and update references in files.

## Use case: purge

While developing a pcb, often variants of symobls and footprints are stored in the project files.

purge will:

* Find all unreferenced symbols and footprints and remove them.

## Implementation: Fileformats/Parsers

* lisp style
  * fp-lib-table
  * 00_project_library.kicad_sym
  * SOT-23.kicad_mod
  * pcb_octoprobe.kicad_pcb
  * pcb_octoprobe.kicad_pcb

* json
  * pcb_octoprobe.kicad_pro
  
### Libraries

* https://github.com/jd-boyd/sexpdata
  * Nice pytest workflow on many python versions
  * Very limited documentation
  * Too flat directory structure
  * https://sexpdata.readthedocs.io/en/latest/index.html
  * Extens use of `**kwds`

* https://github.com/psychogenic/kicad-skip
  * Many features
  * No code formatting
  * No typehints on return types
  * Probably not static type checking
  * Depends on sexpdata

* https://github.com/PySpice-org/kicad-rw
  * Depends on sexpdata
  * Example of reading schemas, crete netlist

* https://github.com/mvnmgrx/kiutils https://kiutils.readthedocs.io
  * Very nice first impression
  * https://kiutils.readthedocs.io/en/latest/usage/examples.html#changing-title-and-revision-in-schematic
  * Very sexy parser: https://github.com/mvnmgrx/kiutils/blob/master/src/kiutils/utils/sexpr.py
  * Very detailed on file attributes, for example footprint model pad: https://github.com/mvnmgrx/kiutils/blob/master/src/kiutils/footprint.py#L354

* https://github.com/vmalat/kipe
  * This file does too many things at one time: https://github.com/vmalat/kipe/blob/main/kipe.py
  * Supports en and cz. Why?

* https://github.com/dvc94ch/pykicad
  * Abandoned?

* https://github.com/realthunder/sexp_parser
* https://github.com/realthunder/kicad_parser
  * Solve on thing at the time: The parser!

## Technical challanges

* Does the library reformat the file? This is unwanted as a diff tool should only display the changes.