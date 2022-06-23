from ir import *


class Izhikevich(Function):
    def __init__(self, floatType: ValueType) -> None:
        super().__init__()
        self.floatType = floatType

    def declare(self):
        # Variables
        self.v = Variable("v", self.floatType)
        self.u = Variable("u", self.floatType)
        self.exc = Variable("exc", self.floatType)
        self.inh = Variable("inh", self.floatType)

        # Constants
        self.a = Const("a", self.floatType)
        self.b = Const("b", self.floatType)
        self.c = Const("c", self.floatType)
        self.d = Const("d", self.floatType)
        self.v_thresh = Const("v_thresh", self.floatType)
        self.dt = Const("dt", self.floatType)
        self.f0_5 = Literal(0.5, self.floatType)
        self.f0_04 = Literal(0.04, self.floatType)
        self.f5_0 = Literal(5.0, self.floatType)
        self.f125_0 = Literal(125.0, self.floatType)
        self.f140_0 = Literal(140.0, self.floatType)

        # Outputs
        self.fire = Output("fire", ValueType.INTEGER)

    def activate(self):
        self.v = self.v + self.exc - self.inh
        self.v = self.v + self.f0_5 * self.dt * \
            (self.v * self.f0_04 * (self.v + self.f125_0) + (self.f140_0 - self.u))
        self.v = self.v + self.f0_5 * self.dt * \
            (self.v * self.f0_04 * (self.v + self.f125_0) + (self.f140_0 - self.u))
        self.u = self.u + self.a * (self.b * self.v - self.u) * self.dt

        self.fire = (self.v >= self.v_thresh)

        self.v = mux(self.fire, self.c, self.v)
        self.u = mux(self.fire, self.d + self.u, self.u)

        # clear
        self.exc = Literal(0, ValueType.INTEGER)
        self.inh = Literal(0, ValueType.INTEGER)


if __name__ == '__main__':
    izhikevich = Izhikevich(ValueType.FLOAT)
    print(gen(izhikevich))
