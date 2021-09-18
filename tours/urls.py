from django.contrib import admin
from django.urls import path, re_path, include
from . import views
from rest_framework import routers
from .admin import admin_site
from . import views

router = routers.DefaultRouter()
router.register('tours', views.TourViewSet, 'tour')
router.register('tour-images', views.TourImageViewSet)
router.register('services', views.ServiceViewSet, 'service')
router.register('categories', views.CategoryViewSet, 'category')
router.register('customers', views.CustomerViewSet, 'customer')
router.register('users', views.UserViewSet, 'user')
router.register('blogs', views.BlogViewSet, 'blog')
router.register('comments', views.CommentViewSet, 'comments')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin_site.urls)
]