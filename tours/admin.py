from django import forms
from django.urls import path
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from ckeditor_uploader.widgets import CKEditorUploadingWidget

from .models import *


class TourForm(forms.ModelForm):
    tour_plan = forms.CharField(widget=CKEditorUploadingWidget)
    description = forms.CharField(widget=CKEditorUploadingWidget)

    class Meta:
        model = Tour
        fields = '__all__'


class TourServiceInlineAdmin(admin.StackedInline):
    model = Tour.service.through


class TourAdmin(admin.ModelAdmin):
    form = TourForm
    list_display = ['tour_name', 'departure', 'depart_date', 'duration', 'rating', 'created_date', 'price_of_tour',
                    'price_of_room', 'active', 'category']
    search_fields = ['tour_name', 'departure', 'depart_date', 'price_of_tour', 'category__name']
    list_filter = ['tour_name', 'departure', 'depart_date']
    inlines = [TourServiceInlineAdmin, ]


class TourImageAdmin(admin.ModelAdmin):
    readonly_fields = ['picture']

    def picture(self, tour_image):
        return mark_safe("<img src='/static/{img_url}' width=120px />".format(img_url=tour_image.image.name))


class TravelWebAdminSite(admin.AdminSite):
    site_header = 'Hệ thống quản lý web du lịch'

    def get_urls(self):
        return [
            path('stats/', self.tour_stats)
        ] + super().get_urls()

    def tour_stats(self, request):
        tour_count = Tour.objects.count()

        return TemplateResponse(request, 'admin/tour-stats.html', {
            'tour_count': tour_count,
        })


admin_site = TravelWebAdminSite(name='mytour')

admin_site.register(Tour, TourAdmin)
admin_site.register(Customer)
admin_site.register(Staff)
admin_site.register(Age)
admin_site.register(TourImage, TourImageAdmin)
admin_site.register(Service)
admin_site.register(Category)
admin_site.register(Country)
admin_site.register(Invoice)
admin_site.register(Blog)
admin_site.register(Comment)
admin_site.register(User)
admin_site.register(Permission)
