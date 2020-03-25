$(function(){
    // 加购物车动画

    var $add_goods = $('.add_goods')


    $add_goods.each(function(a){
        $(this).click(function(){
            var $add_x = $(this).offset().top;
            var $add_y = $(this).offset().left;
            var $to_x = $('.goods_count').offset().top;
            var $to_y = $('.goods_count').offset().left;

            sku_id = $(this).attr('sku_id')
            count = 1
            csrf = $('input[name="csrfmiddlewaretoken"]').val()
            param ={
                'cart_id':sku_id,
                'count':count,
                'csrfmiddlewaretoken':csrf
            }


            $.post('/cart/add',param,function(data){
                if (data.res == 6)
                {
                    $(".add_jump").css({'left':$add_y,'top':$add_x,'display':'block'})
                    $(".add_jump").stop().animate({
                        'left': $to_y+7,
                        'top': $to_x+7},
                        "fast", function() {
                            $(".add_jump").fadeOut('fast',function(){
                                $('.goods_count').html(data.total_count);
                            });

                    });
                }
                else
                {
                    alert(data.errmsg)
                }


            })


        })
    })
})