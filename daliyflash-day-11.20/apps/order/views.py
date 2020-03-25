from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from  django.views.generic import View
from utils.mixin import LoginRequiredMixin
from goods.models import GoodSKU
from user.models import Address
from order.models import OrderInfo,OrderGoods
from django_redis import get_redis_connection
from django.http import JsonResponse
from datetime import datetime
from django.db import transaction #mysql事务
from alipay import AliPay #支付宝支付
from daliyflash import settings
import os
# Create your views here.
class PlaceOrderView(LoginRequiredMixin,View):
    '''提交订单视图类'''
    def post(self,request):
        '''显示提交订单页面页面'''
        user = request.user
        #数据校验
        sku_ids = request.POST.getlist('sku_ids')
        if not sku_ids:
            return redirect(reverse('cart:cart_show'))
        #链接redis数据库
        conn = get_redis_connection('default')
        total_price = 0
        total_count = 0
        skus = []
        str_sku_ids = ','.join(sku_ids)

        for sku_id in sku_ids:
            try:
                sku = GoodSKU.objects.get(id = sku_id)
            except GoodSKU.DoesNotExist:
                return redirect(reverse('cart:cart_show'))
            cart_key = 'cart_%d'%user.id
            #获得购买数量
            count = conn.hget(cart_key,sku_id)

            #添加数量属性
            sku.count =count
            #计算小计
            amount = sku.price * int(count)
            #添加小计属性
            sku.amount = amount

            skus.append(sku)
            #计算总金额 总数量
            total_count += int(count)
            total_price += amount
        transit_price = 20
        #实付款
        total_pay = total_price + transit_price

        #获取用户地址
        addrs = Address.objects.filter(user=user)
        #组织参数
        context = {
            'skus':skus,
            'addrs':addrs,
            'transit_price':transit_price,
            'total_pay':total_pay,
            'total_count':total_count,
            'total_price':total_price,
            'str_sku_ids':str_sku_ids,
        }


        return render(request,'order/place_order.html',context)

#悲观锁
class CommitOrderView1(View):
    '''提交订单'''

    @transaction.atomic
    def post(self,request):
        '''提交'''
        #1、登录验证
        user = request.user
        if not user.is_authenticated():
            context = {
                'res':1,
                'errmsg':'用户未登陆'
            }
            return JsonResponse(context)
        #2、接受参数
        sku_ids = request.POST.get('sku_ids')
        addr_id = request.POST.get('addr_id')
        pay_style = request.POST.get('pay_style')
        #3、数据校验
        if not all([sku_ids,addr_id,pay_style]):
            context = {
                'res':2,
                'errmsg':'数据不完整',
            }
            return JsonResponse(context)
        try :
            addr = Address.objects.get(id = addr_id)
        except Address.DoesNotExist:
            context = {
                'res':3,
                'errmsg':'用户地址不存在',
            }
            return JsonResponse(context)

        if pay_style not in OrderInfo.PAY_METHODS.keys():
            context = {
                'res':4,
                'errmsg':'非法支付方式'
            }
            return JsonResponse(context)
        #4、业务流程：创建订单

        # todo:创建订单核心业务->向OrderInfo中插入一条订单信息
        #1、组织参数
        #自定义订单id：订单号年月日时分秒用户
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        total_count = 0
        total_price = 0
        transit_price = 20
        #2、向OrderInfo表中插入数据
        # 设置事务保存点
        save_id = transaction.savepoint()
        try :
            order = OrderInfo.objects.create(
                order_id = order_id,
                user = user,
                addr = addr,
                pay_method = pay_style,
                total_count = total_count,
                total_price = total_price,
                transit_price = transit_price
            )

            # todo:创建订单核心业务->向OrderGoods中插入订单中商品信息
            #组织参数
            sku_ids = sku_ids.split(',')
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            for sku_id in sku_ids:
                try :
                    #sku = GoodSKU.objects.get(id = sku_id)
                    #应用悲观锁，查询修改数据时加锁，事务提交时解锁，在没获得锁时阻塞
                    # select * from df_goods_sku where id=sku_id for update;
                    sku = GoodSKU.objects.select_for_update().get(id=sku_id)
                except GoodSKU.DoesNotExist:
                    context = {
                        'res':5,
                        'errmsg':'商品不在'
                    }
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse(context)

                # print('user:%d stock:%d' % (user.id, sku.stock))
                # import time
                # time.sleep(10)


                count = conn.hget(cart_key,sku_id)
                try :
                    count = int(count)
                except Exception as e:
                    context ={
                        'res':6,
                        'errmsg':'商品数量不合法'
                    }
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse(context)
                if count > sku.stock:
                    context = {
                        'res':7,
                        'errmsg':'库存不足'
                    }
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse(context)
                #更新商品库存
                sku.stock = sku.stock - count
                sku.sales = sku.sales + count
                sku.save()
                #计算商品总件数
                total_count += count
                amount = count*sku.price
                total_price += amount
                #向OrderGoods插入数据库
                order_goods = OrderGoods.objects.create(
                    order = order,
                    sku = sku,
                    count = count,
                    price = sku.price
                )

            # todo:创建订单核心业务->更新rderInfo中中的total_count，total_price
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            context ={
                'res':9,
                'errmsg':'创建失败'
            }
            transaction.savepoint_rollback(save_id)
            return JsonResponse(context)
        # todo:创建订单核心业务->清楚购物车
        # 提交事务
        transaction.savepoint_commit(save_id)
        conn.hdel(cart_key, *sku_ids)
        #5、返回响应
        context ={
            'res':8,
            'message':'创建成功'
        }
        return JsonResponse(context)


