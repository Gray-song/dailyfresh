$(function(){
	var $slide_con = $('.slide_con');
	var $slide = $('.slide');
	var $slideli = $('.slide li');
	var $prev = $('.prev');
	var $next = $('.next');
	var $points = $('.points')
	var $len = $('.slide li').length;
	var $timer = null;
	var $isMove =false;

	for(var i =0 ;i < $len; i++)
	{
		var $li = $('<li>');
		if(i == 0)
		{
			$li.addClass('active');
		}
		$li.appendTo($points);
	}
	var $pointsli = $('.points li');
	var $currentPoint = 0;
	var $prevPoint = 0;
	$slideli.not(':first').css({'left':760});

	$pointsli.click(function(event) {
		/* Act on the event */
		$currentPoint = $(this).index();
		if($currentPoint == $prevPoint)
		{
			return;
		}
		// alert($currentPoint);
		$(this).addClass('active').siblings().removeClass('active');
		move();
	});

	$prev.click(function(event) {
		/* Act on the event */
		if($isMove)
		{
			return;
		}
		$isMove = true;
		$currentPoint--;
		$pointsli.eq($currentPoint).addClass('active').siblings().removeClass('active');
		move();

	});

	$next.click(function(event) {
		/* Act on the event */
		if($isMove)
		{
			return;
		}
		$isMove = true;
		autoplay();

	});

	$timer = setInterval(autoplay,3000);

	$slide_con.mouseenter(function(event) {
		/* Act on the event */
		clearInterval($timer);
	});

	$slide_con.mouseleave(function(event) {
		/* Act on the event */
		$timer = setInterval(autoplay,3000);
	});

	function autoplay(){
		$currentPoint++;
		$pointsli.eq($currentPoint).addClass('active').siblings().removeClass('active');
		move();
	}

	function move(){

		if($currentPoint<0)
		{
			$currentPoint = $len-1;
			$prevPoint = 0;
			$slideli.eq($currentPoint).css({'left':-760});
			$slideli.eq($prevPoint).animate({'left':760});
			$slideli.eq($currentPoint).animate({'left':0},function(){
				$isMove = false;
			});
			$prevPoint = $currentPoint;
			return;
		}

		if($currentPoint>($len-1))
		{
			$currentPoint = 0;
			$prevPoint = $len-1;
			$slideli.eq($currentPoint).css({'left':760});
			$slideli.eq($prevPoint).animate({'left':-760});
			$slideli.eq($currentPoint).animate({'left':0},function(){
				$isMove = false;
			});
			$prevPoint = $currentPoint;
			return;

		}

		if( $currentPoint > $prevPoint)
		{
			$slideli.eq($currentPoint).css({'left':760});
			$slideli.eq($prevPoint).animate({'left':-760});
		}
		else
		{
			$slideli.eq($currentPoint).css({'left':-760});
			$slideli.eq($prevPoint).animate({'left':760});
		}

		$slideli.eq($currentPoint).animate({'left':0},function(){
				$isMove = false;
		});
		$prevPoint = $currentPoint;

	}
})