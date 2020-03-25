from django.shortcuts import render,redirect
from  django.core.urlresolvers import reverse
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from  itsdangerous import SignatureExpired
from django.core.mail import send_mail
from daliyflash import settings
from django.http import HttpResponse
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate,login,logout
from utils.mixin import LoginRequiredMixin
import re
from user.models import User,Address
from goods.models import  GoodSKU
from order.models import OrderInfo,OrderGoods
from django_redis import get_redis_connection
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger

# Create your views here.
def register(request):
    '''显示注册页面'''
    if request.method =='GET':

        return render(request,'user/register.html')
    else:
        return register_handle(request)


def register_handle(request):
    '''注册业务'''
    #1、接受数据
    t_userName = request.POST.get('user_name')
    t_userPwd = request.POST.get('pwd')
    t_userEmail = request.POST.get('email')
    t_userAllow = request.POST.get('allow')
    #2、数据校验
    #2.1、数据完整性校验
    if not all([t_userName,t_userPwd,t_userEmail]):
        return render(request,'user/register.html',{'errmsg':'数据不完整'})
    # 2.2、邮箱校验
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', t_userEmail):
        return render(request, 'user/register.html', {'errmsg': '邮箱格式不正确'})
    #2.3、同意校验
    if t_userAllow !='on':
        return render(request,'user/register.html',{'errmsg':'请同意协议'})
    #2.4、用户名是否存在校验
    try:
        user = User.objects.get(username = t_userName)
    except User.DoesNotExist:
        user = None
    if user:
        # 用户名已存在
        return render(request, 'user/register.html', {'errmsg': '用户名已存在'})
    #3、业务处理：注册
    #3.1、 将数据插入数据库
    user = User.objects.create_user(t_userName, t_userEmail, t_userPwd)
    #3.2、将该用户改成非激活状态
    user.is_active = 0
    user.save()
    #3.3、发送激活码到注册的邮箱
    #3.3.1、生成token
    serializer = Serializer(settings.SECRET_KEY,3600)
    info = {'confirm':user.id}
    token = serializer.dumps(info)
    token = token.decode('utf-8')
    #3.3.2发送激活码
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver =[t_userEmail]
    html_message ='<h1>%s,欢迎您成为天天生鲜注册会员</h1>请点击下面的链接激活你的账户</br><a href ="http://192.168.17.131:8000/user/active/%s">http://192.168.17.131:8000/user/active/%s</a>'%(t_userName,token,token)
    send_mail(subject,message,sender,receiver,html_message = html_message)
    #4、返回响应
    return redirect(reverse('goods:index'))


class RegisterView(View):
    '''注册视图'''
    def get(self,request):
        return render(request, 'user/register.html')

    def post(self,request):
        '''注册业务'''
        # 1、接受数据
        t_userName = request.POST.get('user_name')
        t_userPwd = request.POST.get('pwd')
        t_userEmail = request.POST.get('email')
        t_userAllow = request.POST.get('allow')
        # 2、数据校验
        # 2.1、数据完整性校验
        if not all([t_userName, t_userPwd, t_userEmail]):
            return render(request, 'user/register.html', {'errmsg': '数据不完整'})
        # 2.2、邮箱校验
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', t_userEmail):
            return render(request, 'user/register.html', {'errmsg': '邮箱格式不正确'})
        # 2.3、同意校验
        if t_userAllow != 'on':
            return render(request, 'user/register.html', {'errmsg': '请同意协议'})
        # 2.4、用户名是否存在校验
        try:
            user = User.objects.get(username=t_userName)
        except User.DoesNotExist:
            user = None
        if user:
            # 用户名已存在
            return render(request, 'user/register.html', {'errmsg': '用户名已存在'})
        # 3、业务处理：注册
        user = User.objects.create_user(t_userName, t_userEmail, t_userPwd)
        user.is_active = 0
        user.save()
        # 3.3、发送激活码到注册的邮箱
        # 3.3.1、生成token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode('utf-8')
        # 3.3.2发送激活码
        #subject = '天天生鲜欢迎信息'
        #message = ''
        #sender = settings.EMAIL_FROM
        #receiver = [t_userEmail]
        #html_message = '<h1>%s,欢迎您成为天天生鲜注册会员</h1>请点击下面的链接激活你的账户</br><a href ="http://192.168.17.131:8000/user/active/%s">http://192.168.17.131:8000/user/active/%s</a>' % (
        #t_userName, token, token)
        #send_mail(subject, message, sender, receiver, html_message=html_message)
        send_register_active_email.delay(t_userEmail,t_userName,token)
        # 4、返回响应
        return redirect(reverse('goods:index'))



