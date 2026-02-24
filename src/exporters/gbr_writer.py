import struct


def write_gbr(image, filepath, brush_name, spacing=25):
    # Escribe una imagen como archivo GBR (GIMP/Krita brush)
    if image.mode != "L":
        image = image.convert("L")

    width, height = image.size
    pixel_data = image.tobytes()

    name_bytes = brush_name.encode("utf-8") + b"\x00"
    header_size = 28 + len(name_bytes)
    magic = 0x47494D50  # "GIMP"

    header = struct.pack(
        ">IIIIIII",
        header_size, 2, width, height,
        1, magic, spacing
    )

    with open(filepath, "wb") as f:
        f.write(header)
        f.write(name_bytes)
        f.write(pixel_data)
