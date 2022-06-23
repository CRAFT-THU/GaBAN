import sys
from typing import NamedTuple, Set, TypedDict


class Inst(TypedDict):
    lhs: str
    op: str
    args: list[str]
    live: Set[str]
    reg: int


insts: list[Inst] = []
num_registers = 32

with open(sys.argv[1], 'r') as f:
    for line in f:
        lhs, rhs = line.split('=')
        lhs = lhs.strip()
        op, arglist = rhs.split('(')
        op = op.strip()
        args = [s.strip() for s in arglist.strip()[:-1].split(',')]

        insts.append({
            'lhs': lhs,
            'op': op,
            'args': args,
            'live': set(),
            'reg': -1
        })

# liveness set
# reverse
live: Set[str] = set()
for i in range(len(insts)-1, -1, -1):
    insts[i]['live'] = live.copy()
    # def
    if insts[i]['lhs'] in live:
        live.remove(insts[i]['lhs'])
    # use
    for arg in insts[i]['args']:
        # only consider temp variables
        if arg.startswith("T_"):
            live.add(arg)

# linear register allocation
alloced_registers = set()
reg_mapping = {}
last_live: Set[str] = set()
for i in range(len(insts)):
    # TODO: spill
    if insts[i]['lhs'].startswith('T_'):
        for reg in range(num_registers):
            if reg not in alloced_registers:
                # assign lhs to reg
                insts[i]['reg'] = reg
                alloced_registers.add(reg)
                reg_mapping[insts[i]['lhs']] = reg
                break

    # free regs not in live set
    non_live = last_live - insts[i]['live']
    for freed in non_live:
        alloced_registers.remove(reg_mapping[freed])

    last_live = insts[i]['live'].copy()

# allocate index for memory
print("Memories:")
mem_mapping = {}
mem_count = 0

# first pass: indexed
for inst in insts:
    args = inst["args"]

    # rhs
    for i in range(len(args)):
        if (args[i].startswith("VI_") or args[i].startswith("II_") or args[i].startswith("CI_")) \
                and args[i] not in mem_mapping:
            # memory
            print(f'{mem_count}: {args[i]}')
            mem_mapping[args[i]] = mem_count
            mem_count = mem_count + 1

# second pass: exc/inh
for inst in insts:
    args = inst["args"]

    # rhs
    for i in range(len(args)):
        if (args[i] == 'V_exc' or args[i] == 'V_inh') \
                and args[i] not in mem_mapping:
            # memory
            print(f'{mem_count}: {args[i]}')
            mem_mapping[args[i]] = mem_count
            mem_count = mem_count + 1

# third pass: strided
for inst in insts:
    args = inst["args"]
    for i in range(len(args)):
        if (args[i].startswith("V_") or args[i].startswith("I_") or args[i].startswith("C_")) \
                and args[i] not in mem_mapping:
            # memory
            print(f'{mem_count}: {args[i]}')
            mem_mapping[args[i]] = mem_count
            mem_count = mem_count + 1

    # lhs
    if not inst["lhs"].startswith("T_") and inst["lhs"] not in mem_mapping:
        print(f'{mem_count}: {inst["lhs"]}')
        mem_mapping[inst["lhs"]] = mem_count
        mem_count = mem_count + 1
print(f'Total memories: {mem_count}')

print("Instructions:")
for inst in insts:
    args = inst["args"]
    for i in range(len(args)):
        if args[i] in reg_mapping:
            # register
            args[i] = f"r{reg_mapping[args[i]]}"
        elif args[i].isalnum():
            args[i] = f"{args[i]}"
        else:
            args[i] = f"mem[{mem_mapping[args[i]]}]"
    if inst['reg'] != -1:
        print(f'r{inst["reg"]} = {inst["op"]}({", ".join(args)})')
    else:
        print(
            f'mem[{mem_mapping[inst["lhs"]]}] = {inst["op"]}({", ".join(args)})')
    #print(f'live set = {inst["live"]}')
