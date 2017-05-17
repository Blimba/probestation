import numpy as np
import matplotlib.pyplot as plt

sigmoid_center = 1.5
sigmoid_steepness = 0.8
sigmoid_high = 20
sigmoid_low = 4
d=np.arange(32768,65535)

tmp = ((d-32768)/3277) - sigmoid_center
threshold1 = sigmoid_high*(0.5-(tmp/(sigmoid_steepness+np.abs(tmp)))*0.5)+sigmoid_low
v = (d-32768)/3277
threshold2 = np.repeat(20,36000-32768)
threshold2 = np.append(threshold2,27000/(d[(36000-32768):]-35000)+4)
plt.plot(v,threshold1)
plt.plot(v,threshold2)
plt.show()
