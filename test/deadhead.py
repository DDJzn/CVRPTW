# coding=utf-8
import json
import random


def distance(a, b):
    # 检查输入是否在有效范围内
    if not (1 <= a <= 16) or not (1 <= b <= 16):
        return False

    # 计算行和列索引
    row_a, col_a = (a - 1) // 4, (a - 1) % 4
    row_b, col_b = (b - 1) // 4, (b - 1) % 4

    # 判断是否相邻
    return (abs(row_a - row_b) + abs(col_a - col_b))




bule_time = 15
orange_time = 16

capacity_passengers = {str(i): random.randint(20, 30) for i in range(1, 17)}
capacity_passengers = {str(i): random.randint(20, 30) for i in range(1, 17)}
travel_cost =  {str(i): 1 for i in range(1, 17)}

travel_time = {str(i): {str(j): bule_time * distance(i,j) for j in range(1, 17) } for i in range(1, 17)}
for i in range(1,17):
    travel_time[str(i)]["-1"] = min(distance(int(i),6),distance(int(i),7),distance(int(i),10),distance(int(i),11)) * bule_time + orange_time
    travel_time[str(i)]["9999"] = travel_time[str(i)]["-1"]

travel_time["-1"] = {str(i): min(distance(int(i),6),distance(int(i),7),distance(int(i),10),distance(int(i),11)) * bule_time + orange_time for i in range(1, 17)}
travel_time["-1"]["9999"] =0

travel_time["9999"] = {str(i): min(distance(int(i),6),distance(int(i),7),distance(int(i),10),distance(int(i),11)) * bule_time + orange_time for i in range(1, 17)}
travel_time["9999"]["-1"] =0

print(travel_time)