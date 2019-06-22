const HISTORY_DOM = 'history_dom';

const SPIDER_STATE = {
    CONFIG: 0,
    SPIDER: 1,
    FINISH: 2
};

const SPIDER_TEXT = {
    STOP: '正在停止爬虫并保存数据...',
    DOING: '正在获取说说数据:',
    FINISH: '成功获取说说数据:'
};

const CLEAN_DATA_TEXT = {
    DOING: '数据分析中,请稍后...',
    FINISH: '数据分析完成，请点击下方链接或查看数据按钮进行查看'
};

const CLEAN_DATA_STATE = {
    DOING: 0,
    FINISH: 1
};

const VIEW_DATA_STATE = {
    config: 0,
    data: 1
};

const SPIDER_FRIEND_TEXT = {
    STOP: '正在停止爬虫并保存数据...',
    DOING: '正在获取好友数据:',
    FINISH: '成功获取好友数据:'
};

const SPIDER_FRIEND_STATE = {
    DOING: 0,
    FINISH: 1
};

const LOGIN_STATE = {
    UNLOGIN: 0,
    LOGIN_SUCCESS: 2,
    LOGINING: 1,
    LOGIN_FAIELD: -1
};

const WARM_TIP = [
    {
        one: '如进度条长时间未走动',
        second: '请点击 强制停止 按钮'
    },
    {
        one: '如想提前结束爬虫并保存数据',
        second: '请点击下方 停止 按钮'
    },
    {
        one: '登陆成功后可以退出本页面',
        second: '稍后凭QQ号和校验码可直接查询数据'
    }
];


const INVALID_LOGIN = -2;
const SUCCESS_STATE = 1;
const FINISH_FRIEND = 2;
const FAILED_STATE = -1;
const WAITING_USER_STATE = -3;
const ALREADY_IN = -4;
const CHECK_COOKIE = 0;

const LOGGING_STATE = 3;
const NOT_MATCH_STATE = -5;

const WRONG_PASSWORD_QQ = "QQ号校验码不匹配,如果在爬虫过程中出现此问题，通常是网络错误，请稍后再试";