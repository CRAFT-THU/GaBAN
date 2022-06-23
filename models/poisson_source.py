from ir import *


class PoissonSource(Function):
    def declare(self):
        # Outputs
        self.fire = Output("fire", ValueType.INTEGER)

    def activate(self):
        self.fire = poisson_distribution(0.5)


if __name__ == '__main__':
    poisson_source = PoissonSource()
    print(gen(poisson_source))
