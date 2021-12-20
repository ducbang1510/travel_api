from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from django.db.models import Q
from django.core.mail import EmailMessage

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created

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
import random
from datetime import datetime, date
from time import time


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
                'message': 'Password updated successfully',
                'data': []
            }

            return Response(response, status=status.HTTP_200_OK)

        return Response({"Message": ["Errors."]}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView:
    @receiver(reset_password_token_created)
    def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
        link_reset = "http://localhost:3000/reset-password/{}".format(reset_password_token.key)
        home = "http://localhost:3000"
        subject = "Link Reset Password for {title}".format(title="Website Travio")
        from_email = 'hvnj1510@gmail.com'
        to = reset_password_token.user.email

        html_content = render_to_string('email_reset_pass.html', {'title': subject, 'link': link_reset, 'home': home})
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


class TourViewSet(viewsets.ModelViewSet):
    queryset = Tour.objects.filter(active=True)
    serializer_class = TourSerializer
    pagination_class = TourPagination

    def get_permissions(self):
        if self.action in ['add_comment', 'rate']:
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny()]

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
                count_like = Blog.objects.get(pk=pk).actions.filter(type=0).count()
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
        age = request.data.get('age')
        gender = request.data.get('gender')
        email = request.data.get('email')
        phone = request.data.get('phone')
        address = request.data.get('address')
        age_type = 0

        if name and age and gender and phone and address and email:
            if age == 'Trẻ em':
                age_type = 1
            c = Customer.objects.create(name=name, age=age_type, gender=gender, address=address,
                                        phone=phone, email=email, payer=self.get_object())

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

# Test on webhooks
# ZaloPay: http://127.0.0.1:8000/zalo-callback/
# MomoPay: http://127.0.0.1:8000/momo-confirm-payment/
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
            redirect_url = "http://localhost:3000/tour-detail/" + tour_id + "/booking-3/" + invoice_id + "/1/confirm"
            ipn_url = settings.IPN_URL
            order_id = str(uuid.uuid4())
            amount = str(total_amount)
            order_info = "Đơn đặt tour %s-TourID:%s-PayerID:%s-InvID:%s" % (
                datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                tour_id, payer_id, invoice_id)
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
                "orderUrl": pay_url,
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

            payer_id = int(order_info[order_info.find('PayerID:') + 8: order_info.find('-InvID')])
            payer = Payer.objects.get(pk=payer_id)
            tour_id = int(order_info[order_info.find('TourID:') + 7: order_info.find('-PayerID')])
            tour = Tour.objects.get(pk=tour_id)
            invoice_id = int(order_info[order_info.find('InvID:') + 6: len(order_info)])
            invoice = Invoice.objects.get(pk=invoice_id)
            order_date = date.today().strftime("%d/%m/%Y")

            if signature != request.data.get('signature'):
                mess = "Signature of request is invalid"
            else:
                if result_code == "0":
                    if invoice:
                        invoice.status_payment = 1
                        invoice.save()
                    mess += "Payment success"
                    print(mess)
                    r_code = 0
                else:
                    mess += "Payment failed"
                    print(mess)
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


# Begin Zalo Payment Function
"""
Get request payment from client
Server send request with data and mac encryption with hmacSha256 to ZaloPay server to create order
Note: redirecturl in embed_data can set in server or set in config apps at zalo merchant (https://sbmc.zalopay.vn/apps)
ZaloPay server send return_code and order_url has qr code
"""


class ZaloPayment(APIView):
    def post(self, request):
        total_amount = request.data.get('total_amount')
        tour_id = request.data.get('tour_id')
        payer_id = request.data.get('payer_id')
        invoice_id = request.data.get('invoice_id')

        if total_amount is not None:
            trans_id = random.randrange(1000000)
            order = {
                "app_id": settings.ZALO_APP_ID,
                "app_trans_id": "{:%y%m%d}_{}".format(datetime.today(), trans_id),
                # app_trans_id has format: yyMMdd_xxxx
                "app_user": "user123",
                "app_time": int(round(time() * 1000)),  # miliseconds
                "embed_data": json.dumps({
                    "promotioninfo": "",
                    "merchantinfo": "embeddata123",
                    "redirecturl": "http://localhost:3000/tour-detail/" + tour_id + "/booking-3/" + invoice_id + "/3/confirm",
                }),
                "item": json.dumps([
                    {"tour_id": tour_id, "payer_id": payer_id, "invoice_id": invoice_id, "total_amount": total_amount}
                ]),
                "amount": total_amount,
                "description": "ZaloPay Integration Demo",
                "bank_code": "zalopayapp"
            }

            # app_id|app_trans_id|app_user|amount|apptime|embed_data|item
            data = "{}|{}|{}|{}|{}|{}|{}".format(order["app_id"], order["app_trans_id"], order["app_user"],
                                                 order["amount"], order["app_time"], order["embed_data"], order["item"])

            order["mac"] = hmac.new(settings.ZALO_KEY1.encode(), data.encode(), hashlib.sha256).hexdigest()

            response = urllib.request.urlopen(url=settings.ZALO_URL_CREATE, data=urllib.parse.urlencode(order).encode())
            result = json.loads(response.read())

            return_code = result['return_code']
            order_url = result['order_url']

            if return_code == 1:
                response = {
                    "orderUrl": order_url,
                    'message': 'Success'
                }
            return Response(response, status=status.HTTP_200_OK)

        return Response({'message': 'Error'}, status=status.HTTP_400_BAD_REQUEST)


