from rest_framework import serializers
from orders.models import OrderItem, Order
from products.models import Product


class OrderItemWriteSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.select_related("category", "seller").all(),
        source="product",
    )
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        product = attrs["product"]
        qty = attrs["quantity"]
        if product.stock < qty:
            raise serializers.ValidationError(
                f"Insufficient stock for '{product.name}'.Available: {product.stock}"
            )
        return attrs


class OrderItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    category = serializers.CharField(source="product.category.name", read_only=True)
    seller = serializers.CharField(source="product.seller.username", read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "category",
            "seller",
            "quantity",
            "price",
            "line_total",
        ]

    def get_line_total(self, obj):
        return obj.price * obj.quantity


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "status", "total_price", "created_at", "items"]
        read_only_fields = ["id", "user", "total_price", "created_at"]
