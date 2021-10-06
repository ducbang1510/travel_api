from django import forms
from django.urls import path
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from ckeditor_uploader.widgets import CKEditorUploadingWidget
import calendar

from .models import *
from .utils import report_invoice


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
    list_display = ['tour_name', 'departure', 'depart_date', 'duration', 'created_date', 'price_of_tour',
                    'price_of_room', 'active', 'category']
    search_fields = ['tour_name', 'departure', 'depart_date', 'price_of_tour', 'category__name']
    list_filter = ['departure', 'depart_date', 'category', 'rating']
    inlines = [TourServiceInlineAdmin, TourImageInlineAdmin, ]
    list_per_page = 10


class TourImageAdmin(admin.ModelAdmin):
    list_per_page = 10
    readonly_fields = ['picture']
    search_fields = ['tour__tour_name']

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
    search_fields = ['title', 'author']
    list_filter = ['created_date']
    list_per_page = 10


class CommentForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget)

    class Meta:
        model = Comment
        fields = '__all__'


class CommentAdmin(admin.ModelAdmin):
    list_display = ['content', 'created_date', 'user']
    list_filter = ['created_date']
    search_fields = ['content', 'user', 'blog__title', 'tour__tour_name']
    list_per_page = 10
    form = CommentForm


class RatingAdmin(admin.ModelAdmin):
    list_display = ['tour', 'rate', 'user', 'updated_date']
    list_filter = ['rate', 'updated_date']
    search_fields = ['tour__tour_name', 'user__username']
    list_per_page = 10


class ActionAdmin(admin.ModelAdmin):
    list_display = ['blog', 'type', 'user', 'updated_date']
    list_filter = ['type', 'updated_date']
    search_fields = ['blog__title', 'user__username']
    list_per_page = 10


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'


class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'gender', 'email', 'phone']
    form = CustomerForm
    search_fields = ['name', 'email', 'address']
    list_per_page = 10


class PayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone']
    search_fields = ['name', 'email', 'phone', 'address']
    list_per_page = 10


class StaffAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ['name', 'gender', 'date_of_birth', 'email', 'phone']
    search_fields = ['name', 'email', 'phone']


class InvoiceAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ['tour', 'payer', 'total_amount', 'created_date']
    list_filter = ['created_date', 'total_amount']
    search_fields = ['tour__tour_name', 'payer__name']


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
admin_site.register(Invoice, InvoiceAdmin)
admin_site.register(Payer, PayerAdmin)
admin_site.register(Blog, BlogAdmin)
admin_site.register(Comment, CommentAdmin)
admin_site.register(Rating, RatingAdmin)
admin_site.register(Action, ActionAdmin)
admin_site.register(User)
admin_site.register(Permission)
