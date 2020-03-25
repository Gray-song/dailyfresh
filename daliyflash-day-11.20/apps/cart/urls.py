from django.conf.urls import url
from cart.views import CartView,CartAddView,CartUpdateView,CartDelView

urlpatterns = [
    url(r'^add$',CartAddView.as_view(),name='cart_add'),
    url(r'^update$',CartUpdateView.as_view(),name='cart_update'),
    url(r'^del$',CartDelView.as_view(),name='cart_del'),
    url(r'^$',CartView.as_view(),name='cart_show'),


]
