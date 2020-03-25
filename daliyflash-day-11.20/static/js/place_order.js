$(function () {
    //点击提交订单事件
    $('#order_btn').click(function () {
        var sku_ids = $(this).attr('sku_ids');
        var addr_id = $('input[name="addr_id"]:checked').val()
        var pay_style = $('input[name="pay_style"]:checked').val()
        var csrf = $('input[name="csrfmiddlewaretoken"]').val()
        param = {
            'sku_ids':sku_ids,
            'addr_id':addr_id,
            'pay_style':pay_style,
            'csrfmiddlewaretoken':csrf,
        }
        $.post('/order/commit_order',param,function (data) {
            if (data.res == 8)
            {
                // 创建成功
                    localStorage.setItem('order_finish',2);
                    $('.popup_con').fadeIn('fast', function() {

                        setTimeout(function(){
                            $('.popup_con').fadeOut('fast',function(){
                                window.location.href = '/user/order/1';
                            });
                        },3000)

                    });
            }
            else{
                alert(data.errmsg)
            }
        })
    })
})