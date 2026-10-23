#!/usr/bin/env python3
"""Refresh the committed runtime resources from editable source assets."""
import json
from pathlib import Path
import subprocess
import sys
from level_data import load_levels

ROOT = Path(__file__).resolve().parents[1]


def main():
    load_levels(ROOT / 'assets/cargo_shift/levels.json')
    subprocess.run([sys.executable, str(ROOT / 'tools/build_levels.py')], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / 'tools/build_graphics.py')], cwd=ROOT, check=True)
    ids = json.loads((ROOT / 'assets/common/tiles.json').read_text())
    if any(not isinstance(value, int) or not 0 <= value < 256 for value in ids.values()):
        raise ValueError('Tile IDs must be integers in 0..255')
    header = '#ifndef TILE_IDS_H\n#define TILE_IDS_H\n'
    header += ''.join(f'#define {name} {value}\n' for name, value in ids.items())
    header += '#endif\n'
    (ROOT / 'assets/generated/tile_ids.h').write_text(header)
    print('Updated cargo_config.h, cargo_tiles.chr, cargo_view.h, cargo_levels.h and tile_ids.h.')


if __name__ == '__main__':
    main()
