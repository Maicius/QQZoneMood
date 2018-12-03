import pandas as pd

class drawPicture():
    def __init__(self):
        self.data = pd.read_csv("maicius_final_train.csv")


    def draw_sentiment(self):
        self.data.loc[self.data.sentiments == -1, 'sentiments'] = 0
        data = self.data.groupby(['sentiments'], axis=0).mean().reset_index()
        print(data['n_E'])

    def draw_time(self):
        data = self.data.groupby(['time_state'], axis=0).mean().reset_index()
        print(data['n_E'])

    def draw_type(self):
        data = self.data.groupby(['type'], axis=0).mean().reset_index()
        print(data['n_E'])

    def draw_score(self):
        data = self.data.groupby(['score'], axis=0).mean().reset_index()
        data = data[['score','n_E']]
        print(data)

if __name__ =='__main__':
    draw = drawPicture()
    draw.draw_sentiment()
    draw.draw_score()
