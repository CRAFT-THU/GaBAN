from ir import *


class Spike(Function):
    def declare(self):
        # Variables
        self.weight = Input("weight", ValueType.FLOAT, AccessPattern.INDEXED)
        self.exc = Variable("exc", ValueType.FLOAT, AccessPattern.INDEXED)

    def activate(self):
        self.exc = self.exc + self.weight


if __name__ == '__main__':
    spike = Spike()
    print(gen(spike))
