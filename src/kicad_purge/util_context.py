from __future__ import annotations

from kicad_tools.sexp.parser import SExp, parse_sexp
from kicad_tools import load_schematic, load_pcb, Schematic
from kicad_tools.core import load_symbol_lib

import dataclasses
import pathlib
import logging

logger = logging.getLogger(__file__)

LIBRARY_DELIMITER = ":"


@dataclasses.dataclass(repr=True)
class Purgable:
    id: str
    descr: str | None = None
    referenced: bool = False


class Purgables(dict[str, Purgable]):
    def add(self, id: str, descr: str | None = None) -> None:
        referenced = descr is None
        purgable = self.get(id, None)
        if purgable is None:
            purgable = Purgable(id=id)
            self[id] = purgable

        if referenced:
            purgable.referenced = True
        if descr is not None:
            if purgable.descr is not None:
                logger.debug(
                    f"Footprint '{purgable.id}' with desc='{purgable.descr}': overwrite with '{descr}'"
                )
            purgable.descr = descr

    def print(self, title: str) -> None:
        logger.info(f"**** {title}")
        for id in sorted(self):
            purgable = self[id]
            log = logger.debug if purgable.referenced else logger.info
            # log(f"   {purgable!r}")
            log(f"   {purgable.descr} ({purgable.id})")


@dataclasses.dataclass(frozen=True, repr=True)
class FileSExp:
    filename: pathlib.Path
    sexp: SExp

    @classmethod
    def factory(cls, filename: pathlib.Path) -> FileSExp:
        assert isinstance(filename, pathlib.Path)
        assert filename.is_file(), filename
        text = filename.read_text(encoding="utf-8")
        sexp = parse_sexp(text)
        return FileSExp(filename=filename, sexp=sexp)

    def find_tags(self, tag: str) -> list[SexpProps]:
        assert isinstance(tag, str)

        sexp_libs = self.sexp.find_all(tag)

        list_props: list[SexpProps] = []
        for sexp_lib in sexp_libs:
            props = SexpProps()
            for value in sexp_lib.values:
                # if isinstance(value, str):
                #     # Example:
                #     # 	(symbol "+3V3infra"
                #     #      (power)
                #     #
                #     # props[""] = "+3V3infra"
                #     props[""] = value
                #     continue
                prop_key = value.name
                assert isinstance(prop_key, str)
                prop_value = value.values[0]
                assert isinstance(prop_value, str)
                props[prop_key] = prop_value
            list_props.append(props)

        return list_props


@dataclasses.dataclass(frozen=True, repr=True)
class FileSymbolTable:
    sexp: FileSExp

    @classmethod
    def factory(cls, filename: pathlib.Path) -> FileSymbolTable:
        return FileSymbolTable(sexp=FileSExp.factory(filename=filename))

    def handle_symbols(self, context: Context) -> None:
        logger.info(f"*** Processing {self.sexp.filename.relative_to(context.directory)}")
        for value in self.sexp.sexp.values:
            if value.name == "symbol":
                symbol_name = value.values[0]
                symbol_name_full = (
                    f"{self.sexp.filename.stem}{LIBRARY_DELIMITER}{symbol_name}"
                )
                logging.debug(symbol_name_full)
                context.purgable_symbols.add(
                    id=symbol_name_full,
                    descr=self.sexp.filename.name,
                )
                # if symbol_name_full == "00_project_library:AMS1117-3.3":
                for child in value.children:
                    if child.name == "property":
                        child_value = child.values[0]
                        if child_value == "Footprint":
                            footprint_name = child.values[1]
                            if LIBRARY_DELIMITER in footprint_name:
                                if context.libraries_footprint.startswith(
                                    footprint_name
                                ):
                                    logging.debug(footprint_name)
                                    context.purgable_footprints.add(id=footprint_name)


class SexpProps(dict[str, str]):
    pass


