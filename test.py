import core.effects as e
import random
import numpy

arr = bytes([random.randint(0, 255) for _ in range(100)])

res = e.speedx(arr, 0.5)

print(len(arr), arr)
print(len(res), res)