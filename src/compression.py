import struct


def unpackbits(data, offset, compressed_len, expected_len):
    # Descomprime datos usando PackBits (RLE de Adobe)
    result = bytearray()
    pos = offset
    end = offset + compressed_len

    while pos < end and len(result) < expected_len:
        n = data[pos]
        pos += 1

        if n < 128:
            # Copiar los siguientes n+1 bytes literalmente
            count = n + 1
            chunk = data[pos:pos + count]
            result.extend(chunk)
            pos += count
        elif n > 128:
            # Repetir el siguiente byte (257 - n) veces
            count = 257 - n
            if pos < end:
                result.extend(bytes([data[pos]]) * count)
                pos += 1
        # n == 128 -> no-op

    if len(result) > expected_len:
        result = result[:expected_len]
    elif len(result) < expected_len:
        result.extend(b"\x00" * (expected_len - len(result)))

    return bytes(result)


def decompress_image_data(data, offset, width, height, depth, compression):
    # Descomprime datos de imagen ABR (raw o RLE)
    bytes_per_pixel = max(1, depth // 8)
    row_bytes = width * bytes_per_pixel

    if compression == 0:
        total = row_bytes * height
        if offset + total > len(data):
            return None
        return data[offset:offset + total]

    elif compression == 1:
        # RLE/PackBits: cada fila tiene longitud comprimida (2 bytes)
        off = offset
        if off + height * 2 > len(data):
            return None

        row_lengths = []
        for _ in range(height):
            rl = struct.unpack_from(">H", data, off)[0]
            row_lengths.append(rl)
            off += 2

        result = bytearray()
        for row_len in row_lengths:
            if off + row_len > len(data):
                return None
            row_data = unpackbits(data, off, row_len, row_bytes)
            result.extend(row_data)
            off += row_len

        return bytes(result)

    return None