"""
ZaloPay Server send callback to server by callback url in server
Use ZaloPay Key2 to check mac of request
Config app callback url at https://sbmc.zalopay.vn/apps
Log callback at https://sbmc.zalopay.vn/devtool
if deploy to server add url callback /%url-host%/zalo-callback

If test in localhost
Get data callback from ZaloPay server from middle server test 
https://webhook.site/de7e352f-0e7f-494d-83fc-349bd316b657 (create in webhook) config on zalo merchant
"""


class ZaloCallBack(APIView):
    def post(self, request):
        try:
            cbdata = request.data.get('data')
            mac = hmac.new(settings.ZALO_KEY2.encode(), cbdata.encode(), hashlib.sha256).hexdigest()

            # check callback is valid (from ZaloPay server)
            if mac != request.data.get('mac'):
                # invalid callback
                return_code = -1
                return_message = 'mac not equal'
            else:
                # payment success
                # update status for invoice
                data_json = json.loads(cbdata)

                info_invoice = json.loads(data_json['item'])[0]
                tour_id = info_invoice['tour_id']
                invoice_id = info_invoice['invoice_id']
                payer_id = info_invoice['payer_id']
                amount = info_invoice['total_amount']

                payer = Payer.objects.get(pk=payer_id)
                tour = Tour.objects.get(pk=tour_id)
                invoice = Invoice.objects.get(pk=invoice_id)
                if invoice:
                    invoice.status_payment = 1
                    invoice.save()

                order_date = date.today().strftime("%d/%m/%Y")

                subject = 'Thông báo đơn đặt tour'
                body = 'Gửi khách hàng: <strong>' + payer.name \
                       + '</strong><br>Bạn đã đặt tour <strong>' + tour.tour_name + '</strong> thành công.<br>' \
                       + 'Số tiền đã thanh toán: <strong>' + amount \
                       + '</strong><br>Ngày đặt: ' + order_date \
                       + '<br>Cảm ơn quý khách đã sử dụng dịch vụ của chúng tôi.<br>'
                sender = 'hvnj1510@gmail.com'
                to = payer.email

                msg = EmailMessage(subject, body, sender, [to])
                msg.content_subtype = "html"
                msg.send()

                return_code = 1
                return_message = 'success'
        except Exception as e:
            return_code = 0  # ZaloPay server will callback again (max 3 times)
            return_message = str(e)

        # send response to ZaloPay server
        return Response({'return_code': return_code, 'return_message': return_message})


"""
API send request to ZaloPay server to query the payment status of the order
Get app_id and app_trans_id of params of client send to server
Loop the API call to get the final result while has return_code = 3 and is_process = True
return_code == 1 => succes
return_code == 2 => failded
Send status to client 
"""


class ZaloGetStatusByTransId(APIView):
    def get(self, request):
        app_trans_id = request.query_params.get('apptransid')
        app_id = request.query_params.get('appid')
        amount = request.query_params.get('amount')
        return_code = 3
        is_processing = True

        if app_trans_id is not None and app_id is not None:
            params = {
                "app_id": app_id,
                "app_trans_id": app_trans_id
            }

            data = "{}|{}|{}".format(settings.ZALO_APP_ID, app_trans_id,
                                     settings.ZALO_KEY1)  # app_id|app_trans_id|key1
            params["mac"] = hmac.new(settings.ZALO_KEY1.encode(), data.encode(), hashlib.sha256).hexdigest()

            while return_code == 3 and is_processing is True:
                res = urllib.request.urlopen(url=settings.ZALO_URL_GET_STATUS, data=urllib.parse.urlencode(params).encode())
                result = json.loads(res.read())
                return_code = result['return_code']
                is_processing = result['is_processing']
                if return_code == 1 or return_code == 2:
                    break

            if return_code == 1:
                response = {
                    "amount": amount,
                    "returncode": return_code,
                    "rCode": 0,
                    "message": 'Success'
                }
            else:
                response = {
                    "amount": amount,
                    "returncode": return_code,
                    "rCode": 1,
                    "message": 'Failed'
                }
            return Response(response, status=status.HTTP_200_OK)

        return Response({'message': 'Error'}, status=status.HTTP_400_BAD_REQUEST)
# End Zalo Payment Function