class ActiveView(View):
    '''用户激活业务'''
    def get(self,request,token):
        #解密
        try:
            serializer = Serializer(settings.SECRET_KEY, 3600)
            info = serializer.loads(token)
            #修改数据库
            t_userId = info['confirm']
            user = User.objects.get(id = t_userId)
            user.is_active =1
            user.save()
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            return HttpResponse('激活链接已过期')



class LoginView(View):
    '''登录业务'''
    def get(self,request):
        '''显示登录页'''
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(request, 'user/login.html', {'username':username, 'checked':checked})

    def post(self,request):
        '''登录验证'''
        #1、接收数据
        t_userName = request.POST.get('username')
        t_userPwd = request.POST.get('pwd')
        t_userRemember = request.POST.get('remember')
        #2、数据校验
        #在前端已经做了这一步
        #3、业务处理：登录验证
        user = authenticate(username=t_userName, password=t_userPwd)
        if user is not None:
            # the password verified for the user
            if user.is_active:
                #print("User is valid, active and authenticated")
                #记录登录状态到session
                login(request,user)
                next_url = request.GET.get('next',reverse('goods:index'))
                response = redirect(next_url)
                #判断是否记住用户名
                if t_userRemember == 'on':
                    response.set_cookie('username',t_userName,max_age=7*3600*24)
                else:
                    response.delete_cookie('username')

                return response
            else:
                #print("The password is valid, but the account has been disabled!")
                return render(request, 'user/login.html', {'errmsg': '用户未激活'})
        else:
            # the authentication system was unable to verify the username and password
            #print("The username and password were incorrect.")
            return render(request, 'user/login.html', {'errmsg': '用户名密码不正确'})
        #4、返回响应


class LogoutView(View):
    '''退出登录视图类'''
    def get(self,request):
        '''显示首页'''
        #清除session
        logout(request)
        return redirect(reverse('goods:index'))


class UserInfoView(LoginRequiredMixin,View):
    '''用户个人信息视图类'''

    def get(self,request):
        '''用户个人信息显示'''
        #page = 'user'
        #1、获取用户的基本信息
        user = request.user
        # try:
        #     address = Address.objects.get(user = user,is_default=True)
        # except Address.DoesNotExist:
        #     address = None

        address = Address.objects.get_default_address(user)
        #username  = user.username
        #addr = address.addr
        #phone = address.phone

        #2、获取用户最近浏览记录
        # from redis import StrictRedis
        # sr = StrictRedis(host='172.16.179.130', port='6379', db=9)
        con = get_redis_connection('default')

        history_key = 'history_%d' % user.id

        # 获取用户最新浏览的5个商品的id
        sku_ids = con.lrange(history_key, 0, 4)  # [2,3,1]

        # 从数据库中查询用户浏览的商品的具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)
        #
        # goods_res = []
        # for a_id in sku_ids:
        #     for goods in goods_li:
        #         if a_id == goods.id:
        #             goods_res.append(goods)

        # 遍历获取用户浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文
        context = {'page': 'user',
                   'address': address,
                   'goods_li': goods_li}

        #3、返回响应
        return render(request,'user/user_center_info.html',context)


class UserOrderView(LoginRequiredMixin, View):
    '''用户订单视图类'''

    def get(self, request,page):
        '''用户订单显示'''
        #获取订单信息
        user = request.user

        orders = OrderInfo.objects.filter(user = user).order_by('-create_time')

        if not  orders:
            # return redirect(reverse('cart:cart_show'))
            return  render(request,'user/user_center_order.html',{'page':'order'})
        for order in orders:
            #获取order_goods信息并添加到订单属性中
            order_goods = OrderGoods.objects.filter(order = order.order_id)
            for order_sku in order_goods:
                # 计算小计
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount,保存订单商品的小计
                order_sku.amount = amount
            # 动态给order增加属性，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            order.order_goods = order_goods

        #分页
        paginator = Paginator(orders, 2)
        # 判断用户传进来的页码是否有效
        try:
            orders_page = paginator.page(page)

        except PageNotAnInteger:
            orders_page = paginator.page(1)
        except EmptyPage:
            orders_page = paginator.page(paginator.num_pages)

        # 页码控制，让其只显示5个页码，显示当前夜前两个和当前页以及当前页的夜
        try:
            page = int(page)
        except Exception as e:
            page = 1

        # 1、如果不足物业全部显示，
        if paginator.num_pages < 5:
            pages = range(1, paginator.num_pages + 1)
        elif page <= 3:
            # 2如果当前页是前三页显示显示前五页
            pages = range(1, 6)
        elif page > (paginator.num_pages - 3):
            # 3、如果当前页是后三页
            pages = range(paginator.num_pages - 4, paginator.num_pages + 1)
        else:
            # 4、否则当前页前两页和当前页以及当前页的页
            pages = range(page - 2, page + 3)

        #page = 'order'
        return render(request, 'user/user_center_order.html',{'pages':pages,'orders_page':orders_page,'page': 'order'})


