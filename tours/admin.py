from django import forms
from django.urls import path
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.db.models.functions import ExtractDay, ExtractYear, ExtractMonth
import calendar

from .models import *


class TourForm(forms.ModelForm):
    tour_plan = forms.CharField(widget=CKEditorUploadingWidget)
    description = forms.CharField(widget=CKEditorUploadingWidget)

    class Meta:
        model = Tour
        fields = '__all__'


class TourServiceInlineAdmin(admin.StackedInline):
    model = Tour.service.through


class TourImageInlineAdmin(admin.StackedInline):
    model = TourImage
    fk_name = 'tour'


class TourAdmin(admin.ModelAdmin):
    form = TourForm
    list_display = ['tour_name', 'departure', 'depart_date', 'duration', 'rating', 'created_date', 'price_of_tour',
                    'price_of_room', 'active', 'category', 'country']
    search_fields = ['tour_name', 'departure', 'depart_date', 'price_of_tour', 'category__name']
    list_filter = ['departure', 'depart_date', 'country', 'category']
    inlines = [TourServiceInlineAdmin, TourImageInlineAdmin, ]


class TourImageAdmin(admin.ModelAdmin):
    readonly_fields = ['picture']

    def picture(self, tour_image):
        return mark_safe("<img src='/static/{img_url}' width=480px />".format(img_url=tour_image.image.name))


class BlogForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget)

    class Meta:
        model = Blog
        fields = '__all__'


class BlogAdmin(admin.ModelAdmin):
    form = BlogForm

    list_display = ['title', 'author', 'created_date']
    search_fields = ['title', 'author', 'created_date']


class CommentForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget)

    class Meta:
        model = Comment
        fields = '__all__'


class CommentAdmin(admin.ModelAdmin):
    form = CommentForm


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'


class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'gender', 'email', 'phone']
    form = CustomerForm
    search_fields = ['name', 'email', 'address']


class PayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone']
    search_fields = ['name', 'email', 'phone', 'address']


class StaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'gender', 'date_of_birth', 'email', 'phone']
    search_fields = ['name', 'email', 'phone']


def report_invoice(month, year=None, day=None):
    tong = 0
    if day:
        invoices = Invoice.objects.annotate(day=ExtractDay('created_date'), month=ExtractMonth('created_date'),
                                            year=ExtractYear('created_date')).values('id', 'total_amount', 'tour_id',
                                                                                     'payer_id', 'day', 'month',
                                                                                     'year').filter(day=day,
                                                                                                    month=month,
                                                                                                    year=year)
    else:
        invoices = Invoice.objects.annotate(month=ExtractMonth('created_date'),
                                            year=ExtractYear('created_date')).values('id', 'total_amount', 'tour_id',
                                                                                     'payer_id', 'month',
                                                                                     'year').filter(month=month,
                                                                                                    year=year)

    for i in invoices:
        tong = tong + float(i['total_amount'])

    return tong


class TravelWebAdminSite(admin.AdminSite):
    site_header = 'Hệ thống quản lý web du lịch'

    def get_urls(self):
        return [
            path('stats/', self.tour_stats)
        ] + super().get_urls()

    def tour_stats(self, request):
        tours = Tour.objects.filter(active=True)
        data = []
        label = []
        lx = 'Ngày'
        if request.method == 'POST':
            year = request.POST.get('year', '')
            month = request.POST.get('month', '')
            if month:
                lx = 'Ngày'
                p = calendar.monthrange(int(year), int(month))
                for i in range(1, p[1] + 1):
                    data.append(report_invoice(month, year=year, day=i))
                    label.append(i)
            else:
                lx = 'Tháng'
                for i in range(1, 13):
                    data.append(report_invoice(i, year=year))
                    label.append(i)

            m = int(max(data))
            a = list(str(m))
            for i in range(0, len(a)):
                if i == 0:
                    a[i] = str(int(a[i]) + 1)
                else:
                    a[i] = '0'
            c = int(''.join(a))
            return TemplateResponse(request, 'admin/tour-stats.html', {
                'tours': tours, 'data': data, 'c': c, 'label': label, 'month': month, 'year': year, 'lx': lx,
            })

        return TemplateResponse(request, 'admin/tour-stats.html', {
            'tours': tours, 'data': data, 'c': 0, 'label': label, 'lx': lx,
        })


admin_site = TravelWebAdminSite(name='mytour')

admin_site.register(Tour, TourAdmin)
admin_site.register(Customer, CustomerAdmin)
admin_site.register(Staff, StaffAdmin)
admin_site.register(TourImage, TourImageAdmin)
admin_site.register(Service)
admin_site.register(Category)
admin_site.register(Country)
admin_site.register(Invoice)
admin_site.register(Payer, PayerAdmin)
admin_site.register(Blog, BlogAdmin)
admin_site.register(Comment, CommentAdmin)
admin_site.register(Rating)
admin_site.register(User)
admin_site.register(Permission)
