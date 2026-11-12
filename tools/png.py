"""Minimal PNG reader (stdlib only) so checks run on every team machine and in CI
without installing Pillow. Supports 8-bit, non-interlaced grayscale, RGB, RGBA,
gray+alpha and palette images. That covers Unreal HighResShot / Screenshot output
and normal exports from Aseprite, GIMP and Photoshop."""
import struct
import zlib

_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def read_png(path):
    """Return (width, height, rows) where rows is a list of lists of (r, g, b, a)."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG file")
    pos = 8
    idat = []
    palette = None
    trns = None
    width = height = bit_depth = color_type = interlace = None
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"PLTE":
            palette = [tuple(chunk[i:i + 3]) for i in range(0, len(chunk), 3)]
        elif ctype == b"tRNS":
            trns = chunk
        elif ctype == b"IDAT":
            idat.append(chunk)
        elif ctype == b"IEND":
            break
    if bit_depth != 8:
        raise ValueError(f"{path}: only 8-bit PNGs are supported (got {bit_depth}-bit). Re-export as 8-bit.")
    if interlace:
        raise ValueError(f"{path}: interlaced PNGs are not supported. Re-export without interlacing.")
    if color_type not in _CHANNELS:
        raise ValueError(f"{path}: unsupported PNG color type {color_type}")
    ch = _CHANNELS[color_type]
    raw = zlib.decompress(b"".join(idat))
    stride = width * ch
    prev = bytearray(stride)
    rows = []
    i = 0
    for _ in range(height):
        ftype = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if ftype == 1:
            for x in range(ch, stride):
                line[x] = (line[x] + line[x - ch]) & 0xFF
        elif ftype == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif ftype == 3:
            for x in range(stride):
                left = line[x - ch] if x >= ch else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 0xFF
        elif ftype == 4:
            for x in range(stride):
                left = line[x - ch] if x >= ch else 0
                upleft = prev[x - ch] if x >= ch else 0
                line[x] = (line[x] + _paeth(left, prev[x], upleft)) & 0xFF
        elif ftype != 0:
            raise ValueError(f"{path}: bad PNG filter type {ftype}")
        prev = line
        px = []
        for x in range(width):
            o = x * ch
            if color_type == 2:
                px.append((line[o], line[o + 1], line[o + 2], 255))
            elif color_type == 6:
                px.append((line[o], line[o + 1], line[o + 2], line[o + 3]))
            elif color_type == 0:
                v = line[o]
                px.append((v, v, v, 255))
            elif color_type == 4:
                v = line[o]
                px.append((v, v, v, line[o + 1]))
            else:
                idx = line[o]
                r, g, b = palette[idx]
                a = trns[idx] if trns is not None and idx < len(trns) else 255
                px.append((r, g, b, a))
        rows.append(px)
    return width, height, rows


def write_png(path, width, height, rows):
    """Write RGBA rows to an 8-bit PNG. Used by tests to build fixtures."""
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for r, g, b, a in row:
            raw += bytes((r, g, b, a))

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw))))
        f.write(chunk(b"IEND", b""))
