const HISTORY_DOM = 'history_dom';

const SPIDER_STATE = {
    CONFIG: 0,
    SPIDER: 1,
    FINISH: 2
};

const SPIDER_TEXT = {
    STOP: '正在停止爬虫并保存数据...',
    DOING : '正在获取:',
    FINISH: '成功获取数据:'
};

const CLEAN_DATA_TEXT = {
    DOING: '数据分析中...',
    FINISH: '数据分析完成，点击下面链接查看数据'
};

const CLEAN_DATA_STATE = {
    DOING: 0,
    FINISH: 1
};