class Libraries(dict[str, pathlib.Path]):
    def add(self, name: str, path: pathlib.Path) -> None:
        assert isinstance(name, str)
        assert isinstance(path, pathlib.Path)
        self[name] = path

    def startswith(self, symbol_name: str) -> bool:
        assert isinstance(symbol_name, str)
        # Example 'symbol_name': 00_project_library:TPS259474LRPWR
        for lib in self:
            if symbol_name.startswith(f"{lib}:"):
                return True
        return False


@dataclasses.dataclass(frozen=True, repr=True)
class LibPretty:
    sexp_props: SexpProps

    def find_footprints(self, context: Context, filename_xy: pathlib.Path) -> None:
        # print(p["name"], p["uri"])
        lib_name = self.sexp_props["name"]
        # Example 'lib_name': "00_project_library"
        lib_path = self.sexp_props["uri"]
        # Example 'lib_path': "${KIPRJMOD}/00_project_library.pretty"
        path_prefix = "${KIPRJMOD}/"
        if lib_path.startswith(path_prefix):
            lib_directory = lib_path[len(path_prefix) :]
            logger.debug("PRETTY", lib_name, lib_directory)
            _lib_directory = context.directory / lib_directory
            if not _lib_directory.is_dir():
                logger.warning(f"{filename_xy.relative_to(context.directory)}: References non existing library: {lib_directory}")
                return
            context.libraries_footprint.add(lib_name, _lib_directory)


@dataclasses.dataclass(frozen=True, repr=True)
class LibSym:
    sexp_props: SexpProps

    def find_symbols(self, context: Context) -> None:
        # print(p["name"], p["uri"])
        lib_name = self.sexp_props["name"]
        # Example 'lib_name': "00_project_library"
        lib_path = self.sexp_props["uri"]
        # Example 'lib_path': "${KIPRJMOD}/00_project_library.kicad_sym"
        path_prefix = "${KIPRJMOD}/"
        if lib_path.startswith(path_prefix):
            lib_path = lib_path[len(path_prefix) :]
            logger.debug("SYMBOL", lib_name, lib_path)
            filename = context.directory / lib_path
            assert filename.exists()
            fst = FileSymbolTable.factory(filename=filename)
            fst.handle_symbols(context=context)
            context.libraries_sym.add(lib_name, filename)


@dataclasses.dataclass(frozen=True, repr=True)
class FileKicadPcb:
    sexp: FileSExp

    @classmethod
    def factory(cls, filename_pcb: pathlib.Path) -> FileKicadPcb:
        return FileKicadPcb(sexp=FileSExp.factory(filename=filename_pcb))

    def process_pcb(self, context: Context) -> None:
        logger.info(f"*** Processing {self.sexp.filename.relative_to(context.directory)}")
        for value in self.sexp.sexp.values:
            if value.name == "footprint":
                footprint_name = value.values[0]
                if context.libraries_footprint.startswith(footprint_name):
                    context.purgable_footprints.add(
                        id=footprint_name, descr=self.sexp.filename.name
                    )


@dataclasses.dataclass(frozen=True, repr=True)
class FileKicadSch:
    sexp: FileSExp

    @classmethod
    def factory(cls, filename_sch: pathlib.Path) -> FileKicadSch:
        return FileKicadSch(sexp=FileSExp.factory(filename=filename_sch))

    def process_schematic(self, context: Context) -> None:
        logger.info(f"*** Processing {self.sexp.filename.relative_to(context.directory)}")
        sch = Schematic(self.sexp.sexp)

        for symbol in sch.symbols:
            symbol_name: str = symbol._sexp.values[0]
            # Example 'symbol_name': "00_project_library:+5Vdut"
            if isinstance(symbol_name, str):
                if context.libraries_sym.startswith(symbol_name):
                    context.purgable_symbols.add(id=symbol_name)

            footprint_name = symbol.footprint
            if context.libraries_footprint.startswith(footprint_name):
                context.purgable_footprints.add(id=footprint_name)

        # Access hierarchy
        logger.debug("SHEETS")
        for sheet in sch.sheets:
            logger.debug(" - ".join(["  SHEET", sheet.name, sheet.filename]))
            filename_sch = context.directory / sheet.filename
            kicad_sch = FileKicadSch.factory(filename_sch=filename_sch)
            kicad_sch.process_schematic(context=context)


