from ir import *
from izhikevich import *

if __name__ == '__main__':
    lif = Izhikevich(ValueType.FIXED)
    print(gen(lif))
