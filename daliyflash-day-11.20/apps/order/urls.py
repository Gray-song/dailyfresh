from django.conf.urls import url
from order.views import PlaceOrderView,CommitOrderView,PayOrderView,CheckOrderView,CommentOrderView

urlpatterns = [
    url(r'^place_order$',PlaceOrderView.as_view(),name='place_order'),
    url(r'^commit_order$',CommitOrderView.as_view(),name='commit_order'),
    url(r'^pay_order$',PayOrderView.as_view(),name='pay_order'),
    url(r'^order_check$',CheckOrderView.as_view(),name='order_check'),
    url(r'^order_comment/(?P<order_id>.+)$',CommentOrderView.as_view(),name='order_comment'),
]
