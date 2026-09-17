"""Create the mmap-input.bin memory map used by the ECU tasks.

The ECU task (task_ecu_11F1.py) memory-maps MEM_RANGE (0x3fffff) bytes of
mmap-input.bin, so the file must be at least 0x3fffff + 1 bytes long (the
mapped length cannot exceed the file size). The firmware image is placed at
offset 0, i.e. at CPU address 0x000000.

Usage:
    python make_mmap_input.py <firmware-image.bin> [output.bin]

Relative paths are resolved against the current directory, e.g.:

    python make_mmap_input.py ../firmware/ecu-flash.bin
"""
import os
import sys

MEM_RANGE = 0x3fffff
DEFAULT_OUT = "mmap-input.bin"

if len(sys.argv) < 2:
    sys.exit(__doc__)

src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
size = MEM_RANGE + 1

with open(src, "rb") as f:
    image = f.read()
if len(image) > size:
    raise SystemExit(f"{src} is larger than {size} bytes")

data = bytearray(size)          # zero-filled CPU address space
data[0:len(image)] = image      # flash at address 0
with open(out, "wb") as f:
    f.write(data)

print(f"{out}: {os.path.getsize(out)} bytes "
      f"(flash image {os.path.basename(src)}: {len(image)} bytes at offset 0)")