@dataclasses.dataclass(frozen=True, repr=True)
class FileLibTable:
    sexp: FileSExp

    @classmethod
    def factory(cls, filename_lib: pathlib.Path) -> FileLibTable:
        sexp = FileSExp.factory(filename=filename_lib)
        return FileLibTable(sexp=sexp)

    @property
    def libs(self) -> list[SexpProps]:
        """
        (lib (name "00_project_library")(type "KiCad")(uri "${KIPRJMOD}/00_project_library.pretty")(options "")(descr ""))
        """
        list_props = self.sexp.find_tags("lib")
        list_props = [p for p in list_props if p["type"] == "KiCad"]
        return list_props

    def handle_lib_pretty(self, context: Context) -> None:
        logger.info(f"*** Processing {self.sexp.filename.relative_to(context.directory)}")
        for lib in self.libs:
            lib_pretty = LibPretty(lib)
            lib_pretty.find_footprints(context=context, filename_xy=self.sexp.filename)

    def handle_lib_sym(self, context: Context) -> None:
        logger.info(f"*** Processing {self.sexp.filename.relative_to(context.directory)}")
        for lib in self.libs:
            lib_pretty = LibSym(lib)
            lib_pretty.find_symbols(context=context)


@dataclasses.dataclass(frozen=True, repr=True)
class Context:
    directory: pathlib.Path
    purgable_symbols: Purgables = dataclasses.field(default_factory=lambda: Purgables())
    purgable_footprints: Purgables = dataclasses.field(
        default_factory=lambda: Purgables()
    )
    libraries_sym: Libraries = dataclasses.field(
        default_factory=lambda: Libraries(),
    )
    libraries_footprint: Libraries = dataclasses.field(
        default_factory=lambda: Libraries(),
    )

    def __post_init__(self) -> None:
        pass

    def collect(self) -> None:
        lib_table = FileLibTable.factory(self.directory / "fp-lib-table")
        lib_table.handle_lib_pretty(context=self)
        sym_table = FileLibTable.factory(self.directory / "sym-lib-table")
        sym_table.handle_lib_sym(context=self)

        for filename_proj in self.directory.glob("*.kicad_pro"):
            logger.info(f"*** Processing {filename_proj.name}")
            filename_sch=filename_proj.with_suffix(".kicad_sch")
            kicad_sch = FileKicadSch.factory(
                filename_sch=filename_sch
            )
            kicad_sch.process_schematic(context=self)

            kicad_pcb = FileKicadPcb.factory(
                filename_pcb=filename_proj.with_suffix(".kicad_pcb")
            )
            kicad_pcb.process_pcb(context=self)

        self._process_libraries_footprint()

    def print_libraries(self) -> None:
        def subprint(tag: str, libs: dict[str, pathlib.Path]) -> None:
            logger.info(f"*** {tag}")
            for lib in sorted(libs):
                relative = libs[lib].relative_to(self.directory)
                logger.info(f"      {lib}: {relative}")

        subprint("Libraries footprint", self.libraries_footprint)
        subprint("Libraries symbol", self.libraries_sym)

    def print(self) -> None:
        self.purgable_symbols.print("Symbols to be purged")
        self.purgable_footprints.print("Footprints to be purged")

    def _process_libraries_footprint(self) -> None:
        for lib_name, lib_dir in self.libraries_footprint.items():
            assert lib_dir.is_dir(), lib_dir
            for filename_footprint in lib_dir.glob("*.kicad_mod"):
                id = f"{lib_name}{LIBRARY_DELIMITER}{filename_footprint.stem}"
                self.purgable_footprints.add(id=id, descr=str(filename_footprint.relative_to(self.directory)))
