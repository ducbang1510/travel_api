from django import forms
from django.urls import path
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django_ckeditor_5.widgets import CKEditor5Widget
import calendar

from .models import *
from .utils import report_invoice


class TourForm(forms.ModelForm):
    tour_plan = forms.CharField(widget=CKEditor5Widget)
    description = forms.CharField(widget=CKEditor5Widget)

    class Meta:
        model = Tour
        fields = '__all__'


class TourServiceInlineAdmin(admin.StackedInline):
    model = Tour.service.through


class TourImageInlineAdmin(admin.StackedInline):
    model = TourImage
    fk_name = 'tour'


class TourAdmin(admin.ModelAdmin):
    menu_title = "List Of Tours"
    menu_group = "Manage Tours"
    form = TourForm
    list_display = ['tour_name', 'departure', 'depart_date', 'duration', 'created_date', 'price_of_tour',
                    'price_of_tour_child', 'price_of_room', 'active', 'category']
    search_fields = ['tour_name', 'departure', 'depart_date', 'price_of_tour', 'category__name']
    list_filter = ['departure', 'depart_date', 'category', 'rating']
    inlines = [TourServiceInlineAdmin, TourImageInlineAdmin, ]
    list_per_page = 10


class TourImageAdmin(admin.ModelAdmin):
    menu_title = 'Images Of Tours'
    menu_group = 'Manage Tours'
    list_per_page = 10
    readonly_fields = ['picture']
    search_fields = ['tour__tour_name']

    def picture(self, tour_image):
        return mark_safe("<img src='/static/{img_url}' width=480px />".format(img_url=tour_image.image.name))


class BlogForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditor5Widget)

    class Meta:
        model = Blog
        fields = '__all__'


class BlogAdmin(admin.ModelAdmin):
    menu_title = 'Blogs And News'
    menu_group = 'Manage Blogs'
    form = BlogForm

    list_display = ['title', 'author', 'created_date']
    search_fields = ['title', 'author']
    list_filter = ['created_date']
    list_per_page = 10


class CommentForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditor5Widget)

    class Meta:
        model = Comment
        fields = '__all__'


class CommentAdmin(admin.ModelAdmin):
    menu_title = 'Comments'
    menu_group = 'Manage FeedBack'
    list_display = ['content', 'created_date', 'user']
    list_filter = ['created_date']
    search_fields = ['content', 'user__username', 'blog__title', 'tour__tour_name']
    list_per_page = 10
    form = CommentForm


class RatingAdmin(admin.ModelAdmin):
    menu_title = 'Rating Of Users'
    menu_group = 'Manage FeedBack'
    list_display = ['tour', 'rate', 'user', 'updated_date']
    list_filter = ['rate', 'updated_date']
    search_fields = ['tour__tour_name', 'user__username']
    list_per_page = 10


class ActionAdmin(admin.ModelAdmin):
    menu_title = 'Likes Of Blogs'
    menu_group = 'Manage FeedBack'
    list_display = ['blog', 'type', 'user', 'updated_date']
    list_filter = ['type', 'updated_date']
    search_fields = ['blog__title', 'user__username']
    list_per_page = 10


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'


class CustomerAdmin(admin.ModelAdmin):
    menu_title = 'Customers (Passengers)'
    menu_group = 'Manage Payment Info'
    list_display = ['name', 'gender', 'email', 'phone']
    form = CustomerForm
    search_fields = ['name', 'email', 'address']
    list_per_page = 10


class PayerAdmin(admin.ModelAdmin):
    menu_title = 'Payers'
    menu_group = 'Manage Payment Info'
    list_display = ['name', 'email', 'phone']
    search_fields = ['name', 'email', 'phone', 'address']
    list_per_page = 10


class StaffAdmin(admin.ModelAdmin):
    menu_title = 'Staffs'
    menu_group = 'Manage Staffs'
    list_per_page = 10
    list_display = ['name', 'gender', 'date_of_birth', 'email', 'phone']
    search_fields = ['name', 'email', 'phone']


class InvoiceAdmin(admin.ModelAdmin):
    menu_title = 'Invoices'
    menu_group = 'Manage Payment Info'
    list_per_page = 10
    list_display = ['tour', 'payer', 'total_amount', 'created_date']
    list_filter = ['created_date', 'total_amount']
    search_fields = ['tour__tour_name', 'payer__name']


class ServiceAdmin(admin.ModelAdmin):
    menu_title = 'Services Of Tours'
    menu_group = 'Manage Tours'
    list_per_page = 10
    list_display = ['id', 'name']
    search_fields = ['name']


class CategoryAdmin(admin.ModelAdmin):
    menu_title = 'Categories Of Tours'
    menu_group = 'Manage Tours'
    list_per_page = 10
    list_display = ['id', 'name']
    search_fields = ['name']


class CountryAdmin(admin.ModelAdmin):
    menu_title = 'Countries Of Tours'
    menu_group = 'Manage Tours'
    list_per_page = 10
    list_display = ['id', 'name']
    search_fields = ['name']


class UserAdmin(admin.ModelAdmin):
    menu_title = 'Users'
    menu_group = 'Manage Users'
    list_per_page = 10
    list_display = ["id", "first_name", "last_name", "username", "email", "date_joined"]
    search_fields = ['first_name', 'last_name', 'username', 'email']
    list_filter = ['date_joined']


class PermissionAdmin(admin.ModelAdmin):
    menu_group = 'Manage Users'


class TravelWebAdminSite(admin.AdminSite):
    site_header = 'Travio Administration'
    site_title = 'Travio Site Admin'

    def get_urls(self):
        return [
            path('stats/', self.admin_view(self.tour_stats))
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
admin_site.register(Service, ServiceAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Country, CountryAdmin)
admin_site.register(Invoice, InvoiceAdmin)
admin_site.register(Payer, PayerAdmin)
admin_site.register(Blog, BlogAdmin)
admin_site.register(Comment, CommentAdmin)
admin_site.register(Rating, RatingAdmin)
admin_site.register(Action, ActionAdmin)
admin_site.register(User, UserAdmin)
admin_site.register(Permission, PermissionAdmin)