#乐观锁
class CommitOrderView(View):
    '''提交订单'''

    @transaction.atomic
    def post(self,request):
        '''提交'''
        #1、登录验证
        user = request.user
        if not user.is_authenticated():
            context = {
                'res':1,
                'errmsg':'用户未登陆'
            }
            return JsonResponse(context)
        #2、接受参数
        sku_ids = request.POST.get('sku_ids')
        addr_id = request.POST.get('addr_id')
        pay_style = request.POST.get('pay_style')
        #3、数据校验
        if not all([sku_ids,addr_id,pay_style]):
            context = {
                'res':2,
                'errmsg':'数据不完整',
            }
            return JsonResponse(context)
        try :
            addr = Address.objects.get(id = addr_id)
        except Address.DoesNotExist:
            context = {
                'res':3,
                'errmsg':'用户地址不存在',
            }
            return JsonResponse(context)

        if pay_style not in OrderInfo.PAY_METHODS.keys():
            context = {
                'res':4,
                'errmsg':'非法支付方式'
            }
            return JsonResponse(context)
        #4、业务流程：创建订单

        # todo:创建订单核心业务->向OrderInfo中插入一条订单信息
        #1、组织参数
        #自定义订单id：订单号年月日时分秒用户
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        total_count = 0
        total_price = 0
        transit_price = 20
        #2、向OrderInfo表中插入数据
        # 设置事务保存点
        save_id = transaction.savepoint()
        try :
            order = OrderInfo.objects.create(
                order_id = order_id,
                user = user,
                addr = addr,
                pay_method = pay_style,
                total_count = total_count,
                total_price = total_price,
                transit_price = transit_price
            )

            # todo:创建订单核心业务->向OrderGoods中插入订单中商品信息
            #组织参数
            sku_ids = sku_ids.split(',')
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            for sku_id in sku_ids:
                for i in range(3):
                    try :
                        sku = GoodSKU.objects.get(id = sku_id)
                        # #应用悲观锁，查询修改数据时加锁，事务提交时解锁，在没获得锁时阻塞
                        # # select * from df_goods_sku where id=sku_id for update;
                        # sku = GoodSKU.objects.select_for_update().get(id=sku_id)
                    except GoodSKU.DoesNotExist:
                        context = {
                            'res':5,
                            'errmsg':'商品不在'
                        }
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse(context)




                    count = conn.hget(cart_key,sku_id)
                    try :
                        count = int(count)
                    except Exception as e:
                        context ={
                            'res':6,
                            'errmsg':'商品数量不合法'
                        }
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse(context)
                    if count > sku.stock:
                        context = {
                            'res':7,
                            'errmsg':'库存不足'
                        }
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse(context)
                    #更新商品库存
                    orgin_stock = sku.stock
                    new_stock = orgin_stock - count
                    new_sales = sku.sales + count

                    # print('user:%d times:%d stock:%d' % (user.id, i, sku.stock))
                    # import time
                    # time.sleep(10)

                    # update df_goods_sku set stock=new_stock, sales=new_sales
                    # where id=sku_id and stock = orgin_stock

                    # 返回受影响的行数
                    res = GoodSKU.objects.filter(id=sku_id, stock=orgin_stock).update(stock=new_stock, sales=new_sales)
                    if res == 0:
                        if i == 2:
                            # 尝试的第3次
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'res': 7, 'errmsg': '下单失败2'})
                        continue
                    #计算商品总件数
                    total_count += count
                    amount = count*sku.price
                    total_price += amount
                    #向OrderGoods插入数据库
                    order_goods = OrderGoods.objects.create(
                        order = order,
                        sku = sku,
                        count = count,
                        price = sku.price
                    )
                    break

            # todo:创建订单核心业务->更新rderInfo中中的total_count，total_price
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            context ={
                'res':9,
                'errmsg':'创建失败'
            }
            transaction.savepoint_rollback(save_id)
            return JsonResponse(context)
        # todo:创建订单核心业务->清楚购物车
        # 提交事务
        transaction.savepoint_commit(save_id)
        conn.hdel(cart_key, *sku_ids)
        #5、返回响应
        context ={
            'res':8,
            'message':'创建成功'
        }
        return JsonResponse(context)


