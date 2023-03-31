import pyRAPL
from time import sleep

def sum(a, b):
    return a + b


pyRAPL.setup()
measure = pyRAPL.Measurement("test")
for i in range(10):
    measure.begin()
    sum(1, 2)
    sleep(2)
    measure.end()
    print(measure.result.pkg)
