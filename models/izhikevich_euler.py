from ir import *


class IzhikevichEuler(Function):
    def declare(self):
        # Variables
        self.v = Variable("v", ValueType.FLOAT)
        self.u = Variable("u", ValueType.FLOAT)
        self.exc = Variable("exc", ValueType.FLOAT)
        self.inh = Variable("inh", ValueType.FLOAT)

        # Constants
        self.a = Const("a", ValueType.FLOAT)
        self.b = Const("b", ValueType.FLOAT)
        self.c = Const("c", ValueType.FLOAT)
        self.d = Const("d", ValueType.FLOAT)
        self.f0_04 = Literal(0.04, ValueType.FLOAT)
        self.f125_0 = Literal(125.0, ValueType.FLOAT)
        self.f140_0 = Literal(140.0, ValueType.FLOAT)
        self.v_thresh = Const("v_thresh", ValueType.FLOAT)
        self.dt = Const("dt", ValueType.FLOAT)

        # Outputs
        self.fire = Output("fire", ValueType.INTEGER)

    def activate(self):
        # matches NEST simulator
        # https://github.com/nest/nest-simulator/blob/a387311d97d56d79efc0d5e6bff8fa55b9df7328/models/izhikevich.cpp#L202-L211
        # one step Euler
        # different from Izhikevich paper
        self.v = self.v + self.exc - self.inh
        self.v = self.v + (self.v * self.f0_04 * (self.v +
                           self.f125_0) + self.f140_0 - self.u) * self.dt
        self.u = self.u + self.a * (self.b * self.v - self.u) * self.dt

        self.fire = (self.v >= self.v_thresh)

        self.v = mux(self.fire, self.c, self.v)
        self.u = mux(self.fire, self.d + self.u, self.u)

        # clear
        self.exc = Literal(0, ValueType.INTEGER)
        self.inh = Literal(0, ValueType.INTEGER)


izhikevich_euler = IzhikevichEuler()
print(gen(izhikevich_euler))
