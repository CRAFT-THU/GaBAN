from __future__ import annotations
from typing import Any, Union, List
from enum import Enum
import math


class ValueKind(Enum):
    INPUT = 1
    CONST = 2
    VARIABLE = 3
    OUTPUT = 4
    LITERAL = 5
    TEMPORARY = 6


class AccessPattern(Enum):
    STRIDED = 1
    INDEXED = 2


class ValueType(Enum):
    INTEGER = 1
    FLOAT = 2
    FIXED = 3

    def suffix(self):
        if self == ValueType.INTEGER:
            return "_i"
        elif self == ValueType.FLOAT:
            return "_f"
        else:
            return "_x"


class GlobalState(object):
    def __init__(self):
        self.counter = 0
        # id -> name
        self.name_mapping = {}
        self.all_values = {}


global_state = GlobalState()


class Value:
    index: int
    kind: ValueKind
    ty: ValueType
    op: str
    args: List[Value]
    access: AccessPattern

    def __repr__(self) -> str:
        return f"<Value index={self.index} kind={self.kind} type={self.ty} op={self.op} args={self.args}, access={self.access}>"

    def __init__(self, index: int, kind: ValueKind, ty: ValueType, op: str, args: List[Value], access: AccessPattern = AccessPattern.STRIDED):
        self.index = index
        self.kind = kind
        self.ty = ty
        self.op = op
        self.args = args
        self.access = access
        global_state.all_values[self.index] = self

    def binary(self, other: Value, op: str, ty: ValueType) -> Value:
        return Value(new_index(),
                     ValueKind.TEMPORARY, ty, op, [self, other])

    def cmp(self, other: Value, op: str) -> Value:
        assert(self.ty == other.ty)
        return self.binary(other, f"{op}{self.ty.suffix()}", ValueType.INTEGER)

    def bin(self, other: Value, op: str) -> Value:
        assert(self.ty == other.ty)
        return self.binary(other, f"{op}{self.ty.suffix()}", self.ty)

    def __le__(self, other: Value) -> Value:
        return self.cmp(other, "le")

    def __ge__(self, other: Value) -> Value:
        return self.cmp(other, "ge")

    def __gt__(self, other: Value) -> Value:
        return self.cmp(other, "gt")

    def __sub__(self, other: Value) -> Value:
        return self.bin(other, "sub")

    def __mul__(self, other: Value) -> Value:
        return self.bin(other, "mul")

    def __truediv__(self, other: Value) -> Value:
        return self.bin(other, "div")

    def __add__(self, other: Value) -> Value:
        return self.bin(other, "add")

    def __and__(self, other: Value) -> Value:
        assert(self.ty == other.ty and self.ty == ValueType.INTEGER)
        return self.binary(other, f"and_i", self.ty)

    def __or__(self, other: Value) -> Value:
        assert(self.ty == other.ty and self.ty == ValueType.INTEGER)
        return self.binary(other, f"or_i", self.ty)

    def __invert__(self) -> Value:
        assert(self.ty == ValueType.INTEGER)
        return Value(new_index(),
                     ValueKind.TEMPORARY, self.ty, "not_i", [self])


class Function:
    def declare(self):
        raise "You should override declare() in subclass"

    def activate(self):
        raise "You should override activate() in subclass"

# utility functions


def new_index() -> int:
    global_state.counter = global_state.counter + 1
    return global_state.counter - 1


def get_name(value: Value) -> str:
    if value.access == AccessPattern.INDEXED:
        access = "I"
    else:
        access = ""
    if value.index in global_state.name_mapping:
        if value.kind == ValueKind.INPUT:
            return f"I{access}_{global_state.name_mapping[value.index]}"
        elif value.kind == ValueKind.VARIABLE:
            return f"V{access}_{global_state.name_mapping[value.index]}"
        elif value.kind == ValueKind.CONST:
            return f"C{access}_{global_state.name_mapping[value.index]}"
        elif value.kind == ValueKind.OUTPUT:
            return f"O{access}_{global_state.name_mapping[value.index]}"
        elif value.kind == ValueKind.LITERAL:
            return f"{global_state.name_mapping[value.index]}"
        else:
            return "unknown"
    else:
        return f"T_{value.index}"


