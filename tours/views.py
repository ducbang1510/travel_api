from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from django.db.models import Q

import urllib.request
import urllib.parse
import uuid
import hmac
import hashlib
import codecs
import json
from datetime import datetime

from .models import *
from .serializers import *
from .paginator import *


class UserViewSet(viewsets.ViewSet,
                  generics.CreateAPIView,
                  generics.UpdateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, ]

    def get_permissions(self):
        if self.action == 'current_user':
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny()]

    @action(methods=['get'], detail=False, url_path='current-user')
    def current_user(self, request):
        return Response(self.serializer_class(request.user, context={"request": request}).data,
                        status=status.HTTP_200_OK)


class TourViewSet(viewsets.ModelViewSet):
    queryset = Tour.objects.filter(active=True)
    serializer_class = TourSerializer
    pagination_class = TourPagination

    def get_permissions(self):
        if self.action in ['add_comment', 'rate']:
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny()]

    @swagger_auto_schema(
        operation_description='This API for hide tour from client',
        response={
            status.HTTP_200_OK: TourSerializer()
        }
    )
    @action(methods=['post'], detail=True,
            url_name='hide-tour',
            url_path='hide-tour')
    def hide_tour(self, request, pk=None):
        try:
            t = Tour.objects.get(pk=pk)
            t.active = False
            t.save()
        except Tour.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(data=TourSerializer(t, context={'request': request}).data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='rating')
    def rate(self, request, pk):
        try:
            rating = int(request.data['rating'])
        except IndexError | ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            r = Rating.objects.update_or_create(user=request.user,
                                                tour=self.get_object(),
                                                defaults={"rate": rating})
            if r:
                count_rating = Tour.objects.get(pk=pk).ratings.count()
                rates = Tour.objects.get(pk=pk).ratings.values('rate').all()
                total = 0
                for i in rates:
                    total = total + int(i['rate'])
                rate_range = int(total / count_rating)
                Tour.objects.filter(pk=pk).update(rating=rate_range)

            return Response(RatingSerializer(r).data,
                            status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path="add-comment")
    def add_comment(self, request, pk):
        content = request.data.get('content')

        if content:
            c = Comment.objects.create(content=content,
                                       tour=self.get_object(),
                                       user=request.user)

            return Response(CommentSerializer(c, context={"request": request}).data,
                            status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=True, url_path="comments")
    def get_comments(self, request, pk):
        comments = Tour.objects.get(pk=pk).comments.order_by("-id").all()

        return Response(CommentSerializer(comments, many=True).data,
                        status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path="popular")
    def get_popular_tour(self, request):
        tours = Tour.objects.all().order_by("-rating")[:3]

        return Response(
            TourSerializer(tours, many=True, context={"request": self.request}).data,
            status=status.HTTP_200_OK)

    def get_queryset(self):
        tours = Tour.objects.filter(active=True)

        q = self.request.query_params.get('q')
        if q is not None:
            tours = tours.filter(tour_name__icontains=q)

        cate_id = self.request.query_params.get('category_id')
        if cate_id is not None:
            tours = tours.filter(category_id=cate_id)

        max_price = self.request.query_params.get('max')
        min_price = self.request.query_params.get('min')
        if max_price is not None:
            tours = tours.filter(price_of_tour__lte=max_price)
        if min_price is not None:
            tours = tours.filter(price_of_tour__gte=min_price)

        depart_date = self.request.query_params.get('date')
        if depart_date is not None:
            tours = tours.filter(depart_date=depart_date)

        min_d = self.request.query_params.get('min_d')
        max_d = self.request.query_params.get('max_d')
        if min_d is not None and max_d is not None:
            tours = tours.filter(Q(duration__startswith=min_d) | Q(duration__startswith=max_d))

        rate = self.request.query_params.get('rate')
        if rate is not None:
            tours = tours.filter(rating=rate)

        return tours


class ServiceViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None


class TourImageViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = TourImage.objects.all()
    serializer_class = TourImageSerializer
    pagination_class = TourImagePagination

    def get_queryset(self):
        list_images = TourImage.objects.all()
        tour_id = self.request.query_params.get('tour_id')

        if tour_id is not None:
            list_images = list_images.filter(tour_id=tour_id)

        return list_images


