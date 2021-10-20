from rest_framework.serializers import ModelSerializer, SerializerMethodField, DateTimeField
from .models import *
from django.conf import settings


class UserSerializer(ModelSerializer):
    avatar_url = SerializerMethodField()

    def get_avatar_url(self, user):
        request = self.context.get('request')
        if user.avatar and hasattr(user.avatar, 'name'):
            avatar_url = user.avatar.name
            if avatar_url.startswith('static/'):
                avatar_url = '/%s' % avatar_url
            else:
                avatar_url = '/static/%s' % avatar_url

            return request.build_absolute_uri(avatar_url)
        else:
            return None

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(user.password)
        user.save()

        return user

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name",
                  "username", "password", "email", "date_joined", "avatar_url"]
        extra_kwargs = {
            'password': {'write_only': 'true'}
        }


class CustomerSerializer(ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'gender', 'date_of_birth', 'email', 'phone', 'address', 'avatar']


class PayerSerializer(ModelSerializer):
    class Meta:
        model = Payer
        fields = '__all__'


class InvoiceSerializer(ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class ServiceSerializer(ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name']


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class TourSerializer(ModelSerializer):
    service = ServiceSerializer(many=True)
    image = SerializerMethodField()
    banner = SerializerMethodField()
    rate = SerializerMethodField()

    def get_rate(self, tour):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            r = tour.ratings.filter(user=request.user).first()
            if r:
                return r.rate

        return -1

    def get_image(self, tour):
        request = self.context['request']
        name = tour.image.name
        if name.startswith('static/'):
            path = '/%s' % name
        else:
            path = '/static/%s' % name

        return request.build_absolute_uri(path)

    def get_banner(self, tour):
        request = self.context['request']
        name = tour.banner.name
        if name.startswith('static/'):
            path = '/%s' % name
        else:
            path = '/static/%s' % name

        return request.build_absolute_uri(path)

    class Meta:
        model = Tour
        fields = ['id', 'tour_name', 'departure', 'depart_date', 'slots', 'banner',
                  'duration', 'rating', 'created_date', 'tour_plan', 'description',
                  'price_of_tour', 'price_of_room', 'image', 'category_id', 'service', 'country_id', 'rate']


class TourImageSerializer(ModelSerializer):
    image = SerializerMethodField()

    def get_image(self, tour):
        request = self.context['request']
        name = tour.image.name
        if name.startswith('static/'):
            path = '/%s' % name
        else:
            path = '/static/%s' % name

        return request.build_absolute_uri(path)

    class Meta:
        model = TourImage
        fields = '__all__'


SEARCH_PATTERN = 'src=\"/tours/static/'
REPLACE_WITH = 'src=\"%s/static/' % settings.SITE_DOMAIN


class BlogSerializer(ModelSerializer):
    created_date = DateTimeField(read_only=True, format="%Y-%m-%d")
    image = SerializerMethodField()
    type = SerializerMethodField()
    content = SerializerMethodField()

    def get_type(self, blog):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            t = blog.actions.filter(user=request.user).first()
            if t:
                return t.type

        return -1

    def get_content(self, blog):
        request = self.context.get('request')
        if request:
            text = blog.content
            if text.find(SEARCH_PATTERN):
                c = text.replace(SEARCH_PATTERN, REPLACE_WITH)
            else:
                c = text

        return c

    def get_image(self, tour):
        request = self.context['request']
        name = tour.image.name
        if name.startswith('static/'):
            path = '/%s' % name
        else:
            path = '/static/%s' % name

        return request.build_absolute_uri(path)

    class Meta:
        model = Blog
        fields = ['id', 'title', 'image', 'author', 'content', 'likes', 'created_date', 'type']


class CommentSerializer(ModelSerializer):
    created_date = DateTimeField(read_only=True, format="%Y-%m-%d")
    user = SerializerMethodField()

    def get_user(self, comment):
        return UserSerializer(comment.user, context={"request": self.context.get('request')}).data

    class Meta:
        model = Comment
        fields = ['id', 'content', 'created_date', 'user']


class ActionSerializer(ModelSerializer):
    class Meta:
        model = Action
        fields = ["id", "type", "created_date", "user_id", "blog_id"]


class RatingSerializer(ModelSerializer):
    class Meta:
        model = Rating
        fields = ["id", "rate", "created_date"]