def gen(func: Function) -> str:
    global global_state
    global_state = GlobalState()

    func.declare()
    func.activate()

    result = []
    temps = []
    update_values = []
    for i in range(global_state.counter):
        val = global_state.all_values[i]
        if val.kind == ValueKind.TEMPORARY:
            result.append(
                f"{get_name(val)} = {val.op}({', '.join([get_name(arg) for arg in val.args])})")
            temps.append(i)
        elif val.kind == ValueKind.OUTPUT or val.kind == ValueKind.VARIABLE:
            update_values.append(val)

    # find updated output and variable
    for value in update_values:
        val = func.__dict__[global_state.name_mapping[value.index]]

        found = False
        # insert right after assignment
        for i in range(len(result)):
            if result[i].split('=')[0].strip() == get_name(val):
                # insert fire instruction after write to fire
                if get_name(value) == 'O_fire':
                    result.insert(
                        i+1, f"{get_name(value)} = fire({get_name(val)})")
                else:
                    result.insert(
                        i+1, f"{get_name(value)} = move({get_name(val)})")

                found = True
                break

        # append at last if not found
        if not found:
            result.append(f"{get_name(value)} = move({get_name(val)})")

    return "\n".join(result)


def named(name: str, kind: ValueKind, ty: ValueType, access: AccessPattern) -> Value:
    ret = Value(new_index(), kind, ty, "nop", [], access)
    global_state.name_mapping[ret.index] = name
    global_state.all_values[ret.index] = ret
    return ret


def Input(name: str, ty: ValueType, access: AccessPattern = AccessPattern.STRIDED) -> Value:
    return named(name, ValueKind.INPUT, ty, access)


def Const(name: str, ty: ValueType, access: AccessPattern = AccessPattern.STRIDED) -> Value:
    return named(name, ValueKind.CONST, ty, access)


def Variable(name: str, ty: ValueType, access: AccessPattern = AccessPattern.STRIDED) -> Value:
    return named(name, ValueKind.VARIABLE, ty, access)


def Literal(name: Any, ty: ValueType, access: AccessPattern = AccessPattern.STRIDED) -> Value:
    if ty == ValueType.INTEGER:
        return named(str(int(name)), ValueKind.LITERAL, ty, access)
    elif ty == ValueType.FLOAT:
        return named(str(float(name)), ValueKind.LITERAL, ty, access)
    elif ty == ValueType.FIXED:
        # convert to integer representation
        num = round(float(name) * (1 << 23))
        if num < 0:
            num += 1 << 32
        return named(str(num), ValueKind.LITERAL, ty, access)
    else:
        raise Exception("bad value type")


def Output(name: str, ty: ValueType, access: AccessPattern = AccessPattern.STRIDED) -> Value:
    return named(name, ValueKind.OUTPUT, ty, access)


def mux(cond: Value, true: Value, false: Value) -> Value:
    assert(cond.ty == ValueType.INTEGER and true.ty == false.ty)
    return Value(new_index(),
                 ValueKind.TEMPORARY, true.ty, "mux", [cond, true, false])


def fexp(num: Value) -> Value:
    assert(num.ty == ValueType.FLOAT)
    return Value(new_index(),
                 ValueKind.TEMPORARY, ValueType.FLOAT, "exp_f", [num])


def poisson_distribution(lam: float) -> Value:
    imm = math.exp(-lam) * (2 ** 16)
    return Value(new_index(),
                 ValueKind.TEMPORARY, ValueType.INTEGER, "pois_imm", [Literal(imm, ValueType.INTEGER)])
