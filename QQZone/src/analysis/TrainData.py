from QQZone.src.analysis.TrainMood import TrainMood
import numpy as np
import xgboost as xgb
from sklearn.model_selection import GridSearchCV
import pandas as pd
from sklearn import preprocessing

class TrainData(TrainMood):
    def __init__(self):
        TrainMood.__init__(self, use_redis=True, debug=True, file_name_head='maicius')
        self.train_data = pd.read_csv(self.FINAL_RESULT_TRAIN_DATA)

    # 计算MSE
    def cal_MSE(self, y_predict, y_real):
        n = len(y_predict)
        print("样本数量:" + str(n))
        return np.sum(np.square(y_predict - y_real)) / n


    def train_with_xgboost(self, x_train, y_train, x_test, y_test):
        xgb_model = xgb.XGBModel()
        params = {
            'booster': ['gblinear'],
            'silent': [1],
            'learning_rate': [x for x in np.round(np.linspace(0.01, 1, 20), 2)],
            'reg_lambda': [lambd for lambd in np.logspace(0, 3, 50)],
            'objective': ['reg:linear']
        }
        print('begin')
        clf = GridSearchCV(xgb_model, params,
                           scoring='neg_mean_squared_error',
                           refit=True)
        clf.fit(x_train, y_train)
        preds = clf.predict(x_test)
        print('test mse:', self.cal_MSE(preds, y_test))
        best_parameters, score, _ = max(clf.grid_scores_, key=lambda x: x[1])
        print('Raw RMSE:', score)
        for param_name in sorted(best_parameters.keys()):
            print("%s: %r" % (param_name, best_parameters[param_name]))

    def pre_process_data(self,train_data):
        train_df = train_data.sample(frac=0.7)
        test_df = train_data.sample(frac=0.3)
        train_Y = train_df[['n_E']].values
        test_Y = test_df[['n_E']].values
        train_df.drop(['n_E', 'Unnamed: 0'], axis=1, inplace=True)
        test_df.drop(['n_E', 'Unnamed: 0'], axis=1, inplace=True)
        X = np.vstack((train_df.values, test_df.values))
        # normalize数据
        X = preprocessing.scale(X)
        train_x = X[0:len(train_df)]
        test_x = X[len(train_df):]

        return train_x, train_Y, test_x, test_Y

if __name__ == '__main__':
    td = TrainData()
    train_df, train_Y, test_df, test_Y = td.pre_process_data(td.train_data)
    td.train_with_xgboost(train_df, train_Y, test_df, test_Y)
