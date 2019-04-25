let history_dom = echarts.init(document.getElementById(HISTORY_DOM));
// avalon.config({
//     interpolate: ["[[","]]"]
// });

let vm = avalon.define({
    $id: 'qqzone',
    user: 'maicius',
    test1: 'hello',
    fetch_history_data: function () {
        $.ajax({
            url: '/get_history/maicius',
            success: function (result) {
                console.log(result);
                draw_history_line(history_dom, result, "QQ空间说说历史曲线图");
            }
        })
    }
});



$(document).ready(function () {
    vm.fetch_history_data();
});