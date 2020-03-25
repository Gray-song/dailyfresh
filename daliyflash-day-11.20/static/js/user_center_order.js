$(function () {
    $('.oper_btn').click(function () {
        order_id = $(this).attr('order_id')
        order_status = $(this).attr('status')
        csrf = $('input[name="csrfmiddlewaretoken"]').val()
        param = {
            'order_id':order_id,
            'csrfmiddlewaretoken':csrf,
        }

        if(order_status == 1)
        {

            $.post('/order/pay_order',param,function (data) {
                if(data.res == 4)
                {
                    // 引导用户到支付页面
                    window.open(data.pay_url)
                    // 浏览器访问/order/check, 获取支付交易的结果
                    // ajax post 传递参数:order_id
                    $.post('/order/order_check', params, function (data){
                        if (data.res == 4){
                            alert('支付成功')
                            // 刷新页面
                            location.reload()
                        }
                        else{
                            alert(data.errmsg)
                        }
                    })
                }
                else
                {
                    alert(data.errmsg  )
                }
            })
        }
        else if ((order_status == 4) ||(order_status == 5) ){
            // 其他情况
            // 跳转到评价页面

            location.href = '/order/order_comment/'+order_id
        }

    })
})