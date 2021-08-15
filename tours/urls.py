from django.contrib import admin
from django.urls import path, re_path, include
from . import views
from rest_framework import routers
from .admin import admin_site
from . import views

router = routers.DefaultRouter()
router.register('tours', views.TourViewSet)
router.register('services', views.ServiceViewSet)
router.register('categories', views.CategoryViewSet)
router.register('customers', views.CustomerViewSet)
router.register('users', views.UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin_site.urls)
]