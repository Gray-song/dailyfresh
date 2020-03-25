$(function () {
    //远程更新数据库
    error_update = false;
    total = 0;
    function upate_remote_cart_info(sku_id,count) {
        csrf = $('input[name="csrfmiddlewaretoken"]').val()
        param = {
            'cart_id':sku_id,
            'count':count,
            'csrfmiddlewaretoken':csrf,
        }
         // 设置ajax请求为同步
        $.ajaxSettings.async = false
        $.post('/cart/update',param,function (data) {
            if (data.res == 6)
            {
                error_update = false;
                total = data.total_count
            }
            else
            {
                error_update = true;
                alert(data.errmsg)
            }
        })
         // 设置ajax请求为异步
        $.ajaxSettings.async = true
    }


    //更新总价，总件数
    function update_page_info() {
        //获取cart_list_td所有被选中的input checkbox的父级ul标签
        total_count = 0;
        total_price = 0;
        $('.cart_list_td').find(':checked').parents('ul').each(function () {
            count = $(this).find('.num_show').val();
            amount = $(this).children('.col07').text();

            count = parseInt(count);
            amount = parseFloat(amount);

            total_count += count;
            total_price += amount;
        });

        //显示更新后的总价总件数
        $('.settlements').find('em').text(total_price.toFixed(2));
        $('.settlements').find('b').text(total_count);


    }

    //更新小计
    function update_goods_amount(sku_ul) {
        goods_price = sku_ul.find('.col05').text();
        goods_count = sku_ul.find('.num_show').val();

        goods_price = parseFloat(goods_price);
        goods_count = parseInt(goods_count);

        goods_amount = goods_price*goods_count;
        sku_ul.find('.col07').text(goods_amount.toFixed(2)+'元')
    }

    //    全选
    //获取settlements中所有input checkbox标签
    $('.settlements').find(':checkbox').change(function () {
        is_checked = $(this).prop('checked');
        $('.cart_list_td').find(':checkbox').each(function () {
            $(this).prop('checked',is_checked);
        });
        update_page_info();
    });

    //全选控制
    $('.cart_list_td').find(':checkbox').change(function () {
        total_items = $('.cart_list_td').find(':checkbox').length;
        checked_items = $('.cart_list_td').find(':checked').length;
        if (checked_items < total_items)
        {
            $('.settlements').find(':checkbox').prop('checked',false);
        }
        else
        {
            $('.settlements').find(':checkbox').prop('checked',true);
        }
        update_page_info();
    });
    //点击+事件
    $('.cart_list_td').find('.add').click(function () {
        //获取数显元素
        current_count = $(this).next().val()
        repertory = $(this).attr('repertory')
        sku_id = $(this).attr('sku_id')

        repertory = parseInt(repertory)
        current_count = parseInt(current_count)
        if (current_count === 1)
        {
            $(this).siblings().filter('.minus').removeClass('button_backgroud')
        }
        if (current_count < repertory)
        {

            count = parseInt(current_count) +1
            upate_remote_cart_info(sku_id,count)
            if (error_update == false)
            {
                $(this).next().val(count)
                update_goods_amount($(this).parents('ul'))
                $('.total_count').children('em').text(total)
                is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
                if(is_checked )
                {
                    update_page_info()
                }
            }

        }
        else
        {
            $(this).addClass('button_backgroud')
        }
    })

     //点击-事件
    $('.cart_list_td').find('.minus').click(function () {
        //获取数显元素
        current_count = $(this).prev().val()
        repertory = $(this).attr('repertory')
        sku_id = $(this).attr('sku_id')

        repertory = parseInt(repertory)
        current_count = parseInt(current_count)
        if (current_count <=  repertory)
        {
            $(this).siblings().filter('.add').removeClass('button_backgroud')
        }
        if (current_count > 1)
        {
            count = parseInt(current_count)-1
            upate_remote_cart_info(sku_id,count)
            if (error_update == false)
            {
                $(this).prev().val(count)
                update_goods_amount($(this).parents('ul'))
                $('.total_count').children('em').text(total)
                is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
                if(is_checked )
                {
                    update_page_info()
                }
            }

        }
        else
        {
            $(this).addClass('button_backgroud')
        }
    })

    //输入框获得焦点事件
    last_count = 0
    $('.cart_list_td').find('.num_show').focus(function () {
        last_count = $(this).val()
    })
    //输入框焦点消失事件
    $('.cart_list_td').find('.num_show').blur(function () {
        count = $(this).val()
		//数据校验，判断是否是数字，是否是空格，是否是负数
		if ((isNaN(count))||(count.trim().length == 0)||(parseInt(count) <= 0))
		{
			count = last_count
            $(this).val(last_count)
            return
		}

		sku_id = $(this).next().attr('sku_id')
		count = parseInt(count)
		upate_remote_cart_info(sku_id,count)
        if(error_update == false)
        {
            $(this).val(count)
            update_goods_amount($(this).parents('ul'))
            $('.total_count').children('em').text(total)
            is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
            if(is_checked )
            {
                update_page_info()
            }
        }
        else
        {
            // 设置商品的数目为用户输入之前的数目
            $(this).val(last_count)
        }


    })
    //点击删除事件
    $('.cart_list_td').children('.col08').children('a').click(function () {
        sku_id = $(this).parents('ul').find('.add').attr('sku_id')
        csrf = $('input[name="csrfmiddlewaretoken"]').val()
        param = {
            'cart_id':sku_id,
            'csrfmiddlewaretoken':csrf,
        };

        sku_ul = $(this).parents('ul')
        //如都删除没显示空空如也
        sku_ul_count = sku_ul.siblings('.cart_list_td').length
        str = '<ul class="cart_list_td clearfix">\n' +
            '                <li class="cart_no_goods">\n' +
            '                    空空如也\n' +
            '                </li>\n' +
            '            </ul>'

        $.post('/cart/del',param,function (data) {
            if (data.res == 4)
            {

                if(sku_ul_count == 0)
                {
                    sku_ul.after(str)
                }


                sku_ul.remove()
                total = data.total_count
                $('.total_count em').text(total)
                is_checked = sku_ul.find(':checkbox').prop('checked')
                if (is_checked)
                {

                    update_page_info()
                }
            }
            else
            {

                alert(data.errmsg)
            }
        })


    })

});