class BlogViewSet(viewsets.ViewSet, generics.ListAPIView,
                  generics.RetrieveAPIView, generics.RetrieveUpdateAPIView):
    queryset = Blog.objects.filter(active=True)
    serializer_class = BlogSerializer
    pagination_class = BlogPagination

    def get_permissions(self):
        if self.action in ['add_comment', 'take_action']:
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny()]

    @action(methods=['get'], detail=True, url_path="comments")
    def get_comments(self, request, pk):
        c = self.get_object()
        return Response(CommentSerializer(c.comments.order_by("-id").all(), many=True, context={"request": self.request}).data,
                        status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path="newest")
    def get_newest_blog(self, request):
        blogs = Blog.objects.all().order_by("-created_date")[:3]

        return Response(
            BlogSerializer(blogs, many=True, context={"request": self.request}).data,
            status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='like')
    def take_action(self, request, pk):
        try:
            action_type = int(request.data['type'])
        except IndexError | ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            action = Action.objects.update_or_create(user=request.user,
                                                     blog=self.get_object(),
                                                     defaults={"type": action_type})
            if action:
                count_like = Blog.objects.get(pk=pk).actions.filter(type=1).count()
                Blog.objects.filter(pk=pk).update(likes=count_like)

            return Response(ActionSerializer(action).data,
                            status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path="add-comment")
    def add_comment(self, request, pk):
        content = request.data.get('content')

        if content:
            c = Comment.objects.create(content=content,
                                       blog=self.get_object(),
                                       user=request.user)

            return Response(CommentSerializer(c, context={"request": request}).data,
                            status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        blogs = Blog.objects.filter(active=True)

        q = self.request.query_params.get('q')
        if q is not None:
            blogs = blogs.filter(title__icontains=q)

        author = self.request.query_params.get('author')
        if author is not None:
            blogs = blogs.filter(author__icontains=author)

        return blogs


class CommentViewSet(viewsets.ViewSet, generics.DestroyAPIView,
                     generics.UpdateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        if request.user == self.get_object().creator:
            return super().destroy(request, *args, **kwargs)

        return Response(status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, *args, **kwargs):
        if request.user == self.get_object().creator:
            return super().partial_update(request, *args, **kwargs)

        return Response(status=status.HTTP_403_FORBIDDEN)


class CustomerViewSet(viewsets.ViewSet, generics.ListAPIView,
                      generics.CreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class PayerViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.ListAPIView):
    serializer_class = PayerSerializer
    queryset = Payer.objects.all()

    @action(methods=['post'], detail=True, url_path="add-customer")
    def add_customer(self, request, pk):
        name = request.data.get('name')
        gender = request.data.get('gender')
        email = request.data.get('email')
        phone = request.data.get('phone')
        address = request.data.get('address')

        if name and gender and phone and address and email:
            c = Customer.objects.create(name=name, gender=gender, address=address, phone=phone, email=email
                                        , payer=self.get_object())

            return Response(CustomerSerializer(c).data,
                            status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=True, url_path="add-invoice")
    def add_invoice(self, request, pk):
        total_amount = request.data.get('total_amount')
        tour_id = request.data.get('tour_id')
        tour = Tour.objects.get(pk=tour_id)
        # note = request.data.get('note')

        if total_amount:
            inv = Invoice.objects.create(total_amount=total_amount, payer=self.get_object(), tour=tour)

            return Response(InvoiceSerializer(inv).data,
                            status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class InvoiceViewSet(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = InvoiceSerializer
    queryset = Invoice.objects.all()


class ActionViewSet(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = ActionSerializer
    queryset = Action.objects.all()

    def get_queryset(self):
        action = Action.objects.all()
        user_id = self.request.query_params.get('user_id')
        blog_id = self.request.query_params.get('blog_id')
        if user_id is not None:
            action = Action.objects.filter(user_id=user_id)
        if blog_id is not None:
            action = Action.objects.filter(blog_id=blog_id)

        return action


class AuthInfo(APIView):
    def get(self, request):
        return Response(settings.OAUTH2_INFO, status=status.HTTP_200_OK)
