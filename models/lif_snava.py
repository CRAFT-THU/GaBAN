from ir import *


class LIFSNAVA(Function):
    def __init__(self, floatType: ValueType) -> None:
        super().__init__()
        self.floatType = floatType

    def declare(self):
        # Variables
        self.ref_step = Variable("ref_step", ValueType.INTEGER)
        self.v_m = Variable("v_m", self.floatType)
        self.exc = Variable("exc", self.floatType)
        self.inh = Variable("inh", self.floatType)

        # Constants
        self.e_m = Const("e_m", self.floatType)
        self.v_tmp = Const("v_tmp", self.floatType)
        self.v_thresh = Const("v_thresh", self.floatType)
        self.v_reset = Const("v_reset", self.floatType)
        self.ref_time_m1 = Const("ref_time_m1", ValueType.INTEGER)

        # Outputs
        self.fire = Output("fire", ValueType.INTEGER)

    def activate(self):
        refract = self.ref_step > Literal(0, ValueType.INTEGER)
        self.ref_step = self.ref_step - refract
        self.v_m = mux(refract,
                       self.v_m,
                       self.e_m * self.v_m + self.v_tmp + self.exc - self.inh)

        self.fire = (self.v_m >= self.v_thresh)

        self.ref_step = mux(self.fire, self.ref_time_m1, self.ref_step)
        self.v_m = mux(self.fire, self.v_reset, self.v_m)

        # clear
        self.exc = Literal(0, ValueType.INTEGER)
        self.inh = Literal(0, ValueType.INTEGER)


if __name__ == '__main__':
    lif_snava = LIFSNAVA(ValueType.FLOAT)
    print(gen(lif_snava))
