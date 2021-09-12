from rest_framework.serializers import HyperlinkedModelSerializer, ModelSerializer
from .models import *


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'username', 'password', 'avatar']
        extra_kwargs = {
            'password': {'write_only': 'true'}
        }

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()

        return user


class CustomerSerializer(ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'gender', 'date_of_birth', 'email', 'phone', 'address', 'avatar']


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

    class Meta:
        model = Tour
        fields = ['id', 'tour_name', 'departure', 'depart_date',
                  'duration', 'rating', 'created_date', 'tour_plan', 'description',
                  'price_of_tour', 'price_of_room', 'image', 'category_id', 'service', 'country_id']


class TourImageSerializer(ModelSerializer):
    class Meta:
        model = TourImage
        fields = '__all__'


class BlogSerializer(ModelSerializer):
    class Meta:
        model = Blog
        fields = '__all__'
