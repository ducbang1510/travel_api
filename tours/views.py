from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from .models import *
from .serializers import TourSerializer, UserSerializer


class UserViewSet(viewsets.ViewSet,
                  generics.CreateAPIView,
                  generics.RetrieveAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, ]

    def get_permissions(self):
        if self.action == 'retrieve':
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny()]


class TourViewSet(viewsets.ModelViewSet):
    queryset = Tour.objects.filter(active=True)
    serializer_class = TourSerializer

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

    def get_permissions(self):
        if self.action == 'list':
            return [permissions.AllowAny()]

        return [permissions.IsAuthenticated()]