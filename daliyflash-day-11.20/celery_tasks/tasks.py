# 使用celery
from django.core.mail import send_mail
from django.conf import settings
from celery import Celery
from django.template import loader


# 在任务处理者一端加这几句
import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daliyflash.settings")
# django.setup()

# 创建一个Celery类的实例对象
#app = Celery('celery_tasks.tasks', broker='redis://192.168.0.103:6379/8')
app = Celery('celery_tasks.tasks', broker='redis://192.168.43.138:6379/8')
from goods.models import GoodType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner

# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    '''发送激活邮件'''
    # 组织邮件信息
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    #html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://192.168.0.103:8000/user/active/%s">http://192.168.0.103:8000/user/active/%s</a>' % (username, token, token)
    html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://192.168.43.138:8000/user/active/%s">http://192.168.139.128:8000/user/active/%s</a>' % (username, token, token)
    send_mail(subject, message, sender, receiver, html_message=html_message)

@app.task
def generate_static_index_html():
    '''生成静态首页'''
    # 获取种类数据
    goods_types = GoodType.objects.all()
    # 获取轮番显示数据
    index_goods_banners = IndexGoodsBanner.objects.all().order_by('index')
    # 获取广告展示数据
    index_promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
    # 获取分类展示数据
    for goods_type in goods_types:
        image_banners = IndexTypeGoodsBanner.objects.filter(type=goods_type, display_type=1).order_by('index')
        title_banners = IndexTypeGoodsBanner.objects.filter(type=goods_type, display_type=0).order_by('index')
        goods_type.image_banners = image_banners
        goods_type.title_banners = title_banners

    context = {
        'goods_types': goods_types,
        'index_goods_banners': index_goods_banners,
        'index_promotion_banners': index_promotion_banners,

    }
    #加载模板文件
    temp = loader.get_template('static_index.html')
    #渲染模板文件
    static_index_html = temp.render(context)

    #生成静态文件
    save_path = os.path.join(settings.BASE_DIR,'static/index.html')
    with open(save_path,'w') as f:
        f.write(static_index_html)
