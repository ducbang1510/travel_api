from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import *
from .serializers import *


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
        return Response(self.serializer_class(request.user).data)


class TourPagination(PageNumberPagination):
    page_size = 4


class TourViewSet(viewsets.ModelViewSet):
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ['tour_name', 'departure', 'depart_date']
    queryset = Tour.objects.filter(active=True)
    serializer_class = TourSerializer
    pagination_class = TourPagination

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


class ServiceViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None


class CustomerViewSet(viewsets.ViewSet, generics.ListAPIView,
                      generics.CreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class TourImageViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = TourImage.objects.all()
    serializer_class = TourImageSerializer


class BlogPagination(PageNumberPagination):
    page_size = 5


class BlogViewSet(viewsets.ViewSet, generics.ListAPIView,
                  generics.RetrieveAPIView, generics.RetrieveUpdateAPIView):
    queryset = Blog.objects.filter(active=True)
    serializer_class = BlogSerializer
    pagination_class = BlogPagination

    @action(methods=['get'], detail=True, url_path="comments")
    def get_comments(self, request, pk):
        comments = Blog.objects.get(pk=pk).comments

        return Response(CommentSerializer(comments, many=True).data,
                        status=status.HTTP_200_OK)


class CommentPagination(PageNumberPagination):
    page_size = 3


class CommentViewSet(viewsets.ViewSet, generics.ListAPIView,
                     generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    pagination_class = CommentPagination
