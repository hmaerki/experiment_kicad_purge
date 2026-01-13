# kicad-tools

## Links

https://github.com/rjwalters/kicad-tools

## Examples

export PROJECT=/media/maerki/shared/octohub4/kicad/octohub4_v0.1


kct sch summary --format=json --verbose $PROJECT/pcb_octohub4.kicad_sch
kct sch hierarchy --format=json $PROJECT/pcb_octohub4.kicad_sch
kct sch labels --format=json $PROJECT/pcb_octohub4.kicad_sch
kct sch info --format=json $PROJECT/pcb_octohub4.kicad_sch R312
  Error: TypeError: main() takes 0 positional arguments but 1 was given

kct symbols --format json $PROJECT/pcb_octohub4.kicad_sch
kct pcb summary --format=json $PROJECT/pcb_octohub4.kicad_pcb
kct pcb footprints --sorted --format json $PROJECT/pcb_octohub4.kicad_pcb


kct parts availability $PROJECT/pcb_octohub4.kicad_sch