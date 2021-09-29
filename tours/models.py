from ckeditor.fields import RichTextField
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    avatar = models.ImageField(upload_to='images/avatars/%Y/%m', null=True)


class ItemBase(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=255, null=False)
    gender = models.CharField(max_length=20, null=False)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(max_length=254, null=False)
    phone = models.CharField(max_length=255, null=False)
    address = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Staff(ItemBase):
    class Meta:
        unique_together = ('email', 'phone', 'avatar')

    avatar = models.ImageField(upload_to='images/avatars/%Y/%m', null=True, default=None)


class Tour(models.Model):
    class Meta:
        unique_together = ('tour_name', 'category')
        ordering = ["-id"]

    tour_name = models.CharField(max_length=255, null=False)
    tour_plan = RichTextField(default=None, null=True)
    departure = models.CharField(max_length=255, null=True)
    depart_date = models.DateField(null=True, blank=True)
    duration = models.CharField(max_length=50, null=True)
    rating = models.FloatField(null=True, blank=True)
    price_of_tour = models.FloatField(null=False, blank=False)
    price_of_room = models.FloatField(null=False, blank=False)
    description = RichTextField(default=None, null=True)
    image = models.ImageField(upload_to='images/tours/%Y/%m', default=None)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    category = models.ForeignKey('Category', related_name='tours', on_delete=models.SET_NULL, null=True)
    service = models.ManyToManyField('Service', related_name='tours', blank=True, null=True)
    country = models.ForeignKey('Country', related_name='tours', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.tour_name


class TourImage(models.Model):
    image = models.ImageField(upload_to='images/tours/%Y/%m')
    tour = models.ForeignKey(Tour, related_name='tour_images', on_delete=models.SET_NULL, null=True)


class Service(models.Model):
    name = models.CharField(max_length=255, unique=True, null=False)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, null=False)

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=100, null=False, unique=True)

    def __str__(self):
        return self.name


class Blog(models.Model):
    title = models.CharField(max_length=255, null=False, unique=True)
    image = models.ImageField(upload_to='images/blogs/%Y/%m', default=None)
    author = models.CharField(max_length=100, null=True, default=None)
    content = RichTextField()
    likes = models.IntegerField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)


class Comment(models.Model):
    content = RichTextField()
    created_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name="comments", on_delete=models.CASCADE, null=True)
    blog = models.ForeignKey(Blog, related_name="comments", on_delete=models.CASCADE, null=True)
    tour = models.ForeignKey(Tour, related_name="comments", on_delete=models.CASCADE, null=True)


class ActionBase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Action(ActionBase):
    LIKE, UNLIKE = range(2)
    ACTIONS = [
        (LIKE, 'like'),
        (UNLIKE, 'unlike')
    ]
    type = models.PositiveSmallIntegerField(choices=ACTIONS, default=LIKE)
    blog = models.ForeignKey(Blog, related_name="actions", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("blog", "user")


class Rating(ActionBase):
    rate = models.PositiveSmallIntegerField(default=0)
    tour = models.ForeignKey(Tour, related_name="ratings", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("tour", "user")
        ordering = ["-id"]


# Thông tin khách hàng
class Customer(ItemBase):
    ADULT, CHILD = range(2)
    AGES = [
        (ADULT, 'adult'),
        (CHILD, 'child')
    ]
    avatar = models.ImageField(upload_to='images/avatars/%Y/%m', null=True, default=None)
    age = models.PositiveSmallIntegerField(choices=AGES, default=ADULT)
    payer = models.ForeignKey('Payer', related_name='customers', on_delete=models.SET_NULL, null=True)


# Thông tin liên hệ của người thanh toán
class Payer(models.Model):
    name = models.CharField(max_length=255, null=False)
    email = models.EmailField(max_length=254, null=False)
    phone = models.CharField(max_length=255, null=False)
    address = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


# Thông tin hóa đơn
class Invoice(models.Model):
    total_amount = models.FloatField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    note = models.TextField(null=True, blank=True)
    tour = models.ForeignKey('Tour', related_name='invoices', null=True, on_delete=models.SET_NULL)
    payer = models.ForeignKey('Payer', related_name='invoices', on_delete=models.SET_NULL, null=True)
