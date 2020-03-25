$(function(){

	var $isSuccessfulUserName = false;
	var $isSuccessfulPwd = false;
	var $isSuccessfulCpwd = false;
	var $isSuccessfulEmail = false;
	var $isSuccessfulAllow = true;

	var $userName = $("#user_name");
	var $pwd = $("#pwd");
	var $cpwd = $("#cpwd");
	var $email = $("#email");
	var $allow = $("#allow");
	var $reg_form = $(".reg_form");


	$userName.blur(function()
	{
		check_username();
	})

	$userName.focus(function()
	{
		$(this).next().hide();
	})

	$pwd.blur(function() 
	{
		/* Act on the event */
		check_pwd();
	});

	$pwd.focus(function() 
	{
		/* Act on the event */
		$(this).next().hide();
	});

	$cpwd.blur(function(event) {
		/* Act on the event */
		check_cpwd();
	});

	$cpwd.focus(function(event) {
		/* Act on the event */
		$(this).next().hide();

	});

	$email.blur(function(event) {
		/* Act on the event */
		check_email();
	});

	$email.focus(function(event) {
		/* Act on the event */
		$(this).next().hide();
	});

	$allow.click(function(event) {
		/* Act on the event */
		if($(this).is(':checked'))
		{
			$isSuccessfulAllow = true;
			$(this).siblings('span').hide();
		}
		else
		{
			$isSuccessfulAllow = false;
			$(this).siblings('span').html('请勾选同意');
			$(this).siblings('span').show();
		}
	});

	function check_username()
	{
		var $value = $userName.val();
		var $re = /^\w{6,20}$/;
		// alert($value);
		if( $value == "")
		{
			$userName.next().html("用户名不能为空");
			$userName.next().show();
			$isSuccessfulUserName = false;
		}
		else if($re.test($value))
		{
			$userName.next().hide();
			$isSuccessfulUserName = true;
		}
		else
		{
			$userName.next().html("用户名是5到20个英文或数字，还可包含“_”");
			$userName.next().show();
			$isSuccessfulUserName = false;
		}
	}

	function check_pwd()
	{
		var $value = $pwd.val();
		var $re = /^[\w!@#$%^&*]{6,20}$/;
		if( $value == "")
		{
			$pwd.next().html("密码不能为空");
			$pwd.next().show();
			$isSuccessfulPwd = false;
		}
		else if($re.test($value))
		{
			$pwd.next().hide();
			$isSuccessfulPwd = true;
		}
		else
		{
			$pwd.next().html("密码是6到20位字母、数字，还可包含@!#$%^&*字符");
			$pwd.next().show();
			$isSuccessfulPwd = false;
		}
	}

	function check_cpwd()
	{
		var pwd = $pwd.val();
		var cpwd = $cpwd.val();
		if($isSuccessfulPwd)
		{
			if(pwd == cpwd)
			{
				$cpwd.next().hide();
				$isSuccessfulCpwd = true;
			}
			else
			{
				$cpwd.next().html("两次输入的密码不一致");
				$cpwd.next().show();
				$isSuccessfulCpwd = false;
			}
		}
		else
		{
			$cpwd.next().html("请先输入合法密码");
			$cpwd.next().show();
			$isSuccessfulCpwd = false;
		}
	}

	function check_email()
	{
		var $value = $email.val();
		var $re = /^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$/i;
		// alert($value);
		if( $value == "")
		{
			$email.next().html("邮箱不能为空");
			$email.next().show();
			$isSuccessfulEmail = false;
		}
		else if($re.test($value))
		{
			$email.next().hide();
			$isSuccessfulEmail = true;
		}
		else
		{
			$email.next().html("你输入的邮箱格式不正确");
			$email.next().show();
			$isSuccessfulEmail = false;
		}
	}

	$reg_form.submit(function() {
		/* Act on the event */
		check_username();
		check_pwd();
		check_cpwd();
		check_email();


		if(($isSuccessfulUserName==true)&&($isSuccessfulPwd == true)
			&&($isSuccessfulCpwd == true)&&($isSuccessfulEmail == true)
			&&($isSuccessfulAllow == true))
		{
			return true;
		}
		else
		{
			return false;
		}
	});

})