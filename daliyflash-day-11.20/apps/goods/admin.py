from django.contrib import admin
from goods.models import GoodType,GoodSKU,Goods,GoodsImage,IndexGoodsBanner,IndexTypeGoodsBanner,IndexPromotionBanner

from django.core.cache import cache
# Register your models here.

class BaseAdmin(admin.ModelAdmin):
    '''模型后台管理类'''

    def save_model(self, request, obj, form, change):
        '''重写父类方法，在后台管理界面点击保存会调用该方法，增加更改生成静态页面，清除缓存'''
        super().save_model(request, obj, form, change)
        # 发出生成静态页面的任务任务
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()
        #清除缓存
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        '''重写父类方法，在后台管理界删除时会调用该方法，增加更改生成静态页面，清除缓存'''
        super().delete_model(request, obj)
        # 发出生成静态页面的任务任务
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()
        # 清除缓存
        cache.delete('index_page_data')


class IndexTypeGoodsBannerAdmin(BaseAdmin):
    pass


class GoodTypeAdmin(BaseAdmin):
    pass


class GoodSKUAdmin(BaseAdmin):
    pass


class GoodsAdmin(BaseAdmin):
    pass


class GoodsImageAdmin(BaseAdmin):
    pass

class IndexGoodsBannerAdmin(BaseAdmin):
    pass

class IndexPromotionBannerAdmin(BaseAdmin):
    pass

admin.site.register(GoodType,GoodTypeAdmin)
admin.site.register(GoodSKU,GoodSKUAdmin)
admin.site.register(Goods,GoodsAdmin)
admin.site.register(GoodsImage,GoodsImageAdmin)
admin.site.register(IndexGoodsBanner,IndexGoodsBannerAdmin)
admin.site.register(IndexTypeGoodsBanner,IndexTypeGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner,IndexPromotionBannerAdmin)

