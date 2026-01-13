import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import re


class KiCadProjectAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.project_dir = self.project_path.parent
        self.symbols: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'library_files': set(),
            'reference_files': set()
        })
        self.footprints: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'library_files': set(),
            'reference_files': set()
        })
    
    def parse_project(self):
        """Parse the KiCad project file and find all schematics and PCBs"""
        with open(self.project_path, 'r') as f:
            project_data = json.load(f)
        
        # Find all schematic and PCB files
        schematic_files = list(self.project_dir.glob('*.kicad_sch'))
        pcb_files = list(self.project_dir.glob('*.kicad_pcb'))
        
        print(f"Found {len(schematic_files)} schematic files")
        print(f"Found {len(pcb_files)} PCB files")
        
        # Parse schematics for symbols
        for sch_file in schematic_files:
            self._parse_schematic(sch_file)
        
        # Parse PCBs for footprints
        for pcb_file in pcb_files:
            self._parse_pcb(pcb_file)
        
        # Find library files
        self._find_symbol_libraries()
        self._find_footprint_libraries()
    
    def _parse_schematic(self, sch_file: Path):
        """Parse a schematic file to extract symbol references"""
        content = sch_file.read_text()
        
        # Find all symbol instances in S-expression format
        # Pattern: (symbol (lib_id "library:symbol_name")
        pattern = r'\(symbol\s+\(lib_id\s+"([^:]+):([^"]+)"\)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            library = match.group(1)
            symbol_name = match.group(2)
            full_name = f"{library}:{symbol_name}"
            
            self.symbols[full_name]['count'] += 1
            self.symbols[full_name]['reference_files'].add(str(sch_file.relative_to(self.project_dir)))
    
    def _parse_pcb(self, pcb_file: Path):
        """Parse a PCB file to extract footprint references"""
        content = pcb_file.read_text()
        
        # Find all footprint instances in S-expression format
        # Pattern: (footprint "library:footprint_name"
        pattern = r'\(footprint\s+"([^:]+):([^"]+)"'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            library = match.group(1)
            footprint_name = match.group(2)
            full_name = f"{library}:{footprint_name}"
            
            self.footprints[full_name]['count'] += 1
            self.footprints[full_name]['reference_files'].add(str(pcb_file.relative_to(self.project_dir)))
    
    def _find_symbol_libraries(self):
        """Find symbol library files"""
        # Look for .kicad_sym files
        sym_files = list(self.project_dir.rglob('*.kicad_sym'))
        
        for sym_file in sym_files:
            content = sym_file.read_text()
            # Pattern: (symbol "symbol_name"
            pattern = r'\(symbol\s+"([^"]+)"'
            matches = re.finditer(pattern, content)
            
            for match in matches:
                symbol_name = match.group(1)
                
                # Try to match with referenced symbols
                for full_name in self.symbols.keys():
                    if symbol_name in full_name:
                        self.symbols[full_name]['library_files'].add(
                            str(sym_file.relative_to(self.project_dir))
                        )
    
    def _find_footprint_libraries(self):
        """Find footprint library files"""
        # Look for .kicad_mod files
        mod_files = list(self.project_dir.rglob('*.kicad_mod'))
        
        for mod_file in mod_files:
            content = mod_file.read_text()
            # Get footprint name from file
            footprint_name = mod_file.stem
            
            # Try to match with referenced footprints
            for full_name in self.footprints.keys():
                if footprint_name in full_name:
                    self.footprints[full_name]['library_files'].add(
                        str(mod_file.relative_to(self.project_dir))
                    )
    
    def print_report(self):
        """Print analysis report"""
        print("\n" + "="*80)
        print("SYMBOLS REPORT")
        print("="*80)
        
        for symbol_name in sorted(self.symbols.keys()):
            data = self.symbols[symbol_name]
            print(f"\nSymbol: {symbol_name}")
            print(f"  Count: {data['count']}")
            print(f"  Library files:")
            for lib_file in sorted(data['library_files']):
                print(f"    - {lib_file}")
            print(f"  Referenced in:")
            for ref_file in sorted(data['reference_files']):
                print(f"    - {ref_file}")
        
        print("\n" + "="*80)
        print("FOOTPRINTS REPORT")
        print("="*80)
        
        for footprint_name in sorted(self.footprints.keys()):
            data = self.footprints[footprint_name]
            print(f"\nFootprint: {footprint_name}")
            print(f"  Count: {data['count']}")
            print(f"  Library files:")
            for lib_file in sorted(data['library_files']):
                print(f"    - {lib_file}")
            print(f"  Referenced in:")
            for ref_file in sorted(data['reference_files']):
                print(f"    - {ref_file}")


def main():
    project_file = "/media/maerki/shared/octohub4/kicad/octohub4_v0.1/pcb_octohub4.kicad_pro"
    
    analyzer = KiCadProjectAnalyzer(project_file)
    analyzer.parse_project()
    analyzer.print_report()


if __name__ == "__main__":
    main()
    