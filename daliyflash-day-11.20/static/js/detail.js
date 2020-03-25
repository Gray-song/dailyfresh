$(function(){
	var $num_show  = $('.num_show')
	var $add_button = $('.add')
	var $minus_button = $('.minus')

	var $repertory =$('#repertory')  //获取库存
	var $hidden_msg = $('.hidden_msg')
	//评论切换变量
	var $desc = $('#desc');
	var $comment = $('#comment');
	var $desc_detail = $('#desc_detail')
	var $comment_list = $('#comment_list')

    //更新总价
	update_goods_amount()
	function update_goods_amount() {
		var $num_show  = $('.num_show')
		var $pirce = $('.show_prize em')
		var $total_price = $('.total em')
		current_count = parseInt($num_show.val())
		price =  parseInt(parseFloat($pirce.html())*100)
		total_price = (current_count) * price
		total_price = total_price/100
		$total_price.html(total_price.toString()+'元')

    }
    // $(".add_jump").css({'left':$add_y+80,'top':$add_x+10,'display':'block'})
    $('.add_cart').click(function()
	{

		var $add_x = $('.add_cart').offset().top;
		var $add_y = $('.add_cart').offset().left;
		var $to_x = $('.goods_count').offset().top;
		var $to_y = $('.goods_count').offset().left;
		sku_id = $(this).attr('sku_id')
		count = Number($num_show.val())
		csrf = $('input[name="csrfmiddlewaretoken"]').val()
		param ={
			'cart_id':sku_id,
			'count':count,
			'csrfmiddlewaretoken':csrf
		}
		$.post('/cart/add',param,function(data){
			if (data.res == 6)
			{
				$(".add_jump").css({'left':$add_y+80,'top':$add_x+10,'display':'block'})
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
    //详情评论切换

	$desc.click(function(){
		$desc.addClass('active').siblings().removeClass('active');
		$desc_detail.show().siblings().hide()

	})

	$comment.click(function(){
		$comment.addClass('active').siblings().removeClass('active');
		$comment_list.show().siblings().hide()

	})

    // 数量控制


	$add_button.click(function(){
		// 避免浮点数运算不准确
		repertory = parseInt($repertory.val())
		current_count = parseInt($num_show.val())
		if (current_count === 1)
		{
			$minus_button.removeClass('minus_bakcground')
		}
		if (current_count < repertory)
		{

			$num_show.val(current_count+1)
			update_goods_amount()
		}
		else
		{
			$add_button.addClass('minus_bakcground')
			$hidden_msg.show()
		}


	})

	$minus_button.click(function(){
		// 避免浮点数运算不准确


		repertory = parseInt($repertory.val())
		current_count = parseInt($num_show.val())
		if (current_count <= repertory)
		{
			$add_button.removeClass('minus_bakcground')
			$hidden_msg.hide()
		}
		if (current_count > 1)
		{


			$num_show.val(current_count-1)
			update_goods_amount()

		}
		else
		{
			$minus_button.addClass('minus_bakcground')
		}

	})

	$('.num_show').blur(function () {
		count = $(this).val()
		//数据校验，判断是否是数字，是否是空格，是否是负数
		if ((isNaN(count))||(count.trim().length == 0)||(parseInt(count) <= 0))
		{
			count = 1
		}
		else
		{
			count = parseInt(count)
		}
		count = $(this).val(count)
		update_goods_amount()

    })

})