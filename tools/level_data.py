"""Load and validate Cargo Shift's editable level data."""

import json
from pathlib import Path


BOARD_WIDTH = 10
BOARD_HEIGHT = 8
SUPPORTED_TILES = frozenset("# .$@*+")


def _positive_int(level_name, level, field, maximum):
    value = level.get(field)
    if type(value) is not int or not 0 < value <= maximum:
        raise ValueError(
            f"{level_name}: {field} must be an integer in 1..{maximum}"
        )


def validate_levels(levels):
    if not isinstance(levels, list) or not levels:
        raise ValueError("levels.json must contain a non-empty JSON array")
    if len(levels) > 99:
        raise ValueError("the two-digit stage display supports at most 99 levels")

    names = set()
    for index, level in enumerate(levels, 1):
        label = f"level {index}"
        if not isinstance(level, dict):
            raise ValueError(f"{label} must be a JSON object")

        name = level.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{label}: name must be a non-empty string")
        if name in names:
            raise ValueError(f"{label}: duplicate name {name!r}")
        names.add(name)
        label = f"level {index} ({name})"

        rows = level.get("map")
        if not isinstance(rows, list) or not 3 <= len(rows) <= BOARD_HEIGHT:
            raise ValueError(f"{label}: map height must be in 3..{BOARD_HEIGHT}")
        if any(not isinstance(row, str) for row in rows):
            raise ValueError(f"{label}: every map row must be a string")
        width = len(rows[0])
        if not 3 <= width <= BOARD_WIDTH or any(len(row) != width for row in rows):
            raise ValueError(
                f"{label}: map must be rectangular and 3..{BOARD_WIDTH} cells wide"
            )

        tiles = set("".join(rows))
        unsupported = tiles - SUPPORTED_TILES
        if unsupported:
            raise ValueError(f"{label}: unsupported map tiles {sorted(unsupported)!r}")
        if any(cell != "#" for cell in rows[0] + rows[-1]):
            raise ValueError(f"{label}: top and bottom edges must be walls")
        if any(row[0] != "#" or row[-1] != "#" for row in rows):
            raise ValueError(f"{label}: left and right edges must be walls")

        text = "".join(rows)
        players = sum(text.count(tile) for tile in "@+")
        boxes = sum(text.count(tile) for tile in "$*")
        goals = sum(text.count(tile) for tile in ".*+")
        if players != 1:
            raise ValueError(f"{label}: expected exactly one player, got {players}")
        if boxes == 0 or boxes != goals:
            raise ValueError(
                f"{label}: expected a non-zero, equal number of boxes and goals"
            )

        _positive_int(label, level, "par", 65535)
        _positive_int(label, level, "min_pushes", 65535)

    return levels


def load_levels(path):
    path = Path(path)
    try:
        levels = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: invalid JSON: {error}") from error
    return validate_levels(levels)


def normalized_map(level):
    """Return an 80-cell, left-aligned map for the game model."""
    return "".join(row.ljust(BOARD_WIDTH, "#") for row in level["map"]).ljust(
        BOARD_WIDTH * BOARD_HEIGHT, "#"
    )


def room_offset(level):
    return (BOARD_WIDTH - len(level["map"][0])) // 2


def centered_map(level):
    """Return an 80-cell map centered to match the on-screen room."""
    offset = room_offset(level)
    return "".join(
        ("#" * offset + row).ljust(BOARD_WIDTH, "#") for row in level["map"]
    ).ljust(BOARD_WIDTH * BOARD_HEIGHT, "#")
