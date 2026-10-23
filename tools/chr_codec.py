"""Encode an indexed 128x128 PNG atlas as NES 2bpp CHR data."""

def encode(image):
    if image.mode != 'P' or image.size != (128, 128):
        raise ValueError('each atlas must be a 128x128 indexed PNG (256 tiles)')
    if max(image.tobytes()) > 3:
        raise ValueError('tile pixels must be palette indices 0..3')
    result = bytearray()
    for ty in range(16):
        for tx in range(16):
            for plane in range(2):
                for y in range(8):
                    row = 0
                    for x in range(8):
                        row = row << 1 | (image.getpixel((tx*8+x, ty*8+y)) >> plane & 1)
                    result.append(row)
    return result
