from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView

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
    page_size = 6


class TourViewSet(viewsets.ModelViewSet):
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ['tour_name', 'departure', 'depart_date']
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
            r = Rating.objects.create(rate=rating,
                                      user=request.user,
                                      tour=self.get_object())

            return Response(RatingSerializer(r).data,
                            status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path="add-comment")
    def add_comment(self, request, pk):
        content = request.data.get('content')

        if content:
            c = Comment.objects.create(content=content,
                                       tour=self.get_object(),
                                       user=request.user)

            return Response(CommentSerializer(c).data,
                            status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=True, url_path="comments")
    def get_comments(self, request, pk):
        comments = Tour.objects.get(pk=pk).comments.order_by("-id").all()

        return Response(CommentSerializer(comments, many=True).data,
                        status=status.HTTP_200_OK)

    def get_queryset(self):
        tours = Tour.objects.filter(active=True)

        q = self.request.query_params.get('q')
        if q is not None:
            tours = tours.filter(subject__icontains=q)

        cate_id = self.request.query_params.get('category_id')
        if cate_id is not None:
            tours = tours.filter(category_id=cate_id)

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


class BlogPagination(PageNumberPagination):
    page_size = 5


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
        comments = Blog.objects.get(pk=pk).comments.order_by("-id").all()

        return Response(CommentSerializer(comments, many=True).data,
                        status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='like')
    def take_action(self, request, pk):
        try:
            action_type = int(request.data['type'])
        except IndexError | ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            action = Action.objects.create(type=action_type,
                                           user=request.user,
                                           blog=self.get_object())

            return Response(ActionSerializer(action).data,
                            status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path="add-comment")
    def add_comment(self, request, pk):
        content = request.data.get('content')

        if content:
            c = Comment.objects.create(content=content,
                                       blog=self.get_object(),
                                       user=request.user)

            return Response(CommentSerializer(c).data,
                            status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class CommentPagination(PageNumberPagination):
    page_size = 3


class CommentViewSet(viewsets.ViewSet, generics.ListAPIView,
                     generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    pagination_class = CommentPagination


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


class AuthInfo(APIView):
    def get(self, request):
        return Response(settings.OAUTH2_INFO, status=status.HTTP_200_OK)
