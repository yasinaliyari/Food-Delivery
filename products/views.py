from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet
from products.models import Category, Product
from products.permissions import IsSellerOrReadOnly
from products.serializers import CategorySerializer, ProductSerializer


class CategoryListAPIView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.select_related("category", "seller").all()
    serializer_class = ProductSerializer
    permission_classes = [IsSellerOrReadOnly]
