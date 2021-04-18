import pandas as pd
import json
import csv
from src.spider.QQZoneFriendSpider import QQZoneFriendSpider


# 根据好友数据生成gexf
class CreateGexf(QQZoneFriendSpider):
    def __init__(self, file_name_head=""):
        QQZoneFriendSpider.__init__(self, analysis=True)
        if file_name_head != "":
            self.file_name_head = file_name_head
            self.FRIEND_DETAIL_LIST_FILE_NAME = 'friend/' + self.file_name_head + '_friend_detail_list.csv'
        self.data = pd.read_csv(self.FRIEND_DETAIL_LIST_FILE_NAME)
        self.remove_waste_index()
        print("获取文件：", self.FRIEND_DETAIL_LIST_FILE_NAME)
        self.SOURCE_TARGET_FILE_NAME = '../data/' + self.file_name_head + '_source_targets.csv'
        self.NODE_FILE_NAME = '../data/' + self.file_name_head + '_node.csv'
        self.RELATION_FILE_NAME = '../data/' + self.file_name_head + '_relation.csv'
        name = self.data['common_group_names']
        group_name = pd.DataFrame([name])
        self.people_name = self.data['nick_name'].values
        self.gravity = self.data['common_friend_num'].values
        self.add_friend_time = self.data['add_friend_time'].values
        self.common_group_names = group_name.T
        self.group_name_set = set()
        self.edge_list = []
        self.change_image_url()
        self.calculate()
        self.format_output()

    def remove_waste_index(self):
        index_list = self.data[self.data['add_friend_time'] == 0].index
        self.data.drop(index=index_list, inplace=True)

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
                    if self.node_df.loc[self.node_df.node == group, 'add_friend_time'].values[0] == -1:
                        self.node_df.loc[self.node_df.node == group, 'add_friend_time'] = self.add_friend_time[i]
                    name_id = self.node_df[self.node_df.node == self.people_name[i]].id.values[0]
                    group_people.append((self.people_name[i], self.gravity[i]))
                    self.edge_list.append(dict(group=group_id, name=name_id))
            self.group_people_dict[group] = group_people

        self.node_df.to_csv(self.NODE_FILE_NAME, index=False, header=False)
        self.create_relation_data()

    def create_vertex_data(self):
        all_group_name = pd.DataFrame(list(self.group_name_set))
        all_group_name['friend'] = '-1'
        all_group_name['add_friend_time'] = -1
        all_group_name['img'] = 'http://localhost:8080/static/maicius/458546290_s.png'
        all_people_name = self.data[['nick_name', 'common_friend_num', 'add_friend_time','img']]
        all_people_name.columns = [0, 'friend', 'add_friend_time', 'img']
        node_df = pd.DataFrame(pd.concat([all_group_name, all_people_name], axis=0)).reset_index()
        node_df.drop(['index'],axis=1, inplace=True)
        node_df.fillna('http://localhost:8080/static/maicius/458546290.jpg', inplace=True)
        node_df = node_df.reset_index()
        node_df.columns = ['id', 'node', 'friend', 'add_friend_time', 'img']
        cols = ['id', 'node', 'friend', 'add_friend_time', 'img']
        node_df = node_df.ix[:, cols]
        self.node_df = node_df

    def change_image_url(self):
        raw_url = self.data['img'].values
        for url in raw_url:
            uin = url.split('/')[-2]
            new_url = "http://localhost:8080/static/maicius/" + uin + '.jpg'
            self.data.loc[self.data['friend_uin'] == int(uin), 'img'] = new_url

    def create_relation_data(self):
        edge_df = pd.DataFrame(self.edge_list)
        columns = ['group', 'name']
        edge_df = edge_df.ix[:, columns]
        edge_df.to_csv(self.RELATION_FILE_NAME, index=False, header=False, sep=" ")


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
