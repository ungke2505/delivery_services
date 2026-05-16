#!/usr/bin/env python3
"""
Generate placeholder PWA icons menggunakan Python standard library.
Jalankan sekali saat setup: python3 generate_icons.py
Output: icon-192.png, icon-512.png, icon-driver-192.png, icon-driver-512.png
"""
import struct, zlib, os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

def make_png(size, bg_rgb, emoji_placeholder=""):
    """Buat PNG solid color sederhana."""
    r, g, b = bg_rgb
    # Buat pixel data (RGB)
    row = bytes([r, g, b] * size)
    raw = b''
    for _ in range(size):
        raw += b'\x00' + row  # filter byte per row

    def chunk(name, data):
        c = name + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    ihdr_data = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
    idat_data = zlib.compress(raw)

    return (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', ihdr_data)
        + chunk(b'IDAT', idat_data)
        + chunk(b'IEND', b'')
    )

icons = [
    ('icon-192.png',        192, (16, 185, 129)),   # green - customer
    ('icon-512.png',        512, (16, 185, 129)),
    ('icon-driver-192.png', 192, (245, 158, 11)),   # amber - driver
    ('icon-driver-512.png', 512, (245, 158, 11)),
]

for filename, size, color in icons:
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'wb') as f:
        f.write(make_png(size, color))
    print(f"✓ {filename} ({size}x{size})")

print("\nDone! Ganti dengan icon asli sebelum production.")
