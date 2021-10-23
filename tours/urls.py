from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework import routers
from .admin import admin_site
from . import views

router = routers.DefaultRouter()
router.register('tours', views.TourViewSet, 'tour')
router.register('tour-images', views.TourImageViewSet, 'tour-image')
router.register('services', views.ServiceViewSet, 'service')
router.register('categories', views.CategoryViewSet, 'category')
router.register('customers', views.CustomerViewSet, 'customer')
router.register('payers', views.PayerViewSet, 'payer')
router.register('users', views.UserViewSet, 'user')
router.register('blogs', views.BlogViewSet, 'blog')
router.register('comments', views.CommentViewSet, 'comment')
router.register('actions', views.ActionViewSet, 'action')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin_site.urls),
    path('oauth2-info/', views.AuthInfo.as_view()),
    path('momo-payment/', views.MomoPayment.as_view(), name='momo-payment'),
    path('momo-confirm-payment/', views.MomoConfirmPayment.as_view(), name='momo-confirm-payment'),
    path('zalopay-payment/', views.ZaloPayment.as_view(), name='zalo-payment'),
    path('zalo-callback/', views.ZaloCallBack.as_view(), name='zalo-callback'),
    path('zalopay-confirm/', views.ZaloGetStatusByTransId.as_view(), name='zalo-confirm'),
    path('reset-password/', include('django_rest_passwordreset.urls', namespace='reset-password')),
]