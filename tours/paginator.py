from rest_framework.pagination import PageNumberPagination


class TourPagination(PageNumberPagination):
    page_size = 6


class BlogPagination(PageNumberPagination):
    page_size = 5


class CommentPagination(PageNumberPagination):
    page_size = 3


class TourImagePagination(PageNumberPagination):
    page_size = 20


class CustomerPayerPagination(PageNumberPagination):
    page_size = 20
