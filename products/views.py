from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from products.models import Category
from products.serializers import CategorySerializer


class CategoryListAPIView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
