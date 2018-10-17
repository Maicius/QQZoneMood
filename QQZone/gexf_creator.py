import pandas as pd
import json
import csv

# 文件名
data = pd.read_csv('maicius_friend_detail_list1.csv')

name = data['common_group_names']

group_name = pd.DataFrame([name])
people_name = data['nick_name'].values
gravity = data['common_friend_num'].values

common_group_names = group_name.T
group_list = []
group_name_list = []
for item in common_group_names.values:
    item_json = json.loads(item[0].replace("\'", "\""))
    group_list.extend(item_json)

for i in group_list:
    group_name_list.append(i['name'])

group_name_set = set(group_name_list)

group_people_dict = {}
for group in group_name_set:
    group_people = []
    for i in range(len(common_group_names.values)):
        if str(common_group_names.values[i]).find(group) != -1:
            group_people.append((people_name[i], gravity[i]))

    group_people_dict[group] = group_people

# print(group_people_dict)

target_list = []

with open("source_target.csv", "w") as csvfile:
    writer = csv.writer(csvfile)

    # 先写入columns_name
    writer.writerow(["Source", "Target", "Weight", "Type"])
    # 写入用writerow
    for key, value in group_people_dict.items():
        source = key
        target_list = value
        # print(key), print(target_list)
        for target in target_list:
            writer.writerow([key, target[0], target[1], "undirected"])
