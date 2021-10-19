from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from django.db.models import Q
from django.core.mail import EmailMessage

from .models import *
from .serializers import *
from .paginator import *

import urllib.request
import urllib.parse
import uuid
import hmac
import hashlib
import codecs
import json
from datetime import datetime, date


class UserViewSet(viewsets.ViewSet,
                  generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, ]

    def get_permissions(self):
        if self.action in ['get_current_user', 'change_password']:
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny()]

    @action(methods=['get'], detail=False, url_path="current-user")
    def get_current_user(self, request):
        return Response(self.serializer_class(request.user, context={"request": request}).data,
                        status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False, url_path="change-password")
    def change_password(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        account = request.user

        if old_password is not None and new_password is not None and old_password != new_password:
            if not account.check_password(old_password):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)

            account.set_password(new_password)
            account.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }

            return Response(response)

        return Response({"Message": ["Errors."]}, status=status.HTTP_400_BAD_REQUEST)


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

    @action(methods=['post'], detail=True, url_path='update-slots')
    def update_slots(self, request, pk):
        try:
            count = int(request.data['count'])
        except IndexError | ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            slot = int(Tour.objects.get(pk=pk).slots) - count
            if slot > -1:
                Tour.objects.filter(pk=pk).update(slots=slot)

            return Response({"message": "update success"}, status=status.HTTP_200_OK)

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
        c = self.get_object()
        return Response(
            CommentSerializer(c.comments.order_by("-id").all(), many=True, context={"request": self.request}).data,
            status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path="popular")
    def get_popular_tour(self, request):
        tours = Tour.objects.all().order_by("-rating")[:3]

        return Response(
            TourSerializer(tours, many=True, context={"request": self.request}).data,
            status=status.HTTP_200_OK)

    def get_queryset(self):
        tours = Tour.objects.filter(active=True)

        sort_value = self.request.query_params.get('sort')
        if sort_value is not None:
            if sort_value == '1':
                tours = tours.order_by('tour_name')
            elif sort_value == '2':
                tours = tours.order_by('price_of_tour')
            elif sort_value == '3':
                tours = tours.order_by('-price_of_tour')
            elif sort_value == '4':
                tours = tours.order_by('-rating')
        else:
            pass

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

        depart_date = self.request.query_params.get('depart_date')
        if depart_date is not None:
            tours = tours.filter(depart_date=depart_date)

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
        return Response(
            CommentSerializer(c.comments.order_by("-id").all(), many=True, context={"request": self.request}).data,
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
            action_user = Action.objects.update_or_create(user=request.user,
                                                          blog=self.get_object(),
                                                          defaults={"type": action_type})
            if action_user:
                count_like = Blog.objects.get(pk=pk).actions.filter(type=1).count()
                Blog.objects.filter(pk=pk).update(likes=count_like)

            return Response(ActionSerializer(action_user).data,
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
        list_blog = Blog.objects.filter(active=True)

        q = self.request.query_params.get('q')
        if q is not None:
            list_blog = list_blog.filter(title__icontains=q)

        author = self.request.query_params.get('author')
        if author is not None:
            list_blog = list_blog.filter(author__icontains=author)

        return list_blog


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
    pagination_class = CustomerPayerPagination


class PayerViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.RetrieveAPIView):
    serializer_class = PayerSerializer
    queryset = Payer.objects.all()
    pagination_class = CustomerPayerPagination

    @action(methods=['post'], detail=True, url_path="add-customer")
    def add_customer(self, request, pk):
        name = request.data.get('name')
        gender = request.data.get('gender')
        email = request.data.get('email')
        phone = request.data.get('phone')
        address = request.data.get('address')

        if name and gender and phone and address and email:
            c = Customer.objects.create(name=name, gender=gender, address=address, phone=phone, email=email,
                                        payer=self.get_object())

            return Response(CustomerSerializer(c).data,
                            status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=True, url_path="add-invoice")
    def add_invoice(self, request, pk):
        total_amount = request.data.get('total_amount')
        tour_id = request.data.get('tour_id')
        tour = Tour.objects.get(pk=tour_id)
        note = request.data.get('note')
        status_payment = request.data.get('status_payment')

        if total_amount:
            inv = Invoice.objects.create(total_amount=total_amount, note=note, status_payment=status_payment,
                                         payer=self.get_object(), tour=tour)

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
        actions = Action.objects.all()
        user_id = self.request.query_params.get('user_id')
        blog_id = self.request.query_params.get('blog_id')
        if user_id is not None:
            actions = Action.objects.filter(user_id=user_id)
        if blog_id is not None:
            actions = Action.objects.filter(blog_id=blog_id)

        return actions


class AuthInfo(APIView):
    def get(self, request):
        return Response(settings.OAUTH2_INFO, status=status.HTTP_200_OK)


# Momo Payment Function
secret_key = settings.MOMO_SECRET_KEY
access_key = settings.MOMO_ACCESS_KEY


class MomoPayment(APIView):
    def post(self, request):
        total_amount = request.data.get('total_amount')
        tour_id = request.data.get('tour_id')
        payer_id = request.data.get('payer_id')
        invoice_id = request.data.get('invoice_id')

        if total_amount is not None:
            endpoint = settings.MOMO_ENDPOINT
            partner_code = settings.MOMO_PARTNER_CODE
            request_type = "captureWallet"
            redirect_url = settings.REDIRECT_URL % (tour_id, invoice_id)
            ipn_url = settings.IPN_URL
            order_id = str(uuid.uuid4())
            amount = str(total_amount)
            order_info = "Đơn đặt tour %s-TourID:%s-PayerID:%s" % (datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                                                   tour_id, payer_id)
            request_id = str(uuid.uuid4())
            extra_data = ""

            raw_signature = "accessKey=" + access_key + "&amount=" + amount \
                            + "&extraData=" + extra_data + "&ipnUrl=" + ipn_url + "&orderId=" + order_id \
                            + "&orderInfo=" + order_info + "&partnerCode=" + partner_code \
                            + "&redirectUrl=" + redirect_url + "&requestId=" + request_id \
                            + "&requestType=" + request_type

            signature = hmac.new(codecs.encode(secret_key), codecs.encode(raw_signature), hashlib.sha256).hexdigest()

            data = {
                'partnerCode': partner_code,
                'accessKey': access_key,
                'requestId': request_id,
                'amount': amount,
                'orderId': order_id,
                'orderInfo': order_info,
                'redirectUrl': redirect_url,
                'ipnUrl': ipn_url,
                'lang': "vi",
                'extraData': extra_data,
                'requestType': request_type,
                'signature': signature
            }

            data = json.dumps(data).encode("utf-8")
            content_len = len(data)

            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Content-Length": content_len
            }

            req = urllib.request.Request(endpoint, data, headers)
            f = urllib.request.urlopen(req)

            res = f.read()
            f.close()

            pay_url = json.loads(res)['payUrl']

            response = {
                "payUrl": pay_url,
            }

            return Response(response, status=status.HTTP_200_OK)

        return Response({'message': 'Error'}, status=status.HTTP_400_BAD_REQUEST)


