from ir import *


def exp(val: Value, steps=3, use_exp=True):
    if use_exp:
        return fexp(val)

    res = Literal(1.0, ValueType.FLOAT)
    for i in range(steps, 0, -1):
        res = res * val * Literal(1.0 / i, ValueType.FLOAT) + \
            Literal(i, ValueType.FLOAT)
    return res


class HodgkinHuxley(Function):

    def declare(self):
        # Variables
        self.v = Variable("v", ValueType.FLOAT)
        self.n = Variable("n", ValueType.FLOAT)
        self.m = Variable("m", ValueType.FLOAT)
        self.h = Variable("h", ValueType.FLOAT)
        self.g_exc = Variable("g_exc", ValueType.FLOAT)
        self.g_inh = Variable("g_inh", ValueType.FLOAT)
        self.exc = Variable("exc", ValueType.FLOAT)
        self.inh = Variable("inh", ValueType.FLOAT)

        # Constants
        self.inv_c_m = Const("inv_c_m", ValueType.FLOAT)
        self.g_na = Const("g_na", ValueType.FLOAT)
        self.g_k = Const("g_k", ValueType.FLOAT)
        self.g_l = Const("g_l", ValueType.FLOAT)
        self.e_na = Const("e_na", ValueType.FLOAT)
        self.e_k = Const("e_k", ValueType.FLOAT)
        self.e_l = Const("e_l", ValueType.FLOAT)
        self.e_ex = Const("e_ex", ValueType.FLOAT)
        self.e_in = Const("e_in", ValueType.FLOAT)
        self.inv_tau_syn_E = Const("inv_tau_syn_E", ValueType.FLOAT)
        self.inv_tau_syn_I = Const("inv_tau_syn_I", ValueType.FLOAT)
        self.i_offset = Const("i_offset", ValueType.FLOAT)
        self.v_offset = Const("v_offset", ValueType.FLOAT)
        self.v_thresh = Const("v_thresh", ValueType.FLOAT)
        self.dt = Const("dt", ValueType.FLOAT)

        self.f0_032 = Literal(0.032, ValueType.FLOAT)
        self.f0_128 = Literal(0.128, ValueType.FLOAT)
        self.f0_2 = Literal(0.2, ValueType.FLOAT)
        self.f0_25 = Literal(0.25, ValueType.FLOAT)
        self.f0_28 = Literal(0.28, ValueType.FLOAT)
        self.f0_32 = Literal(0.32, ValueType.FLOAT)
        self.f0_5 = Literal(0.5, ValueType.FLOAT)
        self.f1 = Literal(1.0, ValueType.FLOAT)
        self.f2 = Literal(2, ValueType.FLOAT)
        self.f3 = Literal(3.0, ValueType.FLOAT)
        self.f4 = Literal(4, ValueType.FLOAT)
        self.f5 = Literal(5.0, ValueType.FLOAT)
        self.f10 = Literal(10.0, ValueType.FLOAT)
        self.f13 = Literal(13.0, ValueType.FLOAT)
        self.f15 = Literal(15.0, ValueType.FLOAT)
        self.f17 = Literal(17.0, ValueType.FLOAT)
        self.f18 = Literal(18.0, ValueType.FLOAT)
        self.f40 = Literal(40.0, ValueType.FLOAT)

        # Outputs
        self.fire = Output("fire", ValueType.INTEGER)

    def activate(self):
        i_na = self.g_na * self.m * self.m * \
            self.m * self.h * (self.v - self.e_na)
        i_k = self.g_k * self.n * self.n * \
            self.n * self.n * (self.v - self.e_k)
        i_l = self.g_l * (self.v - self.e_l)
        i_syn_exc = self.g_exc * (self.v - self.e_ex)
        i_syn_inh = self.g_inh * (self.v - self.e_in)
        self.v = self.v + (self.i_offset - i_na - i_k -
                           i_l - i_syn_exc - i_syn_inh) * self.inv_c_m * self.dt
        V = self.v - self.v_offset

        alpha_m = self.f0_32 * (self.f13 - V) / \
            (exp((self.f13 - V) * self.f0_25) - self.f1)
        beta_m = self.f0_28 * (V - self.f40) / \
            (exp((V - self.f40) * self.f0_2) - self.f1)
        alpha_n = self.f0_032 * (self.f15 - V) / \
            (exp((self.f15 - V) * self.f0_2) - self.f1)
        beta_n = self.f0_5 * exp((self.f10 - V) / self.f40)
        alpha_h = self.f0_128 * exp((self.f17 - V) / self.f18)
        beta_h = self.f4 / (self.f1 + exp((self.f40 - V) * self.f0_2))

        self.m = self.m + (alpha_m - (alpha_m + beta_m) * self.m) * self.dt
        self.h = self.h + (alpha_h - (alpha_h + beta_h) * self.h) * self.dt
        self.n = self.n + (alpha_n - (alpha_n + beta_n) * self.n) * self.dt

        self.g_exc = self.g_exc - self.g_exc * self.inv_tau_syn_E * self.dt + self.exc
        self.g_inh = self.g_inh - self.g_inh * self.inv_tau_syn_I * self.dt + self.inh

        self.fire = (self.v >= self.v_thresh)

        # clear
        self.exc = Literal(0, ValueType.INTEGER)
        self.inh = Literal(0, ValueType.INTEGER)


hh = HodgkinHuxley()
print(gen(hh))
