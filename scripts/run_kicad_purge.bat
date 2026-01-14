@rem Run kicad_purge on current directory

@rem NO files will be changed.
@rem All purging has to be manually!

uv run --with=git+https://github.com/hmaerki/experiment_kicad_purge@main kicad_purge

pause