class MomoConfirmPayment(APIView):
    # The function handles the payment confirmation through the information taken from the params returnUrl
    # Processing payment confirmations on the user interface
    def get(self, request):
        order_id = request.query_params.get('orderId')
        result_code = request.query_params.get('resultCode')

        if order_id is not None and result_code is not None:
            param = "accessKey=" + access_key + \
                    "&amount=" + request.query_params.get('amount') + \
                    "&extraData=" + request.query_params.get('extraData') + \
                    "&message=" + request.query_params.get('message') + \
                    "&orderId=" + order_id + \
                    "&orderInfo=" + request.query_params.get('orderInfo') + \
                    "&orderType=" + request.query_params.get('orderType') + \
                    "&partnerCode=" + request.query_params.get('partnerCode') + \
                    "&payType=" + request.query_params.get('payType') + \
                    "&requestId=" + request.query_params.get('requestId') + \
                    "&responseTime=" + request.query_params.get('responseTime') + \
                    "&resultCode=" + result_code + \
                    "&transId=" + request.query_params.get('transId')

            param = urllib.parse.unquote(param)
            signature = hmac.new(codecs.encode(secret_key), codecs.encode(param), hashlib.sha256).hexdigest()

            mess = ""
            r_code = -1

            if signature != request.query_params.get('signature'):
                mess = "Signature of request is invalid"
            else:
                if result_code == "0":
                    mess += "Payment success"
                    r_code = 0
                else:
                    mess += "Payment failed"
                    r_code = 1

            res = {
                "message": mess,
                "rCode": r_code,
            }

            return Response(res, status=status.HTTP_200_OK)

        return Response({"message": "Confirm request failed"}, status=status.HTTP_400_BAD_REQUEST)

    # The function handles the payment confirmation through the information taken from request body by Momo to server
    # Processing payment confirmations: send mail and update status payment invoice in database
    def post(self, request):
        amount = str(request.data.get('amount'))
        extra_data = request.data.get('extraData')
        message = request.data.get('message')
        order_id = request.data.get('orderId')
        order_info = request.data.get('orderInfo')
        order_type = request.data.get('orderType')
        partner_code = request.data.get('partnerCode')
        pay_type = request.data.get('payType')
        request_id = request.data.get('requestId')
        response_time = str(request.data.get('responseTime'))
        result_code = str(request.data.get('resultCode'))
        trans_id = str(request.data.get('transId'))

        if order_id is not None and result_code is not None:
            param = "accessKey=" + access_key + \
                    "&amount=" + amount + \
                    "&extraData=" + extra_data + \
                    "&message=" + message + \
                    "&orderId=" + order_id + \
                    "&orderInfo=" + order_info + \
                    "&orderType=" + order_type + \
                    "&partnerCode=" + partner_code + \
                    "&payType=" + pay_type + \
                    "&requestId=" + request_id + \
                    "&responseTime=" + response_time + \
                    "&resultCode=" + result_code + \
                    "&transId=" + trans_id

            param = urllib.parse.unquote(param)
            signature = hmac.new(codecs.encode(secret_key), codecs.encode(param), hashlib.sha256).hexdigest()

            mess = ""
            r_code = -1

            payer_id = int(order_info[order_info.find('PayerID:') + 8: len(order_info)])
            payer = Payer.objects.get(pk=payer_id)
            tour_id = int(order_info[order_info.find('TourID:') + 7: order_info.find('-PayerID')])
            tour = Tour.objects.get(pk=tour_id)
            order_date = date.today().strftime("%d/%m/%Y")

            if signature != request.data.get('signature'):
                mess = "Signature of request is invalid"
            else:
                if result_code == "0":
                    mess += "Payment success"
                    r_code = 0
                else:
                    mess += "Payment failed"
                    r_code = 1

            subject = 'Thông báo đơn đặt tour'
            body = 'Gửi khách hàng: <strong>' + payer.name \
                   + '</strong><br>Bạn đã đặt tour <strong>' + tour.tour_name + '</strong> thành công.<br>' \
                   + 'Số tiền đã thanh toán: <strong>' + amount \
                   + '</strong><br>Ngày đặt: ' + order_date \
                   + '<br>Cảm ơn quý khách đã sử dụng dịch vụ của chúng tôi.<br>'
            sender = 'hvnj1510@gmail.com'
            to = payer.email

            if r_code > -1:
                if r_code == 0:
                    msg = EmailMessage(subject, body, sender, [to])
                    msg.content_subtype = "html"
                    msg.send()

                partner_code = settings.MOMO_PARTNER_CODE
                result_code = str(r_code)
                message = mess
                extra_data = ''

                raw_signature = "accessKey=" + access_key \
                                + "&extraData=" + extra_data + "&message=" + message \
                                + "&orderId=" + order_id \
                                + "&partnerCode=" + partner_code + "&requestId=" + request_id \
                                + "&responseTime=" + response_time + "&resultCode=" + result_code

                signature = hmac.new(codecs.encode(secret_key), codecs.encode(raw_signature), hashlib.sha256).hexdigest()

                data = {
                    'partnerCode': partner_code,
                    'requestId': request_id,
                    'orderId': order_id,
                    'resultCode': result_code,
                    'message': message,
                    'responseTime': response_time,
                    'extraData': extra_data,
                    'signature': signature
                }

                data = json.dumps(data).encode("utf-8")

                headers = {
                    "Content-Type": "application/json; charset=utf-8",
                }

                return Response(data, status=status.HTTP_200_OK, headers=headers)

        return Response({"message": "Confirm request failed"}, status=status.HTTP_400_BAD_REQUEST)
# End Momo Payment Function
