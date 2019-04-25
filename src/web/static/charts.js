function draw_history_line(domName, result, chartName) {
    let temp = JSON.parse(result);
    let data = JSON.parse(temp);
    var xAxisData = data.map(function (item) {
        return item['time'] + ':' + item['content'];
    });
    var legendData = ['评论量', '点赞量'];
    var serieData = [];
    var metaDate = [
        data.map(function (item) {
            return item['cmt_total_num'];
        }),
        data.map(function (item) {
            return item['like_num'];
        })
    ];
    for (var v = 0; v < legendData.length; v++) {
        var serie = {
            name: legendData[v],
            type: 'line',
            symbol: "circle",
            symbolSize: 1,
            data: metaDate[v]
        };
        serieData.push(serie)
    }
    var colors = ["#036BC8", "#2EF7F3"];
    var option = {
        backgroundColor: '#0f375f',
        title: {
            text: chartName,
            x: 'center',
            textStyle: {
                color: '#98a0c4',
                fontWeight: 'bolder',
                fontSize: 25,
            }
        },

        legend: {
            show: true, left: "right", data: legendData, y: "5%",
            textStyle: {color: "#fff", fontSize: 14},
        },
        dataZoom: [{
            startValue: '2017-06-01 00:00:00',
            textStyle: {
                color: '#8392A5'
            },
            dataBackground: {
                areaStyle: {
                    color: '#8392A5'
                },
                lineStyle: {
                    opacity: 0.8,
                    color: '#8392A5'
                }
            },
        }, {
            type: 'inside'
        }],
        color: colors,
        tooltip: {
            trigger: 'axis',
            axisPointer: {type: 'shadow'},
            formatter: function (params) {
                var text = params[0].name.split(":");
                sub_text = '';
                for (var i = 1; i < text.length; i++) {
                    for (var j = 0; j < text[i].length; j++) {
                        if (j % 30 === 0 && j !== 0) {
                            sub_text = sub_text + text[i][j] + '<br />'
                        } else {
                            sub_text = sub_text + text[i][j]
                        }

                    }
                }
                return text[0] + '<br/>'
                    + sub_text + '<br />'
                    + params[0].seriesName + ' : ' + params[0].value + '<br/>'
                    + params[1].seriesName + ' : ' + params[1].value;
            },
            extraCssText: 'text-align: left;'
        },
        xAxis: [
            {
                type: 'category',
                axisLine: {show: true, lineStyle: {color: '#6173A3'}},
                axisLabel: {show: false, interval: 0},
                axisTick: {show: false},
                data: xAxisData,
            },
        ],
        yAxis: [
            {
                axisTick: {show: false},
                splitLine: {show: false},
                axisLabel: {textStyle: {color: '#9ea7c4', fontSize: 14}},
                axisLine: {show: true, lineStyle: {color: '#6173A3'}},
            },
        ],
        series: serieData
    };
    domName.setOption(option);
}