class AddressView(LoginRequiredMixin,View):
    '''地址信息视图类'''

    def get(self, request):
        '''地址信息显示'''
        #page = 'address'
        #判断是否有参数，有参数执行删除，
        addr_id = request.GET.get('addr_id')
        if addr_id :
            #执行删除操作
            # try:
            #     del_addr=Address.objects.get(id = int(addr_id))
            # except Address.DoesNotExist|Address.MultipleObjectsReturned:
            #     del_addr =None
            del_addr = Address.objects.get_id_address(int(addr_id))
            if del_addr :
                del_addr.delete()



        #查询该用户的所有地址信息
        user = request.user
        address = Address.objects.filter(user = user)
        addr_num = address.count()
        #for i in address:
        #    print(i.id,i.receiver)
        #print(address.count())
        context = {
            'page': 'address',
            'addr':address,
            'addr_num':addr_num,
        }
        #返回响应
        
        return render(request, 'user/user_center_site.html',context)



class AddAddressView(LoginRequiredMixin,View):
    '''添加新地址'''
    def get(self,request):
        '''显示修改或添加地址界面'''
        #判断有无参数有参数，若有将信息显示出来,显示空字符穿
        addr_id = request.GET.get('addr_id')
        receiver = ''
        address = ''
        zip_core = ''
        phone = ''
        default_addr = ''
        if addr_id:
            #执行编辑
            # try:
            #     update_addr=Address.objects.get(id = int(addr_id))
            # except Address.DoesNotExist|Address.MultipleObjectsReturned:
            #     update_addr =None
            update_addr = Address.objects.get_id_address(int(addr_id))
            if update_addr:
                receiver = update_addr.receiver
                address = update_addr.addr
                zip_core = update_addr.zip_code
                phone = update_addr.phone
                is_default = update_addr.is_default
                if is_default :
                    default_addr ='checked'
                else :
                    default_addr = ''

        else:
            #执行添加
            receiver = ''
            address = ''
            zip_core = ''
            phone = ''
            default_addr = ''

        context ={
            'page': 'address',
            'receiver':receiver,
            'address' :address,
            'zip_core':zip_core,
            'phone' :phone,
            'default_addr': default_addr,
        }

        #返回响应
        return render(request,'user/user_center_add_site.html',context)

    def post(self,request):
        '''添加或者更新地址'''
        # 获取数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_core = request.POST.get('zip_core')
        phone = request.POST.get('phone')
        default_addr = request.POST.get('default_addr')
        user = request.user
        addr_id = request.GET.get('addr_id')
        print(request.path)
        print(request.method)

        url = 'user/user_center_add_site.html'
        #校验数
        if not all([receiver, addr, phone]):
            print('1')

            return render(request, url, {'errmsg': '数据不完整','page': 'address',})

            # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            print('2')
            return render(request, url, {'errmsg': '手机格式不正确','page': 'address',})
        #业务处理
        if default_addr =='on':
            #判断之前是否有默认地址
            # try:
            #     default_address = Address.objects.get(user = user,is_default=True)
            # except Address.DoesNotExist:
            #     default_address = None
            default_address = Address.objects.get_default_address(user)
            #用默认地址将其设为非默认
            if default_address :
                default_address.is_default = False
                default_address.save()
            #设置默认地址
            new_default_addr = True
        else:
            new_default_addr = False

        #判断是否有参数

        if addr_id:
            # 有参数更新
            # try:
            #
            #     update_addr = Address.objects.get(id=int(addr_id))
            # except Address.DoesNotExist | Address.MultipleObjectsReturned:
            #
            #     update_addr = None
            update_addr = Address.objects.get_id_address(int(addr_id))
            if update_addr:

                update_addr.receiver = receiver
                update_addr.addr = addr
                update_addr.zip_code = zip_core
                update_addr.phone = phone
                update_addr.is_default = new_default_addr
                update_addr.save()


        else:
            #新增地址
            Address.objects.create(user=user,
                                   receiver=receiver,
                                   addr=addr,
                                   zip_code=zip_core,
                                   phone=phone,
                                   is_default=new_default_addr)



        #无参数添加
        #返回响应
        return redirect(reverse('user:address'))

