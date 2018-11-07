import pandas as pd
import json
import csv
from QQZone.QQZoneFriendSpider import QQZoneFriendSpider

# 根据好友数据生成gexf
class CreateGexf(QQZoneFriendSpider):
    def __init__(self, file_name_head=""):


        QQZoneFriendSpider.__init__(self, analysis=True)
        if file_name_head != "":
            self.file_name_head = file_name_head
            self.FRIEND_DETAIL_LIST_FILE_NAME = 'friend/' + self.file_name_head + '_friend_detail_list.csv'
        self.data = pd.read_csv(self.FRIEND_DETAIL_LIST_FILE_NAME)
        print("获取文件：", self.FRIEND_DETAIL_LIST_FILE_NAME)
        self.SOURCE_TARGET_FILE_NAME = 'data/' + self.file_name_head + '_source_targets.csv'
        self.NODE_FILE_NAME = 'data/' + self.file_name_head + '_node.csv'
        self.RELATION_FILE_NAME = 'data/' + self.file_name_head + '_relation.csv'
        name = self.data['common_group_names']
        group_name = pd.DataFrame([name])
        self.people_name = self.data['nick_name'].values
        self.gravity = self.data['common_friend_num'].values
        self.common_group_names = group_name.T
        self.group_name_set = set()
        self.edge_list = []
        self.calculate()
        self.format_output()

    def calculate(self):
        group_list = []
        group_name_list = []
        for item in self.common_group_names.values:
            item_json = json.loads(item[0].replace("\'", "\""))
            group_list.extend(item_json)
        for i in group_list:
            group_name_list.append(i['name'])
        group_name_set = set(group_name_list)
        self.group_name_set = group_name_set
        self.group_people_dict = {}
        self.create_vertex_data()
        for group in group_name_set:
            group_id = self.node_df[self.node_df.node == group].id.values[0]
            group_people = []
            for i in range(len(self.common_group_names.values)):
                if str(self.common_group_names.values[i]).find(group) != -1:
                    name_id = self.node_df[self.node_df.node == self.people_name[i]].id.values[0]
                    group_people.append((self.people_name[i], self.gravity[i]))
                    self.edge_list.append(dict(group=group_id, name=name_id, gravity=self.gravity[i]))
            self.group_people_dict[group] = group_people

        self.create_relation_data()

    def create_vertex_data(self):
        all_group_name = list(self.group_name_set)
        all_people_name = list(self.people_name)
        all_group_name.extend(all_people_name)
        node_df = pd.DataFrame(all_group_name).reset_index()
        node_df.columns = ['id', 'node']
        self.node_df = node_df
        node_df.to_csv(self.NODE_FILE_NAME, index=False, header=False)

    def create_relation_data(self):
        edge_df = pd.DataFrame(self.edge_list)
        edge_df.to_csv(self.RELATION_FILE_NAME, index=False, header=False)


    def format_output(self):
        print("正在保存文件...", self.SOURCE_TARGET_FILE_NAME)
        with open(self.SOURCE_TARGET_FILE_NAME, "w", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            # 先写入columns_name
            writer.writerow(["Source", "Target", "Weight"])
            # 写入用writerow
            for key, value in self.group_people_dict.items():
                source = key
                target_list = value
                # print(key), print(target_list)
                for target in target_list:
                    writer.writerow([source, target[0], target[1]])

if __name__ == '__main__':
    gexf = CreateGexf(file_name_head="maicius")