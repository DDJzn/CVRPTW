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


def network_to_json(bule_time,orange_time):

    bule_time = 15
    orange_time = 16

    # capacity_passengers = {str(i): random.randint(5, 10) for i in range(1, 17)}
    # capacity_packages = {str(i): random.randint(0, 10) for i in range(1, 17)}
    capacity_passengers = {str(i): 10 for i in range(1, 17)}
    capacity_packages = {str(i): 10 for i in range(1, 17)}
    travel_cost =  {str(i): 1 for i in range(1, 17)}

    travel_time = {str(i): {str(j): bule_time * distance(i,j) for j in range(1, 17) } for i in range(1, 17)}
    for i in range(1,17):
        travel_time[str(i)]["-1"] = min(distance(int(i),6),distance(int(i),7),distance(int(i),10),distance(int(i),11)) * bule_time + orange_time
        travel_time[str(i)]["9999"] = travel_time[str(i)]["-1"]

    travel_time["-1"] = {str(i): min(distance(int(i),6),distance(int(i),7),distance(int(i),10),distance(int(i),11)) * bule_time + orange_time for i in range(1, 17)}
    travel_time["-1"]["9999"] =0

    travel_time["9999"] = {str(i): min(distance(int(i),6),distance(int(i),7),distance(int(i),10),distance(int(i),11)) * bule_time + orange_time for i in range(1, 17)}
    travel_time["9999"]["-1"] =0



    # 要写入JSON文件的数据（可以是字典或列表等）
    data = { "capacity_passengers": capacity_passengers,
             "capacity_packages":capacity_packages,
             "travel_cost":travel_cost,
             "travel_time":travel_time,
             "M": 1000
            }

    # 指定要写入的文件名
    file_name = 'network_data.json'

    # 将数据写入JSON文件
    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


    print(f"network 数据已写入{file_name}")


def order_to_json(num_entries):
    unique_entries = set()  # 使用集合确保唯一性

    while len(unique_entries) < num_entries:
        startstation = random.randint(1, 16)  # 随机生成三位数的起点站
        endstation = startstation  # 初始化终点站为起点站
        while endstation == startstation:  # 确保终点站不与起点站相同
            endstation = random.randint(1, 16)  # 重新生成终点站

        entry = (startstation, endstation)  # 创建一个元组作为唯一标识

        if entry not in unique_entries:  # 检查是否已经存在
            unique_entries.add(entry)

    # 将元组转换为字典列表
    result = { }
    i=1
    for startstation, endstation in unique_entries:

        travel_distance = distance(startstation, endstation)
        starttime_earliest = random.randint(0, 120)
        number_passengers = random.randint(1,5)
        number_packages = random.randint(1, 5)

        seed = random.randint(0, 10)
        if seed >= 5:
            number_passengers = 0
        else:
            number_packages = 0

        result[str(i)]={
            "startstation": startstation * 1000 + i,
            "endstation": endstation * 1000 + i,
            "number_passengers": number_passengers,
            "number_packages": number_packages,
            "starttime_earliest": starttime_earliest,
            "starttime_lastest":starttime_earliest + 20,
            "endtime_earliest": 0,
            "endtime_lastest": starttime_earliest + travel_distance * 25,
            "profit": (number_passengers + number_packages) * travel_distance
        }
        i += 1

    # 指定要写入的文件名
    file_name = 'order_data.json'

    # 将数据写入JSON文件
    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)


    print(f"order 数据已写入{file_name}")


network_to_json(15,16)
order_to_json(50)