class PayOrderView(View):
    '''订单支付'''
    def post(self,request):
        '''订单支付'''
        user = request.user
        #登录验证
        if  not user.is_authenticated():
            return JsonResponse({'res':1,'errmsg':'用户未登陆'})
        #数据校验
        order_id =  request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res':2,'errmsg':'数据不完整'})
        try:
            order = OrderInfo.objects.get(order_id = order_id,user =user,order_status = 1,pay_method = 3)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res':3,'errmsg':'无效订单'})


        #业务流程：支付宝支付
        # #支付宝初始化
        alipay = AliPay(
            appid="2016090800464054",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False沙河环境用TRUE
        )

        # 调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        total_pay = order.total_price + order.transit_price  # Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay),  # 支付总金额
            subject='天天生鲜%s' % order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res':4,'pay_url':pay_url})

class CheckOrderView(View):
    '''检查订单支付结果视图'''
    def post(self,request):
        '''检查订单支付结果视图'''
        user = request.user
        # 登录验证
        if not user.is_authenticated():
            return JsonResponse({'res': 1, 'errmsg': '用户未登陆'})
        # 数据校验
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 2, 'errmsg': '数据不完整'})
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, order_status=1, pay_method=3)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '无效订单'})

        # 业务流程：支付宝支付
        # #支付宝初始化
        alipay = AliPay(
            appid="2016090800464054",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False沙河环境用TRUE
        )

        # 调用支付宝的交易查询接口
        while True:
            response = alipay.api_alipay_trade_query(order_id)

            # response = {
            #         "trade_no": "2017032121001004070200176844", # 支付宝交易号
            #         "code": "10000", # 接口调用是否成功
            #         "invoice_amount": "20.00",
            #         "open_id": "20880072506750308812798160715407",
            #         "fund_bill_list": [
            #             {
            #                 "amount": "20.00",
            #                 "fund_channel": "ALIPAYACCOUNT"
            #             }
            #         ],
            #         "buyer_logon_id": "csq***@sandbox.com",
            #         "send_pay_date": "2017-03-21 13:29:17",
            #         "receipt_amount": "20.00",
            #         "out_trade_no": "out_trade_no15",
            #         "buyer_pay_amount": "20.00",
            #         "buyer_user_id": "2088102169481075",
            #         "msg": "Success",
            #         "point_amount": "0.00",
            #         "trade_status": "TRADE_SUCCESS", # 支付结果
            #         "total_amount": "20.00"
            # }

            code = response.get('code')

            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                # 更新订单状态
                order.trade_no = trade_no
                order.order_status = 4  # 待评价
                order.save()
                # 返回结果
                return JsonResponse({'res': 4, 'message': '支付成功'})
            elif code == '40004' or (code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                # 等待买家付款
                # 业务处理失败，可能一会就会成功
                import time
                time.sleep(5)
                continue
            else:
                # 支付出错
                print(code)
                return JsonResponse({'res': 5, 'errmsg': '支付失败'})



class CommentOrderView(LoginRequiredMixin,View):
    '''评论视图'''
    def get(self,request,order_id):
        '''显示评论视图'''
        user =request.user
        if not order_id:
            return redirect(reverse('user:order',kwargs={"page": 1}))
        try :
            order = OrderInfo.objects.get(order_id=order_id,user= user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('user:order',kwargs={"page": 1}))
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
        order_skus = OrderGoods.objects.filter(order_id= order_id)
        for order_sku in order_skus:
            count = order_sku.count
            price = order_sku.price
            amount = count*price
            order_sku.amount = amount
        order.order_skus = order_skus
        return render(request,'user/user_center_order_comment.html',{'order':order,'page':'order'})

    def post(self,request,order_id):
        '''添加评论'''
        user = request.user
        if not order_id:
            return redirect(reverse('user:order',kwargs={"page": 1}))
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('user:order',kwargs={"page": 1}))
        # 获取评论条数
        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get("sku_%d" % i)  # sku_1 sku_2
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i, '')  # cotent_1 content_2 content_3
            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5  # 已完成
        order.save()

        return redirect(reverse("user:order", kwargs={"page": 1}))

