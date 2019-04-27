// let history_dom = echarts.init(document.getElementById(HISTORY_DOM));
// avalon.config({
//     interpolate: ["[[","]]"]
// });
let history_dom;
let vm = avalon.define({
    $id: 'qqzone',
    nick_name: '',
    qq_id: '',
    stop_num: -1,
    stop_date: '-1',
    no_delete: false,
    agree: false,
    disable: 'false',
    qq_cookie: '',

    fetch_history_data: function () {
        $.ajax({
            url: '/get_history/1272082503/maicius',
            success: function (result) {
                console.log(result);
                draw_history_line(history_dom, result, "QQ空间说说历史曲线图");
            }
        })
    },

    submit_data: function () {
        if (vm.qq_id !== '' && vm.nick_name !== '' && vm.cookie !== '') {
            if (agree) {
                $.ajax({
                    url: "/start_spider",
                    type: 'post',
                    data: {
                        nick_name: vm.nick_name,
                        qq: vm.qq_id,
                        stop_time: vm.stop_date,
                        mood_num: vm.stop_num,
                        cookie: vm.qq_cookie,
                        no_delete: vm.no_delete
                    },
                    success: function (data) {
                        data = JSON.parse(data);
                        if (data.result === 1) {
                            alert("success");
                            vm.query_interval = setInterval(function () {
                                vm.query_spider_info(vm.qq_id);
                            }, 1000);
                        } else {
                            alert("未知错误:" + data.result)
                        }
                    }
                })
            }
        } else {
            alert("昵称、QQ号、Cookie不能为空");
        }

    },

    query_spider_info: function (QQ) {
        $.ajax({
            url: '/query_spider_info/' + QQ,
            type: 'GET',
            success: function (data) {
                data = JSON.parse(data);
                if (data.finish === 1) {
                    clearInterval(vm.query_interval);
                }else{
                    console.log(data.info);
                }
            }
        })
    },
    clear_cache: function () {

    }
});

vm.$watch("agree", function (new_v, old_v) {
    switch (new_v) {
        case true:
            $('#start_get').removeAttr("disabled");
            break;
        case false:
            $('#start_get').attr("disabled", "true");
            break;
    }
});

$(document).ready(function () {
    //vm.fetch_history_data();
});