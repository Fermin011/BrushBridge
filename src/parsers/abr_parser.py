import struct

from src.compression import decompress_image_data
from src.image_utils import make_greyscale_image


def read_abr(filepath):
    # Lee un archivo .abr y devuelve lista de imagenes PIL
    with open(filepath, "rb") as f:
        data = f.read()

    version = struct.unpack_from(">H", data, 0)[0]
    sub_version = struct.unpack_from(">H", data, 2)[0]

    if version in (1, 2):
        return _parse_v1v2(data, version)
    else:
        raise ValueError(f"Version ABR no soportada: {version}")


def _parse_v1v2(data, version):
    # Parsea pinceles de ABR v1 y v2
    brushes = []
    offset = 4

    while offset < len(data):
        if offset + 6 > len(data):
            break

        brush_type = struct.unpack_from(">H", data, offset)[0]
        brush_size = struct.unpack_from(">I", data, offset + 2)[0]
        brush_end = offset + 6 + brush_size

        # Solo procesar sampled brushes (tipo 2)
        if brush_type == 2:
            img = _read_sampled_brush(data, offset + 6, version)
            if img is not None:
                brushes.append(img)

        offset = brush_end

    return brushes


def _read_sampled_brush(data, offset, version):
    # Lee un sampled brush de ABR v1/v2
    spacing = struct.unpack_from(">H", data, offset + 4)[0]
    off = offset + 6

    # v2 tiene nombre unicode antes de los bounds
    if version == 2:
        name_len = struct.unpack_from(">I", data, off)[0]
        off += 4
        if name_len > 0:
            off += name_len * 2

    if off + 8 > len(data):
        return None

    top = struct.unpack_from(">H", data, off)[0]
    left = struct.unpack_from(">H", data, off + 2)[0]
    bottom = struct.unpack_from(">H", data, off + 4)[0]
    right = struct.unpack_from(">H", data, off + 6)[0]
    off += 8

    width = right - left
    height = bottom - top

    if width <= 0 or height <= 0 or width > 10000 or height > 10000:
        return None

    depth = struct.unpack_from(">H", data, off)[0]
    compression = data[off + 2]
    off += 3

    pixel_data = decompress_image_data(data, off, width, height, depth, compression)
    if pixel_data is None:
        return None

    return make_greyscale_image(pixel_data, width, height, depth)
