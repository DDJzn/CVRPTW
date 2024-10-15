# result processing from solution


import pandas as pd
import random
import json
import os
import re
import matplotlib.pyplot as plt
import numpy as np
import warnings
warnings.filterwarnings("ignore")
plt.rcParams['font.sans-serif'] = ['Heiti TC'] 
plt.rcParams['axes.unicode_minus'] = False 
plt.style.use('ggplot')
pd.set_option('display.max_rows', None)


result_path = 'result_test.sol'
df = pd.read_csv(result_path, sep=' ', skiprows=2, names=['variable', 'objective'])
df = df[round(df['objective']) != 0]
df = df[~df['variable'].str.contains('AU|sigma')]


# variables X
df_X = df[df['variable'].str.contains('X')]
print(df_X)


# variables t
df_t = df[df['variable'].str.contains('t')]
print(df_t)


# variables qr
df_qr = df[df['variable'].str.contains('qr')]
print(df_qr)


# variables S
df_S = df[df['variable'].str.contains('S')]
print(df_S)


