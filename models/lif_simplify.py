from ir import *


class LIF(Function):
    def declare(self):
        # Variables
        self.ref_step = Variable("ref_step", ValueType.INTEGER)
        self.v_m = Variable("v_m", ValueType.FLOAT)
        self.i_e = Variable("i_e", ValueType.FLOAT)
        self.i_i = Variable("i_i", ValueType.FLOAT)
        self.exc = Variable("exc", ValueType.FLOAT)
        self.inh = Variable("inh", ValueType.FLOAT)

        # Constants
        self.e_m = Const("e_m", ValueType.FLOAT)
        self.v_tmp = Const("v_tmp", ValueType.FLOAT)
        self.c_e = Const("c_e", ValueType.FLOAT)
        self.c_i = Const("c_i", ValueType.FLOAT)
        self.e_e = Const("e_e", ValueType.FLOAT)
        self.e_i = Const("e_i", ValueType.FLOAT)
        self.v_thresh = Const("v_thresh", ValueType.FLOAT)
        self.v_reset = Const("v_reset", ValueType.FLOAT)
        self.ref_time_m1 = Const("ref_time_m1", ValueType.INTEGER)

        # Outputs
        self.fire = Output("fire", ValueType.INTEGER)

    def activate(self):
        refract = self.ref_step > Literal(0, ValueType.INTEGER)
        self.ref_step = self.ref_step - refract
        self.v_m = mux(refract,
                       self.v_m,
                       self.e_m * self.v_m + self.v_tmp +
                       self.i_e * self.c_e + self.i_i * self.c_i)
        self.i_e = self.i_e * self.e_e + self.exc
        self.i_i = self.i_i * self.e_i + self.inh

        self.fire = (self.v_m >= self.v_thresh)

        self.ref_step = mux(self.fire, self.ref_time_m1, self.ref_step)
        self.v_m = mux(self.fire, self.v_reset, self.v_m)

        # clear
        self.exc = Literal(0, ValueType.INTEGER)
        self.inh = Literal(0, ValueType.INTEGER)


lif = LIF()
print(gen(lif))
