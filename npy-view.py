# run -> python3 python/WifiBruteie/npy-view.py
import numpy as np
data = np.load("sample.npy", allow_pickle=True)
print(data)
