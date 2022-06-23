import sys
import os

hex_file = sys.argv[1]
asm_file = sys.argv[2]
name = os.path.basename(hex_file).split('.')[0]

print("#include <stdint.h>")

memory_begin = False
with open(asm_file, "r") as f:
    for line in f:
        if 'Total memories:' in line:
            count = int(line.split(':')[1].strip())
            memory_begin = False
            break
        elif memory_begin:
            index, site = line.split(':')
            site = site.strip()
            print(f"const uint32_t offset_{site} = {index};")
        if line.startswith('Memories:'):
            memory_begin = True
print(f"const uint32_t mem_{name} = {count}; // number of memory sites")

print("// instructions")
print(f"const uint32_t inst_{name}[] = {{")
with open(hex_file, "r") as f:
    for line in f:
        line = line.strip()
        print(f"  0x{line},")
print("};")