import sys

opcode_map = {
    'lu_imm': 0b00_00001,
    'ls_imm': 0b00_00010,
    'pois_imm': 0b00_00011,

    'not_i': 0b01_00000,
    'gt_i_imm': 0b01_00001,
    'sub_i_imm': 0b01_00010,
    'or_i_imm': 0b01_00011,
    'move': 0b01_00100,
    'fire': 0b01_00101,
    'exp_f': 0b01_00110,

    'and_i': 0b10_00000,
    'or_i': 0b10_00001,
    'sub_i': 0b10_00010,
    'mul_f': 0b10_00011,
    'add_f': 0b10_00100,
    'sub_f': 0b10_00101,
    'ge_f': 0b10_00110,
    'div_f': 0b10_00111,
    'le_f': 0b10_01000,
    'mul_x': 0b10_01001,
    'add_x': 0b10_01010,
    'sub_x': 0b10_01011,
    'ge_x': 0b10_01100,
    'le_x': 0b10_01101,

    'muladd_f': 0b11_00000,
    'mulsub_f': 0b11_00001,
    'mux': 0b11_00010,
}


def name_to_index(name: str) -> int:
    if name.startswith("mem["):
        # mem[0]
        index = int(name.split("[")[1][:-1])
        assert(index < 32)
        return 0b100000 + index
    elif name.startswith("r"):
        # r0
        index = int(name[1:])
        assert(index < 32)
        return 0b000000 + index
    assert(False)


with open(sys.argv[1], "r") as f:
    lines = f.readlines()
    for line in lines:
        if '=' not in line:
            continue
        lhs, rhs = line.split('=')
        lhs = lhs.strip()
        op, arglist = rhs.split('(')
        op = op.strip()
        args = [s.strip() for s in arglist.strip()[:-1].split(',')]

        src = [0, 0, 0]
        imm0 = 0
        for i in range(len(args)):
            if args[i].startswith("mem[") or args[i].startswith("r"):
                src[i] = name_to_index(args[i])
            else:
                # literal
                imm = int(args[i])
                if i == 1:
                    # imm[12:0]
                    # bounds checking
                    assert(-2 ** 13 <= imm and imm <= 2 ** 13 - 1)
                    src[1] = imm >> 7
                    src[2] = (imm >> 1) & 0b111111
                    imm0 = imm & 1
                elif i == 0:
                    # imm[18:0]
                    # bounds checking
                    assert(-2 ** 19 <= imm and imm <= 2 ** 19 - 1)
                    src[0] = imm >> 13
                    src[1] = (imm >> 7) & 0b111111
                    src[2] = (imm >> 1) & 0b111111
                    imm0 = imm & 1
                else:
                    assert False, "Unexpected imm"
        dst = name_to_index(lhs)
        opcode = opcode_map[op]

        inst = (src[0] << 26) + (src[1] << 20) + \
            (src[2] << 14) + (imm0 << 13) + (dst << 7) + opcode
        print(hex(inst)[2:].zfill(8))
