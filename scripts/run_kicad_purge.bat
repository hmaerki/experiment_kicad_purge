rem Double click this file and it will loop over all .csv file in this directory
rem to generated png diagrams

uv run --with=git+https://github.com/hmaerki/experiment_kicad_purge@main kicad_purge

pause