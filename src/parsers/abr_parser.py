import re
import struct

from src.compression import decompress_image_data
from src.image_utils import make_greyscale_image

# Patron UUID usado en ABR v6+
_UUID_RE = re.compile(
    rb"\$[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\x00"
)


def read_abr(filepath):
    # Lee un archivo .abr y devuelve lista de imagenes PIL
    with open(filepath, "rb") as f:
        data = f.read()

    version = struct.unpack_from(">H", data, 0)[0]
    sub_version = struct.unpack_from(">H", data, 2)[0]

    if version in (1, 2):
        return _parse_v1v2(data, version)
    elif version in (6, 7, 10):
        return _parse_v6plus(data, sub_version)
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


# -- ABR v6+ (Photoshop CS2 en adelante) --

def _parse_v6plus(data, sub_version):
    # Parsea ABR v6+ buscando secciones 8BIM con key 'samp'
    brushes = []

    samp_start, samp_end = _find_8bim_section(data, b"samp")
    if samp_start is None:
        return brushes

    # Offset del header segun sub_version
    header_skip = 47 if sub_version == 1 else 301

    # Buscar todos los tags UUID en la seccion samp
    uuid_positions = [m.start() for m in _UUID_RE.finditer(data, samp_start, samp_end)]

    for idx, uuid_off in enumerate(uuid_positions):
        img = _try_read_brush_v6(data, uuid_off, header_skip, samp_end)
        if img is not None:
            brushes.append(img)

    return brushes


def _find_8bim_section(data, key):
    # Encuentra una seccion 8BIM por su key
    offset = 4
    while offset + 12 <= len(data):
        if data[offset:offset + 4] != b"8BIM":
            offset += 1
            continue
        section_key = data[offset + 4:offset + 8]
        block_size = struct.unpack_from(">I", data, offset + 8)[0]
        data_start = offset + 12
        data_end = data_start + block_size
        if section_key == key:
            return data_start, data_end
        offset = data_end
    return None, None


def _try_read_brush_v6(data, uuid_off, header_skip, samp_end):
    # Intenta leer un pincel v6 desde la posicion de su UUID
    # Prueba con el offset estandar y variaciones cercanas
    for skip in (header_skip, header_skip + 2, header_skip + 3,
                 header_skip - 1, header_skip + 1, header_skip - 2):
        bounds_off = uuid_off + skip
        if bounds_off + 19 > samp_end:
            continue

        top = struct.unpack_from(">i", data, bounds_off)[0]
        left = struct.unpack_from(">i", data, bounds_off + 4)[0]
        bottom = struct.unpack_from(">i", data, bounds_off + 8)[0]
        right = struct.unpack_from(">i", data, bounds_off + 12)[0]

        width = right - left
        height = bottom - top

        if not (0 < width < 16384 and 0 < height < 16384):
            continue

        depth = struct.unpack_from(">H", data, bounds_off + 16)[0]
        comp = data[bounds_off + 18]

        if depth not in (1, 8, 16) or comp not in (0, 1):
            continue

        pixel_off = bounds_off + 19
        pixel_data = decompress_image_data(
            data, pixel_off, width, height, depth, comp
        )
        if pixel_data is None:
            continue

        img = make_greyscale_image(pixel_data, width, height, depth)
        if img is not None:
            return img

    return None
