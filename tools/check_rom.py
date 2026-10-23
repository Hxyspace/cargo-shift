"""Check the Cargo Shift cartridge header and vectors (stdlib only)."""
from pathlib import Path
import sys


def check(path):
    data = Path(path).read_bytes()
    if len(data) < 16 or data[:4] != b"NES\x1a":
        raise ValueError("missing iNES header")
    header = data[:16]
    if header[7] & 0x0f:
        raise ValueError("expected a standard iNES 1.0 console header")
    mapper = (header[6] >> 4) | (header[7] & 0xf0)
    if mapper != 0:
        raise ValueError(f"expected Mapper 0, got {mapper}")
    if header[6] & 0x0e:
        raise ValueError("battery, trainer and four-screen flags must be off")
    if header[4] not in (1, 2) or header[5] != 1:
        raise ValueError("expected 16/32 KiB PRG and 8 KiB CHR ROM")
    expected = 16 + header[4] * 16384 + header[5] * 8192
    if len(data) != expected:
        raise ValueError(f"expected {expected} bytes, got {len(data)}")
    prg = data[16:16 + header[4] * 16384]
    vectors = [int.from_bytes(prg[i:i + 2], "little") for i in (-6, -4)]
    vectors.append(int.from_bytes(prg[-2:], "little"))
    if any(address < 0x8000 for address in vectors):
        raise ValueError("interrupt/reset vectors must point into PRG ROM")
    print(f"{path}: OK; Mapper 0, PRG {header[4] * 16} KiB, "
          f"CHR 8 KiB, no battery; {len(data)} bytes")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 tools/check_rom.py ROM [ROM ...]")
    try:
        for rom_path in sys.argv[1:]:
            check(rom_path)
    except (OSError, ValueError) as error:
        sys.exit(str(error))
