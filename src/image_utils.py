import struct
from PIL import Image


def make_greyscale_image(pixel_data, width, height, depth):
    # Convierte datos de pixeles raw a imagen PIL greyscale
    if depth == 8:
        return Image.frombytes("L", (width, height), pixel_data)

    elif depth == 16:
        # 16-bit big-endian a 8-bit (solo MSB)
        pixels_8bit = bytearray()
        for i in range(0, len(pixel_data), 2):
            if i + 1 < len(pixel_data):
                val16 = struct.unpack_from(">H", pixel_data, i)[0]
                pixels_8bit.append(val16 >> 8)
            else:
                pixels_8bit.append(0)
        return Image.frombytes("L", (width, height), bytes(pixels_8bit))

    elif depth == 1:
        # 1-bit bitpacked a greyscale
        img = Image.frombytes("1", (width, height), pixel_data)
        return img.convert("L")

    return None
