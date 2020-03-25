from django.shortcuts import render,redirect
from django.views.generic import View
from goods.models import GoodType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner,GoodSKU
from order.models import OrderGoods
from django_redis import get_redis_connection
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
# Create your views here.

#index
class IndexView(View):
    '''首页视图类'''

    def get(self,request):
        '''显示首页'''
        #读取缓存
        context = cache.get('index_page_data')
        if context is None:
            print('设置缓存')
            #获取种类数据
            goods_types = GoodType.objects.all()
            #获取轮番显示数据
            index_goods_banners = IndexGoodsBanner.objects.all().order_by('index')
            #获取广告展示数据
            index_promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
            #获取分类展示数据
            for goods_type in goods_types:
                image_banners = IndexTypeGoodsBanner.objects.filter(type = goods_type,display_type = 1).order_by('index')
                title_banners = IndexTypeGoodsBanner.objects.filter(type = goods_type,display_type = 0).order_by('index')
                goods_type.image_banners = image_banners
                goods_type.title_banners = title_banners
            context = {
                'goods_types': goods_types,
                'index_goods_banners': index_goods_banners,
                'index_promotion_banners': index_promotion_banners,
            }
            cache.set('index_page_data',context,3600)
        #获取购物车数量
        #判断是否登录
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            conn_redis = get_redis_connection('default')
            cart_key = 'cart_%d'%(user.id,)
            cart_count = conn_redis.hlen(cart_key)

        context.update(cart_count=cart_count)


        return render(request, 'goods/index.html',context)
#goods/goods_id
class DetailView(View):
    '''商品详情视图类'''
    def get(self,request,goods_id):
        '''显示查询结果'''
        #获取商品详细信息
        try:
            goods_sku = GoodSKU.objects.get(id = goods_id)
        except GoodSKU.DoesNotExist:
            return redirect(reverse('goods:index'))
        #获取商品分类信息
        goods_types = GoodType.objects.all()

        #获取推荐商品（根据同种类商品添加时间排序）
        new_goods = GoodSKU.objects.filter(type = goods_sku.type).order_by('-create_time')[0:2]

        # 获取同一个SPU的其他规格商品
        same_spu_skus = GoodSKU.objects.filter(goods=goods_sku.goods).exclude(id=goods_id)

        #获取评论
        goods_comment = OrderGoods.objects.filter(sku = goods_sku).exclude(comment='').order_by('-update_time')

        #获取购物车信息
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            conn_redis = get_redis_connection('default')
            cart_key = 'cart_%d' % (user.id,)
            cart_count = conn_redis.hlen(cart_key)
        #添加历史浏览记录
            # 添加用户的历史记录
            conn = get_redis_connection('default')
            history_key = 'history_%d' % user.id
            # 移除列表中的goods_id
            conn.lrem(history_key, 0, goods_id)
            # 把goods_id插入到列表的左侧
            conn.lpush(history_key, goods_id)
            # 只保存用户最新浏览的5条信息
            conn.ltrim(history_key, 0, 4)

        context = {
            'goods_sku':goods_sku,
            'goods_types':goods_types,
            'new_goods':new_goods,
            'goods_comment':goods_comment,
            'cart_count':cart_count,
            'same_spu_skus':same_spu_skus,
        }
        return render(request,'goods/detail.html',context)
#url list/type_id/page?sort=排序方式
class ListView(View):
    '''列表页视图类'''
    def get(self,request,type_id,page):
        '''显示列表而页'''
        #获取种类信息，校验用户传进来的种类id是否有效
        try:
            goods_type = GoodType.objects.get(id = type_id)
        except GoodType.DoesNotExist:
            '''种类ｉｄ不存在'''
            return redirect(reverse('goods:index'))

        #获取分类信息
        goods_types = GoodType.objects.all()
        #获取新品信息
        new_goods = GoodSKU.objects.filter(type = goods_type).order_by('-create_time')[0:2]

        #获取购物车数量
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            conn_redis = get_redis_connection('default')
            cart_key = 'cart_%d' % (user.id,)
            cart_count = conn_redis.hlen(cart_key)
        #获取分类商品信息　排序方式，判断用户传进来的排序方式是否有效，若无效按默认方式排序
        sort = request.GET.get('sort')
        if sort == 'price':
            skus = GoodSKU.objects.filter(type = goods_type).order_by('price')
        elif sort == 'hot':
            skus = GoodSKU.objects.filter(type = goods_type).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodSKU.objects.filter(type = goods_type).order_by('-id')
        #分页
        #生成Paginator对象
        paginator = Paginator(skus,2)
        #判断用户传进来的页码是否有效
        try:
            skus_page = paginator.page(page)

        except PageNotAnInteger:
            skus_page = paginator.page(1)
        except EmptyPage:
            skus_page = paginator.page(paginator.num_pages)
        #页码控制，让其只显示5个页码，显示当前夜前两个和当前页以及当前页的夜
        try:
            page = int(page)
        except Exception as e:
            page = 1

        #1、如果不足物业全部显示，
        if paginator.num_pages < 5:
            pages = range(1,paginator.num_pages+1)
        elif page <= 3:
        #2如果当前页是前三页显示显示前五页
            pages =  range(1,6)
        elif page > (paginator.num_pages-3):
        # 3、如果当前页是后三页
            pages = range(paginator.num_pages-4,paginator.num_pages+1)
        else:
        #4、否则当前页前两页和当前页以及当前页的页
            pages = range(page-2,page+3)

        context = {
            'goods_type':goods_type,
            'new_goods':new_goods,
            'goods_types':goods_types,
            'cart_count':cart_count,
            'skus_page':skus_page,
            'sort':sort,
            'pages':pages,


        }

        return render(request,'goods/list.html',context)

