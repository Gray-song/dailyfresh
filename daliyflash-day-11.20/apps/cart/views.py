from django.shortcuts import render
from django.views.generic import View
from utils.mixin import LoginRequiredMixin
from django.http import JsonResponse
from goods.models import GoodSKU
from django_redis import get_redis_connection
# Create your views here.

class CartView(LoginRequiredMixin,View):
    '''购物车视图类'''
    def get(self,request):
        '''显示购物车页面'''
        #redis数据库获取购物车信息
        #1、连接数据库
        conn = get_redis_connection('default')
        user = request.user
        cart_key = 'cart_%d'%user.id
        cart_dict = conn.hgetall(cart_key)
        skus = []
        total_count = 0
        total_amount = 0
        for sku_id ,count in cart_dict.items():
            sku = GoodSKU.objects.get(id = sku_id)
            amount = sku.price*int(count)
            sku.count = count
            sku.amount = amount
            skus.append(sku)

            total_count += int(count)
            total_amount += amount

        context ={
            'skus':skus,
            'total_count':total_count,
            'total_amount':total_amount,
        }

        return render(request,'cart/cart.html',context)

class CartAddView(View):
    '''添加购物车视图类 '''
    def post(self,request):
        '''添加购物车业务'''
        #登录判断,因为用的是ajax提交的所以不能用登录装饰器
        user = request.user
        if not user.is_authenticated():
            #用户未登录
            context = {
                'res':1,
                'errmsg':'请先登录'
            }
            return JsonResponse(context)
        #获取数据
        sku_id = request.POST.get('cart_id')
        sku_count = request.POST.get('count')
        #数据校验
        #1、校验数据完整性
        if not all([sku_id,sku_count]):
            context = {
                'res':2,
                'errmsg':'数据不完整'
            }
            return JsonResponse(context)
        #2、校验商品id是否存在
        try:
            sku = GoodSKU.objects.get(id = sku_id)
        except GoodSKU.DoesNotExist:
            context ={
                'res':3,
                'errmsg':'商品地不存在',
            }
            return JsonResponse(context)
        #3、检验商品数量是否是数字
        try:
            count = int(sku_count)
        except Exception  as e:
            context ={
                'res':4,
                'errmsg':'商品数量不合法'
            }
            return JsonResponse(context)
        #业务处理：向redis数据库中添加购物车记录
        #连接redis数据库
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        cart_count = conn.hget(cart_key,sku.id)
        if cart_count:
            count += int(cart_count)
        if count > sku.stock:
            context = {
                'res':5,
                'errmsg':'库存不足',
            }
            return  JsonResponse(context)
        conn.hset(cart_key,sku_id,count)

        total_count = conn.hlen(cart_key)
        context = {
            'res':6,
            'total_count':total_count,
            'message':'添加成功'
        }
        #返回json数据对象
        return JsonResponse(context)


class CartUpdateView(View):
    '''购物车更新视图类'''
    def post(self,request):
        '''添加购物车业务'''
        # 登录判断,因为用的是ajax提交的所以不能用登录装饰器
        user = request.user
        if not user.is_authenticated():
            # 用户未登录
            context = {
                'res': 1,
                'errmsg': '请先登录'
            }
            return JsonResponse(context)
        # 获取数据
        sku_id = request.POST.get('cart_id')
        sku_count = request.POST.get('count')
        # 数据校验
        # 1、校验数据完整性
        if not all([sku_id, sku_count]):
            context = {
                'res': 2,
                'errmsg': '数据不完整'
            }
            return JsonResponse(context)
        # 2、校验商品id是否存在
        try:
            sku = GoodSKU.objects.get(id=sku_id)
        except GoodSKU.DoesNotExist:
            context = {
                'res': 3,
                'errmsg': '商品地不存在',
            }
            return JsonResponse(context)
        # 3、检验商品数量是否是数字
        try:
            count = int(sku_count)
        except Exception  as e:
            context = {
                'res': 4,
                'errmsg': '商品数量不合法'
            }
            return JsonResponse(context)
        # 业务处理：向redis数据库中添加购物车记录
        # 连接redis数据库
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # cart_count = conn.hget(cart_key, sku.id)
        # if cart_count:
        #     count += int(cart_count)
        if count > sku.stock:
            context = {
                'res': 5,
                'errmsg': '库存不足',
            }
            return JsonResponse(context)
        conn.hset(cart_key, sku_id, count)

        # 计算用户购物车中商品的总件数 {'1':5, '2':3}
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        context = {
            'res':6,
            'total_count':total_count,
            'message':'更新成功',
        }
        return JsonResponse(context)


class CartDelView(View):
    '''删除购物车记录视图'''
    def post(self,request):
        '''业务'''
        user = request.user
        if not user.is_authenticated():
            # 用户未登录
            context = {
                'res': 1,
                'errmsg': '请先登录'
            }
            return JsonResponse(context)
        # 获取数据
        sku_id = request.POST.get('cart_id')

        # 数据校验
        # 1、校验数据完整性
        if not sku_id:
            context = {
                'res': 2,
                'errmsg': '无效商品'
            }
            return JsonResponse(context)
        # 2、校验商品id是否存在
        try:
            sku = GoodSKU.objects.get(id=sku_id)
        except GoodSKU.DoesNotExist:
            context = {
                'res': 3,
                'errmsg': '商品地不存在',
            }
            return JsonResponse(context)

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 删除 hdel
        conn.hdel(cart_key, sku_id)

        # 计算用户购物车中商品的总件数 {'1':5, '2':3}
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)
        context = {
            'res':4,
            'total_count':total_count,
            'message':'删除成功'
        }
        return JsonResponse(context)
