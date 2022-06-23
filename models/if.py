from ir import *


class IF(Function):
    def declare(self):
        # Variables
        self.ref_step = Variable("ref_step", ValueType.INTEGER)
        self.v_m = Variable("v_m", ValueType.FLOAT)
        self.exc = Variable("exc", ValueType.FLOAT)
        self.inh = Variable("inh", ValueType.FLOAT)

        # Constants
        self.c_e = Const("c_e", ValueType.FLOAT)
        self.c_i = Const("c_i", ValueType.FLOAT)
        self.v_thresh = Const("v_thresh", ValueType.FLOAT)
        self.v_reset = Const("v_reset", ValueType.FLOAT)
        self.ref_time = Const("ref_time", ValueType.INTEGER)

        # Outputs
        self.fire = Output("fire", ValueType.INTEGER)

    def activate(self):
        refract = self.ref_step > Literal(0, ValueType.INTEGER)
        self.ref_step = self.ref_step - refract
        self.v_m = mux(refract,
                       self.v_m,
                       self.v_m + self.exc * self.c_e + self.inh * self.c_i)
        self.fire = (self.v_m >= self.v_thresh)

        self.ref_step = mux(self.fire, self.ref_time -
                            Literal(1, ValueType.INTEGER), self.ref_step)
        self.v_m = mux(self.fire, self.v_reset, self.v_m)

        # clear
        self.exc = Literal(0, ValueType.INTEGER)
        self.inh = Literal(0, ValueType.INTEGER)


if_model = IF()
print(gen(if_model))
